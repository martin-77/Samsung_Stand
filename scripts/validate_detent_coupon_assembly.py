#!/usr/bin/env python3
"""OCC validation for the compact v5 detent calibration rig."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import geometry_model as G
import v5_geometry as DG
import v5_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_detent_coupon")
CALIBRATION_T = 2.2


def v(x,y,z):
    return App.Vector(float(x),float(y),float(z))


def load_step(name):
    path=os.path.join(OUT,name+".step")
    doc=App.newDocument("asm_"+name)
    Import.insert(path,doc.Name)
    doc.recompute()
    shapes=[o.Shape.copy() for o in doc.Objects if hasattr(o,"Shape") and not o.Shape.isNull()]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No STEP shape: "+path)
    sh=shapes[0]
    for other in shapes[1:]:
        sh=sh.fuse(other)
    return sh.removeSplitter()


def common_volume(a,b):
    return float(a.common(b).Volume)


def distance(a,b):
    return float(a.distToShape(b)[0])


def installed_cam(angle_deg):
    sh=load_step("detent_coupon_cam")
    sh.translate(v(0,0,P.DETENT_MOUNT_TOP_Z))
    sh.rotate(v(G.PIVOT.x,G.PIVOT.y,0),v(0,0,1),angle_deg)
    return sh


def main():
    base=load_step("detent_coupon_base")
    cassette=DG.install_cassette(DG.detent_cassette_shape(CALIBRATION_T))
    body=DG.install_cassette(DG.detent_cassette_body_shape(CALIBRATION_T))
    nose=DG.install_cassette(DG.detent_nose_shape())

    failures=[]

    cassette_vol=common_volume(cassette,base)
    cassette_gap=distance(cassette,base)
    if cassette_vol>0.05:
        failures.append(f"cassette/base penetration {cassette_vol:.6f} mm3")
    if cassette_gap>0.05:
        failures.append(f"cassette not seated on coupon mount {cassette_gap:.6f} mm")

    sweep={}
    for angle in (-15.0,-7.5,0.0,7.5,15.0):
        cam=installed_cam(angle)
        base_vol=common_volume(cam,base)
        base_gap=distance(cam,base)
        body_vol=common_volume(cam,body)
        nose_vol=common_volume(cam,nose)
        nose_gap=distance(cam,nose)

        sweep[f"{angle:+.1f}"]={
            "cam_base_common_volume_mm3":round(base_vol,6),
            "cam_base_distance_mm":round(base_gap,6),
            "spring_body_common_volume_mm3":round(body_vol,6),
            "nose_common_volume_mm3":round(nose_vol,6),
            "nose_distance_mm":round(nose_gap,6),
        }

        if base_vol>0.05:
            failures.append(f"{angle:+.1f} deg cam/base collision {base_vol:.6f} mm3")
        if body_vol>0.05:
            failures.append(f"{angle:+.1f} deg spring body/cam collision {body_vol:.6f} mm3")

        if angle==0.0:
            if not 0.05<=nose_gap<=0.25:
                failures.append(f"zero nose gap {nose_gap:.6f} mm outside v5 target")
            if nose_vol>0.05:
                failures.append(f"zero nose penetrates cam {nose_vol:.6f} mm3")
        else:
            if nose_vol<=0.05:
                failures.append(f"{angle:+.1f} deg nose does not engage cam")

    neg=sweep["-15.0"]["nose_common_volume_mm3"]
    pos=sweep["+15.0"]["nose_common_volume_mm3"]
    sym=abs(neg-pos)/max(abs(neg),abs(pos),1.0)
    if sym>0.03:
        failures.append(f"cam/nose asymmetry {sym:.6f}")

    report={
        "version":"detent-coupon",
        "calibration_thickness_mm":CALIBRATION_T,
        "cassette_mount":{
            "distance_mm":round(cassette_gap,6),
            "common_volume_mm3":round(cassette_vol,6),
        },
        "sweep":sweep,
        "nose_symmetry_relative_delta":round(sym,8),
        "failed":failures,
    }

    with open(os.path.join(OUT,"DETENT_COUPON_ASSEMBLY_VALIDATION.json"),"w",encoding="utf-8") as f:
        json.dump(report,f,indent=2)

    print(json.dumps(report,indent=2))
    if failures:
        raise SystemExit("DETENT COUPON ASSEMBLY FAILED: "+" | ".join(failures))


if __name__=="__main__":
    main()
