#!/usr/bin/env python3
"""Mesh validation for v6 measurement-driven contact parts."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G
import v2_params as V2
import v3_params as V3


def main(out_dir: str = "build_v6_contacts"):
    paths = sorted(glob.glob(os.path.join(out_dir, "samsung_stand_v6_*.stl")))
    if not paths:
        raise SystemExit("No v6 contact STL files found")

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
            "extents_mm": [round(float(x),3) for x in ext],
            "bounds_mm": [
                [round(float(x),3) for x in mesh.bounds[0]],
                [round(float(x),3) for x in mesh.bounds[1]],
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

    # Hard envelopes inherited from the receiving structural parts.
    for side in ("left", "right"):
        name = f"samsung_stand_v6_saddle_insert_{side}.stl"
        e = results[name]["extents_mm"]
        if e[0] > V2.SADDLE_INSERT_LENGTH + 0.1 or e[1] > V2.SADDLE_INSERT_WIDTH + 0.1:
            failed.append(name + ": exceeds saddle pocket XY envelope")

        name = f"samsung_stand_v6_outer_liner_{side}.stl"
        e = results[name]["extents_mm"]
        if e[0] > V3.OUTER_VISIBLE_LENGTH + 0.1:
            failed.append(name + ": exceeds outer guide length")
        if e[1] > V3.OUTER_CHANNEL_PLACEHOLDER_WIDTH + 0.1:
            failed.append(name + ": exceeds outer guide channel width")
        if e[2] > V3.OUTER_WALL_HEIGHT - V3.OUTER_FLOOR_THICKNESS + 0.1:
            failed.append(name + ": exceeds available liner height")

    report = {
        "version": "v6-contact-parts",
        "meshes": results,
        "failed": failed,
    }

    with open(
        os.path.join(out_dir, "MESH_VALIDATION_v6_contacts.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failed:
        raise SystemExit("V6 contact mesh validation failed: " + " | ".join(failed))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="build_v6_contacts")
    ns = ap.parse_args()
    main(ns.out)
