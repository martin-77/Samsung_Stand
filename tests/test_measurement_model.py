#!/usr/bin/env python3

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from measurement_model import MeasurementError, load_measurements, symmetry_report


def rect_profile(width=24.0, height=8.0):
    w = width / 2.0
    return [[-w, 0.0], [w, 0.0], [w, height], [-w, height]]


def complete_measurements():
    return {
        "meta": {
            "model": "Samsung UE55J6250",
            "stand_part": "BN96-38964A",
            "measured_by": "test",
            "date": "2026-09-20",
            "caliper_resolution_mm": 0.01,
            "notes": "",
        },
        "global": {
            "stand_width_mm": 840.0,
            "stand_depth_mm": 289.0,
            "pivot_to_rear_mm": 80.0,
            "left_tip_xy_mm": [-420.0, 208.0],
            "right_tip_xy_mm": [420.0, 208.0],
        },
        "inner_saddle": {
            "left": {
                "station_radius_mm": 279.0,
                "profile_points_mm": rect_profile(26.0, 9.0),
                "notes": "",
            },
            "right": {
                "station_radius_mm": 279.5,
                "profile_points_mm": rect_profile(26.2, 9.1),
                "notes": "",
            },
        },
        "outer_guide": {
            "left": {
                "root": {"station_radius_mm": 320.0, "profile_points_mm": rect_profile(24.0, 8.5)},
                "mid": {"station_radius_mm": 390.0, "profile_points_mm": rect_profile(22.0, 8.0)},
                "tip": {"station_radius_mm": 455.0, "profile_points_mm": rect_profile(20.0, 7.5)},
                "notes": "",
            },
            "right": {
                "root": {"station_radius_mm": 320.5, "profile_points_mm": rect_profile(24.2, 8.6)},
                "mid": {"station_radius_mm": 390.5, "profile_points_mm": rect_profile(22.1, 8.1)},
                "tip": {"station_radius_mm": 455.5, "profile_points_mm": rect_profile(20.1, 7.6)},
                "notes": "",
            },
        },
        "contact_pad": {
            "used": False,
            "compressed_thickness_mm": 0.0,
            "notes": "",
        },
    }


class MeasurementModelTests(unittest.TestCase):
    def write_temp(self, data):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(data, f)
        f.close()
        self.addCleanup(lambda: pathlib.Path(f.name).unlink(missing_ok=True))
        return f.name

    def test_complete_measurement_set_loads(self):
        ms = load_measurements(self.write_temp(complete_measurements()))
        self.assertAlmostEqual(ms.stand_width, 840.0)
        self.assertAlmostEqual(ms.inner_left.profile.width, 26.0)
        self.assertEqual(len(ms.outer_left), 3)

    def test_left_right_differences_are_reported_not_rejected(self):
        ms = load_measurements(self.write_temp(complete_measurements()))
        report = symmetry_report(ms)
        self.assertAlmostEqual(report["inner_profile_width_delta_mm"], 0.2, places=6)
        self.assertAlmostEqual(report["tip_y_delta_mm"], 0.0, places=6)

    def test_missing_profile_is_rejected(self):
        d = complete_measurements()
        d["inner_saddle"]["left"]["profile_points_mm"] = None
        with self.assertRaises(MeasurementError):
            load_measurements(self.write_temp(d))

    def test_self_intersecting_profile_is_rejected(self):
        d = complete_measurements()
        d["inner_saddle"]["left"]["profile_points_mm"] = [
            [-10.0, 0.0], [10.0, 8.0], [-10.0, 8.0], [10.0, 0.0]
        ]
        with self.assertRaises(MeasurementError):
            load_measurements(self.write_temp(d))

    def test_pad_thickness_must_match_used_flag(self):
        d = complete_measurements()
        d["contact_pad"]["compressed_thickness_mm"] = 1.0
        with self.assertRaises(MeasurementError):
            load_measurements(self.write_temp(d))

    def test_outer_station_radii_must_increase(self):
        d = complete_measurements()
        d["outer_guide"]["left"]["mid"]["station_radius_mm"] = 319.0
        with self.assertRaises(MeasurementError):
            load_measurements(self.write_temp(d))

    def test_implausible_global_width_rejected(self):
        d = complete_measurements()
        d["global"]["stand_width_mm"] = 600.0
        with self.assertRaises(MeasurementError):
            load_measurements(self.write_temp(d))


if __name__ == "__main__":
    unittest.main()
