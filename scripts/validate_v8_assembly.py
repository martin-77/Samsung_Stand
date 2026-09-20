#!/usr/bin/env python3
"""Installed OCC validation for v8 structural retention."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import geometry_model as G
import v2_params as V2
import v3_params as V3
import v8_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v8")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(name):
    path = os.path.join(OUT, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing v8 STEP: " + path)

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


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def installed_rotor(swivel_deg=0.0, lift_mm=0.0):
    sh = load_step("samsung_stand_v8_rotor")
    sh.translate(v(0, 0, V2.ROTOR_INSTALL_Z + lift_mm))
    sh.rotate(
        v(G.PIVOT.x, G.PIVOT.y, 0),
        v(0, 0, 1),
        swivel_deg,
    )
    return sh


def installed_inner(side, swivel_deg=0.0):
    angle = (
        V2.RIGHT_ARM_ANGLE_DEG
        if side == "right"
        else V2.LEFT_ARM_ANGLE_DEG
    ) + swivel_deg

    sh = load_step("samsung_stand_v8_inner_arm")
    sh.translate(v(V2.INNER_R0, 0, 0))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, V2.TRACK_TOP_Z))
    return sh


def installed_outer(side, swivel_deg=0.0):
    angle = (
        V2.RIGHT_ARM_ANGLE_DEG
        if side == "right"
        else V2.LEFT_ARM_ANGLE_DEG
    ) + swivel_deg

    sh = load_step("samsung_stand_v8_outer_guide")
    sh.translate(v(V3.OUTER_R0, 0, 0))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, V2.TRACK_TOP_Z))
    return sh


def installed_base_pin(x_center, y_center):
    sh = load_step("samsung_stand_v8_joint_lock_pin")
    if y_center < 0:
        angle = 90.0
        y0 = y_center + P.BASE_LOCK_PIN_AXIS_START
    else:
        # Mirror the front pin rather than repeating the rear insertion
        # direction. This keeps both head/barb ends out of the asymmetric
        # center-base rib field.
        angle = -90.0
        y0 = y_center - P.BASE_LOCK_PIN_AXIS_START
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle)
    sh.translate(
        v(
            x_center,
            y0,
            P.BASE_LOCK_PIN_INSTALL_Z,
        )
    )
    return sh


def installed_inner_pin(side):
    angle = (
        V2.RIGHT_ARM_ANGLE_DEG
        if side == "right"
        else V2.LEFT_ARM_ANGLE_DEG
    )

    sh = load_step("samsung_stand_v8_joint_lock_pin")
    sh.rotate(v(0, 0, 0), v(0, 0, 1), 90.0)
    sh.translate(
        v(
            V2.ARM_RETAINER_RADIUS,
            -V2.ARM_LOCK_HOLE_TRANSVERSE_LENGTH / 2.0,
            V2.ROTOR_INSTALL_Z
            + V2.ARM_LOCK_HOLE_BOTTOM_Z_ROTOR
            + 0.25,
        )
    )
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, 0))
    return sh


def installed_outer_pin(side):
    angle = (
        V2.RIGHT_ARM_ANGLE_DEG
        if side == "right"
        else V2.LEFT_ARM_ANGLE_DEG
    )
    radius = V2.INNER_R0 + V3.OUTER_LOCK_CENTER_X

    sh = load_step("samsung_stand_v8_outer_lock_pin")
    sh.rotate(v(0, 0, 0), v(0, 0, 1), 90.0)
    sh.translate(
        v(
            radius,
            P.OUTER_PIN_INSTALL_AXIS_START,
            V2.TRACK_TOP_Z + P.OUTER_PIN_INSTALL_Z,
        )
    )
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, 0))
    return sh


def installed_pivot_pin():
    sh = load_step("samsung_stand_v8_pivot_lock_pin")
    sh.translate(
        v(
            G.PIVOT.x + P.PIVOT_PIN_INSTALL_X0,
            G.PIVOT.y,
            P.PIVOT_PIN_INSTALL_Z,
        )
    )
    return sh


def main():
    center = load_step("samsung_stand_v8_base_center")
    left_base = load_step("samsung_stand_v8_base_left")
    right_base = load_step("samsung_stand_v8_base_right")

    failures = []

    # ------------------------------------------------------------------
    # Base module assembly + four above-base pins.
    # ------------------------------------------------------------------
    base_join = {
        "center_left_common_volume_mm3": round(
            common_volume(center, left_base), 6
        ),
        "center_right_common_volume_mm3": round(
            common_volume(center, right_base), 6
        ),
        "center_left_distance_mm": round(distance(center, left_base), 6),
        "center_right_distance_mm": round(distance(center, right_base), 6),
    }
    if base_join["center_left_common_volume_mm3"] > 0.05:
        failures.append("BASE_LEFT penetrates BASE_CENTER")
    if base_join["center_right_common_volume_mm3"] > 0.05:
        failures.append("BASE_RIGHT penetrates BASE_CENTER")
    if base_join["center_left_distance_mm"] > 0.05:
        failures.append("BASE_LEFT disconnected from BASE_CENTER")
    if base_join["center_right_distance_mm"] > 0.05:
        failures.append("BASE_RIGHT disconnected from BASE_CENTER")

    base_pins = {}
    for side, x, side_base in (
        ("left", -P.BASE_LOCK_X_ABS, left_base),
        ("right", +P.BASE_LOCK_X_ABS, right_base),
    ):
        for y in G.JOINT_Y_CENTERS:
            pin = installed_base_pin(x, y)
            cv = common_volume(pin, center)
            sv = common_volume(pin, side_base)
            bb = pin.BoundBox
            key = f"{side}_{int(y):+d}"
            base_pins[key] = {
                "pin_center_common_volume_mm3": round(cv, 6),
                "pin_side_common_volume_mm3": round(sv, 6),
                "z_min_mm": round(bb.ZMin, 6),
                "z_max_mm": round(bb.ZMax, 6),
            }
            if cv > 0.05 or sv > 0.05:
                failures.append(
                    f"base pin {key} penetrates structural joint "
                    f"(center={cv:.6f}, side={sv:.6f})"
                )
            if bb.ZMin < -0.01:
                failures.append(
                    f"base pin {key} protrudes below Sounddeck plane"
                )

    # ------------------------------------------------------------------
    # Rotor -> INNER_ARM compact pins.
    # ------------------------------------------------------------------
    rotor = installed_rotor(0.0)
    inner_pins = {}
    inners = {
        "left": installed_inner("left"),
        "right": installed_inner("right"),
    }

    for side in ("left", "right"):
        pin = installed_inner_pin(side)
        pv_rotor = common_volume(pin, rotor)
        pv_inner = common_volume(pin, inners[side])
        inner_pins[side] = {
            "pin_rotor_common_volume_mm3": round(pv_rotor, 6),
            "pin_inner_common_volume_mm3": round(pv_inner, 6),
            "pin_z_min_mm": round(pin.BoundBox.ZMin, 6),
        }
        if pv_rotor > 0.05 or pv_inner > 0.05:
            failures.append(
                f"{side} rotor/inner pin penetration "
                f"(rotor={pv_rotor:.6f}, inner={pv_inner:.6f})"
            )

    # ------------------------------------------------------------------
    # INNER_ARM -> OUTER_GUIDE long pins. V8 explicitly re-opened the
    # previously inaccessible tunnel through the full saddle width.
    # ------------------------------------------------------------------
    outer_pins = {}
    outers = {
        "left": installed_outer("left"),
        "right": installed_outer("right"),
    }

    for side in ("left", "right"):
        pin = installed_outer_pin(side)
        pv_inner = common_volume(pin, inners[side])
        pv_outer = common_volume(pin, outers[side])
        pin_outer_gap = distance(pin, outers[side])
        outer_pins[side] = {
            "pin_inner_common_volume_mm3": round(pv_inner, 6),
            "pin_outer_common_volume_mm3": round(pv_outer, 6),
            "pin_outer_distance_mm": round(pin_outer_gap, 6),
            "pin_z_min_mm": round(pin.BoundBox.ZMin, 6),
        }
        if pv_inner > 0.05 or pv_outer > 0.05:
            failures.append(
                f"{side} inner/outer pin penetration "
                f"(inner={pv_inner:.6f}, outer={pv_outer:.6f})"
            )

    # ------------------------------------------------------------------
    # Positive pivot retention.
    # ------------------------------------------------------------------
    pivot_pin = installed_pivot_pin()
    pivot_pin_base_volume = common_volume(pivot_pin, center)
    pivot_rest = installed_rotor(0.0, 0.0)
    pivot_pin_rotor_rest_volume = common_volume(pivot_pin, pivot_rest)
    pivot_pin_rotor_rest_gap = distance(pivot_pin, pivot_rest)

    if pivot_pin_base_volume > 0.05:
        failures.append(
            f"pivot pin penetrates fixed post: "
            f"{pivot_pin_base_volume:.6f} mm3"
        )
    if pivot_pin_rotor_rest_volume > 0.05:
        failures.append(
            f"pivot pin penetrates rotor at rest: "
            f"{pivot_pin_rotor_rest_volume:.6f} mm3"
        )
    if not 0.45 <= pivot_pin_rotor_rest_gap <= 0.95:
        failures.append(
            f"pivot axial rest gap {pivot_pin_rotor_rest_gap:.6f} mm "
            "outside expected retention clearance"
        )

    pivot_rotation = {}
    for angle in (-15.0, -7.5, 0.0, 7.5, 15.0):
        rr = installed_rotor(angle, 0.0)
        vol = common_volume(pivot_pin, rr)
        gap = distance(pivot_pin, rr)
        pivot_rotation[f"{angle:+.1f}"] = {
            "pin_rotor_common_volume_mm3": round(vol, 6),
            "pin_rotor_distance_mm": round(gap, 6),
        }
        if vol > 0.05:
            failures.append(
                f"pivot pin blocks rotation at {angle:+.1f} deg: "
                f"{vol:.6f} mm3"
            )

    lift_behavior = {}
    for lift in (0.0, 0.5, 0.7, 1.0):
        rr = installed_rotor(0.0, lift)
        vol = common_volume(pivot_pin, rr)
        gap = distance(pivot_pin, rr)
        lift_behavior[f"{lift:.1f}"] = {
            "common_volume_mm3": round(vol, 6),
            "distance_mm": round(gap, 6),
        }

    if lift_behavior["0.5"]["common_volume_mm3"] > 0.05:
        failures.append("pivot retention engages before 0.5 mm lift")
    if lift_behavior["0.5"]["distance_mm"] > 0.30:
        failures.append(
            "pivot 0.5 mm lift did not approach retention shoulder"
        )
    if lift_behavior["1.0"]["common_volume_mm3"] < 1.0:
        failures.append(
            "pivot cross-pin does not positively block 1.0 mm rotor lift"
        )

    report = {
        "version": "v8",
        "base_module_joint": base_join,
        "base_lock_pins": base_pins,
        "rotor_inner_lock_pins": inner_pins,
        "inner_outer_lock_pins": outer_pins,
        "pivot_retention": {
            "pin_base_common_volume_mm3": round(
                pivot_pin_base_volume, 6
            ),
            "rest_pin_rotor_common_volume_mm3": round(
                pivot_pin_rotor_rest_volume, 6
            ),
            "rest_pin_rotor_distance_mm": round(
                pivot_pin_rotor_rest_gap, 6
            ),
            "rotation_sweep": pivot_rotation,
            "axial_lift_behavior": lift_behavior,
        },
        "legacy_retainer_status": {
            "vertical_base_retainer": "not used",
            "pivot_c_clip": "not used",
            "v2_arm_lock_pin": "not used",
        },
        "failed": failures,
    }

    with open(
        os.path.join(OUT, "ASSEMBLY_VALIDATION_v8.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(
            "V8 ASSEMBLY VALIDATION FAILED: " + " | ".join(failures)
        )


if __name__ == "__main__":
    main()
