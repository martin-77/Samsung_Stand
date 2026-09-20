#!/usr/bin/env python3
"""Assembly validation for measurement-driven v6 contact parts."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import v2_params as V2
import v3_params as V3


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V5_STEP = os.path.join(ROOT, "cad", "v5", "STEP")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(path):
    if not os.path.isfile(path):
        raise RuntimeError("Missing STEP: " + path)
    doc = App.newDocument("asm_" + os.path.basename(path).replace(".", "_"))
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = [
        obj.Shape.copy()
        for obj in doc.Objects
        if hasattr(obj, "Shape") and not obj.Shape.isNull()
    ]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No STEP shape: " + path)
    sh = shapes[0]
    for other in shapes[1:]:
        sh = sh.fuse(other)
    return sh.removeSplitter()


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def main(contact_dir: str = "build_v6_contacts"):
    inner = load_step(os.path.join(V5_STEP, "samsung_stand_v5_inner_arm.step"))
    guide = load_step(os.path.join(V5_STEP, "samsung_stand_v5_outer_guide.step"))

    failures = []
    result = {"version": "v6-contact-parts", "saddles": {}, "liners": {}}

    for side in ("left", "right"):
        saddle = load_step(
            os.path.join(
                contact_dir,
                f"samsung_stand_v6_saddle_insert_{side}.step",
            )
        )
        saddle.translate(v(V2.SADDLE_U, 0, V2.SADDLE_POCKET_FLOOR))

        vol = common_volume(saddle, inner)
        gap = distance(saddle, inner)
        bb = saddle.BoundBox

        row = {
            "common_volume_mm3": round(vol, 6),
            "distance_to_inner_arm_mm": round(gap, 6),
            "installed_bbox_mm": [
                round(bb.XMin,3), round(bb.XMax,3),
                round(bb.YMin,3), round(bb.YMax,3),
                round(bb.ZMin,3), round(bb.ZMax,3),
            ],
        }
        result["saddles"][side] = row

        if vol > 0.05:
            failures.append(f"{side} saddle penetrates INNER_ARM: {vol:.6f} mm3")
        if gap > 0.05:
            failures.append(f"{side} saddle is not seated in INNER_ARM pocket: {gap:.6f} mm")

    for side in ("left", "right"):
        liner = load_step(
            os.path.join(
                contact_dir,
                f"samsung_stand_v6_outer_liner_{side}.step",
            )
        )
        liner.translate(v(0, 0, V3.OUTER_FLOOR_THICKNESS))

        vol = common_volume(liner, guide)
        gap = distance(liner, guide)
        bb = liner.BoundBox

        row = {
            "common_volume_mm3": round(vol, 6),
            "distance_to_outer_guide_mm": round(gap, 6),
            "installed_bbox_mm": [
                round(bb.XMin,3), round(bb.XMax,3),
                round(bb.YMin,3), round(bb.YMax,3),
                round(bb.ZMin,3), round(bb.ZMax,3),
            ],
            "top_matches_guide_wall_mm": round(
                V3.OUTER_WALL_HEIGHT - bb.ZMax, 6
            ),
        }
        result["liners"][side] = row

        if vol > 0.05:
            failures.append(f"{side} liner penetrates OUTER_GUIDE: {vol:.6f} mm3")
        if gap > 0.05:
            failures.append(f"{side} liner is not seated in OUTER_GUIDE: {gap:.6f} mm")
        if bb.ZMax > V3.OUTER_WALL_HEIGHT + 0.05:
            failures.append(
                f"{side} liner exceeds OUTER_GUIDE wall height: zmax={bb.ZMax:.3f}"
            )

    result["failed"] = failures

    os.makedirs(contact_dir, exist_ok=True)
    with open(
        os.path.join(contact_dir, "ASSEMBLY_VALIDATION_v6_contacts.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit("V6 CONTACT ASSEMBLY FAILED: " + " | ".join(failures))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--contacts", default="build_v6_contacts")
    ns = ap.parse_args()
    main(ns.contacts)
