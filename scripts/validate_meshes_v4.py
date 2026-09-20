#!/usr/bin/env python3
"""Mesh and print-envelope validation for Samsung_Stand v4."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G
import v2_params as V2
import v3_params as V3


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v4")

paths = sorted(glob.glob(os.path.join(OUT, "samsung_stand_v4_*.stl")))
if not paths:
    raise SystemExit("No v4 STL files found")

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

rotor = results.get("samsung_stand_v4_rotor.stl")
rotor_gate = {"ok": False}
if rotor:
    x, y, z = rotor["extents_mm"]
    rotor_gate = {
        "actual_extents_mm": [x, y, z],
        "ok": (
            x <= G.PREFERRED_PART_XY
            and y <= G.PREFERRED_PART_XY
            and z <= G.PRINTER_Z
            and rotor["bounds_mm"][0][2] >= -0.01
        ),
    }
    if not rotor_gate["ok"]:
        failed.append("v4_rotor_print_envelope")

center = results.get("samsung_stand_v4_base_center.stl")
center_gate = {"ok": False}
if center:
    x, y, z = center["extents_mm"]
    center_gate = {
        "actual_extents_mm": [x, y, z],
        "ok": (
            x <= G.BASE_CENTER_WIDTH + 0.1
            and y <= G.BASE.depth + 0.1
            and x <= G.PREFERRED_PART_XY
            and y <= G.PREFERRED_PART_XY
        ),
    }
    if not center_gate["ok"]:
        failed.append("v4_center_print_envelope")

outer = results.get("samsung_stand_v4_outer_guide.stl")
outer_gate = {"ok": False}
if outer:
    x, y, z = outer["extents_mm"]
    outer_gate = {
        "actual_extents_mm": [x, y, z],
        "expected_max_mm": [
            V3.OUTER_PRINT_LENGTH,
            V3.OUTER_PRINT_WIDTH,
            V3.OUTER_PRINT_HEIGHT,
        ],
        "ok": (
            x <= V3.OUTER_PRINT_LENGTH + 0.1
            and y <= V3.OUTER_PRINT_WIDTH + 0.1
            and z <= V3.OUTER_PRINT_HEIGHT + 0.1
        ),
    }
    if not outer_gate["ok"]:
        failed.append("v4_outer_guide_print_envelope")

left = results.get("samsung_stand_v4_base_left.stl")
right = results.get("samsung_stand_v4_base_right.stl")
side_symmetry = {"ok": False}
if left and right:
    size_delta = [abs(a-b) for a,b in zip(left["extents_mm"], right["extents_mm"])]
    volume_delta = abs(left["volume_mm3"] - right["volume_mm3"])
    ref = max(left["volume_mm3"], right["volume_mm3"], 1.0)
    side_symmetry = {
        "size_delta_mm": [round(x, 6) for x in size_delta],
        "relative_volume_delta": volume_delta / ref,
        "ok": all(x <= 0.03 for x in size_delta) and volume_delta/ref <= 2e-6,
    }
    if not side_symmetry["ok"]:
        failed.append("v4_side_base_symmetry")

report = {
    "version": "v4",
    "meshes": results,
    "rotor_gate": rotor_gate,
    "center_gate": center_gate,
    "outer_guide_gate": outer_gate,
    "side_base_symmetry": side_symmetry,
    "failed": failed,
}

with open(os.path.join(OUT, "MESH_VALIDATION_v4.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("V4 mesh validation failed: " + ", ".join(failed))
