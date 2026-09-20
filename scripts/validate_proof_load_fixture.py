#!/usr/bin/env python3
"""Validate proof-load saddle pad against the current v8 INNER_ARM."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import v2_params as V2


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_proof_load_fixture")
V8_STEP = os.path.join(ROOT, "cad", "v8", "STEP")


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
        raise RuntimeError("No shape in " + path)
    sh = shapes[0]
    for other in shapes[1:]:
        sh = sh.fuse(other)
    return sh.removeSplitter()


def main():
    inner = load_step(os.path.join(V8_STEP, "samsung_stand_v8_inner_arm.step"))
    pad = load_step(os.path.join(OUT, "proof_load_saddle_pad.step"))

    pad.translate(v(V2.SADDLE_U, 0, V2.SADDLE_POCKET_FLOOR))

    common = float(pad.common(inner).Volume)
    gap = float(pad.distToShape(inner)[0])
    bb = pad.BoundBox

    failures = []
    if common > 0.05:
        failures.append(f"proof pad penetrates INNER_ARM: {common:.6f} mm3")
    if gap > 0.05:
        failures.append(f"proof pad not seated in INNER_ARM: gap {gap:.6f} mm")
    if bb.ZMax <= V2.INNER_TOTAL_HEIGHT + 1.0:
        failures.append(
            "proof pad does not stand sufficiently proud for isolated load application"
        )

    report = {
        "version": "proof-load-fixture",
        "pad_inner_arm_common_volume_mm3": round(common, 6),
        "pad_inner_arm_distance_mm": round(gap, 6),
        "installed_pad_bbox_mm": [
            round(bb.XMin, 3), round(bb.XMax, 3),
            round(bb.YMin, 3), round(bb.YMax, 3),
            round(bb.ZMin, 3), round(bb.ZMax, 3),
        ],
        "inner_arm_top_z_mm": V2.INNER_TOTAL_HEIGHT,
        "proud_height_mm": round(bb.ZMax - V2.INNER_TOTAL_HEIGHT, 3),
        "failed": failures,
    }

    with open(
        os.path.join(OUT, "PROOF_LOAD_ASSEMBLY_VALIDATION.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("PROOF LOAD FIXTURE VALIDATION FAILED: " + " | ".join(failures))


if __name__ == "__main__":
    main()
