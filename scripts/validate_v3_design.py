#!/usr/bin/env python3
"""Hard-gate v3 outer guide geometry before FreeCAD generation."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G
import v2_params as V2
import v3_params as P


def main() -> int:
    checks = {}

    checks["outer_guide_reaches_beyond_reconstructed_tip"] = (
        P.OUTER_TIP_RADIUS >= P.STAND_TIP_RADIUS + 5.0
    )
    checks["outer_guide_print_length_under_295"] = (
        P.OUTER_PRINT_LENGTH <= G.PREFERRED_PART_XY
    )
    checks["outer_guide_print_width_under_295"] = (
        P.OUTER_PRINT_WIDTH <= G.PREFERRED_PART_XY
    )
    checks["outer_body_starts_beyond_fixed_glide_track"] = (
        P.OUTER_BODY_RADIAL_GAP_TO_TRACK >= 4.0
    )
    checks["normal_vertical_clearance_is_large"] = (
        P.NORMAL_VERTICAL_CLEARANCE_TO_GUIDE_FLOOR >= 8.0
    )

    rise = P.OUTER_KEY_APEX_Z - P.OUTER_KEY_WALL_TOP_Z
    roof_angle = math.degrees(math.atan2(rise, P.OUTER_KEY_HALF_WIDTH))
    checks["outer_key_roof_support_friendly"] = roof_angle >= 30.0
    # 32 degrees is still printable in PETG when the roof is a short symmetric
    # bridge/chamfer, but keep a documented gate instead of silently accepting it.
    checks["outer_key_not_flat_bridge"] = roof_angle >= 30.0

    checks["outer_key_clearance_reasonable"] = (
        0.30 <= P.OUTER_KEY_CLEARANCE <= 0.55
    )
    checks["outer_receiver_keeps_floor"] = (
        P.OUTER_RECEIVER_CAVITY_BOTTOM_Z >= 2.0
    )
    checks["outer_receiver_keeps_roof"] = (
        V2.INNER_TOTAL_HEIGHT - P.OUTER_RECEIVER_CAVITY_APEX_Z >= 3.5
    )
    checks["outer_key_has_deliberate_underside_clearance"] = abs(
        P.OUTER_KEY_BOTTOM_Z
        - P.OUTER_RECEIVER_CAVITY_BOTTOM_Z
        - P.OUTER_KEY_UNDERSIDE_CLEARANCE
    ) < 1e-9

    lock_rise = P.OUTER_LOCK_HOLE_APEX_Z - P.OUTER_LOCK_HOLE_WALL_TOP_Z
    lock_run = P.OUTER_LOCK_HOLE_WIDTH / 2.0
    lock_angle = math.degrees(math.atan2(lock_rise, lock_run))
    checks["outer_lock_tunnel_support_friendly"] = lock_angle >= 45.0

    checks["placeholder_channel_explicitly_oversized"] = (
        P.OUTER_CHANNEL_PLACEHOLDER_WIDTH >= 55.0
    )

    # The full outer guide may overhang the Sounddeck by design. Its fixed-base
    # collision risk is checked here only at its inward/full-floor start.
    checks["outer_guide_is_not_declared_vertical_support"] = (
        P.OUTER_BODY_RADIAL_GAP_TO_TRACK > 0.0
        and P.OUTER_KEY_BOTTOM_Z > 0.0
    )

    details = {
        "reconstructed_samsung_tip_radius_mm": round(P.STAND_TIP_RADIUS, 3),
        "outer_guide_start_radius_mm": round(P.OUTER_R0, 3),
        "outer_guide_tip_radius_mm": round(P.OUTER_TIP_RADIUS, 3),
        "tip_coverage_beyond_reconstruction_mm": round(
            P.OUTER_TIP_RADIUS - P.STAND_TIP_RADIUS, 3
        ),
        "track_outer_radius_mm": round(P.TRACK_OUTER_RADIUS, 3),
        "body_radial_gap_to_track_mm": round(P.OUTER_BODY_RADIAL_GAP_TO_TRACK, 3),
        "stand_contact_plane_global_z_mm": round(P.STAND_CONTACT_PLANE_GLOBAL_Z, 3),
        "outer_floor_top_global_z_mm": round(P.OUTER_FLOOR_TOP_GLOBAL_Z, 3),
        "normal_vertical_clearance_mm": round(
            P.NORMAL_VERTICAL_CLEARANCE_TO_GUIDE_FLOOR, 3
        ),
        "outer_key_roof_angle_deg": round(roof_angle, 3),
        "outer_lock_roof_angle_deg": round(lock_angle, 3),
        "placeholder_channel_inside_width_mm": P.OUTER_CHANNEL_PLACEHOLDER_WIDTH,
        "contact_status": (
            "structural U-guide only; final side-contact/shim geometry requires "
            "physical Samsung arm cross-section measurements"
        ),
    }

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "version": "v3",
        "checks": checks,
        "details": details,
        "failed": failed,
    }

    print(json.dumps(report, indent=2))
    if failed:
        print("V3 DESIGN VALIDATION FAILED: " + " | ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
