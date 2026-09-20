#!/usr/bin/env python3
"""Mesh/print validation for v8 retainer coupons."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_retainer_coupons")

paths = sorted(glob.glob(os.path.join(OUT, "retainer_coupon_*.stl")))
if not paths:
    raise SystemExit("No retainer coupon STL files found")

results = {}
failed = []

for path in paths:
    name = os.path.basename(path)
    m = trimesh.load(path, force="mesh", process=True)
    ext = m.extents
    info = {
        "watertight": bool(m.is_watertight),
        "winding_consistent": bool(m.is_winding_consistent),
        "volume_mm3": float(abs(m.volume)),
        "extents_mm": [round(float(x), 3) for x in ext],
        "bounds_mm": [
            [round(float(x), 3) for x in m.bounds[0]],
            [round(float(x), 3) for x in m.bounds[1]],
        ],
        "fits_core_one_l": bool(
            ext[0] <= G.PRINTER_X + 1e-6
            and ext[1] <= G.PRINTER_Y + 1e-6
            and ext[2] <= G.PRINTER_Z + 1e-6
        ),
    }
    info["ok"] = (
        info["watertight"]
        and info["winding_consistent"]
        and info["volume_mm3"] > 1.0
        and info["fits_core_one_l"]
        and info["bounds_mm"][0][2] >= -0.01
    )
    if not info["ok"]:
        failed.append(name)
    results[name] = info

report = {
    "version": "retainer-coupons",
    "meshes": results,
    "failed": failed,
}

with open(
    os.path.join(OUT, "RETAINER_COUPON_MESH_VALIDATION.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit(
        "RETAINER COUPON MESH VALIDATION FAILED: " + " | ".join(failed)
    )
