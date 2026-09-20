#!/usr/bin/env python3
"""Validate generated v1 STL meshes and print-bed envelopes."""

from __future__ import annotations

import glob
import json
import os
import sys

import trimesh

import geometry_model as G


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v1")

paths = sorted(glob.glob(os.path.join(OUT, "samsung_stand_v1_*.stl")))
if not paths:
    raise SystemExit("No v1 STL files found")

results = {}
failed = []

for path in paths:
    name = os.path.basename(path)
    mesh = trimesh.load(path, force="mesh", process=True)
    ext = mesh.extents
    info = {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_mm3": float(abs(mesh.volume)),
        "faces": int(len(mesh.faces)),
        "extents_mm": [round(float(v), 3) for v in ext],
        "bounds_mm": [
            [round(float(v), 3) for v in mesh.bounds[0]],
            [round(float(v), 3) for v in mesh.bounds[1]],
        ],
    }

    info["fits_core_one_l"] = bool(
        ext[0] <= G.PRINTER_X + 1e-6
        and ext[1] <= G.PRINTER_Y + 1e-6
        and ext[2] <= G.PRINTER_Z + 1e-6
    )
    info["positive_volume"] = info["volume_mm3"] > 1.0

    ok = (
        info["watertight"]
        and info["winding_consistent"]
        and info["positive_volume"]
        and info["fits_core_one_l"]
    )
    info["ok"] = ok
    if not ok:
        failed.append(name)
    results[name] = info

# Left/right base should be materially symmetric even if tessellation ordering differs.
left = results.get("samsung_stand_v1_base_left.stl")
right = results.get("samsung_stand_v1_base_right.stl")
mirror_check = {"ok": False}
if left and right:
    size_delta = [
        abs(a - b) for a, b in zip(left["extents_mm"], right["extents_mm"])
    ]
    volume_delta = abs(left["volume_mm3"] - right["volume_mm3"])
    volume_ref = max(left["volume_mm3"], right["volume_mm3"], 1.0)
    mirror_check = {
        "size_delta_mm": [round(v, 6) for v in size_delta],
        "volume_delta_mm3": round(volume_delta, 6),
        "relative_volume_delta": volume_delta / volume_ref,
        "ok": all(v <= 0.02 for v in size_delta)
        and volume_delta / volume_ref <= 1e-6,
    }
    if not mirror_check["ok"]:
        failed.append("left_right_base_symmetry")

report = {
    "version": "v1",
    "meshes": results,
    "left_right_symmetry": mirror_check,
    "failed": failed,
}

with open(os.path.join(OUT, "MESH_VALIDATION_v1.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("V1 mesh validation failed: " + ", ".join(failed))
