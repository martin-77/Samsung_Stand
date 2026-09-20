#!/usr/bin/env python3
"""Build v5: validated v4 structure plus replaceable zero-detent cassette."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import
import MeshPart

import v5_geometry as DG
import v5_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v5")
V4_STEP = os.path.join(ROOT, "cad", "v4", "STEP")
os.makedirs(OUT, exist_ok=True)


def load_step(name):
    path = os.path.join(V4_STEP, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing validated v4 STEP: " + path)
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


def base_center_v5():
    base = load_step("samsung_stand_v4_base_center")
    mount = DG.detent_mount_shape()
    sh = base.fuse(mount).removeSplitter()
    # Blind locating-pin holes are cut after the platform is fused so legacy
    # floor material cannot close them.
    sh = sh.cut(DG.detent_mount_holes_shape()).removeSplitter()
    require_single(sh, "BASE_CENTER_V5")
    return sh


def rotor_v5():
    rotor = load_step("samsung_stand_v4_rotor")
    track = DG.rotor_detent_track_shape()
    sh = rotor.fuse(track).removeSplitter()
    require_single(sh, "ROTOR_V5")
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
    "samsung_stand_v5_base_center": base_center_v5(),
    "samsung_stand_v5_base_left": load_step("samsung_stand_v4_base_left"),
    "samsung_stand_v5_base_right": load_step("samsung_stand_v4_base_right"),
    "samsung_stand_v5_rotor": rotor_v5(),
    "samsung_stand_v5_inner_arm": load_step("samsung_stand_v4_inner_arm"),
    "samsung_stand_v5_outer_guide": load_step("samsung_stand_v4_outer_guide"),
    "samsung_stand_v5_saddle_insert_blank": load_step(
        "samsung_stand_v4_saddle_insert_blank"
    ),
    "samsung_stand_v5_arm_lock_pin": load_step("samsung_stand_v4_arm_lock_pin"),
    "samsung_stand_v5_base_joint_retainer": load_step(
        "samsung_stand_v4_base_joint_retainer"
    ),
    "samsung_stand_v5_pivot_clip": load_step("samsung_stand_v4_pivot_clip"),
    "samsung_stand_v5_detent_pin": DG.detent_pin_shape(),
}

for thickness in P.DETENT_SPRING_THICKNESSES:
    suffix = str(int(round(thickness * 10.0)))
    parts[f"samsung_stand_v5_detent_cassette_t{suffix}"] = (
        DG.detent_cassette_shape(thickness)
    )

report = {
    "version": "v5",
    "freecad_version": App.Version(),
    "upstream": "validated cad/v4/STEP",
    "detent_architecture": {
        "position": "zero only",
        "track": "flat rotor cam sector with shallow V-notch",
        "spring": "replaceable in-plane PETG cantilever cassette",
        "variants_mm": list(P.DETENT_SPRING_THICKNESSES),
        "retention": "two removable locating pins; detent loads are non-structural",
        "force_status": "calibration variants; not treated as measured PETG behavior",
    },
    "print_quantities": {
        "core_structure": "same as v4",
        "detent_cassette": "print one selected variant after calibration",
        "detent_pin": 2,
    },
    "parts": {},
}

for name, sh in parts.items():
    report["parts"][name] = export_shape(name, sh)

with open(os.path.join(OUT, "VALIDATION_v5_source.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
