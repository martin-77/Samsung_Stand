#!/usr/bin/env python3
"""Parameter gates for v7 replaceable wear surfaces."""

from __future__ import annotations

import json
import sys

import geometry_model as G
import v2_params as V2
import v7_params as P


def main() -> int:
    checks={}

    checks["wear_thickness_printable"] = 0.8 <= P.WEAR_THICKNESS <= 1.6
    checks["center_insert_top_preserves_v5_plane"] = abs(
        P.CENTER_INSERT_TOP_Z - G.BEARING_TOP_Z
    ) < 1e-9
    checks["track_insert_top_preserves_v5_plane"] = abs(
        P.TRACK_INSERT_TOP_Z - V2.TRACK_TOP_Z
    ) < 1e-9

    center_residual = P.CENTER_RECESS_Z0 - G.BASE_FLOOR_THICKNESS
    track_residual = P.TRACK_RECESS_Z0 - V2.TRACK_Z0
    checks["center_bearing_keeps_structural_depth"] = center_residual >= 4.5
    checks["side_track_keeps_structural_depth"] = track_residual >= 12.0

    checks["center_insert_clearance_reasonable"] = (
        0.20 <= P.CENTER_INSERT_RADIAL_CLEARANCE <= 0.60
    )
    checks["track_insert_clearance_reasonable"] = (
        0.20 <= P.TRACK_INSERT_RADIAL_CLEARANCE <= 0.60
    )
    checks["track_recess_overbreak_small"] = (
        0.30 <= P.TRACK_RECESS_OVERBREAK_MM <= 1.00
        and 0.20 <= P.TRACK_RECESS_OVERBREAK_DEG <= 0.80
    )

    angular_margin = P.TRACK_INSERT_HALF_ANGLE_DEG - G.SWIVEL_LIMIT_DEG
    checks["track_insert_covers_full_swivel_with_margin"] = angular_margin >= 1.0
    checks["track_insert_stays_inside_recess"] = (
        P.TRACK_INSERT_HALF_ANGLE_DEG < P.TRACK_RECESS_HALF_ANGLE_DEG
        and P.TRACK_INSERT_R_INNER > P.TRACK_RECESS_R_INNER
        and P.TRACK_INSERT_R_OUTER < P.TRACK_RECESS_R_OUTER
    )

    checks["center_insert_area_large"] = P.CENTER_INSERT_AREA_MM2 >= 11500.0
    checks["center_pressure_low_at_500N"] = P.CENTER_PRESSURE_MPA_AT_500N <= 0.045
    checks["side_insert_area_large"] = P.TRACK_INSERT_AREA_MM2 >= 7500.0
    checks["side_pressure_low_at_250N"] = P.TRACK_PRESSURE_MPA_AT_250N <= 0.04

    recess_samples=[]
    recess_inside=True
    import math
    for side,center in (
        ("right",V2.RIGHT_ARM_ANGLE_DEG),
        ("left",V2.LEFT_ARM_ANGLE_DEG),
    ):
        for radius in (P.TRACK_RECESS_R_INNER,P.TRACK_RECESS_R_OUTER):
            for angle in (
                center-P.TRACK_RECESS_HALF_ANGLE_DEG,
                center+P.TRACK_RECESS_HALF_ANGLE_DEG,
            ):
                x=G.PIVOT.x+radius*math.cos(math.radians(angle))
                y=G.PIVOT.y+radius*math.sin(math.radians(angle))
                if side=="right":
                    inside=(
                        G.BASE_CENTER_WIDTH/2.0 <= x <= G.BASE.xmax
                        and G.BASE.ymin <= y <= G.BASE.ymax
                    )
                else:
                    inside=(
                        G.BASE.xmin <= x <= -G.BASE_CENTER_WIDTH/2.0
                        and G.BASE.ymin <= y <= G.BASE.ymax
                    )
                recess_inside &= inside
                recess_samples.append([side,round(x,3),round(y,3),inside])
    checks["track_recess_overbreak_stays_inside_side_modules"] = recess_inside

    details={
        "wear_thickness_mm":P.WEAR_THICKNESS,
        "center_residual_bearing_depth_mm":round(center_residual,3),
        "track_residual_depth_mm":round(track_residual,3),
        "center_insert_area_mm2":round(P.CENTER_INSERT_AREA_MM2,2),
        "center_pressure_mpa_at_500N":round(P.CENTER_PRESSURE_MPA_AT_500N,5),
        "track_insert_area_mm2":round(P.TRACK_INSERT_AREA_MM2,2),
        "track_pressure_mpa_at_250N":round(P.TRACK_PRESSURE_MPA_AT_250N,5),
        "track_insert_angular_margin_beyond_swivel_deg":round(angular_margin,3),
        "track_recess_overbreak_mm":P.TRACK_RECESS_OVERBREAK_MM,
        "track_recess_overbreak_deg":P.TRACK_RECESS_OVERBREAK_DEG,
        "track_recess_boundary_samples":recess_samples,
        "service_note":(
            "Wear pieces are fully supported in shallow recesses and restore "
            "the exact v5 bearing/glide top planes."
        ),
    }

    failed=[k for k,v in checks.items() if not v]
    report={"version":"v7","checks":checks,"details":details,"failed":failed}
    print(json.dumps(report,indent=2))
    if failed:
        print("V7 DESIGN VALIDATION FAILED: "+" | ".join(failed),file=sys.stderr)
        return 1
    return 0


if __name__=="__main__":
    raise SystemExit(main())
