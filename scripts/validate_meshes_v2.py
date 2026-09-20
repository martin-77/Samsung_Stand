#!/usr/bin/env python3
"""Validate generated v2 meshes and the mirrored side/base geometry."""

from __future__ import annotations

import glob
import json
import os
import sys

import trimesh

import geometry_model as G
import v2_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v2")

paths = sorted(glob.glob(os.path.join(OUT, "samsung_stand_v2_*.stl")))
if not paths:
    raise SystemExit("No v2 STL files found")

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
    info["ok"] = (
        info["watertight"]
        and info["winding_consistent"]
        and info["positive_volume"]
        and info["fits_core_one_l"]
    )
    if not info["ok"]:
        failed.append(name)
    results[name] = info

# Fixed side modules must remain exact mirrored structural equivalents.
left = results.get("samsung_stand_v2_base_left.stl")
right = results.get("samsung_stand_v2_base_right.stl")
side_symmetry = {"ok": False}
if left and right:
    size_delta = [abs(a - b) for a, b in zip(left["extents_mm"], right["extents_mm"])]
    volume_delta = abs(left["volume_mm3"] - right["volume_mm3"])
    volume_ref = max(left["volume_mm3"], right["volume_mm3"], 1.0)
    side_symmetry = {
        "size_delta_mm": [round(v, 6) for v in size_delta],
        "volume_delta_mm3": round(volume_delta, 6),
        "relative_volume_delta": volume_delta / volume_ref,
        "ok": all(v <= 0.03 for v in size_delta)
        and volume_delta / volume_ref <= 2e-6,
    }
    if not side_symmetry["ok"]:
        failed.append("left_right_base_track_symmetry")

# The universal inner arm is deliberately printed once and used on both sides.
inner = results.get("samsung_stand_v2_inner_arm.stl")
inner_gate = {"ok": False}
if inner:
    x, y, z = inner["extents_mm"]
    inner_gate = {
        "actual_extents_mm": [x, y, z],
        "declared_print_envelope_mm": [
            P.INNER_PRINT_LENGTH,
            P.INNER_PRINT_WIDTH,
            P.INNER_PRINT_HEIGHT,
        ],
        "ok": (
            x <= P.INNER_PRINT_LENGTH + 0.1
            and y <= P.INNER_PRINT_WIDTH + 0.1
            and z <= P.INNER_TOTAL_HEIGHT + 1.1
            and x <= G.PREFERRED_PART_XY
            and y <= G.PREFERRED_PART_XY
        ),
    }
    if not inner_gate["ok"]:
        failed.append("inner_arm_print_envelope")

# The snap lock must lie flat: no negative Z and small build height.
pin = results.get("samsung_stand_v2_arm_lock_pin.stl")
lock_pin_gate = {"ok": False}
if pin:
    zmin = pin["bounds_mm"][0][2]
    zmax = pin["bounds_mm"][1][2]
    lock_pin_gate = {
        "z_range_mm": [zmin, zmax],
        "ok": zmin >= -0.01 and zmax <= 7.0,
    }
    if not lock_pin_gate["ok"]:
        failed.append("arm_lock_pin_flat_print_gate")

# The blank saddle insert is intentionally a calibration cartridge, not final
# Samsung-contact geometry. Its mesh nevertheless must fit the declared pocket.
insert = results.get("samsung_stand_v2_saddle_insert_blank.stl")
insert_gate = {"ok": False}
if insert:
    x, y, z = insert["extents_mm"]
    insert_gate = {
        "actual_extents_mm": [x, y, z],
        "pocket_mm": [
            P.SADDLE_POCKET_LENGTH,
            P.SADDLE_POCKET_WIDTH,
            P.INNER_TOTAL_HEIGHT - P.SADDLE_POCKET_FLOOR,
        ],
        "ok": (
            x < P.SADDLE_POCKET_LENGTH
            and y < P.SADDLE_POCKET_WIDTH
            and z <= P.SADDLE_INSERT_HEIGHT + 0.1
        ),
    }
    if not insert_gate["ok"]:
        failed.append("saddle_insert_fit_gate")

report = {
    "version": "v2",
    "meshes": results,
    "left_right_base_track_symmetry": side_symmetry,
    "inner_arm_gate": inner_gate,
    "arm_lock_pin_gate": lock_pin_gate,
    "saddle_insert_gate": insert_gate,
    "contact_profile_status": (
        "blank calibration insert only; final Samsung arm contact profile "
        "requires physical arm cross-section measurement"
    ),
    "failed": failed,
}

with open(os.path.join(OUT, "MESH_VALIDATION_v2.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("V2 mesh validation failed: " + ", ".join(failed))
