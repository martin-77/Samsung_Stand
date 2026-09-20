#!/usr/bin/env python3
"""Mesh and print-envelope validation for Samsung_Stand v5."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G
import v5_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v5")

paths = sorted(glob.glob(os.path.join(OUT, "samsung_stand_v5_*.stl")))
if not paths:
    raise SystemExit("No v5 STL files found")

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

cassette_gates = {}
variant_volumes = []
for thickness in P.DETENT_SPRING_THICKNESSES:
    suffix = int(round(thickness * 10.0))
    name = f"samsung_stand_v5_detent_cassette_t{suffix}.stl"
    item = results.get(name)
    gate = {"ok": False}
    if item:
        x, y, z = item["extents_mm"]
        gate = {
            "thickness_mm": thickness,
            "actual_extents_mm": [x, y, z],
            "z_min_mm": item["bounds_mm"][0][2],
            "ok": (
                x <= 20.0
                and y <= 52.0
                and z <= P.DETENT_SPRING_HEIGHT + 0.1
                and item["bounds_mm"][0][2] >= -0.01
            ),
        }
        variant_volumes.append((thickness, item["volume_mm3"]))
        if not gate["ok"]:
            failed.append(name + "_flat_print_gate")
    cassette_gates[name] = gate

monotonic = all(
    variant_volumes[i][1] < variant_volumes[i + 1][1]
    for i in range(len(variant_volumes) - 1)
)
if len(variant_volumes) != len(P.DETENT_SPRING_THICKNESSES) or not monotonic:
    failed.append("detent_variant_volume_monotonicity")

pin = results.get("samsung_stand_v5_detent_pin.stl")
pin_gate = {"ok": False}
if pin:
    x, y, z = pin["extents_mm"]
    pin_gate = {
        "actual_extents_mm": [x, y, z],
        "ok": (
            x <= P.DETENT_PIN_HEAD_SIZE + 0.1
            and y <= P.DETENT_PIN_HEAD_SIZE + 0.1
            and z <= P.DETENT_PIN_SHAFT_HEIGHT + P.DETENT_PIN_HEAD_HEIGHT + 0.1
            and pin["bounds_mm"][0][2] >= -0.01
        ),
    }
    if not pin_gate["ok"]:
        failed.append("detent_pin_print_gate")

left = results.get("samsung_stand_v5_base_left.stl")
right = results.get("samsung_stand_v5_base_right.stl")
side_symmetry = {"ok": False}
if left and right:
    size_delta = [abs(a-b) for a,b in zip(left["extents_mm"], right["extents_mm"])]
    volume_delta = abs(left["volume_mm3"] - right["volume_mm3"])
    ref = max(left["volume_mm3"], right["volume_mm3"], 1.0)
    side_symmetry = {
        "size_delta_mm": [round(x, 6) for x in size_delta],
        "relative_volume_delta": volume_delta/ref,
        "ok": all(x <= 0.03 for x in size_delta) and volume_delta/ref <= 2e-6,
    }
    if not side_symmetry["ok"]:
        failed.append("v5_side_base_symmetry")

report = {
    "version": "v5",
    "meshes": results,
    "detent_cassette_gates": cassette_gates,
    "detent_variant_volumes": [
        [t, round(vol, 3)] for t, vol in variant_volumes
    ],
    "detent_variant_volume_monotonic": monotonic,
    "detent_pin_gate": pin_gate,
    "side_base_symmetry": side_symmetry,
    "failed": failed,
}

with open(os.path.join(OUT, "MESH_VALIDATION_v5.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
if failed:
    raise SystemExit("V5 mesh validation failed: " + ", ".join(failed))
