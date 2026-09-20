#!/usr/bin/env python3
"""Validate a complete physical Samsung stand measurement file."""

from __future__ import annotations

import argparse
import json
import sys

from measurement_model import MeasurementError, load_measurements, symmetry_report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ns = ap.parse_args()

    try:
        ms = load_measurements(ns.path)
    except (MeasurementError, json.JSONDecodeError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 2

    report = {
        "ok": True,
        "global": {
            "stand_width_mm": ms.stand_width,
            "stand_depth_mm": ms.stand_depth,
            "pivot_to_rear_mm": ms.pivot_to_rear,
            "left_tip_xy_mm": ms.left_tip_xy,
            "right_tip_xy_mm": ms.right_tip_xy,
        },
        "inner_saddle": {
            "left": {
                "radius_mm": ms.inner_left.radius,
                "profile_width_mm": round(ms.inner_left.profile.width, 4),
                "profile_height_mm": round(ms.inner_left.profile.height, 4),
                "profile_area_mm2": round(ms.inner_left.profile.area, 4),
            },
            "right": {
                "radius_mm": ms.inner_right.radius,
                "profile_width_mm": round(ms.inner_right.profile.width, 4),
                "profile_height_mm": round(ms.inner_right.profile.height, 4),
                "profile_area_mm2": round(ms.inner_right.profile.area, 4),
            },
        },
        "outer_guide": {},
        "contact_pad": {
            "used": ms.pad_used,
            "compressed_thickness_mm": ms.pad_thickness,
        },
        "symmetry_report": {
            k: round(v, 4) for k, v in symmetry_report(ms).items()
        },
        "symmetry_note": (
            "Differences are reported, not rejected. Final contact parts remain side-specific."
        ),
    }

    for side, stations in (("left", ms.outer_left), ("right", ms.outer_right)):
        report["outer_guide"][side] = []
        for name, st in zip(("root", "mid", "tip"), stations):
            report["outer_guide"][side].append(
                {
                    "station": name,
                    "radius_mm": st.radius,
                    "profile_width_mm": round(st.profile.width, 4),
                    "profile_height_mm": round(st.profile.height, 4),
                    "profile_area_mm2": round(st.profile.area, 4),
                }
            )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
