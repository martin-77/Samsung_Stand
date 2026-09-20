#!/usr/bin/env python3
"""Parameter gates for v4 positive swivel stops."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G
import v2_params as V2
import v4_params as P


def polar_xy(radius, angle_deg):
    a=math.radians(angle_deg)
    return (
        G.PIVOT.x + radius*math.cos(a),
        G.PIVOT.y + radius*math.sin(a),
    )


def main():
    checks = {}

    checks["stop_target_matches_swivel_limit"] = abs(
        P.STOP_TARGET_DEG - G.SWIVEL_LIMIT_DEG
    ) < 1e-9
    checks["rotor_stop_starts_on_print_bed"] = (
        P.ROTOR_STOP_TAB_Z0 == 0.0
        and P.ROTOR_STOP_SPOKE_Z0 == 0.0
    )
    checks["stop_clearance_starts_at_bearing_plane"] = abs(
        P.STOP_CLEARANCE_Z0 - V2.ROTOR_INSTALL_Z
    ) < 1e-9
    checks["stop_clearance_covers_radial_sweep"] = (
        P.STOP_CLEARANCE_R0 <= P.STOP_SWEEP_MIN_RADIUS - 1.0
        and P.STOP_CLEARANCE_R1 >= P.STOP_SWEEP_MAX_RADIUS + 1.0
    )
    checks["stop_clearance_covers_angular_sweep"] = (
        P.STOP_CLEARANCE_HALF_ANGLE_DEG
        >= P.STOP_SWEEP_MAX_HALF_ANGLE_DEG + 1.0
    )
    checks["stop_tab_connects_back_to_rotor"] = (
        P.ROTOR_STOP_SPOKE_R0 <= G.BEARING_OUTER_DIAMETER / 2.0
        and P.ROTOR_STOP_SPOKE_R1 >= P.STOP_RADIUS - P.ROTOR_STOP_TAB_RADIAL_LENGTH/2.0
    )
    checks["fixed_tower_has_large_contact_height"] = (
        P.FIXED_STOP_TOP_Z - P.ROTOR_STOP_GLOBAL_BOTTOM_Z >= 8.0
    )

    # Fixed towers must remain comfortably inside the center module XY footprint.
    tower_points=[]
    towers_inside=True
    radial_half=P.FIXED_STOP_RADIAL_LENGTH/2.0
    tang_half=P.FIXED_STOP_TANGENTIAL_WIDTH/2.0
    for angle in (P.FIXED_STOP_ANGLE_NEG_DEG,P.FIXED_STOP_ANGLE_POS_DEG):
        a=math.radians(angle)
        er=(math.cos(a),math.sin(a))
        et=(-math.sin(a),math.cos(a))
        cx,cy=polar_xy(P.STOP_RADIUS,angle)
        for sr in (-1,1):
            for st in (-1,1):
                x=cx+sr*radial_half*er[0]+st*tang_half*et[0]
                y=cy+sr*radial_half*er[1]+st*tang_half*et[1]
                inside=(
                    -G.BASE_CENTER_WIDTH/2.0 <= x <= G.BASE_CENTER_WIDTH/2.0
                    and G.BASE.ymin <= y <= G.BASE.ymax
                )
                towers_inside &= inside
                tower_points.append([round(x,3),round(y,3),inside])
    checks["fixed_stop_towers_inside_center_module"] = towers_inside

    beam_half_angle_at_clearance_r0 = math.degrees(
        math.atan2(V2.INNER_BEAM_WIDTH / 2.0, P.ARM_SWEEP_CLEARANCE_R0)
    )
    checks["arm_sweep_clearance_has_angular_width_margin"] = (
        P.ARM_SWEEP_CLEARANCE_ANGLE_MARGIN_DEG
        >= beam_half_angle_at_clearance_r0 + 0.5
    )
    track_inner_radius = V2.TRACK_RADIUS - V2.TRACK_RADIAL_WIDTH / 2.0
    checks["arm_sweep_clearance_stops_before_glide_track"] = (
        P.ARM_SWEEP_CLEARANCE_R1 <= track_inner_radius - 2.0
    )
    checks["arm_sweep_clearance_is_above_load_plane"] = (
        P.ARM_SWEEP_CLEARANCE_Z0 < V2.TRACK_TOP_Z
        and V2.TRACK_TOP_Z - P.ARM_SWEEP_CLEARANCE_Z0 >= 0.3
    )
    checks["arm_sweep_clearance_preserves_lower_buttress"] = (
        P.ARM_SWEEP_CLEARANCE_Z0 - G.BASE_FLOOR_THICKNESS >= 13.0
    )

    checks["tower_angles_are_symmetric"] = abs(
        (P.ROTOR_STOP_HOME_ANGLE_DEG-P.FIXED_STOP_ANGLE_NEG_DEG)
        -(P.FIXED_STOP_ANGLE_POS_DEG-P.ROTOR_STOP_HOME_ANGLE_DEG)
    ) < 1e-9

    details={
        "target_stop_deg":P.STOP_TARGET_DEG,
        "tab_half_angle_deg":round(P.ROTOR_TAB_HALF_ANGLE_DEG,4),
        "tower_half_angle_deg":round(P.FIXED_TOWER_HALF_ANGLE_DEG,4),
        "stop_contact_calibration_deg":round(P.STOP_CONTACT_CALIBRATION_DEG,6),
        "fixed_stop_angles_deg":[
            round(P.FIXED_STOP_ANGLE_NEG_DEG,4),
            round(P.FIXED_STOP_ANGLE_POS_DEG,4),
        ],
        "stop_clearance_radial_range_mm":[
            P.STOP_CLEARANCE_R0,P.STOP_CLEARANCE_R1
        ],
        "stop_sweep_radial_range_mm":[
            round(P.STOP_SWEEP_MIN_RADIUS,3),
            round(P.STOP_SWEEP_MAX_RADIUS,3),
        ],
        "stop_clearance_half_angle_deg":round(
            P.STOP_CLEARANCE_HALF_ANGLE_DEG,4
        ),
        "stop_sweep_max_half_angle_deg":round(
            P.STOP_SWEEP_MAX_HALF_ANGLE_DEG,4
        ),
        "printability_note":"rotor stop spoke and tab both begin at Z=0",
        "arm_sweep_clearance_radial_range_mm":[
            P.ARM_SWEEP_CLEARANCE_R0,P.ARM_SWEEP_CLEARANCE_R1
        ],
        "arm_sweep_clearance_angle_margin_deg":
            P.ARM_SWEEP_CLEARANCE_ANGLE_MARGIN_DEG,
        "arm_beam_half_angle_at_clearance_r0_deg":round(
            beam_half_angle_at_clearance_r0,4
        ),
        "arm_sweep_clearance_z0_mm":P.ARM_SWEEP_CLEARANCE_Z0,
        "preserved_buttress_height_above_floor_mm":round(
            P.ARM_SWEEP_CLEARANCE_Z0-G.BASE_FLOOR_THICKNESS,3
        ),
        "tower_corner_samples":tower_points,
        "note":"Exact end-stop behavior is OCC-gated after CAD generation.",
    }

    failed=[name for name,ok in checks.items() if not ok]
    report={"version":"v4","checks":checks,"details":details,"failed":failed}
    print(json.dumps(report,indent=2))
    if failed:
        print("V4 DESIGN VALIDATION FAILED: "+" | ".join(failed),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
