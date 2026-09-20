#!/usr/bin/env python3
"""Mesh and print-envelope validation for Samsung_Stand v7."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G
import v7_params as P


ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"build_v7")

paths=sorted(glob.glob(os.path.join(OUT,"samsung_stand_v7_*.stl")))
if not paths:
    raise SystemExit("No v7 STL files found")

results={}
failed=[]
for path in paths:
    name=os.path.basename(path)
    mesh=trimesh.load(path,force="mesh",process=True)
    ext=mesh.extents
    info={
        "watertight":bool(mesh.is_watertight),
        "winding_consistent":bool(mesh.is_winding_consistent),
        "volume_mm3":float(abs(mesh.volume)),
        "faces":int(len(mesh.faces)),
        "extents_mm":[round(float(x),3) for x in ext],
        "bounds_mm":[
            [round(float(x),3) for x in mesh.bounds[0]],
            [round(float(x),3) for x in mesh.bounds[1]],
        ],
        "fits_core_one_l":bool(
            ext[0]<=G.PRINTER_X+1e-6
            and ext[1]<=G.PRINTER_Y+1e-6
            and ext[2]<=G.PRINTER_Z+1e-6
        ),
    }
    info["ok"]=(
        info["watertight"]
        and info["winding_consistent"]
        and info["volume_mm3"]>1.0
        and info["fits_core_one_l"]
    )
    if not info["ok"]:
        failed.append(name)
    results[name]=info

ring=results.get("samsung_stand_v7_center_wear_ring.stl")
arc=results.get("samsung_stand_v7_track_wear_arc.stl")
wear_gate={"ok":False}
if ring and arc:
    wear_gate={
        "ring_extents_mm":ring["extents_mm"],
        "arc_extents_mm":arc["extents_mm"],
        "expected_thickness_mm":P.WEAR_THICKNESS,
        "ok":(
            abs(ring["extents_mm"][2]-P.WEAR_THICKNESS)<=0.02
            and abs(arc["extents_mm"][2]-P.WEAR_THICKNESS)<=0.02
            and ring["extents_mm"][0]<=G.PREFERRED_PART_XY
            and ring["extents_mm"][1]<=G.PREFERRED_PART_XY
            and arc["extents_mm"][0]<=G.PREFERRED_PART_XY
            and arc["extents_mm"][1]<=G.PREFERRED_PART_XY
        ),
    }
    if not wear_gate["ok"]:
        failed.append("v7_wear_insert_envelope")

left=results.get("samsung_stand_v7_base_left.stl")
right=results.get("samsung_stand_v7_base_right.stl")
sym={"ok":False}
if left and right:
    size_delta=[abs(a-b) for a,b in zip(left["extents_mm"],right["extents_mm"])]
    vol_delta=abs(left["volume_mm3"]-right["volume_mm3"])
    ref=max(left["volume_mm3"],right["volume_mm3"],1.0)
    sym={
        "size_delta_mm":[round(x,6) for x in size_delta],
        "relative_volume_delta":vol_delta/ref,
        "ok":all(x<=0.03 for x in size_delta) and vol_delta/ref<=2e-6,
    }
    if not sym["ok"]:
        failed.append("v7_side_base_symmetry")

report={
    "version":"v7",
    "meshes":results,
    "wear_insert_gate":wear_gate,
    "side_base_symmetry":sym,
    "failed":failed,
}
with open(os.path.join(OUT,"MESH_VALIDATION_v7.json"),"w",encoding="utf-8") as f:
    json.dump(report,f,indent=2)

print(json.dumps(report,indent=2))
if failed:
    raise SystemExit("V7 MESH VALIDATION FAILED: "+" | ".join(failed))
