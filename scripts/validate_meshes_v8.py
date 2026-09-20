#!/usr/bin/env python3
"""Mesh and print-envelope validation for Samsung_Stand v8."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v8")

paths = sorted(glob.glob(os.path.join(OUT, "samsung_stand_v8_*.stl")))
if not paths:
    raise SystemExit("No v8 STL files found")

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
        "faces": int(len(m.faces)),
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
    )

    if not info["ok"]:
        failed.append(name)
    results[name] = info

# Left/right bases must remain mirrored after new transverse tunnels.
left = results.get("samsung_stand_v8_base_left.stl")
right = results.get("samsung_stand_v8_base_right.stl")
base_symmetry = {"ok": False}
if left and right:
    size_delta = [
        abs(a - b)
        for a, b in zip(left["extents_mm"], right["extents_mm"])
    ]
    volume_delta = abs(left["volume_mm3"] - right["volume_mm3"])
    ref = max(left["volume_mm3"], right["volume_mm3"], 1.0)
    base_symmetry = {
        "size_delta_mm": [round(x, 6) for x in size_delta],
        "relative_volume_delta": volume_delta / ref,
        "ok": (
            all(x <= 0.03 for x in size_delta)
            and volume_delta / ref <= 2e-6
        ),
    }
    if not base_symmetry["ok"]:
        failed.append("v8_side_base_symmetry")

# All replacement retainers must print with their intended flat orientation and
# none may contain negative-Z geometry.
retainer_names = (
    "samsung_stand_v8_joint_lock_pin.stl",
    "samsung_stand_v8_outer_lock_pin.stl",
    "samsung_stand_v8_pivot_lock_pin.stl",
)
retainers = {}
for name in retainer_names:
    info = results.get(name)
    if not info:
        failed.append(name + ": missing")
        continue
    zmin = info["bounds_mm"][0][2]
    retainers[name] = {
        "z_min_mm": zmin,
        "extents_mm": info["extents_mm"],
        "ok": zmin >= -0.01,
    }
    if not retainers[name]["ok"]:
        failed.append(name + ": negative-Z print geometry")

# Legacy retainers must not leak into the new output namespace.
legacy_fragments = (
    "base_joint_retainer",
    "pivot_clip",
    "arm_lock_pin",
)
legacy_outputs = [
    name
    for name in results
    if any(fragment in name for fragment in legacy_fragments)
]
if legacy_outputs:
    failed.append(
        "legacy retainers still present: " + ", ".join(legacy_outputs)
    )

report = {
    "version": "v8",
    "meshes": results,
    "base_symmetry": base_symmetry,
    "replacement_retainer_gates": retainers,
    "legacy_retainer_outputs": legacy_outputs,
    "failed": failed,
}

with open(
    os.path.join(OUT, "MESH_VALIDATION_v8.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit(
        "V8 MESH VALIDATION FAILED: " + " | ".join(failed)
    )
