#!/usr/bin/env python3
"""OCC-level installed-assembly checks for Samsung_Stand v2.

This validator is intentionally independent from the parameter-only gates. It
loads the actually generated STEP files, places them in installed coordinates,
and checks that intended support contacts are surface contacts rather than
interpenetrating solids.
"""

from __future__ import annotations

import json
import math
import os
import sys

import FreeCAD as App
import Import
import Part

import geometry_model as G
import v2_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v2")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(name):
    path = os.path.join(OUT, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing generated v2 STEP: " + path)
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
        raise RuntimeError("No shape in " + path)
    sh = shapes[0]
    for other in shapes[1:]:
        sh = sh.fuse(other)
    return sh.removeSplitter()


def installed_rotor():
    sh = load_step("samsung_stand_v2_rotor")
    sh.translate(v(0, 0, P.ROTOR_INSTALL_Z))
    return sh


def installed_inner(angle_deg):
    sh = load_step("samsung_stand_v2_inner_arm")
    sh.translate(v(P.INNER_R0, 0, 0))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, P.TRACK_TOP_Z))
    return sh


def installed_insert(angle_deg):
    sh = load_step("samsung_stand_v2_saddle_insert_blank")
    sh.translate(v(P.INNER_R0 + P.SADDLE_U, 0, P.TRACK_TOP_Z + P.SADDLE_POCKET_FLOOR))
    sh.rotate(v(G.PIVOT.x, G.PIVOT.y, 0), v(0, 0, 1), angle_deg)
    # Previous rotate call uses global pivot only for XY; correct to explicit
    # local-plan transform below by undoing/replacing if pivot is non-origin.
    # Rebuild deterministically:
    sh = load_step("samsung_stand_v2_saddle_insert_blank")
    sh.translate(v(P.INNER_R0 + P.SADDLE_U, 0, P.TRACK_TOP_Z + P.SADDLE_POCKET_FLOOR))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, 0))
    return sh


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def main():
    center = load_step("samsung_stand_v2_base_center")
    left_base = load_step("samsung_stand_v2_base_left")
    right_base = load_step("samsung_stand_v2_base_right")
    rotor = installed_rotor()
    left_arm = installed_inner(P.LEFT_ARM_ANGLE_DEG)
    right_arm = installed_inner(P.RIGHT_ARM_ANGLE_DEG)
    left_insert = installed_insert(P.LEFT_ARM_ANGLE_DEG)
    right_insert = installed_insert(P.RIGHT_ARM_ANGLE_DEG)

    pairs_no_intersection = {
        "rotor_vs_center": (rotor, center),
        "rotor_vs_left_base": (rotor, left_base),
        "rotor_vs_right_base": (rotor, right_base),
        "left_arm_vs_rotor": (left_arm, rotor),
        "right_arm_vs_rotor": (right_arm, rotor),
        "left_arm_vs_left_base": (left_arm, left_base),
        "right_arm_vs_right_base": (right_arm, right_base),
        "left_arm_vs_right_arm": (left_arm, right_arm),
        "left_insert_vs_left_arm": (left_insert, left_arm),
        "right_insert_vs_right_arm": (right_insert, right_arm),
    }

    intersections = {}
    failures = []
    for name, (a, b) in pairs_no_intersection.items():
        vol = common_volume(a, b)
        intersections[name] = round(vol, 6)
        if vol > 0.05:
            failures.append(f"{name}: common volume {vol:.6f} mm3")

    contacts = {
        # Broad annular rotor support on center base.
        "rotor_to_center": distance(rotor, center),
        # Root landing and outer glide track should each create zero-distance
        # support while remaining non-interpenetrating.
        "left_arm_to_rotor": distance(left_arm, rotor),
        "right_arm_to_rotor": distance(right_arm, rotor),
        "left_arm_to_left_track_base": distance(left_arm, left_base),
        "right_arm_to_right_track_base": distance(right_arm, right_base),
    }

    for name, d in contacts.items():
        if d > 0.05:
            failures.append(f"{name}: intended support gap {d:.6f} mm")

    # Contact insert should be located inside its pocket without penetrating the
    # carrier. A small explicit XY clearance is part of the design.
    insert_distances = {
        "left_insert_to_arm": distance(left_insert, left_arm),
        "right_insert_to_arm": distance(right_insert, right_arm),
    }
    for name, d in insert_distances.items():
        if d > 0.05:
            failures.append(f"{name}: insert not seated, gap {d:.6f} mm")

    report = {
        "version": "v2",
        "coordinate_note": (
            "rotor installed at z=10; universal inner arm installed at z=18 "
            "and rotated to reconstructed Samsung arm plan angles"
        ),
        "common_volumes_mm3": intersections,
        "intended_contact_distances_mm": {
            k: round(vv, 6) for k, vv in contacts.items()
        },
        "insert_seating_distances_mm": {
            k: round(vv, 6) for k, vv in insert_distances.items()
        },
        "contact_model": {
            "root_support": "flat landing, global z=18",
            "outer_support": "side glide track, top global z=18",
            "key_tongue": (
                f"{P.ARM_KEY_UNDERSIDE_CLEARANCE:.2f} mm underside clearance; "
                "form-lock/guidance rather than primary vertical bearing"
            ),
        },
        "failed": failures,
    }

    with open(os.path.join(OUT, "ASSEMBLY_VALIDATION_v2.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("V2 ASSEMBLY VALIDATION FAILED: " + " | ".join(failures))


if __name__ == "__main__":
    main()
