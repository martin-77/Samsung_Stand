#!/usr/bin/env python3
"""Mesh and print-envelope validation for Samsung_Stand v3."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G
import v2_params as V2
import v3_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v3")

paths = sorted(glob.glob(os.path.join(OUT, "samsung_stand_v3_*.stl")))
if not paths:
    raise SystemExit("No v3 STL files found")

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
        "extents_mm": [round(float(x), 3) for x in ext],
        "bounds_mm": [
            [round(float(x), 3) for x in mesh.bounds[0]],
            [round(float(x), 3) for x in mesh.bounds[1]],
        ],
    }
    info["fits_core_one_l"] = bool(
        ext[0] <= G.PRINTER_X + 1e-6
        and ext[1] <= G.PRINTER_Y + 1e-6
        and ext[2] <= G.PRINTER_Z + 1e-6
    )
    info["ok"] = (
        info["watertight"]
        and info["winding_consistent"]
        and info["volume_mm3"] > 1.0
        and info["fits_core_one_l"]
    )
    if not info["ok"]:
        failed.append(name)
    results[name] = info

outer = results.get("samsung_stand_v3_outer_guide.stl")
outer_gate = {"ok": False}
if outer:
    x, y, z = outer["extents_mm"]
    outer_gate = {
        "actual_extents_mm": [x, y, z],
        "expected_max_mm": [
            P.OUTER_PRINT_LENGTH,
            P.OUTER_PRINT_WIDTH,
            P.OUTER_PRINT_HEIGHT,
        ],
        "ok": (
            x <= P.OUTER_PRINT_LENGTH + 0.1
            and y <= P.OUTER_PRINT_WIDTH + 0.1
            and z <= P.OUTER_PRINT_HEIGHT + 0.1
            and x <= G.PREFERRED_PART_XY
            and y <= G.PREFERRED_PART_XY
        ),
    }
    if not outer_gate["ok"]:
        failed.append("outer_guide_print_envelope")

inner = results.get("samsung_stand_v3_inner_arm.stl")
inner_gate = {"ok": False}
if inner:
    x, y, z = inner["extents_mm"]
    inner_gate = {
        "actual_extents_mm": [x, y, z],
        "ok": (
            x <= V2.INNER_PRINT_LENGTH + 0.1
            and y <= V2.INNER_PRINT_WIDTH + 0.1
            and z <= V2.INNER_PRINT_HEIGHT + 0.1
        ),
    }
    if not inner_gate["ok"]:
        failed.append("v3_inner_arm_print_envelope")

left = results.get("samsung_stand_v3_base_left.stl")
right = results.get("samsung_stand_v3_base_right.stl")
base_symmetry = {"ok": False}
if left and right:
    volume_delta = abs(left["volume_mm3"] - right["volume_mm3"])
    ref = max(left["volume_mm3"], right["volume_mm3"], 1.0)
    size_delta = [abs(a-b) for a,b in zip(left["extents_mm"], right["extents_mm"])]
    base_symmetry = {
        "size_delta_mm": size_delta,
        "relative_volume_delta": volume_delta/ref,
        "ok": all(v <= 0.03 for v in size_delta) and volume_delta/ref <= 2e-6,
    }
    if not base_symmetry["ok"]:
        failed.append("v3_base_symmetry")

report = {
    "version": "v3",
    "meshes": results,
    "outer_guide_gate": outer_gate,
    "inner_arm_gate": inner_gate,
    "base_symmetry": base_symmetry,
    "guide_contact_status": (
        "placeholder 60 mm inside channel; final Samsung side-contact fit "
        "is intentionally not claimed"
    ),
    "failed": failed,
}

with open(os.path.join(OUT, "MESH_VALIDATION_v3.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("V3 mesh validation failed: " + ", ".join(failed))
