#!/usr/bin/env python3
"""Compare fixed-base depth and pivot-Y trade-offs without changing CAD.

This is an analytical decision aid. It does not approve a base depth. The
actual usable flat top of the Magnat Sounddeck must still be measured before a
larger base is released.
"""

from __future__ import annotations

import json

import geometry_model as G


CANDIDATE_DEPTHS_MM = (295.0, 300.0, 310.0, 320.0, 330.0, 335.0)
PIVOT_SEARCH_MIN_Y_MM = -100.0
PIVOT_SEARCH_MAX_Y_MM = -20.0
PIVOT_SEARCH_STEP_MM = 0.05


def saddle_centers_for_pivot(
    angle_deg: float,
    pivot_y_mm: float,
) -> tuple[G.Point2, G.Point2]:
    left_local = G.Point2(-G.SADDLE_LOCAL_X, G.SADDLE_LOCAL_Y)
    right_local = G.Point2(+G.SADDLE_LOCAL_X, G.SADDLE_LOCAL_Y)
    left = G.rotate_local(left_local, angle_deg)
    right = G.rotate_local(right_local, angle_deg)
    return (
        G.Point2(left.x, left.y + pivot_y_mm),
        G.Point2(right.x, right.y + pivot_y_mm),
    )


def minimum_support_pad_margin_mm(
    base: G.Rect,
    pivot_y_mm: float,
) -> float:
    margin = float("inf")
    for angle in G.sweep_angles(0.25):
        for p in saddle_centers_for_pivot(angle, pivot_y_mm):
            margin = min(
                margin,
                G.support_pad_edge_margin(base, p),
            )
    return margin


def bearing_edge_margins_mm(
    base: G.Rect,
    pivot_y_mm: float,
) -> tuple[float, float]:
    r = G.BEARING_OUTER_DIAMETER / 2.0
    rear = (pivot_y_mm - r) - base.ymin
    front = base.ymax - (pivot_y_mm + r)
    return rear, front


def critical_margin_mm(
    base: G.Rect,
    pivot_y_mm: float,
) -> float:
    support = minimum_support_pad_margin_mm(base, pivot_y_mm)
    bearing_rear, bearing_front = bearing_edge_margins_mm(
        base,
        pivot_y_mm,
    )
    return min(support, bearing_rear, bearing_front)


def optimized_pivot_y_mm(base: G.Rect) -> tuple[float, float]:
    best_y = None
    best_margin = float("-inf")
    steps = round(
        (PIVOT_SEARCH_MAX_Y_MM - PIVOT_SEARCH_MIN_Y_MM)
        / PIVOT_SEARCH_STEP_MM
    )
    for i in range(steps + 1):
        y = PIVOT_SEARCH_MIN_Y_MM + i * PIVOT_SEARCH_STEP_MM
        margin = critical_margin_mm(base, y)
        if margin > best_margin:
            best_y = y
            best_margin = margin
    assert best_y is not None
    return best_y, best_margin


def candidate_report(depth_mm: float) -> dict:
    base = G.Rect(width=G.BASE.width, depth=depth_mm)
    support = minimum_support_pad_margin_mm(base, G.PIVOT.y)
    bearing_rear, bearing_front = bearing_edge_margins_mm(
        base,
        G.PIVOT.y,
    )
    optimized_y, optimized_margin = optimized_pivot_y_mm(base)

    return {
        "base_depth_mm": depth_mm,
        "nominal_sounddeck_front_rear_margin_mm": round(
            (G.SOUNDDECK.depth - depth_mm) / 2.0,
            3,
        ),
        "current_pivot_y_mm": G.PIVOT.y,
        "current_pivot_support_pad_margin_mm": round(support, 3),
        "current_pivot_bearing_rear_margin_mm": round(
            bearing_rear, 3
        ),
        "current_pivot_bearing_front_margin_mm": round(
            bearing_front, 3
        ),
        "current_pivot_critical_margin_mm": round(
            min(support, bearing_rear, bearing_front),
            3,
        ),
        "balanced_pivot_y_mm": round(optimized_y, 3),
        "balanced_critical_margin_mm": round(
            optimized_margin, 3
        ),
        "fits_nominal_300mm_printer_y": (
            depth_mm <= G.PRINTER_Y
        ),
        "keeps_preferred_295mm_part_y": (
            depth_mm <= G.PREFERRED_PART_XY
        ),
        "needs_new_y_segmentation_for_preferred_margin": (
            depth_mm > G.PREFERRED_PART_XY
        ),
    }


def main() -> dict:
    candidates = [
        candidate_report(depth)
        for depth in CANDIDATE_DEPTHS_MM
    ]
    report = {
        "current_base_mm": [G.BASE.width, G.BASE.depth],
        "sounddeck_nominal_mm": [
            G.SOUNDDECK.width,
            G.SOUNDDECK.depth,
        ],
        "note": (
            "Analytical trade-off only. Nominal Sounddeck dimensions do not "
            "prove its usable flat top. Measure the real flat surface before "
            "selecting a deeper base."
        ),
        "candidates": candidates,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    main()
