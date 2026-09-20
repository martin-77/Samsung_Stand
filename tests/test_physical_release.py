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
            "single_saddle_proof_load_min_n":250.0,
            "creep_load_min_n":164.0,
            "creep_dwell_min_hours":24.0,
            "swivel_cycles_min":100,
            "end_stop_contacts_each_side_min":20,
            "rationale":"Synthetic CI criteria only; real project criteria must be chosen before test.",
        },
        "proof_setup":{
            "support_surface":"rigid_surrogate",
            "sounddeck_used":False,
            "notes":"synthetic CI",
        },
        "measurement_gate":{
            "real_measurements_complete":True,
            "measured_contact_parts_generated":True,
            "dry_fit_original_stand_passed":True,
            "saddle_root_center_tip_contact_confirmed":True,
            "saddle_rocking_detected":False,
            "saddle_unexpected_hard_spot_detected":False,
            "outer_guide_lateral_fit_confirmed":True,
            "outer_guide_vertical_free_clearance_confirmed":True,
            "outer_guide_floor_contact_detected":False,
            "outer_liners_fully_seated":True,
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
            "left_saddle_only":{**proof(),"load_n":250.0},
            "right_saddle_only":{**proof(),"load_n":250.0},
        },
        "sounddeck_interface":{
            "test_load_n":164.0,
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
            "outer_liner_unseated":False,
            "outer_liner_axial_walkout":False,
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

    def test_release_is_bound_to_petg_and_target_printer(self):
        d=passing_record()
        d["meta"]["material"]="PLA"
        d["meta"]["printer"]="Other Printer"
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("meta.printer must be" in x for x in report["failed"]))
        self.assertTrue(any("meta.material must be" in x for x in report["failed"]))

    def test_contact_parts_version_is_required(self):
        d=passing_record()
        d["meta"]["contact_parts_version"]=""
        with self.assertRaises(V.ReleaseError):
            V.main(self.write(d))

    def test_saddle_rocking_fails_release(self):
        d=passing_record()
        d["measurement_gate"]["saddle_rocking_detected"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("saddle_rocking_detected" in x for x in report["failed"]))

    def test_outer_guide_floor_contact_fails_release(self):
        d=passing_record()
        d["measurement_gate"]["outer_guide_floor_contact_detected"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("outer_guide_floor_contact_detected" in x for x in report["failed"]))

    def test_missing_three_section_contact_confirmation_fails(self):
        d=passing_record()
        d["measurement_gate"]["saddle_root_center_tip_contact_confirmed"]=False
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("saddle_root_center_tip_contact_confirmed" in x for x in report["failed"]))

    def test_proof_criterion_cannot_be_below_500N(self):
        d=passing_record()
        d["criteria"]["proof_load_min_n"]=499.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("development load" in x for x in report["failed"]))

    def test_single_saddle_branch_load_floor_is_enforced(self):
        d=passing_record()
        d["criteria"]["single_saddle_proof_load_min_n"]=249.0
        d["proof_load"]["left_saddle_only"]["load_n"]=249.0
        d["proof_load"]["right_saddle_only"]["load_n"]=249.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("one-side development branch load" in x for x in report["failed"]))

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

    def test_structural_proof_cannot_use_real_sounddeck(self):
        d=passing_record()
        d["proof_setup"]["support_surface"]="sounddeck"
        d["proof_setup"]["sounddeck_used"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("rigid_surrogate" in x for x in report["failed"]))
        self.assertTrue(any("500 N structural proof" in x for x in report["failed"]))

    def test_sounddeck_interface_load_is_limited_to_near_service_load(self):
        d=passing_record()
        d["sounddeck_interface"]["test_load_n"]=500.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("110% service-load" in x for x in report["failed"]))

    def test_sounddeck_interface_load_cannot_be_below_service_load(self):
        d=passing_record()
        d["sounddeck_interface"]["test_load_n"]=150.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("below real TV service load" in x for x in report["failed"]))

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

    def test_creep_criterion_cannot_be_below_real_tv_service_load(self):
        d=passing_record()
        d["criteria"]["creep_load_min_n"]=150.0
        d["creep_dwell"]["load_n"]=150.0
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("static TV service load" in x for x in report["failed"]))

    def test_outer_liner_unseating_fails_cycling_gate(self):
        d=passing_record()
        d["cycling"]["outer_liner_unseated"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("outer_liner_unseated" in x for x in report["failed"]))

    def test_outer_liner_axial_walkout_fails_cycling_gate(self):
        d=passing_record()
        d["cycling"]["outer_liner_axial_walkout"]=True
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("outer_liner_axial_walkout" in x for x in report["failed"]))

    def test_cycle_counts_are_enforced(self):
        d=passing_record()
        d["cycling"]["swivel_cycles_completed"]=99
        report=V.main(self.write(d))
        self.assertFalse(report["ok"])
        self.assertTrue(any("swivel_cycles_completed" in x for x in report["failed"]))

    def test_false_gate_helper_accepts_false_and_rejects_true(self):
        failures=[]
        V.require_false(False,"x",failures)
        self.assertEqual(failures,[])
        V.require_false(True,"x",failures)
        self.assertEqual(failures,["x is true"])


if __name__=="__main__":
    unittest.main()
