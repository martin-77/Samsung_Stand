#!/usr/bin/env python3
"""Validate generated fit-coupon STL meshes."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import fit_coupon_params as C


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_fit_coupons")

paths = sorted(glob.glob(os.path.join(OUT, "fit_*.stl")))
expected = len(C.FAMILIES) * (1 + len(C.CLEARANCES_MM))
failed = []
results = {}

if len(paths) != expected:
    failed.append(f"expected {expected} STL files, found {len(paths)}")

for path in paths:
    name = os.path.basename(path)
    mesh = trimesh.load(path, force="mesh", process=True)
    ext = mesh.extents
    bounds = mesh.bounds
    info = {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        "volume_mm3": float(abs(mesh.volume)),
        "extents_mm": [round(float(x), 3) for x in ext],
        "z_min_mm": round(float(bounds[0][2]), 3),
        "fits_100x100_coupon_plate": bool(
            ext[0] <= 100.0 and ext[1] <= 100.0 and ext[2] <= 40.0
        ),
    }
    info["ok"] = (
        info["watertight"]
        and info["winding_consistent"]
        and info["volume_mm3"] > 1.0
        and info["fits_100x100_coupon_plate"]
        and info["z_min_mm"] >= -0.01
    )
    if not info["ok"]:
        failed.append(name)
    results[name] = info

report = {
    "expected_count": expected,
    "meshes": results,
    "failed": failed,
}

with open(
    os.path.join(OUT, "FIT_COUPON_MESH_VALIDATION.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("FIT COUPON MESH VALIDATION FAILED: " + ", ".join(failed))
