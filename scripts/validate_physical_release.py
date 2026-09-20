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
    nonempty(meta.get("printer"),"meta.printer")
    nonempty(meta.get("material"),"meta.material")
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
    creep_min=number(criteria.get("creep_load_min_n"),"criteria.creep_load_min_n",positive=True)
    creep_hours=number(criteria.get("creep_dwell_min_hours"),"criteria.creep_dwell_min_hours",positive=True)
    swivel_min=number(criteria.get("swivel_cycles_min"),"criteria.swivel_cycles_min",positive=True)
    stop_min=number(
        criteria.get("end_stop_contacts_each_side_min"),
        "criteria.end_stop_contacts_each_side_min",
        positive=True,
    )
    nonempty(criteria.get("rationale"),"criteria.rationale")

    measurement=data.get("measurement_gate",{})
    for key in (
        "real_measurements_complete",
        "measured_contact_parts_generated",
        "dry_fit_original_stand_passed",
    ):
        require_true(measurement.get(key),f"measurement_gate.{key}",failures)

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
    for position in ("center","minus_15","plus_15"):
        row=proof.get(position,{})
        load=number(row.get("load_n"),f"proof_load.{position}.load_n",positive=True)
        dwell=number(row.get("duration_minutes"),f"proof_load.{position}.duration_minutes",positive=True)
        if load+1e-9<proof_min:
            failures.append(f"proof_load.{position}.load_n below declared criterion")
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
    for key in ("stop_damage","detent_degraded","retainer_walkout"):
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
        "declared_criteria":{
            "proof_load_min_n":proof_min,
            "proof_dwell_min_minutes_per_position":proof_dwell,
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
