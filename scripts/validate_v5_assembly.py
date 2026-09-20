#!/usr/bin/env python3
"""Installed OCC validation for v5 zero-position detent calibration cassette."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import geometry_model as G
import v2_params as V2
import v5_geometry as DG
import v5_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v5")
CALIBRATION_THICKNESS = 2.2


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(name):
    path = os.path.join(OUT, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing generated v5 STEP: " + path)
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
    sh = load_step("samsung_stand_v5_rotor")
    sh.translate(v(0, 0, V2.ROTOR_INSTALL_Z))
    sh.rotate(v(G.PIVOT.x, G.PIVOT.y, 0), v(0, 0, 1), angle_deg)
    return sh


def main():
    center = load_step("samsung_stand_v5_base_center")
    body = DG.install_cassette(
        DG.detent_cassette_body_shape(CALIBRATION_THICKNESS)
    )
    nose = DG.install_cassette(DG.detent_nose_shape())
    cassette = DG.install_cassette(
        DG.detent_cassette_shape(CALIBRATION_THICKNESS)
    )

    failures = []

    # Cassette anchor must sit on the fixed mount without penetrating it.
    cassette_to_base_volume = common_volume(cassette, center)
    cassette_to_base_distance = distance(cassette, center)
    if cassette_to_base_volume > 0.05:
        failures.append(
            f"cassette/base penetration {cassette_to_base_volume:.6f} mm3"
        )
    if cassette_to_base_distance > 0.05:
        failures.append(
            f"cassette not seated on mount: gap {cassette_to_base_distance:.6f} mm"
        )

    # At 0 deg the relaxed nose sits in the V-notch with a small deliberate
    # clearance. No spring deflection is required at the exact center position.
    rotor_zero = installed_rotor(0.0)
    center_nose_gap = distance(nose, rotor_zero)
    center_nose_volume = common_volume(nose, rotor_zero)
    if not (0.05 <= center_nose_gap <= 0.25):
        failures.append(
            f"zero-detent nose clearance {center_nose_gap:.6f} mm outside target"
        )
    if center_nose_volume > 0.05:
        failures.append(
            f"zero-detent nose penetrates track {center_nose_volume:.6f} mm3"
        )

    # The spring body/anchor must never become a collision surface. Only the
    # nose is allowed to geometrically interfere away from the center notch.
    body_sweep = {}
    nose_sweep = {}
    for angle in (-15.0, -7.5, 0.0, 7.5, 15.0):
        rotor = installed_rotor(angle)
        body_vol = common_volume(body, rotor)
        body_gap = distance(body, rotor)
        nose_vol = common_volume(nose, rotor)
        nose_gap = distance(nose, rotor)

        body_sweep[f"{angle:+.1f}"] = {
            "distance_mm": round(body_gap, 6),
            "common_volume_mm3": round(body_vol, 6),
        }
        nose_sweep[f"{angle:+.1f}"] = {
            "distance_mm": round(nose_gap, 6),
            "common_volume_mm3": round(nose_vol, 6),
        }

        if body_vol > 0.05:
            failures.append(
                f"{angle:+.1f} deg detent spring body hits rotor: {body_vol:.6f} mm3"
            )

        if angle != 0.0 and nose_vol <= 0.05:
            failures.append(
                f"{angle:+.1f} deg nose does not engage normal cam surface"
            )

    # Rigid nose interference should be symmetric. In the physical part this
    # interference is taken up by in-plane spring deflection.
    neg = nose_sweep["-15.0"]["common_volume_mm3"]
    pos = nose_sweep["+15.0"]["common_volume_mm3"]
    nose_symmetry = abs(neg - pos) / max(abs(neg), abs(pos), 1.0)
    if nose_symmetry > 0.03:
        failures.append(
            f"detent cam symmetry relative delta {nose_symmetry:.6f}"
        )

    # Re-prove the v4 positive mechanical stop after adding the v5 rotor track
    # and fixed cassette mount.
    stop_behavior = {}
    for angle in (-15.5, -15.0, -14.0, 0.0, 14.0, 15.0, 15.5):
        rotor = installed_rotor(angle)
        vol = common_volume(rotor, center)
        stop_behavior[f"{angle:+.1f}"] = round(vol, 6)

    for angle in (-14.0, 0.0, 14.0, -15.0, 15.0):
        vol = stop_behavior[f"{angle:+.1f}"]
        if vol > 0.10:
            failures.append(
                f"v5 changed pre-stop/stop contact at {angle:+.1f} deg: {vol:.6f} mm3"
            )
    for angle in (-15.5, 15.5):
        vol = stop_behavior[f"{angle:+.1f}"]
        if vol < 1.0:
            failures.append(
                f"v5 lost positive stop beyond target at {angle:+.1f} deg"
            )

    report = {
        "version": "v5",
        "calibration_variant_thickness_mm": CALIBRATION_THICKNESS,
        "cassette_to_base": {
            "distance_mm": round(cassette_to_base_distance, 6),
            "common_volume_mm3": round(cassette_to_base_volume, 6),
        },
        "zero_detent": {
            "nose_distance_mm": round(center_nose_gap, 6),
            "nose_common_volume_mm3": round(center_nose_volume, 6),
        },
        "spring_body_sweep": body_sweep,
        "relaxed_nose_sweep": nose_sweep,
        "relaxed_nose_symmetry_relative_delta": round(nose_symmetry, 8),
        "v4_stop_recheck_common_volumes_mm3": stop_behavior,
        "interpretation": {
            "zero": "relaxed nose is in the V-notch with small positive clearance",
            "off_zero": (
                "rigid nose interference is intentional and represents the "
                "in-plane spring deflection demand"
            ),
            "spring_body": "must remain collision-free through full sweep",
            "force": "not validated by OCC; physical coupon selection remains required",
        },
        "failed": failures,
    }

    with open(
        os.path.join(OUT, "ASSEMBLY_VALIDATION_v5.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit("V5 ASSEMBLY VALIDATION FAILED: " + " | ".join(failures))


if __name__ == "__main__":
    main()
