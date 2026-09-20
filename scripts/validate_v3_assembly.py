#!/usr/bin/env python3
"""Installed OCC assembly validation for v3 outer guide rails."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import geometry_model as G
import v2_params as V2
import v3_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v3")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(name):
    path = os.path.join(OUT, name + ".step")
    doc = App.newDocument("asm_" + name)
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


def install_radial(shape, radius, angle_deg, z):
    sh = shape.copy()
    sh.translate(v(radius, 0, 0))
    sh.rotate(v(0,0,0), v(0,0,1), angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, z))
    return sh


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def main():
    center = load_step("samsung_stand_v3_base_center")
    left_base = load_step("samsung_stand_v3_base_left")
    right_base = load_step("samsung_stand_v3_base_right")

    rotor = load_step("samsung_stand_v3_rotor")
    rotor.translate(v(0,0,V2.ROTOR_INSTALL_Z))

    inner_template = load_step("samsung_stand_v3_inner_arm")
    outer_template = load_step("samsung_stand_v3_outer_guide")

    right_inner = install_radial(
        inner_template, V2.INNER_R0, V2.RIGHT_ARM_ANGLE_DEG, V2.TRACK_TOP_Z
    )
    left_inner = install_radial(
        inner_template, V2.INNER_R0, V2.LEFT_ARM_ANGLE_DEG, V2.TRACK_TOP_Z
    )
    right_outer = install_radial(
        outer_template, P.OUTER_R0, V2.RIGHT_ARM_ANGLE_DEG, V2.TRACK_TOP_Z
    )
    left_outer = install_radial(
        outer_template, P.OUTER_R0, V2.LEFT_ARM_ANGLE_DEG, V2.TRACK_TOP_Z
    )

    pairs = {
        "right_outer_vs_right_inner": (right_outer, right_inner),
        "left_outer_vs_left_inner": (left_outer, left_inner),
        "right_outer_vs_right_base": (right_outer, right_base),
        "left_outer_vs_left_base": (left_outer, left_base),
        "right_outer_vs_center": (right_outer, center),
        "left_outer_vs_center": (left_outer, center),
        "right_outer_vs_rotor": (right_outer, rotor),
        "left_outer_vs_rotor": (left_outer, rotor),
        "right_outer_vs_left_outer": (right_outer, left_outer),
    }

    volumes = {name: common_volume(a,b) for name,(a,b) in pairs.items()}
    failures = [
        f"{name}: common volume {vol:.6f} mm3"
        for name,vol in volumes.items()
        if vol > 0.05
    ]

    # Joint parts should meet (surface distance zero) but the outer guides must
    # stay off every fixed-base load surface in normal geometry.
    joint_distances = {
        "right_outer_to_inner": distance(right_outer, right_inner),
        "left_outer_to_inner": distance(left_outer, left_inner),
    }
    for name,d in joint_distances.items():
        if d > 0.05:
            failures.append(f"{name}: disconnected joint gap {d:.6f} mm")

    fixed_clearances = {
        "right_outer_to_fixed_base": min(
            distance(right_outer, right_base), distance(right_outer, center)
        ),
        "left_outer_to_fixed_base": min(
            distance(left_outer, left_base), distance(left_outer, center)
        ),
    }
    for name,d in fixed_clearances.items():
        if d < 0.15:
            failures.append(
                f"{name}: only {d:.6f} mm; outer guide would become fixed-base support"
            )

    report = {
        "version": "v3",
        "common_volumes_mm3": {k: round(v,6) for k,v in volumes.items()},
        "joint_contact_distances_mm": {
            k: round(v,6) for k,v in joint_distances.items()
        },
        "outer_to_fixed_base_clearances_mm": {
            k: round(v,6) for k,v in fixed_clearances.items()
        },
        "load_path_note": (
            "OUTER_GUIDE is connected only to the rotating INNER_ARM and has "
            "positive clearance to the fixed base; it is lateral guidance, "
            "not a normal vertical support."
        ),
        "failed": failures,
    }

    with open(os.path.join(OUT, "ASSEMBLY_VALIDATION_v3.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("V3 ASSEMBLY VALIDATION FAILED: " + " | ".join(failures))


if __name__ == "__main__":
    main()
