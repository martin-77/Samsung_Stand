#!/usr/bin/env python3
"""Mesh validation for v8 proof-load saddle pad."""

from __future__ import annotations

import json
import os

import trimesh

import geometry_model as G
import v2_params as V2


ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"build_proof_load_fixture")
PATH=os.path.join(OUT,"proof_load_saddle_pad.stl")

mesh=trimesh.load(PATH,force="mesh",process=True)
ext=mesh.extents
failures=[]

if not mesh.is_watertight:
    failures.append("mesh not watertight")
if not mesh.is_winding_consistent:
    failures.append("mesh winding inconsistent")
if abs(mesh.volume)<=1.0:
    failures.append("non-positive/empty mesh volume")
if ext[0]>G.PRINTER_X or ext[1]>G.PRINTER_Y or ext[2]>G.PRINTER_Z:
    failures.append("does not fit CORE One L")
if ext[0]>V2.SADDLE_POCKET_LENGTH or ext[1]>V2.SADDLE_POCKET_WIDTH:
    failures.append("proof pad exceeds saddle pocket XY envelope")

report={
    "version":"proof-load-fixture",
    "watertight":bool(mesh.is_watertight),
    "winding_consistent":bool(mesh.is_winding_consistent),
    "volume_mm3":float(abs(mesh.volume)),
    "extents_mm":[round(float(x),3) for x in ext],
    "bounds_mm":[
        [round(float(x),3) for x in mesh.bounds[0]],
        [round(float(x),3) for x in mesh.bounds[1]],
    ],
    "failed":failures,
}

with open(
    os.path.join(OUT,"PROOF_LOAD_MESH_VALIDATION.json"),
    "w",encoding="utf-8"
) as f:
    json.dump(report,f,indent=2)

print(json.dumps(report,indent=2))
if failures:
    raise SystemExit("PROOF LOAD MESH VALIDATION FAILED: "+" | ".join(failures))
