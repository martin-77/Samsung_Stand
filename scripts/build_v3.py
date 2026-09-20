#!/usr/bin/env python3
"""Build v3: validated v2 load path plus modular outer guide rails."""

from __future__ import annotations

import json
import math
import os

import FreeCAD as App
import Import
import MeshPart
import Part

import geometry_model as G
import v2_params as V2
import v3_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v3")
V2_STEP = os.path.join(ROOT, "cad", "v2", "STEP")
V1_STEP = os.path.join(ROOT, "cad", "v1", "STEP")
os.makedirs(OUT, exist_ok=True)


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def fuse_all(shapes):
    out = shapes[0]
    for sh in shapes[1:]:
        out = out.fuse(sh)
    return out.removeSplitter()


def require_single(shape, label):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def load_step(directory, name):
    path = os.path.join(directory, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing validated upstream STEP: " + path)
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
    sh = fuse_all(shapes)
    require_single(sh, "import " + name)
    return sh


def roof_prism_x(xmin, xmax, half_width, z_bottom, z_wall_top, z_apex):
    pts = [
        v(xmin, -half_width, z_bottom),
        v(xmin, +half_width, z_bottom),
        v(xmin, +half_width, z_wall_top),
        v(xmin, 0, z_apex),
        v(xmin, -half_width, z_wall_top),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(xmax - xmin, 0, 0))


def house_tunnel_y(x_center, y_length, x_half, z_bottom, z_wall_top, z_apex):
    y0 = -y_length / 2.0
    pts = [
        v(x_center - x_half, y0, z_bottom),
        v(x_center + x_half, y0, z_bottom),
        v(x_center + x_half, y0, z_wall_top),
        v(x_center, y0, z_apex),
        v(x_center - x_half, y0, z_wall_top),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, y_length, 0))


def inner_arm_v3():
    sh = load_step(V2_STEP, "samsung_stand_v2_inner_arm")

    cavity = roof_prism_x(
        P.OUTER_RECEIVER_START_X - P.OUTER_KEY_CLEARANCE,
        P.OUTER_RECEIVER_END_X,
        P.OUTER_KEY_HALF_WIDTH + P.OUTER_KEY_CLEARANCE,
        P.OUTER_RECEIVER_CAVITY_BOTTOM_Z,
        P.OUTER_RECEIVER_CAVITY_WALL_TOP_Z,
        P.OUTER_RECEIVER_CAVITY_APEX_Z,
    )
    lock_tunnel = house_tunnel_y(
        P.OUTER_LOCK_CENTER_X,
        P.OUTER_LOCK_HOLE_LENGTH,
        P.OUTER_LOCK_HOLE_WIDTH / 2.0,
        P.OUTER_LOCK_HOLE_BOTTOM_Z,
        P.OUTER_LOCK_HOLE_WALL_TOP_Z,
        P.OUTER_LOCK_HOLE_APEX_Z,
    )

    sh = sh.cut(cavity).cut(lock_tunnel).removeSplitter()
    require_single(sh, "INNER_ARM_V3")
    return sh


