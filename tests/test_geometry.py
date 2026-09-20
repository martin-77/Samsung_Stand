#!/usr/bin/env python3

import math
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import geometry_model as G


class GeometryBaselineTests(unittest.TestCase):
    def test_fixed_base_fits_sounddeck(self):
        self.assertLessEqual(G.BASE.width, G.SOUNDDECK.width)
        self.assertLessEqual(G.BASE.depth, G.SOUNDDECK.depth)

    def test_expected_zero_degree_stand_overhang(self):
        self.assertAlmostEqual(
            (G.STAND_WIDTH - G.SOUNDDECK.width) / 2.0,
            70.0,
            places=6,
        )

    def test_arm_reconstruction_matches_tip(self):
        self.assertAlmostEqual(
            G.STAND_HALF_WIDTH * G.ARM_SLOPE,
            G.STAND_TIP_Y,
            places=9,
        )

    def test_saddle_radius(self):
        expected = math.hypot(G.SADDLE_LOCAL_X, G.SADDLE_LOCAL_Y)
        self.assertAlmostEqual(G.SADDLE_RADIUS, expected, places=9)
        self.assertGreater(G.SADDLE_RADIUS, 275.0)
        self.assertLess(G.SADDLE_RADIUS, 282.0)

    def test_zero_degree_saddles_are_symmetric(self):
        left, right = G.saddle_centers(0.0)
        self.assertAlmostEqual(left.x, -right.x, places=9)
        self.assertAlmostEqual(left.y, right.y, places=9)

    def test_full_sweep_keeps_saddle_centers_on_sounddeck(self):
        for angle in G.sweep_angles(0.5):
            with self.subTest(angle=angle):
                for p in G.saddle_centers(angle):
                    self.assertTrue(G.rect_contains_point(G.SOUNDDECK, p))

    def test_full_sweep_keeps_40mm_support_pads_on_sounddeck(self):
        for angle in G.sweep_angles(0.5):
            with self.subTest(angle=angle):
                for p in G.saddle_centers(angle):
                    self.assertTrue(G.support_pad_inside_sounddeck(p))

    def test_end_positions_are_mirrored(self):
        left_neg, right_neg = G.saddle_centers(-G.SWIVEL_LIMIT_DEG)
        left_pos, right_pos = G.saddle_centers(+G.SWIVEL_LIMIT_DEG)

        self.assertAlmostEqual(left_neg.x, -right_pos.x, places=9)
        self.assertAlmostEqual(left_neg.y, right_pos.y, places=9)
        self.assertAlmostEqual(right_neg.x, -left_pos.x, places=9)
        self.assertAlmostEqual(right_neg.y, left_pos.y, places=9)

    def test_declared_modules_fit_core_one_l(self):
        for name, (x, y, z) in G.PRINT_MODULES.items():
            with self.subTest(module=name):
                self.assertLessEqual(x, G.PRINTER_X)
                self.assertLessEqual(y, G.PRINTER_Y)
                self.assertLessEqual(z, G.PRINTER_Z)

    def test_large_parts_keep_preferred_xy_margin(self):
        for name, (x, y, _z) in G.PRINT_MODULES.items():
            with self.subTest(module=name):
                self.assertLessEqual(x, G.PREFERRED_PART_XY)
                self.assertLessEqual(y, G.PREFERRED_PART_XY)

    def test_v1_side_module_envelope_includes_joint_overlap(self):
        expected = G.BASE_SIDE_WIDTH + G.JOINT_OVERLAP
        self.assertAlmostEqual(G.PRINT_MODULES["BASE_LEFT"][0], expected)
        self.assertAlmostEqual(G.PRINT_MODULES["BASE_RIGHT"][0], expected)

    def test_joint_roof_is_support_friendly(self):
        rise = G.JOINT_KEY_APEX_Z - G.JOINT_KEY_WALL_TOP_Z
        run = G.JOINT_KEY_HALF_WIDTH
        angle = math.degrees(math.atan2(rise, run))
        self.assertGreaterEqual(angle, 45.0)

    def test_swivel_bearing_fits_rear_offset_base(self):
        radius = G.BEARING_OUTER_DIAMETER / 2.0
        rear_margin = (G.PIVOT.y - radius) - G.BASE.ymin
        front_margin = G.BASE.ymax - (G.PIVOT.y + radius)
        self.assertGreaterEqual(rear_margin, 8.0)
        self.assertGreater(front_margin, rear_margin)

    def test_verified_service_load_is_below_development_proof_load(self):
        self.assertAlmostEqual(G.TV_WITH_STAND_MASS_KG, 16.7, places=6)
        self.assertGreater(G.SERVICE_VERTICAL_LOAD_N, 160.0)
        self.assertLess(G.SERVICE_VERTICAL_LOAD_N, 170.0)
        self.assertGreater(
            G.DESIGN_VERTICAL_LOAD_N / G.SERVICE_VERTICAL_LOAD_N,
            3.0,
        )

    def test_annular_bearing_is_primary_large_area_path(self):
        self.assertGreaterEqual(G.BEARING_NOMINAL_AREA_MM2, 12000.0)
        self.assertLessEqual(G.BEARING_NOMINAL_PRESSURE_MPA, 0.04)

    def test_pivot_has_clearance_but_clip_captures_rotor(self):
        self.assertGreaterEqual(
            G.PIVOT_BORE_DIAMETER - G.PIVOT_STEM_DIAMETER,
            1.0,
        )
        self.assertGreater(
            G.PIVOT_CLIP_OUTER_DIAMETER,
            G.PIVOT_BORE_DIAMETER + 4.0,
        )


if __name__ == "__main__":
    unittest.main()
