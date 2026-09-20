#!/usr/bin/env python3
"""Validate a recorded physical release test against declared project criteria.

Passing this validator means the repository's declared physical gates were
recorded as passed. It is not a certification or independent safety approval.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import geometry_model as G


class ReleaseError(ValueError):
    pass


def number(v: Any, path: str, *, positive=False) -> float:
    if not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(float(v)):
        raise ReleaseError(f"{path}: expected finite number")
    x=float(v)
    if positive and x<=0:
        raise ReleaseError(f"{path}: expected > 0")
    return x


def boolean(v: Any, path: str) -> bool:
    if not isinstance(v,bool):
        raise ReleaseError(f"{path}: expected boolean")
    return v


def nonempty(v: Any, path: str) -> str:
    if not isinstance(v,str) or not v.strip():
        raise ReleaseError(f"{path}: expected non-empty text")
    return v.strip()


def require_false(v: Any, path: str, failures: list[str]) -> None:
    if boolean(v,path):
        failures.append(path+" is true")


def require_true(v: Any, path: str, failures: list[str]) -> None:
    if not boolean(v,path):
        failures.append(path+" is false")


def main(path: str) -> dict[str,Any]:
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    failures=[]

    meta=data.get("meta",{})
    if meta.get("structural_version")!="v8":
        failures.append("meta.structural_version must be v8")
    printer=nonempty(meta.get("printer"),"meta.printer")
    material=nonempty(meta.get("material"),"meta.material")
    contact_parts_version=nonempty(
        meta.get("contact_parts_version"),
        "meta.contact_parts_version",
    )
    if printer != G.PRINTER_MODEL:
        failures.append(
            f"meta.printer must be {G.PRINTER_MODEL!r}, got {printer!r}"
        )
    if material.upper() != G.PRINT_MATERIAL:
        failures.append(
            f"meta.material must be {G.PRINT_MATERIAL!r}, got {material!r}"
        )
    number(meta.get("nozzle_mm"),"meta.nozzle_mm",positive=True)
    number(meta.get("layer_height_mm"),"meta.layer_height_mm",positive=True)
    nonempty(meta.get("tested_by"),"meta.tested_by")
    nonempty(meta.get("date"),"meta.date")

    criteria=data.get("criteria",{})
    proof_min=number(criteria.get("proof_load_min_n"),"criteria.proof_load_min_n",positive=True)
    if proof_min+1e-9 < G.DESIGN_VERTICAL_LOAD_N:
        failures.append(
            f"criteria.proof_load_min_n {proof_min:.1f} N is below "
            f"project development load {G.DESIGN_VERTICAL_LOAD_N:.1f} N"
        )
    proof_dwell=number(
        criteria.get("proof_dwell_min_minutes_per_position"),
        "criteria.proof_dwell_min_minutes_per_position",
        positive=True,
    )
    single_saddle_min=number(
        criteria.get("single_saddle_proof_load_min_n"),
        "criteria.single_saddle_proof_load_min_n",
        positive=True,
    )
    expected_single_saddle=G.DESIGN_VERTICAL_LOAD_N / 2.0
    if single_saddle_min + 1e-9 < expected_single_saddle:
        failures.append(
            f"criteria.single_saddle_proof_load_min_n "
            f"{single_saddle_min:.1f} N is below nominal one-side "
            f"development branch load {expected_single_saddle:.1f} N"
        )
    creep_min=number(
        criteria.get("creep_load_min_n"),
        "criteria.creep_load_min_n",
        positive=True,
    )
    if creep_min + 1e-9 < G.SERVICE_VERTICAL_LOAD_N:
        failures.append(
            f"criteria.creep_load_min_n {creep_min:.1f} N is below "
            f"verified static TV service load "
            f"{G.SERVICE_VERTICAL_LOAD_N:.1f} N"
        )
    creep_hours=number(criteria.get("creep_dwell_min_hours"),"criteria.creep_dwell_min_hours",positive=True)
    swivel_min=number(criteria.get("swivel_cycles_min"),"criteria.swivel_cycles_min",positive=True)
    stop_min=number(
        criteria.get("end_stop_contacts_each_side_min"),
        "criteria.end_stop_contacts_each_side_min",
        positive=True,
    )
    nonempty(criteria.get("rationale"),"criteria.rationale")

    proof_setup=data.get("proof_setup",{})
    if proof_setup.get("support_surface")!="rigid_surrogate":
        failures.append(
            "proof_setup.support_surface must be rigid_surrogate"
        )
    if proof_setup.get("sounddeck_used") is not False:
        failures.append(
            "proof_setup.sounddeck_used must be false; 500 N structural "
            "proof is not permitted on the real Sounddeck"
        )

    measurement=data.get("measurement_gate",{})
    for key in (
        "real_measurements_complete",
        "measured_contact_parts_generated",
        "dry_fit_original_stand_passed",
        "saddle_root_center_tip_contact_confirmed",
        "outer_guide_lateral_fit_confirmed",
        "outer_guide_vertical_free_clearance_confirmed",
        "outer_liners_fully_seated",
    ):
        require_true(measurement.get(key),f"measurement_gate.{key}",failures)

    for key in (
        "saddle_rocking_detected",
        "saddle_unexpected_hard_spot_detected",
        "outer_guide_floor_contact_detected",
    ):
        require_false(measurement.get(key),f"measurement_gate.{key}",failures)

    coupons=data.get("fit_coupons",{})
    for key in (
        "base_roof_key_clearance_mm",
        "inner_roof_key_clearance_mm",
        "outer_roof_key_clearance_mm",
    ):
        c=number(coupons.get(key),f"fit_coupons.{key}",positive=True)
        if not 0.20<=c<=0.70:
            failures.append(f"fit_coupons.{key}={c:.3f} mm outside sanity range 0.20..0.70")
    for key in (
        "base_retainer_passed",
        "outer_retainer_passed",
        "pivot_retainer_passed",
        "detent_passed",
    ):
        require_true(coupons.get(key),f"fit_coupons.{key}",failures)
    detent=number(coupons.get("detent_variant_mm"),"fit_coupons.detent_variant_mm",positive=True)
    if min(abs(detent-x) for x in (1.8,2.2,2.6))>1e-6:
        failures.append("fit_coupons.detent_variant_mm must be 1.8, 2.2 or 2.6")

    proof=data.get("proof_load",{})
    proof_cases=(
        ("center",proof_min),
        ("minus_15",proof_min),
        ("plus_15",proof_min),
        ("left_saddle_only",single_saddle_min),
        ("right_saddle_only",single_saddle_min),
    )
    for position,required_load in proof_cases:
        row=proof.get(position,{})
        load=number(row.get("load_n"),f"proof_load.{position}.load_n",positive=True)
        dwell=number(row.get("duration_minutes"),f"proof_load.{position}.duration_minutes",positive=True)
        if load+1e-9<required_load:
            failures.append(
                f"proof_load.{position}.load_n below declared criterion"
            )
        if dwell+1e-9<proof_dwell:
            failures.append(f"proof_load.{position}.duration_minutes below declared criterion")
        for key in (
            "permanent_deformation_detected",
            "crack_or_layer_separation",
            "whitening",
            "retainer_loosened",
            "wear_insert_unseated",
        ):
            require_false(row.get(key),f"proof_load.{position}.{key}",failures)

    interface=data.get("sounddeck_interface",{})
    sounddeck_test_load=number(
        interface.get("test_load_n"),
        "sounddeck_interface.test_load_n",
        positive=True,
    )
    if sounddeck_test_load + 1e-9 < G.SERVICE_VERTICAL_LOAD_N:
        failures.append(
            f"sounddeck_interface.test_load_n {sounddeck_test_load:.1f} N "
            f"is below real TV service load {G.SERVICE_VERTICAL_LOAD_N:.1f} N"
        )
    if sounddeck_test_load > G.SERVICE_VERTICAL_LOAD_N * 1.10:
        failures.append(
            f"sounddeck_interface.test_load_n {sounddeck_test_load:.1f} N "
            "exceeds the allowed 110% service-load interface-test ceiling; "
            "do not use the Sounddeck as the 500 N structural proof fixture"
        )
    for key in (
        "unloaded_base_movement_detected",
        "loaded_base_movement_detected",
        "surface_damage_or_indentation",
    ):
        require_false(interface.get(key),f"sounddeck_interface.{key}",failures)

    creep=data.get("creep_dwell",{})
    creep_load=number(creep.get("load_n"),"creep_dwell.load_n",positive=True)
    creep_duration=number(creep.get("duration_hours"),"creep_dwell.duration_hours",positive=True)
    if creep_load+1e-9<creep_min:
        failures.append("creep_dwell.load_n below declared criterion")
    if creep_duration+1e-9<creep_hours:
        failures.append("creep_dwell.duration_hours below declared criterion")
    for key in (
        "progressive_set_detected",
        "joint_play_increased",
        "whitening",
        "wear_insert_unseated",
    ):
        require_false(creep.get(key),f"creep_dwell.{key}",failures)
    require_true(creep.get("post_unload_swivel_ok"),"creep_dwell.post_unload_swivel_ok",failures)

    cycling=data.get("cycling",{})
    swivel=number(cycling.get("swivel_cycles_completed"),"cycling.swivel_cycles_completed",positive=True)
    neg=number(cycling.get("minus_end_stop_contacts"),"cycling.minus_end_stop_contacts",positive=True)
    pos=number(cycling.get("plus_end_stop_contacts"),"cycling.plus_end_stop_contacts",positive=True)
    if swivel+1e-9<swivel_min:
        failures.append("cycling.swivel_cycles_completed below declared criterion")
    if neg+1e-9<stop_min:
        failures.append("cycling.minus_end_stop_contacts below declared criterion")
    if pos+1e-9<stop_min:
        failures.append("cycling.plus_end_stop_contacts below declared criterion")
    for key in (
        "stop_damage",
        "detent_degraded",
        "retainer_walkout",
        "outer_liner_unseated",
        "outer_liner_axial_walkout",
    ):
        require_false(cycling.get(key),f"cycling.{key}",failures)

    evidence=data.get("evidence",{})
    require_true(evidence.get("photos_committed"),"evidence.photos_committed",failures)
    require_true(
        evidence.get("measurement_results_committed"),
        "evidence.measurement_results_committed",
        failures,
    )

    report={
        "ok":not failures,
        "structural_version":"v8",
        "contact_parts_version":contact_parts_version,
        "printer":printer,
        "material":material,
        "proof_setup":{
            "support_surface":proof_setup.get("support_surface"),
            "sounddeck_used":proof_setup.get("sounddeck_used"),
        },
        "sounddeck_interface_test_load_n":sounddeck_test_load,
        "verified_service_load":{
            "tv_with_stand_mass_kg":G.TV_WITH_STAND_MASS_KG,
            "static_vertical_load_n":round(G.SERVICE_VERTICAL_LOAD_N,3),
            "source":"Samsung Quick Start Guide BN68-07177M-00, p.14",
        },
        "declared_criteria":{
            "proof_load_min_n":proof_min,
            "proof_dwell_min_minutes_per_position":proof_dwell,
            "single_saddle_proof_load_min_n":single_saddle_min,
            "creep_load_min_n":creep_min,
            "creep_dwell_min_hours":creep_hours,
            "swivel_cycles_min":swivel_min,
            "end_stop_contacts_each_side_min":stop_min,
        },
        "interpretation":(
            "Passing means the project's declared physical gates were recorded "
            "as passed. It is not certification, a rated load, or independent approval."
        ),
        "failed":failures,
    }
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("path")
    ns=ap.parse_args()
    try:
        report=main(ns.path)
    except (ReleaseError,json.JSONDecodeError,OSError) as exc:
        report={"ok":False,"failed":[str(exc)]}
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report.get("ok") else 2)