def outer_guide():
    floor = Part.makeBox(
        P.OUTER_VISIBLE_LENGTH,
        P.OUTER_BODY_WIDTH,
        P.OUTER_FLOOR_THICKNESS,
        v(0, -P.OUTER_BODY_WIDTH / 2.0, 0),
    )

    left_wall = Part.makeBox(
        P.OUTER_VISIBLE_LENGTH,
        P.OUTER_WALL_THICKNESS,
        P.OUTER_WALL_HEIGHT,
        v(0, -P.OUTER_BODY_WIDTH / 2.0, 0),
    )
    right_wall = Part.makeBox(
        P.OUTER_VISIBLE_LENGTH,
        P.OUTER_WALL_THICKNESS,
        P.OUTER_WALL_HEIGHT,
        v(
            0,
            P.OUTER_BODY_WIDTH / 2.0 - P.OUTER_WALL_THICKNESS,
            0,
        ),
    )

    # Short cross-ties stiffen the U-section without putting a normal support
    # surface near the reconstructed Samsung foot underside.
    root_tie = Part.makeBox(
        P.OUTER_ROOT_TIE_LENGTH,
        P.OUTER_BODY_WIDTH,
        P.OUTER_TIE_HEIGHT,
        v(0, -P.OUTER_BODY_WIDTH / 2.0, 0),
    )
    tip_tie = Part.makeBox(
        P.OUTER_TIP_TIE_LENGTH,
        P.OUTER_BODY_WIDTH,
        P.OUTER_TIE_HEIGHT,
        v(
            P.OUTER_VISIBLE_LENGTH - P.OUTER_TIP_TIE_LENGTH,
            -P.OUTER_BODY_WIDTH / 2.0,
            0,
        ),
    )

    male = roof_prism_x(
        -P.OUTER_KEY_OVERLAP,
        P.OUTER_KEY_EMBED,
        P.OUTER_KEY_HALF_WIDTH,
        P.OUTER_KEY_BOTTOM_Z,
        P.OUTER_KEY_WALL_TOP_Z,
        P.OUTER_KEY_APEX_Z,
    )

    local_lock_x = P.OUTER_LOCK_CENTER_X - V2.INNER_LENGTH
    lock_tunnel = house_tunnel_y(
        local_lock_x,
        P.OUTER_LOCK_HOLE_LENGTH,
        P.OUTER_LOCK_HOLE_WIDTH / 2.0,
        P.OUTER_LOCK_HOLE_BOTTOM_Z,
        P.OUTER_LOCK_HOLE_WALL_TOP_Z,
        P.OUTER_LOCK_HOLE_APEX_Z,
    )

    sh = fuse_all([floor, left_wall, right_wall, root_tie, tip_tie, male])
    sh = sh.cut(lock_tunnel).removeSplitter()
    require_single(sh, "OUTER_GUIDE")
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
    "samsung_stand_v3_base_center": load_step(V2_STEP, "samsung_stand_v2_base_center"),
    "samsung_stand_v3_base_left": load_step(V2_STEP, "samsung_stand_v2_base_left"),
    "samsung_stand_v3_base_right": load_step(V2_STEP, "samsung_stand_v2_base_right"),
    "samsung_stand_v3_rotor": load_step(V2_STEP, "samsung_stand_v2_rotor"),
    "samsung_stand_v3_inner_arm": inner_arm_v3(),
    "samsung_stand_v3_outer_guide": outer_guide(),
    "samsung_stand_v3_saddle_insert_blank": load_step(
        V2_STEP, "samsung_stand_v2_saddle_insert_blank"
    ),
    "samsung_stand_v3_arm_lock_pin": load_step(
        V2_STEP, "samsung_stand_v2_arm_lock_pin"
    ),
    "samsung_stand_v3_base_joint_retainer": load_step(
        V1_STEP, "samsung_stand_v1_joint_retainer"
    ),
    "samsung_stand_v3_pivot_clip": load_step(
        V1_STEP, "samsung_stand_v1_pivot_clip"
    ),
}

report = {
    "version": "v3",
    "freecad_version": App.Version(),
    "upstream": {
        "load_path": "validated cad/v2/STEP",
        "small_retainers": "validated cad/v1/STEP",
    },
    "parameters": {
        "outer_start_radius_mm": P.OUTER_R0,
        "outer_visible_length_mm": P.OUTER_VISIBLE_LENGTH,
        "outer_tip_radius_mm": P.OUTER_TIP_RADIUS,
        "reconstructed_stand_tip_radius_mm": round(P.STAND_TIP_RADIUS, 3),
        "outer_channel_placeholder_width_mm": P.OUTER_CHANNEL_PLACEHOLDER_WIDTH,
        "normal_vertical_clearance_mm": P.NORMAL_VERTICAL_CLEARANCE_TO_GUIDE_FLOOR,
    },
    "print_quantities": {
        "samsung_stand_v3_base_center": 1,
        "samsung_stand_v3_base_left": 1,
        "samsung_stand_v3_base_right": 1,
        "samsung_stand_v3_rotor": 1,
        "samsung_stand_v3_inner_arm": 2,
        "samsung_stand_v3_outer_guide": 2,
        "samsung_stand_v3_saddle_insert_blank": 2,
        "samsung_stand_v3_arm_lock_pin": 4,
        "samsung_stand_v3_base_joint_retainer": 4,
        "samsung_stand_v3_pivot_clip": 1,
    },
    "parts": {},
}

for name, sh in parts.items():
    report["parts"][name] = export_shape(name, sh)

with open(os.path.join(OUT, "VALIDATION_v3_source.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
