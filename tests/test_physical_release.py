#!/usr/bin/env python3

import json
import pathlib
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

import validate_physical_release as V


def passing_record():
    def proof():
        return {
            "load_n":500.0,
            "duration_minutes":15.0,
            "permanent_deformation_detected":False,
            "crack_or_layer_separation":False,
            "whitening":False,
            "retainer_loosened":False,
            "wear_insert_unseated":False,
        }
    return {
        "meta":{
            "structural_version":"v8",
            "contact_parts_version":"v6_contacts",
            "printer":"Prusa CORE One L",
            "material":"PETG",
            "nozzle_mm":0.4,
            "layer_height_mm":0.2,
            "tested_by":"synthetic-ci",
            "date":"2026-09-20",
            "notes":"",
        },
        "criteria":{
            "proof_load_min_n":500.0,
            "proof_dwell_min_minutes_per_position":10.0,
            "creep_load_min_n":164.0,
            "creep_dwell_min_hours":24.0,
            "swivel_cycles_min":100,
            "end_stop_contacts_each_side_min":20,
            "rationale":"Synthetic CI criteria only; real project criteria must be chosen before test.",
        },
        "measurement_gate":{
            "real_measurements_complete":True,
            "measured_contact_parts_generated":True,
            "dry_fit_original_stand_passed":True,
        },
        "fit_coupons":{
            "base_roof_key_clearance_mm":0.4,
            "inner_roof_key_clearance_mm":0.4,
            "outer_roof_key_clearance_mm":0.4,
            "base_retainer_passed":True,
            "outer_retainer_passed":True,
            "pivot_retainer_passed":True,
            "detent_variant_mm":2.2,
            "detent_passed":True,
        },
        "proof_load":{
            "center":proof(),
            "minus_15":proof(),
            "plus_15":proof(),
        },
        "sounddeck_interface":{
            "unloaded_base_movement_detected":False,
            "loaded_base_movement_detected":False,
            "surface_damage_or_indentation":False,
        },
        "creep_dwell":{
            "load_n":164.0,
            "duration_hours":24.0,
            "progressive_set_detected":False,
            "joint_play_increased":False,
            "whitening":False,
            "wear_insert_unseated":False,
            "post_unload_swivel_ok":True,
        },
        "cycling":{
            "swivel_cycles_completed":100,
            "minus_end_stop_contacts":20,
            "plus_end_stop_contacts":20,
            "stop_damage":False,
            "detent_degraded":False,
            "retainer_walkout":False,
        },
        "evidence":{
            "photos_committed":True,
            "measurement_results_committed":True,
            "notes":"",
        },
    }


class PhysicalReleaseValidationTests(unittest.TestCase):
    def write(self,data):
        f=tempfile.NamedTemporaryFile(mode="w",suffix=".json",delete=False)
        json.dump(data,f)
        f.close()
        self.addCleanup(lambda:pathlib.Path(f.name).unlink(missing_ok=True))
        return f.name

    def test_complete_record_passes(self):
        report=V.main(self.write(passing_record()))
        self.assertTrue(report["ok"])
        self.assertEqual(report["failed"],[])

    def test_proof_criterion_cannot_be_below_500N(self):
        d=passing_record()
        d["criteria"]["proof_load_min_n"]=499.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("development load" in x for x in report["failed"]))

    def test_declared_proof_dwell_is_enforced(self):
        d=passing_record()
        d["proof_load"]["plus_15"]["duration_minutes"]=9.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("plus_15" in x for x in report["failed"]))

    def test_detected_whitening_fails(self):
        d=passing_record()
        d["proof_load"]["center"]["whitening"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("whitening" in x for x in report["failed"]))

    def test_anti_slip_failure_fails(self):
        d=passing_record()
        d["sounddeck_interface"]["loaded_base_movement_detected"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("loaded_base_movement" in x for x in report["failed"]))

    def test_creep_criterion_is_declared_then_enforced(self):
        d=passing_record()
        d["criteria"]["creep_dwell_min_hours"]=48.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("creep_dwell.duration_hours" in x for x in report["failed"]))

    def test_cycle_counts_are_enforced(self):
        d=passing_record()
        d["cycling"]["swivel_cycles_completed"]=99
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("swivel_cycles_completed" in x for x in report["failed"]))


if __name__=="__main__":
    unittest.main()
