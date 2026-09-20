#!/usr/bin/env python3
"""Hard gates for fit-coupon parameter fidelity."""

from __future__ import annotations

import json
import math
import sys

import fit_coupon_params as C
import geometry_model as G
import v2_params as V2
import v3_params as V3


def main():
    checks = {}

    families = {f.name: f for f in C.FAMILIES}
    checks["three_joint_families_present"] = set(families) == {
        "base", "inner", "outer"
    }
    checks["clearance_ladder_brackets_nominal"] = (
        min(C.CLEARANCES_MM) < 0.40 < max(C.CLEARANCES_MM)
        and 0.40 in C.CLEARANCES_MM
    )

    base = families["base"]
    checks["base_coupon_matches_production_key"] = (
        base.half_width == G.JOINT_KEY_HALF_WIDTH
        and base.wall_top_from_bottom
        == G.JOINT_KEY_WALL_TOP_Z - G.BASE_FLOOR_THICKNESS
        and base.apex_from_bottom
        == G.JOINT_KEY_APEX_Z - G.BASE_FLOOR_THICKNESS
        and base.nominal_clearance == G.JOINT_CLEARANCE
    )

    inner = families["inner"]
    checks["inner_coupon_matches_production_key"] = (
        inner.half_width == V2.ARM_KEY_HALF_WIDTH
        and inner.wall_top_from_bottom
        == V2.ARM_KEY_WALL_TOP_Z - V2.ARM_KEY_BOTTOM_Z
        and inner.apex_from_bottom
        == V2.ARM_KEY_APEX_Z - V2.ARM_KEY_BOTTOM_Z
        and inner.nominal_clearance == V2.ARM_KEY_CLEARANCE
    )

    outer = families["outer"]
    checks["outer_coupon_matches_production_key"] = (
        outer.half_width == V3.OUTER_KEY_HALF_WIDTH
        and outer.wall_top_from_bottom
        == V3.OUTER_KEY_WALL_TOP_Z - V3.OUTER_KEY_BOTTOM_Z
        and outer.apex_from_bottom
        == V3.OUTER_KEY_APEX_Z - V3.OUTER_KEY_BOTTOM_Z
        and outer.nominal_clearance == V3.OUTER_KEY_CLEARANCE
    )

    checks["all_roofs_at_least_45_deg"] = True
    roof_angles = {}
    for family in C.FAMILIES:
        rise = family.apex_from_bottom - family.wall_top_from_bottom
        angle = math.degrees(math.atan2(rise, family.half_width))
        roof_angles[family.name] = round(angle, 4)
        checks["all_roofs_at_least_45_deg"] &= angle >= 45.0

    checks["coupon_axis_is_short"] = (
        C.PROBE_HEIGHT <= 35.0 and C.SOCKET_HEIGHT <= 25.0
    )

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "checks": checks,
        "roof_angles_deg": roof_angles,
        "clearances_mm": list(C.CLEARANCES_MM),
        "nominal_clearance_mm": 0.40,
        "failed": failed,
    }
    print(json.dumps(report, indent=2))
    if failed:
        print("FIT COUPON DESIGN FAILED: " + " | ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
