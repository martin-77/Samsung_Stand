#!/usr/bin/env python3
"""Installed OCC validation for v4 positive mechanical swivel stops."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import geometry_model as G
import v2_params as V2
import v3_params as V3
import v4_geometry as SG
import v4_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v4")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(name):
    path = os.path.join(OUT, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing generated v4 STEP: " + path)
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


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def installed_rotor(angle_deg):
    sh = load_step("samsung_stand_v4_rotor")
    sh.translate(v(0, 0, V2.ROTOR_INSTALL_Z))
    sh.rotate(v(G.PIVOT.x, G.PIVOT.y, 0), v(0, 0, 1), angle_deg)
    return sh


def installed_inner(angle_deg, side):
    base_angle = V2.RIGHT_ARM_ANGLE_DEG if side == "right" else V2.LEFT_ARM_ANGLE_DEG
    sh = load_step("samsung_stand_v4_inner_arm")
    sh.translate(v(V2.INNER_R0, 0, 0))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), base_angle + angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, V2.TRACK_TOP_Z))
    return sh


def installed_outer(angle_deg, side):
    base_angle = V2.RIGHT_ARM_ANGLE_DEG if side == "right" else V2.LEFT_ARM_ANGLE_DEG
    sh = load_step("samsung_stand_v4_outer_guide")
    sh.translate(v(V3.OUTER_R0, 0, 0))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), base_angle + angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, V2.TRACK_TOP_Z))
    return sh


def installed_stop_probe(angle_deg):
    sh = SG.rotor_stop_shape()
    sh.translate(v(0, 0, V2.ROTOR_INSTALL_Z))
    return SG.rotate_about_pivot(sh, angle_deg)


def main():
    center = load_step("samsung_stand_v4_base_center")
    left_base = load_step("samsung_stand_v4_base_left")
    right_base = load_step("samsung_stand_v4_base_right")
    fixed_stop_pair = SG.fixed_stop_pair_shape()

    failures = []

    # Exact stop behavior. 14 deg must still be free, 15 deg must touch without
    # meaningful penetration, 15.5 deg must be physically blocked.
    stop_behavior = {}
    for angle in (-15.5, -15.0, -14.0, 0.0, 14.0, 15.0, 15.5):
        probe = installed_stop_probe(angle)
        d = distance(probe, fixed_stop_pair)
        vol = common_volume(probe, fixed_stop_pair)
        stop_behavior[f"{angle:+.1f}"] = {
            "distance_mm": round(d, 6),
            "common_volume_mm3": round(vol, 6),
        }

    for angle in (-14.0, 14.0):
        row = stop_behavior[f"{angle:+.1f}"]
        if row["distance_mm"] < 0.25 or row["common_volume_mm3"] > 0.05:
            failures.append(
                f"{angle:+.1f} deg: stop engages too early "
                f"(gap={row['distance_mm']:.6f}, volume={row['common_volume_mm3']:.6f})"
            )

    for angle in (-15.0, 15.0):
        row = stop_behavior[f"{angle:+.1f}"]
        if row["distance_mm"] > 0.05 or row["common_volume_mm3"] > 0.10:
            failures.append(
                f"{angle:+.1f} deg: target stop is not clean contact "
                f"(gap={row['distance_mm']:.6f}, volume={row['common_volume_mm3']:.6f})"
            )

    for angle in (-15.5, 15.5):
        row = stop_behavior[f"{angle:+.1f}"]
        if row["common_volume_mm3"] < 1.0:
            failures.append(
                f"{angle:+.1f} deg: positive stop does not block beyond target "
                f"(volume={row['common_volume_mm3']:.6f})"
            )

    # Full rotor must not collide with BASE_CENTER before the intended stop.
    full_rotor = {}
    for angle in (-14.0, -7.5, 0.0, 7.5, 14.0):
        rotor = installed_rotor(angle)
        vol = common_volume(rotor, center)
        full_rotor[f"{angle:+.1f}"] = round(vol, 6)
        if vol > 0.05:
            failures.append(
                f"rotor/base collision before stop at {angle:+.1f} deg: {vol:.6f} mm3"
            )

    # Complete rotating carriers: no penetration into fixed side/base geometry
    # across representative sweep positions. Surface contact on the glide track
    # is expected and therefore checked by volume, not by distance.
    sweep_intersections = {}
    for angle in (-15.0, -7.5, 0.0, 7.5, 15.0):
        right_inner = installed_inner(angle, "right")
        left_inner = installed_inner(angle, "left")
        right_outer = installed_outer(angle, "right")
        left_outer = installed_outer(angle, "left")

        checks = {
            "right_inner_vs_right_base": common_volume(right_inner, right_base),
            "left_inner_vs_left_base": common_volume(left_inner, left_base),
            "right_outer_vs_right_base": common_volume(right_outer, right_base),
            "left_outer_vs_left_base": common_volume(left_outer, left_base),
            "right_outer_vs_center": common_volume(right_outer, center),
            "left_outer_vs_center": common_volume(left_outer, center),
        }
        sweep_intersections[f"{angle:+.1f}"] = {
            k: round(val, 6) for k, val in checks.items()
        }
        for name, vol in checks.items():
            if vol > 0.05:
                failures.append(
                    f"{angle:+.1f} deg {name}: common volume {vol:.6f} mm3"
                )

    # Symmetry is a hard property of the end-stop pair.
    neg = stop_behavior["-15.5"]["common_volume_mm3"]
    pos = stop_behavior["+15.5"]["common_volume_mm3"]
    symmetry_rel = abs(neg - pos) / max(abs(neg), abs(pos), 1.0)
    if symmetry_rel > 0.01:
        failures.append(
            f"stop penetration asymmetry too high: relative delta {symmetry_rel:.6f}"
        )

    report = {
        "version": "v4",
        "stop_behavior": stop_behavior,
        "full_rotor_pre_stop_common_volumes_mm3": full_rotor,
        "rotating_carrier_sweep_common_volumes_mm3": sweep_intersections,
        "stop_symmetry_relative_delta": round(symmetry_rel, 8),
        "interpretation": {
            "14_deg": "must be free",
            "15_deg": "must be surface contact",
            "15_5_deg": "must produce solid interference and therefore be mechanically blocked",
            "detent": "not part of this gate; detent will not carry stop load",
        },
        "failed": failures,
    }

    with open(
        os.path.join(OUT, "ASSEMBLY_VALIDATION_v4.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("V4 ASSEMBLY VALIDATION FAILED: " + " | ".join(failures))


if __name__ == "__main__":
    main()
