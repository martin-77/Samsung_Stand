#!/usr/bin/env python3
"""Hard checks for the first printable v1 base/rotor architecture."""

from __future__ import annotations

import json
import math
import sys

import geometry_model as G


def main() -> int:
    checks = {}
    details = {}

    # Joint geometry: two long roof keys per side, retained by a separate snap pin.
    roof_rise = G.JOINT_KEY_APEX_Z - G.JOINT_KEY_WALL_TOP_Z
    roof_run = G.JOINT_KEY_HALF_WIDTH
    roof_angle_deg = math.degrees(math.atan2(roof_rise, roof_run))

    checks["two_joint_keys_per_side"] = len(G.JOINT_Y_CENTERS) == 2
    checks["joint_overlap_at_least_50mm"] = G.JOINT_OVERLAP >= 50.0
    checks["joint_clearance_petg_reasonable"] = 0.30 <= G.JOINT_CLEARANCE <= 0.55
    checks["roof_is_support_friendly_45deg_or_steeper"] = roof_angle_deg >= 45.0
    checks["receiver_has_minimum_roof_wall"] = (
        G.JOINT_RECEIVER_HEIGHT - (G.JOINT_KEY_APEX_Z + G.JOINT_CLEARANCE) >= 3.0
    )
    checks["retainer_hole_clears_pin"] = (
        G.RETAINER_HOLE_X > G.RETAINER_PIN_X
        and G.RETAINER_HOLE_Y > G.RETAINER_PIN_Y
    )
    checks["retainer_hole_lies_inside_overlap"] = (
        8.0 <= G.RETAINER_HOLE_LOCAL_X <= G.JOINT_OVERLAP - 8.0
    )

    # Center module stays one uninterrupted print under the entire swivel ring.
    checks["bearing_fits_center_module_x"] = (
        G.BEARING_OUTER_DIAMETER <= G.BASE_CENTER_WIDTH - 20.0
    )
    bearing_radius = G.BEARING_OUTER_DIAMETER / 2.0
    bearing_ymin = G.PIVOT.y - bearing_radius
    bearing_ymax = G.PIVOT.y + bearing_radius
    rear_margin = bearing_ymin - G.BASE.ymin
    front_margin = G.BASE.ymax - bearing_ymax
    checks["bearing_fits_center_module_y"] = (
        bearing_ymin >= G.BASE.ymin and bearing_ymax <= G.BASE.ymax
    )
    checks["bearing_keeps_min_8mm_rear_margin"] = rear_margin >= 8.0
    checks["pivot_bore_has_radial_clearance"] = (
        G.PIVOT_BORE_DIAMETER - G.PIVOT_STEM_DIAMETER >= 1.0
    )
    checks["pivot_clip_captures_rotor_bore"] = (
        G.PIVOT_CLIP_OUTER_DIAMETER > G.PIVOT_BORE_DIAMETER + 4.0
        and G.PIVOT_CLIP_INNER_DIAMETER > G.PIVOT_NECK_DIAMETER
    )

    # The ring, not the pilot, is the intended vertical load path.
    checks["bearing_nominal_area_large"] = G.BEARING_NOMINAL_AREA_MM2 >= 12000.0
    checks["bearing_nominal_pressure_low"] = G.BEARING_NOMINAL_PRESSURE_MPA <= 0.04

    # Printability.
    module_results = {}
    for name, dims in G.PRINT_MODULES.items():
        x, y, z = dims
        fits = x <= G.PRINTER_X and y <= G.PRINTER_Y and z <= G.PRINTER_Z
        preferred_xy = x <= G.PREFERRED_PART_XY and y <= G.PREFERRED_PART_XY
        module_results[name] = {
            "size_mm": [x, y, z],
            "fits_core_one_l": fits,
            "within_preferred_xy_295": preferred_xy,
        }

    checks["all_v1_modules_fit_core_one_l"] = all(
        item["fits_core_one_l"] for item in module_results.values()
    )
    checks["all_v1_modules_keep_295mm_xy_margin"] = all(
        item["within_preferred_xy_295"] for item in module_results.values()
    )

    # Global support sweep remains valid with the current saddle concept.
    all_supports_inside = True
    min_edge_margin = float("inf")
    sweep = []
    for angle in G.sweep_angles(0.5):
        centers = G.saddle_centers(angle)
        angle_ok = True
        for p in centers:
            angle_ok &= G.support_pad_inside_sounddeck(p)
            edge_margin = min(
                p.x - G.SADDLE_PAD_HALF_X - G.SOUNDDECK.xmin,
                G.SOUNDDECK.xmax - (p.x + G.SADDLE_PAD_HALF_X),
                p.y - G.SADDLE_PAD_HALF_Y - G.SOUNDDECK.ymin,
                G.SOUNDDECK.ymax - (p.y + G.SADDLE_PAD_HALF_Y),
            )
            min_edge_margin = min(min_edge_margin, edge_margin)
        all_supports_inside &= angle_ok
        sweep.append(
            {
                "angle_deg": round(angle, 2),
                "supports_inside": angle_ok,
                "left_xy_mm": [round(centers[0].x, 3), round(centers[0].y, 3)],
                "right_xy_mm": [round(centers[1].x, 3), round(centers[1].y, 3)],
            }
        )

    checks["support_pads_inside_sounddeck_full_sweep"] = all_supports_inside
    checks["support_pads_have_positive_edge_margin"] = min_edge_margin > 0.0

    details.update(
        {
            "joint_roof_angle_deg": round(roof_angle_deg, 3),
            "bearing_area_mm2": round(G.BEARING_NOMINAL_AREA_MM2, 2),
            "bearing_rear_margin_mm": round(rear_margin, 3),
            "bearing_front_margin_mm": round(front_margin, 3),
            "bearing_nominal_pressure_mpa_at_500N": round(
                G.BEARING_NOMINAL_PRESSURE_MPA, 5
            ),
            "minimum_40x40_support_pad_edge_margin_mm": round(min_edge_margin, 3),
            "load_path_note": (
                "Roof keys transfer vertical/lateral joint loads through large "
                "form-locking surfaces. Retainer pin prevents withdrawal; its snap "
                "barbs only retain the pin. Pivot stem guides rotation; annular "
                "bearing is the intended primary vertical load path."
            ),
        }
    )

    failed = [name for name, ok in checks.items() if not ok]
    report = {
        "version": "v1",
        "checks": checks,
        "details": details,
        "modules": module_results,
        "sweep": sweep,
        "failed": failed,
    }

    print(json.dumps(report, indent=2))
    if failed:
        print("V1 DESIGN VALIDATION FAILED: " + " | ".join(failed), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
