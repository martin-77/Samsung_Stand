#!/usr/bin/env python3
"""Installed OCC validation for v7 replaceable wear surfaces."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import geometry_model as G
import v2_params as V2
import v7_params as P


ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
OUT=os.path.join(ROOT,"build_v7")


def v(x,y,z):
    return App.Vector(float(x),float(y),float(z))


def load_step(name):
    path=os.path.join(OUT,name+".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing v7 STEP: "+path)
    doc=App.newDocument("asm_"+name)
    Import.insert(path,doc.Name)
    doc.recompute()
    shapes=[o.Shape.copy() for o in doc.Objects if hasattr(o,"Shape") and not o.Shape.isNull()]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No shape in "+path)
    sh=shapes[0]
    for other in shapes[1:]:
        sh=sh.fuse(other)
    return sh.removeSplitter()


def common_volume(a,b):
    return float(a.common(b).Volume)


def distance(a,b):
    return float(a.distToShape(b)[0])


def installed_center_ring():
    sh=load_step("samsung_stand_v7_center_wear_ring")
    sh.translate(v(G.PIVOT.x,G.PIVOT.y,P.CENTER_INSERT_INSTALL_Z))
    return sh


def installed_track_arc(side):
    sh=load_step("samsung_stand_v7_track_wear_arc")
    angle=V2.RIGHT_ARM_ANGLE_DEG if side=="right" else V2.LEFT_ARM_ANGLE_DEG
    sh.rotate(v(0,0,0),v(0,0,1),angle)
    sh.translate(v(G.PIVOT.x,G.PIVOT.y,P.TRACK_INSERT_INSTALL_Z))
    return sh


def installed_rotor(swivel_deg):
    sh=load_step("samsung_stand_v7_rotor")
    sh.translate(v(0,0,V2.ROTOR_INSTALL_Z))
    sh.rotate(v(G.PIVOT.x,G.PIVOT.y,0),v(0,0,1),swivel_deg)
    return sh


def installed_inner(side,swivel_deg):
    sh=load_step("samsung_stand_v7_inner_arm")
    angle=(V2.RIGHT_ARM_ANGLE_DEG if side=="right" else V2.LEFT_ARM_ANGLE_DEG)+swivel_deg
    sh.translate(v(V2.INNER_R0,0,0))
    sh.rotate(v(0,0,0),v(0,0,1),angle)
    sh.translate(v(G.PIVOT.x,G.PIVOT.y,V2.TRACK_TOP_Z))
    return sh


def main():
    center=load_step("samsung_stand_v7_base_center")
    left_base=load_step("samsung_stand_v7_base_left")
    right_base=load_step("samsung_stand_v7_base_right")
    ring=installed_center_ring()
    left_arc=installed_track_arc("left")
    right_arc=installed_track_arc("right")

    failures=[]

    seating={}
    for name,insert,base in (
        ("center_ring",ring,center),
        ("left_track_arc",left_arc,left_base),
        ("right_track_arc",right_arc,right_base),
    ):
        vol=common_volume(insert,base)
        gap=distance(insert,base)
        seating[name]={
            "common_volume_mm3":round(vol,6),
            "distance_to_recess_mm":round(gap,6),
        }
        if vol>0.05:
            failures.append(f"{name} penetrates base: {vol:.6f} mm3")
        if gap>0.05:
            failures.append(f"{name} not seated in recess: gap {gap:.6f} mm")

    rotor_contacts={}
    for angle in (-15.0,0.0,15.0):
        rotor=installed_rotor(angle)
        rv=common_volume(rotor,ring)
        rd=distance(rotor,ring)
        bv=common_volume(rotor,center)
        rotor_contacts[f"{angle:+.1f}"]={
            "rotor_ring_common_volume_mm3":round(rv,6),
            "rotor_ring_distance_mm":round(rd,6),
            "rotor_base_common_volume_mm3":round(bv,6),
            "rotor_base_distance_mm":round(distance(rotor,center),6),
        }
        if rv>0.05:
            failures.append(f"{angle:+.1f} rotor penetrates wear ring: {rv:.6f} mm3")
        if rd>0.05:
            failures.append(f"{angle:+.1f} rotor not supported by wear ring: gap {rd:.6f} mm")
        # Structural stop contact occurs only beyond +/-15; at target and inside
        # there must be no solid rotor/base interference.
        if bv>0.10:
            failures.append(f"{angle:+.1f} rotor/base interference before stop: {bv:.6f} mm3")

    track_contacts={}
    for side,arc,base in (
        ("left",left_arc,left_base),
        ("right",right_arc,right_base),
    ):
        track_contacts[side]={}
        for angle in (-15.0,0.0,15.0):
            arm=installed_inner(side,angle)
            av=common_volume(arm,arc)
            ad=distance(arm,arc)
            bv=common_volume(arm,base)
            track_contacts[side][f"{angle:+.1f}"]={
                "arm_wear_common_volume_mm3":round(av,6),
                "arm_wear_distance_mm":round(ad,6),
                "arm_base_common_volume_mm3":round(bv,6),
                "arm_base_distance_mm":round(distance(arm,base),6),
            }
            if av>0.05:
                failures.append(
                    f"{side} {angle:+.1f} arm penetrates wear arc: {av:.6f} mm3"
                )
            if ad>0.05:
                failures.append(
                    f"{side} {angle:+.1f} arm not supported by wear arc: gap {ad:.6f} mm"
                )
            if bv>0.05:
                failures.append(
                    f"{side} {angle:+.1f} arm penetrates recessed base: {bv:.6f} mm3"
                )

    # Re-prove positive end stops after center-bearing recess.
    stop_behavior={}
    for angle in (-15.5,-15.0,-14.0,0.0,14.0,15.0,15.5):
        rotor=installed_rotor(angle)
        vol=common_volume(rotor,center)
        stop_behavior[f"{angle:+.1f}"]=round(vol,6)

    for angle in (-15.0,-14.0,0.0,14.0,15.0):
        if stop_behavior[f"{angle:+.1f}"]>0.10:
            failures.append(
                f"v7 changed pre-stop behavior at {angle:+.1f}: "
                f"{stop_behavior[f'{angle:+.1f}']:.6f} mm3"
            )
    for angle in (-15.5,15.5):
        if stop_behavior[f"{angle:+.1f}"]<1.0:
            failures.append(f"v7 lost positive stop beyond {angle:+.1f}")

    report={
        "version":"v7",
        "wear_insert_seating":seating,
        "center_bearing_sweep":rotor_contacts,
        "side_track_sweep":track_contacts,
        "positive_stop_recheck_common_volumes_mm3":stop_behavior,
        "top_plane_contract":{
            "center_top_z_mm":P.CENTER_INSERT_TOP_Z,
            "expected_center_top_z_mm":G.BEARING_TOP_Z,
            "track_top_z_mm":P.TRACK_INSERT_TOP_Z,
            "expected_track_top_z_mm":V2.TRACK_TOP_Z,
        },
        "failed":failures,
    }

    with open(os.path.join(OUT,"ASSEMBLY_VALIDATION_v7.json"),"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2)

    print(json.dumps(report,indent=2))
    if failures:
        raise SystemExit("V7 ASSEMBLY VALIDATION FAILED: "+" | ".join(failures))


if __name__=="__main__":
    main()
