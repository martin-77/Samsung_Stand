#!/usr/bin/env python3
"""Hard parameter gates for v8 above-base locking and positive pivot retention."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G
import v2_params as V2
import v3_params as V3
import v8_params as P


def roof_angle_deg(apex: float, wall_top: float, half_width: float) -> float:
    return math.degrees(math.atan2(apex - wall_top, half_width))


def main() -> int:
    checks = {}

    base_roof = roof_angle_deg(
        P.BASE_LOCK_HOLE_APEX_Z,
        P.BASE_LOCK_HOLE_WALL_TOP_Z,
        P.BASE_LOCK_HOLE_WIDTH / 2.0,
    )
    pivot_roof = roof_angle_deg(
        P.PIVOT_PIN_HOLE_APEX_Z,
        P.PIVOT_PIN_HOLE_WALL_TOP_Z,
        P.PIVOT_PIN_HOLE_WIDTH / 2.0,
    )
    outer_roof = roof_angle_deg(
        P.OUTER_LOCK_HOLE_APEX_Z,
        P.OUTER_LOCK_HOLE_WALL_TOP_Z,
        P.OUTER_LOCK_HOLE_WIDTH / 2.0,
    )

    checks["base_lock_roof_support_friendly"] = base_roof >= 45.0
    checks["pivot_lock_roof_support_friendly"] = pivot_roof >= 45.0
    checks["outer_lock_roof_support_friendly"] = outer_roof >= 45.0

    checks["base_pin_fits_straight_tunnel"] = (
        P.JOINT_PIN_WIDTH < P.BASE_LOCK_HOLE_WIDTH
        and P.BASE_LOCK_PIN_INSTALL_Z >= P.BASE_LOCK_HOLE_BOTTOM_Z
        and P.BASE_LOCK_PIN_INSTALL_Z + P.JOINT_PIN_HEIGHT
        <= P.BASE_LOCK_HOLE_WALL_TOP_Z
    )
    checks["outer_pin_fits_straight_tunnel"] = (
        P.OUTER_PIN_WIDTH < P.OUTER_LOCK_HOLE_WIDTH
        and P.OUTER_PIN_INSTALL_Z >= P.OUTER_LOCK_HOLE_BOTTOM_Z
        and P.OUTER_PIN_INSTALL_Z + P.OUTER_PIN_HEIGHT
        <= P.OUTER_LOCK_HOLE_WALL_TOP_Z
    )
    checks["pivot_pin_fits_straight_tunnel"] = (
        P.PIVOT_PIN_WIDTH < P.PIVOT_PIN_HOLE_WIDTH
        and P.PIVOT_PIN_INSTALL_Z >= P.PIVOT_PIN_HOLE_BOTTOM_Z
        and P.PIVOT_PIN_INSTALL_Z + P.PIVOT_PIN_HEIGHT
        <= P.PIVOT_PIN_HOLE_WALL_TOP_Z
    )

    checks["base_lock_fully_above_sounddeck_plane"] = (
        P.BASE_LOCK_PIN_INSTALL_Z > 0.0
    )
    checks["outer_lock_fully_above_structure_floor"] = (
        P.OUTER_PIN_INSTALL_Z > 0.0
    )
    checks["pivot_post_has_printable_roof_wall"] = (
        P.PIVOT_POST_TOP_Z - P.PIVOT_PIN_HOLE_APEX_Z >= 0.8
    )

    # Legacy vertical holes remain unused in v8, so keep a meaningful material
    # ligament between those holes and the new horizontal tunnel.
    base_lock_ligament = (
        abs(P.LEGACY_VERTICAL_LOCK_X_ABS - P.BASE_LOCK_X_ABS)
        - G.RETAINER_HOLE_X / 2.0
        - P.BASE_LOCK_HOLE_WIDTH / 2.0
    )
    checks["base_lock_keeps_ligament_to_legacy_hole"] = (
        base_lock_ligament >= 5.0
    )

    # The base receiver is 50 mm wide in Y. The v8 tunnel deliberately overcuts
    # this by 1 mm per side so STL tessellation has no coplanar end seam.
    checks["base_tunnel_overcuts_receiver_faces"] = (
        P.BASE_LOCK_TUNNEL_LENGTH >= G.JOINT_RECEIVER_WIDTH + 2.0
    )

    # Pin barb must be relaxed only after it is outside the far receiver face.
    base_pin_far_face_local_x = (
        -P.BASE_LOCK_PIN_AXIS_START + G.JOINT_RECEIVER_WIDTH / 2.0
    )
    base_barb_start = (
        P.JOINT_PIN_LENGTH - P.JOINT_PIN_SPLIT_LENGTH + 1.0
    )
    checks["base_barb_peak_beyond_receiver"] = (
        P.JOINT_PIN_BARB_PEAK_X > base_pin_far_face_local_x + 2.0
    )
    checks["base_barb_transition_begins_near_far_face"] = (
        base_barb_start >= base_pin_far_face_local_x - 5.0
    )

    # Existing rotor/INNER tunnel is already through the 40 mm receiver. The
    # same compact joint pin should snap only after leaving that receiver.
    inner_receiver_far_face_local_x = (
        P.JOINT_PIN_LENGTH * 0.0
        + V2.ARM_LOCK_HOLE_TRANSVERSE_LENGTH / 2.0
    )
    inner_pin_axis_start = -V2.ARM_LOCK_HOLE_TRANSVERSE_LENGTH / 2.0
    inner_material_far_face_local_x = (
        -inner_pin_axis_start + V2.ROTOR_RECEIVER_WIDTH / 2.0
    )
    checks["joint_pin_barb_beyond_rotor_receiver"] = (
        base_barb_start > inner_material_far_face_local_x
    )

    # The v3 outer-lock tunnel was hidden inside the 58 mm saddle. V8 must open
    # all the way through with margin.
    checks["outer_lock_tunnel_exits_saddle"] = (
        P.OUTER_LOCK_TUNNEL_LENGTH >= V2.SADDLE_PLATFORM_WIDTH + 4.0
    )
    outer_far_face_local_x = (
        -P.OUTER_PIN_INSTALL_AXIS_START + V2.SADDLE_PLATFORM_WIDTH / 2.0
    )
    outer_barb_start = (
        P.OUTER_PIN_LENGTH - P.OUTER_PIN_SPLIT_LENGTH + 1.0
    )
    checks["outer_barb_starts_after_saddle_face"] = (
        outer_barb_start > outer_far_face_local_x - 4.0
    )
    checks["outer_barb_peak_beyond_saddle_face"] = (
        P.OUTER_PIN_BARB_PEAK_X > outer_far_face_local_x + 3.0
    )

    # Pivot counterbore must contain every part of the installed pin through a
    # full 360-degree rotor sweep.
    head_x_min = (
        P.PIVOT_PIN_INSTALL_X0 - P.PIVOT_PIN_HEAD_LENGTH
    )
    head_x_max = P.PIVOT_PIN_INSTALL_X0
    pin_radial_max = max(
        math.hypot(head_x_min, P.PIVOT_PIN_HEAD_WIDTH / 2.0),
        math.hypot(head_x_max, P.PIVOT_PIN_HEAD_WIDTH / 2.0),
        math.hypot(
            P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_LENGTH,
            P.PIVOT_PIN_WIDTH / 2.0,
        ),
        math.hypot(
            P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_BARB_PEAK_X,
            P.PIVOT_PIN_BARB_HALF_WIDTH,
        ),
    )
    pivot_counterbore_margin = (
        P.PIVOT_COUNTERBORE_RADIUS - pin_radial_max
    )
    checks["pivot_pin_fits_inside_rotor_counterbore"] = (
        pivot_counterbore_margin >= 1.0
    )
    pin_total_x_span = (
        P.PIVOT_PIN_LENGTH + P.PIVOT_PIN_HEAD_LENGTH
    )
    checks["pivot_counterbore_is_top_down_assembly_chamber"] = (
        2.0 * P.PIVOT_COUNTERBORE_RADIUS >= pin_total_x_span + 15.0
    )
    checks["pivot_counterbore_stops_before_arm_receivers"] = (
        P.PIVOT_COUNTERBORE_RADIUS
        <= V2.ROTOR_RECEIVER_R_INNER - 0.4
    )
    checks["pivot_post_fits_existing_rotor_bore_below_shoulder"] = (
        P.PIVOT_POST_DIAMETER < G.PIVOT_BORE_DIAMETER
    )

    # Retention shoulder: pin must extend radially beyond the original rotor
    # bore, otherwise lifting the rotor would simply pass around the pin.
    post_radius = P.PIVOT_POST_DIAMETER / 2.0
    rotor_bore_radius = G.PIVOT_BORE_DIAMETER / 2.0
    pin_right_reach = P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_LENGTH
    pin_left_reach = abs(
        P.PIVOT_PIN_INSTALL_X0 - P.PIVOT_PIN_HEAD_LENGTH
    )
    checks["pivot_pin_spans_beyond_rotor_bore_both_sides"] = (
        pin_right_reach >= rotor_bore_radius + 2.0
        and pin_left_reach >= rotor_bore_radius + 2.0
    )
    checks["pivot_pin_barb_starts_outside_post"] = (
        P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_BARB_START_X
        >= post_radius - 0.05
    )
    checks["pivot_pin_barb_snaps_beyond_post"] = (
        P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_BARB_PEAK_X
        >= post_radius + 1.5
    )

    checks["pivot_retention_has_small_lift_clearance"] = (
        0.4 <= P.PIVOT_ROTOR_LIFT_CLEARANCE <= 1.0
    )
    checks["pivot_development_bending_stress_reasonable"] = (
        P.PIVOT_PIN_BENDING_STRESS_MPA_AT_500N <= 20.0
    )

    details = {
        "base_lock_roof_angle_deg": round(base_roof, 3),
        "pivot_lock_roof_angle_deg": round(pivot_roof, 3),
        "outer_lock_roof_angle_deg": round(outer_roof, 3),
        "base_lock_ligament_to_legacy_vertical_hole_mm": round(
            base_lock_ligament, 3
        ),
        "base_pin_far_receiver_face_local_x_mm": round(
            base_pin_far_face_local_x, 3
        ),
        "joint_pin_barb_start_local_x_mm": round(base_barb_start, 3),
        "outer_pin_far_saddle_face_local_x_mm": round(
            outer_far_face_local_x, 3
        ),
        "outer_pin_barb_start_local_x_mm": round(outer_barb_start, 3),
        "pivot_pin_max_radius_mm": round(pin_radial_max, 3),
        "pivot_counterbore_radial_margin_mm": round(
            pivot_counterbore_margin, 3
        ),
        "pivot_counterbore_diameter_mm": round(
            2.0 * P.PIVOT_COUNTERBORE_RADIUS, 3
        ),
        "pivot_pin_total_x_span_mm": round(pin_total_x_span, 3),
        "pivot_receiver_radial_margin_mm": round(
            V2.ROTOR_RECEIVER_R_INNER - P.PIVOT_COUNTERBORE_RADIUS,
            3
        ),
        "pivot_rotor_lift_clearance_mm": round(
            P.PIVOT_ROTOR_LIFT_CLEARANCE, 3
        ),
        "pivot_barb_start_global_x_mm": round(
            P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_BARB_START_X, 3
        ),
        "pivot_barb_peak_global_x_mm": round(
            P.PIVOT_PIN_INSTALL_X0 + P.PIVOT_PIN_BARB_PEAK_X, 3
        ),
        "pivot_pin_bending_stress_mpa_at_500N_development_only": round(
            P.PIVOT_PIN_BENDING_STRESS_MPA_AT_500N, 3
        ),
        "retainer_architecture": (
            "No v8 structural retainer protrudes below the base. Base and arm "
            "locks use transverse snap pins; pivot retention uses a fixed "
            "cross-pin inside a top-open circular rotor counterbore that "
            "also provides the real assembly/removal chamber."
        ),
    }

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "version": "v8",
        "checks": checks,
        "details": details,
        "failed": failed,
    }
    print(json.dumps(report, indent=2))
    if failed:
        print(
            "V8 DESIGN VALIDATION FAILED: " + " | ".join(failed),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
