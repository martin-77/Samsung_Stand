#!/usr/bin/env python3
"""Hard-gate the current global layout before CAD generation."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G


def main() -> int:
    checks = {}
    details = {}

    checks["base_fits_sounddeck_width"] = G.BASE.width <= G.SOUNDDECK.width
    checks["base_fits_sounddeck_depth"] = G.BASE.depth <= G.SOUNDDECK.depth

    checks["stand_width_exceeds_sounddeck_as_expected"] = G.STAND_WIDTH > G.SOUNDDECK.width
    details["stand_side_overhang_zero_deg_mm"] = (
        G.STAND_WIDTH - G.SOUNDDECK.width
    ) / 2.0

    checks["saddle_radius_matches_geometry"] = abs(
        G.SADDLE_RADIUS - math.hypot(G.SADDLE_LOCAL_X, G.SADDLE_LOCAL_Y)
    ) < 1e-9

    sweep = []
    all_centers_inside = True
    all_pads_inside = True

    for angle in G.sweep_angles(1.0):
        left, right = G.saddle_centers(angle)
        center_ok = (
            G.rect_contains_point(G.SOUNDDECK, left)
            and G.rect_contains_point(G.SOUNDDECK, right)
        )
        pads_ok = (
            G.support_pad_inside_sounddeck(left)
            and G.support_pad_inside_sounddeck(right)
        )
        all_centers_inside &= center_ok
        all_pads_inside &= pads_ok
        sweep.append(
            {
                "angle_deg": round(angle, 3),
                "left": [round(left.x, 3), round(left.y, 3)],
                "right": [round(right.x, 3), round(right.y, 3)],
                "centers_inside": center_ok,
                "40x40_pads_inside": pads_ok,
            }
        )

    checks["saddle_centers_inside_sounddeck_full_sweep"] = all_centers_inside
    checks["40x40_support_pads_inside_sounddeck_full_sweep"] = all_pads_inside

    module_checks = {}
    for name, (x, y, z) in G.PRINT_MODULES.items():
        module_checks[name] = {
            "size_mm": [x, y, z],
            "fits_printer": (
                x <= G.PRINTER_X
                and y <= G.PRINTER_Y
                and z <= G.PRINTER_Z
            ),
        }
    checks["all_declared_modules_fit_printer"] = all(
        item["fits_printer"] for item in module_checks.values()
    )

    report = {
        "sounddeck_mm": [G.SOUNDDECK.width, G.SOUNDDECK.depth],
        "fixed_base_mm": [G.BASE.width, G.BASE.depth],
        "stand_width_mm": G.STAND_WIDTH,
        "stand_depth_status": "reconstructed; not yet physical manufacturing truth",
        "pivot_sounddeck_xy_mm": [G.PIVOT.x, G.PIVOT.y],
        "swivel_limit_deg": G.SWIVEL_LIMIT_DEG,
        "saddle_local_xy_mm": [G.SADDLE_LOCAL_X, G.SADDLE_LOCAL_Y],
        "saddle_orbit_radius_mm": round(G.SADDLE_RADIUS, 3),
        "support_pad_assumption_mm": [
            2 * G.SADDLE_PAD_HALF_X,
            2 * G.SADDLE_PAD_HALF_Y,
        ],
        "checks": checks,
        "details": details,
        "modules": module_checks,
        "sweep": sweep,
    }

    failed = [name for name, ok in checks.items() if not ok]
    report["failed"] = failed

    print(json.dumps(report, indent=2))
    if failed:
        print("LAYOUT VALIDATION FAILED: " + " | ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
