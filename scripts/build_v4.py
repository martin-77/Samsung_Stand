#!/usr/bin/env python3
"""Build v4: v3 outer guides plus positive mechanical +/-15 deg swivel stops."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import
import MeshPart

import v4_geometry as SG


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v4")
V3_STEP = os.path.join(ROOT, "cad", "v3", "STEP")
os.makedirs(OUT, exist_ok=True)


def load_step(name):
    path = os.path.join(V3_STEP, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing validated v3 STEP: " + path)
    doc = App.newDocument("import_" + name)
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = [
        obj.Shape.copy()
        for obj in doc.Objects
        if hasattr(obj, "Shape") and not obj.Shape.isNull()
    ]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No shape imported from " + path)
    sh = shapes[0]
    for other in shapes[1:]:
        sh = sh.fuse(other)
    return sh.removeSplitter()


def require_single(shape, label):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def base_center_v4():
    base = load_step("samsung_stand_v3_base_center")
    clearance = SG.stop_sweep_clearance_shape()
    base = base.cut(clearance).removeSplitter()
    require_single(base, "BASE_CENTER_V4_CLEARANCED")

    towers = SG.fixed_stop_pair_shape()
    sh = base.fuse(towers).removeSplitter()
    require_single(sh, "BASE_CENTER_V4")
    return sh


def side_base_v4(side):
    if side == "right":
        base = load_step("samsung_stand_v3_base_right")
    elif side == "left":
        base = load_step("samsung_stand_v3_base_left")
    else:
        raise ValueError(side)

    clearance = SG.arm_sweep_clearance_shape(side)
    sh = base.cut(clearance).removeSplitter()
    require_single(sh, "BASE_" + side.upper() + "_V4")
    return sh


def rotor_v4():
    rotor = load_step("samsung_stand_v3_rotor")
    stop = SG.rotor_stop_shape()
    sh = rotor.fuse(stop).removeSplitter()
    require_single(sh, "ROTOR_V4")
    return sh


def export_shape(name, shape):
    require_single(shape, name)

    step = os.path.join(OUT, name + ".step")
    fcstd = os.path.join(OUT, name + ".FCStd")
    stl = os.path.join(OUT, name + ".stl")

    shape.exportStep(step)

    doc = App.newDocument("export_" + name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape.copy()
    doc.recompute()
    doc.saveAs(fcstd)
    App.closeDocument(doc.Name)

    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=0.08,
        AngularDeflection=0.25,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ": empty tessellation")
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "volume_mm3": round(float(shape.Volume), 3),
        "bbox_mm": [
            round(bb.XMin, 3), round(bb.XMax, 3),
            round(bb.YMin, 3), round(bb.YMax, 3),
            round(bb.ZMin, 3), round(bb.ZMax, 3),
        ],
        "size_mm": [
            round(bb.XLength, 3),
            round(bb.YLength, 3),
            round(bb.ZLength, 3),
        ],
        "facets": int(mesh.CountFacets),
    }


parts = {
    "samsung_stand_v4_base_center": base_center_v4(),
    "samsung_stand_v4_base_left": side_base_v4("left"),
    "samsung_stand_v4_base_right": side_base_v4("right"),
    "samsung_stand_v4_rotor": rotor_v4(),
    "samsung_stand_v4_inner_arm": load_step("samsung_stand_v3_inner_arm"),
    "samsung_stand_v4_outer_guide": load_step("samsung_stand_v3_outer_guide"),
    "samsung_stand_v4_saddle_insert_blank": load_step(
        "samsung_stand_v3_saddle_insert_blank"
    ),
    "samsung_stand_v4_arm_lock_pin": load_step("samsung_stand_v3_arm_lock_pin"),
    "samsung_stand_v4_base_joint_retainer": load_step(
        "samsung_stand_v3_base_joint_retainer"
    ),
    "samsung_stand_v4_pivot_clip": load_step("samsung_stand_v3_pivot_clip"),
}

report = {
    "version": "v4",
    "freecad_version": App.Version(),
    "upstream": "validated cad/v3/STEP",
    "stop_architecture": {
        "type": "positive mechanical end stop",
        "target_deg": 15.0,
        "rotor_stop": "radial spoke + broad tab",
        "fixed_stop": "two broad towers fused to BASE_CENTER",
        "detent_status": "not yet added; stop is structural, detent will be positional only",
    },
    "print_quantities": {
        "samsung_stand_v4_base_center": 1,
        "samsung_stand_v4_base_left": 1,
        "samsung_stand_v4_base_right": 1,
        "samsung_stand_v4_rotor": 1,
        "samsung_stand_v4_inner_arm": 2,
        "samsung_stand_v4_outer_guide": 2,
        "samsung_stand_v4_saddle_insert_blank": 2,
        "samsung_stand_v4_arm_lock_pin": 4,
        "samsung_stand_v4_base_joint_retainer": 4,
        "samsung_stand_v4_pivot_clip": 1,
    },
    "parts": {},
}

for name, sh in parts.items():
    report["parts"][name] = export_shape(name, sh)

with open(os.path.join(OUT, "VALIDATION_v4_source.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
