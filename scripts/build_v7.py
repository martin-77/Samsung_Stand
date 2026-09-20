#!/usr/bin/env python3
"""Build v7: validated v5 structure with replaceable flush PETG wear surfaces."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import
import MeshPart

import v7_geometry as WG
import v7_params as P


ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"build_v7")
V5_STEP=os.path.join(ROOT,"cad","v5","STEP")
os.makedirs(OUT,exist_ok=True)


def load_step(name):
    path=os.path.join(V5_STEP,name+".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing validated v5 STEP: "+path)
    doc=App.newDocument("import_"+name)
    Import.insert(path,doc.Name)
    doc.recompute()
    shapes=[
        obj.Shape.copy()
        for obj in doc.Objects
        if hasattr(obj,"Shape") and not obj.Shape.isNull()
    ]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No shape imported from "+path)
    sh=shapes[0]
    for other in shapes[1:]:
        sh=sh.fuse(other)
    return sh.removeSplitter()


def require_single(shape,label):
    if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or shape.Volume<=0:
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def base_center_v7():
    sh=load_step("samsung_stand_v5_base_center")
    sh=sh.cut(WG.center_recess()).removeSplitter()
    require_single(sh,"BASE_CENTER_V7")
    return sh


def side_base_v7(side):
    name=(
        "samsung_stand_v5_base_right"
        if side=="right"
        else "samsung_stand_v5_base_left"
    )
    sh=load_step(name)
    sh=sh.cut(WG.track_recess(side)).removeSplitter()
    require_single(sh,"BASE_"+side.upper()+"_V7")
    return sh


def export_shape(name,shape):
    require_single(shape,name)
    step=os.path.join(OUT,name+".step")
    fcstd=os.path.join(OUT,name+".FCStd")
    stl=os.path.join(OUT,name+".stl")

    shape.exportStep(step)
    doc=App.newDocument("export_"+name)
    obj=doc.addObject("Part::Feature",name)
    obj.Shape=shape.copy()
    doc.recompute()
    doc.saveAs(fcstd)
    App.closeDocument(doc.Name)

    mesh=MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=0.06,
        AngularDeflection=0.20,
        Relative=False,
    )
    if mesh.CountFacets<=0:
        raise RuntimeError(name+": empty tessellation")
    mesh.write(stl)

    bb=shape.BoundBox
    return {
        "volume_mm3":round(float(shape.Volume),3),
        "size_mm":[round(bb.XLength,3),round(bb.YLength,3),round(bb.ZLength,3)],
        "bbox_mm":[
            round(bb.XMin,3),round(bb.XMax,3),
            round(bb.YMin,3),round(bb.YMax,3),
            round(bb.ZMin,3),round(bb.ZMax,3),
        ],
        "facets":int(mesh.CountFacets),
    }


parts={
    "samsung_stand_v7_base_center":base_center_v7(),
    "samsung_stand_v7_base_left":side_base_v7("left"),
    "samsung_stand_v7_base_right":side_base_v7("right"),
    "samsung_stand_v7_rotor":load_step("samsung_stand_v5_rotor"),
    "samsung_stand_v7_inner_arm":load_step("samsung_stand_v5_inner_arm"),
    "samsung_stand_v7_outer_guide":load_step("samsung_stand_v5_outer_guide"),
    "samsung_stand_v7_saddle_insert_blank":load_step("samsung_stand_v5_saddle_insert_blank"),
    "samsung_stand_v7_arm_lock_pin":load_step("samsung_stand_v5_arm_lock_pin"),
    "samsung_stand_v7_base_joint_retainer":load_step("samsung_stand_v5_base_joint_retainer"),
    "samsung_stand_v7_pivot_clip":load_step("samsung_stand_v5_pivot_clip"),
    "samsung_stand_v7_detent_pin":load_step("samsung_stand_v5_detent_pin"),
    "samsung_stand_v7_detent_cassette_t18":load_step("samsung_stand_v5_detent_cassette_t18"),
    "samsung_stand_v7_detent_cassette_t22":load_step("samsung_stand_v5_detent_cassette_t22"),
    "samsung_stand_v7_detent_cassette_t26":load_step("samsung_stand_v5_detent_cassette_t26"),
    "samsung_stand_v7_center_wear_ring":WG.center_wear_ring(),
    "samsung_stand_v7_track_wear_arc":WG.universal_track_wear_arc(),
}

report={
    "version":"v7",
    "upstream":"validated cad/v5/STEP",
    "wear":{
        "material":"PETG",
        "thickness_mm":P.WEAR_THICKNESS,
        "center_ring_quantity":1,
        "track_arc_quantity":2,
        "top_planes_unchanged":True,
    },
    "print_quantities":{
        "samsung_stand_v7_base_center":1,
        "samsung_stand_v7_base_left":1,
        "samsung_stand_v7_base_right":1,
        "samsung_stand_v7_rotor":1,
        "samsung_stand_v7_inner_arm":2,
        "samsung_stand_v7_outer_guide":2,
        "samsung_stand_v7_center_wear_ring":1,
        "samsung_stand_v7_track_wear_arc":2,
    },
    "parts":{},
}

for name,sh in parts.items():
    report["parts"][name]=export_shape(name,sh)

with open(os.path.join(OUT,"VALIDATION_v7_source.json"),"w",encoding="utf-8") as f:
    json.dump(report,f,indent=2)

print(json.dumps(report,indent=2))
