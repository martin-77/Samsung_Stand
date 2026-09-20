#!/usr/bin/env python3
"""Build v8: validated v7 structure with real assembled structural retainers.

v8 removes the legacy retention concept from the print list:
- no vertical base joint retainers below/through the Sounddeck plane;
- no loose C-clip around the pivot neck;
- no inaccessible v3 outer-guide lock tunnel.

Replacement:
- 4 transverse above-base snap pins for BASE<->CENTER;
- 2 transverse snap pins for ROTOR<->INNER_ARM;
- 2 longer transverse snap pins for INNER_ARM<->OUTER_GUIDE;
- 1 fixed pivot cross-pin inside a rotor counterbore.
"""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import
import MeshPart

import geometry_model as G
import v2_params as V2
import v3_params as V3
import v8_geometry as LG
import v8_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v8")
V7_STEP = os.path.join(ROOT, "cad", "v7", "STEP")
os.makedirs(OUT, exist_ok=True)


def load_step(name):
    path = os.path.join(V7_STEP, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing validated v7 STEP: " + path)

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
    if (
        shape.isNull()
        or not shape.isValid()
        or len(shape.Solids) != 1
        or shape.Volume <= 0
    ):
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def base_center_v8():
    sh = load_step("samsung_stand_v7_base_center")

    # Positive pivot retention post extension.
    sh = sh.fuse(LG.pivot_post_extension()).removeSplitter()
    require_single(sh, "BASE_CENTER_V8_EXTENDED_POST")
    sh = sh.cut(LG.pivot_post_tunnel()).removeSplitter()

    # Four horizontal joint locks, two on each side.
    for x in (-P.BASE_LOCK_X_ABS, +P.BASE_LOCK_X_ABS):
        for y in G.JOINT_Y_CENTERS:
            sh = sh.cut(LG.base_lock_tunnel(x, y)).removeSplitter()

    require_single(sh, "BASE_CENTER_V8")
    return sh


def side_base_v8(side):
    if side == "right":
        sh = load_step("samsung_stand_v7_base_right")
        x = +P.BASE_LOCK_X_ABS
    elif side == "left":
        sh = load_step("samsung_stand_v7_base_left")
        x = -P.BASE_LOCK_X_ABS
    else:
        raise ValueError(side)

    for y in G.JOINT_Y_CENTERS:
        sh = sh.cut(LG.base_lock_tunnel(x, y)).removeSplitter()

    require_single(sh, "BASE_" + side.upper() + "_V8")
    return sh


def rotor_v8():
    sh = load_step("samsung_stand_v7_rotor")
    sh = sh.cut(LG.rotor_counterbore()).removeSplitter()
    require_single(sh, "ROTOR_V8")
    return sh


def inner_arm_v8():
    sh = load_step("samsung_stand_v7_inner_arm")

    # Re-open the v3 outer-joint tunnel all the way through the 58 mm saddle.
    sh = sh.cut(
        LG.outer_lock_tunnel(V3.OUTER_LOCK_CENTER_X)
    ).removeSplitter()

    require_single(sh, "INNER_ARM_V8")
    return sh


def outer_guide_v8():
    sh = load_step("samsung_stand_v7_outer_guide")

    local_lock_x = V3.OUTER_LOCK_CENTER_X - V2.INNER_LENGTH
    sh = sh.cut(LG.outer_lock_tunnel(local_lock_x)).removeSplitter()

    require_single(sh, "OUTER_GUIDE_V8")
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
        LinearDeflection=0.06,
        AngularDeflection=0.20,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ": empty tessellation")
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "volume_mm3": round(float(shape.Volume), 3),
        "size_mm": [
            round(bb.XLength, 3),
            round(bb.YLength, 3),
            round(bb.ZLength, 3),
        ],
        "bbox_mm": [
            round(bb.XMin, 3),
            round(bb.XMax, 3),
            round(bb.YMin, 3),
            round(bb.YMax, 3),
            round(bb.ZMin, 3),
            round(bb.ZMax, 3),
        ],
        "facets": int(mesh.CountFacets),
    }


parts = {
    "samsung_stand_v8_base_center": base_center_v8(),
    "samsung_stand_v8_base_left": side_base_v8("left"),
    "samsung_stand_v8_base_right": side_base_v8("right"),
    "samsung_stand_v8_rotor": rotor_v8(),
    "samsung_stand_v8_inner_arm": inner_arm_v8(),
    "samsung_stand_v8_outer_guide": outer_guide_v8(),
    "samsung_stand_v8_saddle_insert_blank": load_step(
        "samsung_stand_v7_saddle_insert_blank"
    ),
    "samsung_stand_v8_detent_pin": load_step(
        "samsung_stand_v7_detent_pin"
    ),
    "samsung_stand_v8_detent_cassette_t18": load_step(
        "samsung_stand_v7_detent_cassette_t18"
    ),
    "samsung_stand_v8_detent_cassette_t22": load_step(
        "samsung_stand_v7_detent_cassette_t22"
    ),
    "samsung_stand_v8_detent_cassette_t26": load_step(
        "samsung_stand_v7_detent_cassette_t26"
    ),
    "samsung_stand_v8_center_wear_ring": load_step(
        "samsung_stand_v7_center_wear_ring"
    ),
    "samsung_stand_v8_track_wear_arc": load_step(
        "samsung_stand_v7_track_wear_arc"
    ),
    "samsung_stand_v8_joint_lock_pin": LG.joint_lock_pin(),
    "samsung_stand_v8_outer_lock_pin": LG.outer_lock_pin(),
    "samsung_stand_v8_pivot_lock_pin": LG.pivot_lock_pin(),
}

report = {
    "version": "v8",
    "upstream": "validated cad/v7/STEP",
    "retention_architecture": {
        "base_to_center": "4x transverse above-base snap pin",
        "rotor_to_inner": "2x compact transverse snap pin",
        "inner_to_outer": "2x long transverse snap pin through full saddle width",
        "pivot": "1x fixed cross-pin inside circular rotor counterbore",
        "legacy_vertical_base_retainer": "removed from print list",
        "legacy_pivot_c_clip": "removed from print list",
        "legacy_arm_lock_pin": "replaced",
    },
    "print_quantities": {
        "samsung_stand_v8_base_center": 1,
        "samsung_stand_v8_base_left": 1,
        "samsung_stand_v8_base_right": 1,
        "samsung_stand_v8_rotor": 1,
        "samsung_stand_v8_inner_arm": 2,
        "samsung_stand_v8_outer_guide": 2,
        "samsung_stand_v8_saddle_insert_blank": 2,
        "samsung_stand_v8_center_wear_ring": 1,
        "samsung_stand_v8_track_wear_arc": 2,
        "samsung_stand_v8_joint_lock_pin": 6,
        "samsung_stand_v8_outer_lock_pin": 2,
        "samsung_stand_v8_pivot_lock_pin": 1,
        "samsung_stand_v8_detent_pin": 2,
        "detent_cassette": "choose one of t18/t22/t26 after coupon calibration",
    },
    "parts": {},
}

for name, shape in parts.items():
    report["parts"][name] = export_shape(name, shape)

with open(
    os.path.join(OUT, "VALIDATION_v8_source.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
