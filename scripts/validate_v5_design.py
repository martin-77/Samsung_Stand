#!/usr/bin/env python3
"""Parameter gates for v5 replaceable zero-position detent cassette."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G
import v2_params as V2
import v5_params as P


def local_to_global(x, y):
    a = math.radians(P.DETENT_HOME_ANGLE_DEG)
    return (
        G.PIVOT.x + (P.DETENT_NOSE_CENTER_RADIUS + x) * math.cos(a) - y * math.sin(a),
        G.PIVOT.y + (P.DETENT_NOSE_CENTER_RADIUS + x) * math.sin(a) + y * math.cos(a),
    )


def main():
    checks = {}

    checks["detent_track_covers_full_swivel"] = (
        P.DETENT_TRACK_HALF_ANGLE_DEG >= P.DETENT_REQUIRED_TRACK_HALF_ANGLE_DEG
    )
    checks["detent_track_stays_inside_rotating_clearance"] = (
        P.DETENT_TRACK_R_OUTER <= V2.ROTATING_CLEARANCE_RADIUS - 1.5
    )
    checks["detent_track_fuses_to_rotor_disk"] = (
        P.DETENT_TRACK_R_INNER <= G.BEARING_OUTER_DIAMETER / 2.0 - 2.0
    )
    checks["center_notch_has_small_positive_relaxed_clearance"] = (
        0.05 <= P.DETENT_CENTER_CLEARANCE <= 0.30
    )
    checks["normal_cam_deflection_is_calibration_scale"] = (
        0.8 <= P.DETENT_NORMAL_DEFLECTION <= 1.4
    )

    max_strain = max(P.DETENT_STRAIN_ESTIMATES.values())
    checks["spring_geometry_strain_estimate_below_0_6_percent"] = max_strain <= 0.006

    # Mount must live outside the rotating-clearance cylinder and inside the
    # fixed center module. Check all anchor corners.
    corners = []
    mount_outside_rotor_clearance = True
    mount_inside_center = True
    for x in (P.DETENT_ANCHOR_X0, P.DETENT_ANCHOR_X1):
        for y in (P.DETENT_ANCHOR_Y0, P.DETENT_ANCHOR_Y1):
            gx, gy = local_to_global(x, y)
            radius = math.hypot(gx - G.PIVOT.x, gy - G.PIVOT.y)
            outside = radius >= V2.ROTATING_CLEARANCE_RADIUS + 0.5
            inside = (
                -G.BASE_CENTER_WIDTH / 2.0 <= gx <= G.BASE_CENTER_WIDTH / 2.0
                and G.BASE.ymin <= gy <= G.BASE.ymax
            )
            mount_outside_rotor_clearance &= outside
            mount_inside_center &= inside
            corners.append(
                [round(gx, 3), round(gy, 3), round(radius, 3), outside, inside]
            )

    checks["detent_mount_outside_rotating_clearance"] = mount_outside_rotor_clearance
    checks["detent_mount_inside_center_module"] = mount_inside_center

    checks["cassette_bottom_matches_mount_top"] = abs(
        P.DETENT_MOUNT_TOP_Z - V2.ROTOR_INSTALL_Z
    ) < 1e-9
    checks["cassette_stays_below_inner_arm"] = (
        P.DETENT_MOUNT_TOP_Z + P.DETENT_SPRING_HEIGHT
        <= V2.TRACK_TOP_Z - 1.5
    )

    checks["locating_pins_span_mount_and_cassette"] = (
        P.DETENT_PIN_SHAFT_HEIGHT
        >= P.DETENT_MOUNT_HEIGHT + P.DETENT_ANCHOR_HEIGHT
    )
    checks["locating_pin_has_clearance"] = (
        P.DETENT_PIN_HOLE_SIZE - P.DETENT_PIN_SHAFT_SIZE >= 0.3
    )
    checks["locating_pin_head_covers_hole"] = (
        P.DETENT_PIN_HEAD_SIZE >= P.DETENT_PIN_HOLE_SIZE + 2.0
    )

    details = {
        "home_angle_deg": P.DETENT_HOME_ANGLE_DEG,
        "track_angle_range_deg": [
            P.DETENT_HOME_ANGLE_DEG - P.DETENT_TRACK_HALF_ANGLE_DEG,
            P.DETENT_HOME_ANGLE_DEG + P.DETENT_TRACK_HALF_ANGLE_DEG,
        ],
        "track_required_half_angle_deg": P.DETENT_REQUIRED_TRACK_HALF_ANGLE_DEG,
        "normal_spring_deflection_mm": P.DETENT_NORMAL_DEFLECTION,
        "center_notch_clearance_mm": P.DETENT_CENTER_CLEARANCE,
        "spring_variants": {
            str(t): {
                "surface_strain_percent": round(
                    100.0 * P.DETENT_STRAIN_ESTIMATES[t], 4
                ),
                "informational_force_range_n": [
                    round(P.DETENT_FORCE_RANGES_N[t][0], 3),
                    round(P.DETENT_FORCE_RANGES_N[t][1], 3),
                ],
            }
            for t in P.DETENT_SPRING_THICKNESSES
        },
        "mount_corner_samples": corners,
        "material_note": (
            "strain is a geometric beam estimate; force range uses a broad nominal "
            "PETG modulus and is not treated as measured print behavior"
        ),
        "positioning_note": (
            "only zero position is detented; +/-15 deg remain positive mechanical stops"
        ),
    }

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "version": "v5",
        "checks": checks,
        "details": details,
        "failed": failed,
    }

    print(json.dumps(report, indent=2))
    if failed:
        print("V5 DESIGN VALIDATION FAILED: " + " | ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
