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
    checks["rotating_stop_clears_normal_fixed_ribs_vertically"] = (
        P.ROTATING_STOP_UNDERSIDE_GAP >= 1.5
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

    checks["tower_angles_are_symmetric"] = abs(
        (P.ROTOR_STOP_HOME_ANGLE_DEG-P.FIXED_STOP_ANGLE_NEG_DEG)
        -(P.FIXED_STOP_ANGLE_POS_DEG-P.ROTOR_STOP_HOME_ANGLE_DEG)
    ) < 1e-9

    details={
        "target_stop_deg":P.STOP_TARGET_DEG,
        "tab_half_angle_deg":round(P.ROTOR_TAB_HALF_ANGLE_DEG,4),
        "tower_half_angle_deg":round(P.FIXED_TOWER_HALF_ANGLE_DEG,4),
        "fixed_stop_angles_deg":[
            round(P.FIXED_STOP_ANGLE_NEG_DEG,4),
            round(P.FIXED_STOP_ANGLE_POS_DEG,4),
        ],
        "rotating_stop_underside_gap_to_normal_ribs_mm":round(
            P.ROTATING_STOP_UNDERSIDE_GAP,3
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
