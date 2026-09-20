#!/usr/bin/env python3

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_base_depth as A
import geometry_model as G


class BaseDepthTradeoffTests(unittest.TestCase):
    def test_current_base_margin_matches_v2_gate(self):
        row = A.candidate_report(295.0)
        self.assertAlmostEqual(
            row["current_pivot_support_pad_margin_mm"],
            7.204,
            places=3,
        )
        self.assertAlmostEqual(
            row["current_pivot_bearing_rear_margin_mm"],
            8.5,
            places=3,
        )
        self.assertAlmostEqual(
            row["current_pivot_critical_margin_mm"],
            7.204,
            places=3,
        )

    def test_current_pivot_is_near_balanced_optimum(self):
        row = A.candidate_report(G.BASE.depth)
        self.assertAlmostEqual(
            row["balanced_pivot_y_mm"],
            -64.65,
            delta=0.1,
        )
        self.assertLess(
            abs(row["balanced_pivot_y_mm"] - G.PIVOT.y),
            1.0,
        )

    def test_deeper_base_improves_both_critical_y_margins(self):
        current = A.candidate_report(295.0)
        deeper = A.candidate_report(320.0)
        self.assertGreater(
            deeper["current_pivot_support_pad_margin_mm"],
            current["current_pivot_support_pad_margin_mm"],
        )
        self.assertGreater(
            deeper["current_pivot_bearing_rear_margin_mm"],
            current["current_pivot_bearing_rear_margin_mm"],
        )
        self.assertAlmostEqual(
            deeper["nominal_sounddeck_front_rear_margin_mm"],
            10.0,
            places=6,
        )

    def test_more_than_295mm_requires_new_preferred_y_segmentation(self):
        row = A.candidate_report(320.0)
        self.assertTrue(
            row["needs_new_y_segmentation_for_preferred_margin"]
        )
        self.assertFalse(row["keeps_preferred_295mm_part_y"])


if __name__ == "__main__":
    unittest.main()
