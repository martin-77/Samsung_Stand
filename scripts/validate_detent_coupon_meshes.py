#!/usr/bin/env python3
"""Mesh/print validation for detent calibration rig."""

from __future__ import annotations

import glob
import json
import os

import trimesh

import geometry_model as G


ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"build_detent_coupon")

paths=sorted(glob.glob(os.path.join(OUT,"detent_coupon_*.stl")))
if not paths:
    raise SystemExit("No detent coupon STL files found")

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

# Spring variants must remain geometry-identical in envelope while volume rises.
volumes=[]
for suffix,t in (("18",1.8),("22",2.2),("26",2.6)):
    name=f"detent_coupon_cassette_t{suffix}.stl"
    volumes.append((t,results[name]["volume_mm3"]))

if not all(volumes[i][1]<volumes[i+1][1] for i in range(len(volumes)-1)):
    failed.append("detent cassette volumes are not monotonic with thickness")

report={
    "version":"detent-coupon",
    "meshes":results,
    "cassette_volumes":volumes,
    "failed":failed,
}
with open(os.path.join(OUT,"DETENT_COUPON_MESH_VALIDATION.json"),"w",encoding="utf-8") as f:
    json.dump(report,f,indent=2)

print(json.dumps(report,indent=2))
if failed:
    raise SystemExit("DETENT COUPON MESH VALIDATION FAILED: "+" | ".join(failed))
