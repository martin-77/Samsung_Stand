#!/usr/bin/env python3
"""Hard-gate v2 support-plane, tracks and rotating inner-arm geometry."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G
import v2_params as P


def polar(point: G.Point2) -> tuple[float, float]:
    x = point.x - G.PIVOT.x
    y = point.y - G.PIVOT.y
    return math.hypot(x, y), math.degrees(math.atan2(y, x))


def angle_in_range(angle: float, bounds: tuple[float, float]) -> bool:
    lo, hi = bounds
    return lo <= angle <= hi


def main() -> int:
    checks = {}
    details = {}

    checks["support_plane_matches_rotor_top"] = abs(
        P.TRACK_TOP_Z - (G.BEARING_TOP_Z + G.ROTOR_THICKNESS)
    ) < 1e-9
    root_landing_global_top = P.ROTOR_INSTALL_Z + P.ROOT_LANDING_TOP_Z
    checks["root_landing_coplanar_with_glide_track"] = abs(
        root_landing_global_top - P.TRACK_TOP_Z
    ) < 1e-9
    checks["key_underside_clearance_is_deliberate"] = abs(
        P.ARM_KEY_INSTALLED_BOTTOM_ROTOR_Z - P.ROTOR_KEY_CAVITY_BOTTOM_Z
        - P.ARM_KEY_UNDERSIDE_CLEARANCE
    ) < 1e-9
    checks["receiver_keeps_floor_under_key"] = (
        P.ROTOR_KEY_CAVITY_BOTTOM_Z - P.ROTOR_RECEIVER_Z0 >= 0.35
    )
    checks["track_has_positive_height"] = P.TRACK_HEIGHT > 0.0
    checks["inner_print_length_under_295"] = P.INNER_PRINT_LENGTH <= G.PREFERRED_PART_XY
    checks["inner_print_width_under_295"] = P.INNER_PRINT_WIDTH <= G.PREFERRED_PART_XY

    key_rise = P.ARM_KEY_APEX_Z - P.ARM_KEY_WALL_TOP_Z
    key_angle = math.degrees(math.atan2(key_rise, P.ARM_KEY_HALF_WIDTH))
    checks["arm_key_roof_support_friendly"] = key_angle >= 45.0
    checks["arm_key_clearance_reasonable"] = 0.30 <= P.ARM_KEY_CLEARANCE <= 0.55
    lock_roof_rise = (
        P.ARM_LOCK_HOLE_APEX_Z_ROTOR - P.ARM_LOCK_HOLE_WALL_TOP_Z_ROTOR
    )
    lock_roof_run = P.ARM_LOCK_HOLE_RADIAL_WIDTH / 2.0
    lock_roof_angle = math.degrees(math.atan2(lock_roof_rise, lock_roof_run))
    checks["arm_lock_tunnel_roof_support_friendly"] = lock_roof_angle >= 45.0
    checks["arm_lock_pin_fits_tunnel"] = (
        P.ARM_LOCK_PIN_RADIAL_WIDTH < P.ARM_LOCK_HOLE_RADIAL_WIDTH
        and P.ARM_LOCK_PIN_HEIGHT
        < P.ARM_LOCK_HOLE_WALL_TOP_Z_ROTOR - P.ARM_LOCK_HOLE_BOTTOM_Z_ROTOR
    )

    receiver_roof_margin = P.ROTOR_RECEIVER_TOP_Z - (
        (P.ARM_KEY_APEX_Z + P.TRACK_TOP_Z - G.BEARING_TOP_Z)
        + P.ARM_KEY_CLEARANCE
    )
    checks["rotor_receiver_keeps_roof_wall"] = receiver_roof_margin >= 3.0

    checks["saddle_lies_on_inner_arm"] = (
        0.0 < P.SADDLE_U < P.INNER_LENGTH
        and P.SADDLE_U + P.SADDLE_PLATFORM_LENGTH / 2.0 <= P.INNER_LENGTH + 1e-9
    )

    rmin = P.TRACK_RADIUS - P.TRACK_RADIAL_WIDTH / 2.0
    rmax = P.TRACK_RADIUS + P.TRACK_RADIAL_WIDTH / 2.0

    sweep = []
    all_on_tracks = True
    all_on_base = True
    min_base_margin = float("inf")

    for angle in G.sweep_angles(0.5):
        left, right = G.saddle_centers(angle)
        rows = []
        for label, point, angle_range in (
            ("left", left, P.LEFT_TRACK_ANGLE_RANGE),
            ("right", right, P.RIGHT_TRACK_ANGLE_RANGE),
        ):
            radius, theta = polar(point)
            on_track = (
                rmin <= radius <= rmax
                and angle_in_range(theta, angle_range)
            )
            pad_on_base = (
                G.BASE.xmin <= point.x - G.SADDLE_PAD_HALF_X
                and point.x + G.SADDLE_PAD_HALF_X <= G.BASE.xmax
                and G.BASE.ymin <= point.y - G.SADDLE_PAD_HALF_Y
                and point.y + G.SADDLE_PAD_HALF_Y <= G.BASE.ymax
            )
            margin = min(
                point.x - G.SADDLE_PAD_HALF_X - G.BASE.xmin,
                G.BASE.xmax - (point.x + G.SADDLE_PAD_HALF_X),
                point.y - G.SADDLE_PAD_HALF_Y - G.BASE.ymin,
                G.BASE.ymax - (point.y + G.SADDLE_PAD_HALF_Y),
            )
            min_base_margin = min(min_base_margin, margin)
            all_on_tracks &= on_track
            all_on_base &= pad_on_base
            rows.append(
                {
                    "side": label,
                    "radius_mm": round(radius, 3),
                    "angle_deg": round(theta, 3),
                    "on_track": on_track,
                    "40x40_pad_on_fixed_base": pad_on_base,
                }
            )
        sweep.append({"swivel_deg": round(angle, 2), "supports": rows})

    checks["saddle_centers_follow_tracks_full_sweep"] = all_on_tracks
    checks["40x40_saddle_pads_stay_on_fixed_base"] = all_on_base
    checks["minimum_fixed_base_margin_positive"] = min_base_margin > 0.0

    # Track sectors must stay within their own physical side module, so the
    # moving-load path never crosses a modular base seam.
    sector_samples = []
    tracks_inside_side_modules = True
    for side, angle_range in (
        ("right", P.RIGHT_TRACK_ANGLE_RANGE),
        ("left", P.LEFT_TRACK_ANGLE_RANGE),
    ):
        for radius in (rmin, rmax):
            for i in range(41):
                a = angle_range[0] + (angle_range[1] - angle_range[0]) * i / 40.0
                x = G.PIVOT.x + radius * math.cos(math.radians(a))
                y = G.PIVOT.y + radius * math.sin(math.radians(a))
                if side == "right":
                    inside = (
                        G.BASE_CENTER_WIDTH / 2.0 <= x <= G.BASE.xmax
                        and G.BASE.ymin <= y <= G.BASE.ymax
                    )
                else:
                    inside = (
                        G.BASE.xmin <= x <= -G.BASE_CENTER_WIDTH / 2.0
                        and G.BASE.ymin <= y <= G.BASE.ymax
                    )
                tracks_inside_side_modules &= inside
                sector_samples.append([side, round(x, 3), round(y, 3), inside])

    checks["glide_tracks_stay_inside_side_modules"] = tracks_inside_side_modules

    # Contact insert is explicitly replaceable because the real Samsung arm
    # cross-section remains the largest unresolved physical measurement.
    checks["blank_insert_has_fit_clearance"] = (
        P.SADDLE_INSERT_LENGTH < P.SADDLE_POCKET_LENGTH
        and P.SADDLE_INSERT_WIDTH < P.SADDLE_POCKET_WIDTH
    )

    details = {
        "track_top_z_mm": P.TRACK_TOP_Z,
        "root_landing_global_top_z_mm": root_landing_global_top,
        "key_bottom_rotor_local_z_mm": P.ARM_KEY_INSTALLED_BOTTOM_ROTOR_Z,
        "key_cavity_floor_rotor_local_z_mm": P.ROTOR_KEY_CAVITY_BOTTOM_Z,
        "key_underside_clearance_mm": P.ARM_KEY_UNDERSIDE_CLEARANCE,
        "inner_arm_install_z_mm": P.TRACK_TOP_Z,
        "right_arm_angle_deg": round(P.RIGHT_ARM_ANGLE_DEG, 4),
        "left_arm_angle_deg": round(P.LEFT_ARM_ANGLE_DEG, 4),
        "track_radial_range_mm": [round(rmin, 3), round(rmax, 3)],
        "right_track_angle_range_deg": [round(x, 3) for x in P.RIGHT_TRACK_ANGLE_RANGE],
        "left_track_angle_range_deg": [round(x, 3) for x in P.LEFT_TRACK_ANGLE_RANGE],
        "inner_saddle_u_mm": round(P.SADDLE_U, 3),
        "minimum_40x40_pad_margin_on_fixed_base_mm": round(min_base_margin, 3),
        "arm_key_roof_angle_deg": round(key_angle, 3),
        "arm_lock_tunnel_roof_angle_deg": round(lock_roof_angle, 3),
        "rotor_receiver_roof_margin_mm": round(receiver_roof_margin, 3),
        "contact_profile_status": "blank replaceable insert; physical Samsung arm section still required",
    }

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "version": "v2",
        "checks": checks,
        "details": details,
        "sweep": sweep,
        "track_boundary_samples": sector_samples,
        "failed": failed,
    }

    print(json.dumps(report, indent=2))
    if failed:
        print("V2 DESIGN VALIDATION FAILED: " + " | ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
