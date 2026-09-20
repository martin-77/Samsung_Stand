#!/usr/bin/env python3
"""Build compact physical fit coupons for v8 structural retainers."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import MeshPart
import Part

import geometry_model as G
import v8_geometry as LG
import v8_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_retainer_coupons")
os.makedirs(OUT, exist_ok=True)


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def require_single(shape, label):
    if (
        shape.isNull()
        or not shape.isValid()
        or len(shape.Solids) != 1
        or shape.Volume <= 0
    ):
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def base_lock_receiver():
    block = Part.makeBox(
        22.0,
        G.JOINT_RECEIVER_WIDTH,
        20.0,
        v(-11.0, -G.JOINT_RECEIVER_WIDTH / 2.0, 0),
    )
    sh = block.cut(LG.base_lock_tunnel(0.0, 0.0)).removeSplitter()
    require_single(sh, "BASE_LOCK_RECEIVER_COUPON")
    return sh


def outer_lock_receiver():
    # Reproduce the 58 mm saddle width that originally hid the v3 lock tunnel.
    block = Part.makeBox(
        22.0,
        58.0,
        15.0,
        v(-11.0, -29.0, 0),
    )
    sh = block.cut(LG.outer_lock_tunnel(0.0)).removeSplitter()
    require_single(sh, "OUTER_LOCK_RECEIVER_COUPON")
    return sh


def pivot_post_receiver():
    flange = Part.makeCylinder(20.0, 4.0)
    post = Part.makeCylinder(
        P.PIVOT_POST_DIAMETER / 2.0,
        P.PIVOT_POST_TOP_Z,
    )
    sh = flange.fuse(post).removeSplitter()

    tunnel = LG.pivot_post_tunnel()
    tunnel.translate(v(-G.PIVOT.x, -G.PIVOT.y, 0))
    sh = sh.cut(tunnel).removeSplitter()

    require_single(sh, "PIVOT_POST_RECEIVER_COUPON")
    return sh


def export_shape(name, shape):
    require_single(shape, name)

    step = os.path.join(OUT, name + ".step")
    fcstd = os.path.join(OUT, name + ".FCStd")
    stl = os.path.join(OUT, name + ".stl")

    shape.exportStep(step)

    doc = App.newDocument("export_" + name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape.copy()
    doc.recompute()
    doc.saveAs(fcstd)
    App.closeDocument(doc.Name)

    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=0.05,
        AngularDeflection=0.20,
        Relative=False,
    )
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "volume_mm3": round(float(shape.Volume), 3),
        "size_mm": [
            round(bb.XLength, 3),
            round(bb.YLength, 3),
            round(bb.ZLength, 3),
        ],
        "facets": int(mesh.CountFacets),
    }


parts = {
    "retainer_coupon_base_receiver": base_lock_receiver(),
    "retainer_coupon_joint_pin": LG.joint_lock_pin(),
    "retainer_coupon_outer_receiver": outer_lock_receiver(),
    "retainer_coupon_outer_pin": LG.outer_lock_pin(),
    "retainer_coupon_pivot_post": pivot_post_receiver(),
    "retainer_coupon_pivot_pin": LG.pivot_lock_pin(),
}

report = {
    "purpose": "physical calibration of v8 snap retainers before large prints",
    "families": {
        "base_joint": {
            "receiver_width_mm": G.JOINT_RECEIVER_WIDTH,
            "pin": "retainer_coupon_joint_pin",
            "receiver": "retainer_coupon_base_receiver",
        },
        "outer_joint": {
            "receiver_width_mm": 58.0,
            "pin": "retainer_coupon_outer_pin",
            "receiver": "retainer_coupon_outer_receiver",
        },
        "pivot": {
            "post_diameter_mm": P.PIVOT_POST_DIAMETER,
            "pin": "retainer_coupon_pivot_pin",
            "receiver": "retainer_coupon_pivot_post",
        },
    },
    "test_rule": (
        "Pin must insert without cracking/whitening, snap positively after the "
        "far wall, resist light manual pullout, and remain removable by "
        "compressing the split-end legs. Reject any family that requires "
        "hammering or leaves permanent PETG set."
    ),
    "parts": {},
}

for name, shape in parts.items():
    report["parts"][name] = export_shape(name, shape)

with open(
    os.path.join(OUT, "RETAINER_COUPON_REPORT.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
