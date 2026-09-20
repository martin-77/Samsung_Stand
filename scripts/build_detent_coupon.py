#!/usr/bin/env python3
"""Build a compact physical calibration rig for the v5 zero detent.

The rig reuses the exact v5 cam track and cassette geometry so spring feel can
be selected before printing the full structural base/rotor.
"""

from __future__ import annotations

import json
import math
import os

import FreeCAD as App
import MeshPart
import Part

import geometry_model as G
import v5_geometry as DG
import v5_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_detent_coupon")
os.makedirs(OUT, exist_ok=True)

BASE_XMIN = -45.0
BASE_XMAX = 135.0
BASE_YMIN = -110.0
BASE_YMAX = 45.0
BASE_THICKNESS = 4.0

PIVOT_POST_RADIUS = 5.0
PIVOT_POST_TOP_Z = 18.0
ROTOR_BORE_RADIUS = 5.5

HUB_SUPPORT_R_INNER = 8.0
HUB_SUPPORT_R_OUTER = 31.0
HUB_SUPPORT_TOP_Z = P.DETENT_MOUNT_TOP_Z

ROTOR_HUB_RADIUS = 35.0
ROTOR_THICKNESS = P.DETENT_TRACK_HEIGHT
TRACK_SPOKE_R0 = 30.0
TRACK_SPOKE_R1 = P.DETENT_TRACK_R_INNER + 3.0
TRACK_SPOKE_WIDTH = 12.0

HANDLE_ANGLE_DEG = 205.0
HANDLE_R0 = 25.0
HANDLE_R1 = 85.0
HANDLE_WIDTH = 14.0
HANDLE_KNOB_RADIUS = 10.0


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def require_single(shape, label):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def radial_box(r0, r1, angle_deg, width, z0, height):
    sh = Part.makeBox(
        r1 - r0,
        width,
        height,
        v(G.PIVOT.x + r0, G.PIVOT.y - width / 2.0, z0),
    )
    sh.rotate(v(G.PIVOT.x, G.PIVOT.y, 0), v(0,0,1), angle_deg)
    return sh


def fixed_base():
    floor = Part.makeBox(
        BASE_XMAX - BASE_XMIN,
        BASE_YMAX - BASE_YMIN,
        BASE_THICKNESS,
        v(BASE_XMIN, BASE_YMIN, 0),
    )

    support_outer = Part.makeCylinder(
        HUB_SUPPORT_R_OUTER,
        HUB_SUPPORT_TOP_Z - BASE_THICKNESS,
        v(G.PIVOT.x, G.PIVOT.y, BASE_THICKNESS),
    )
    support_inner = Part.makeCylinder(
        HUB_SUPPORT_R_INNER,
        HUB_SUPPORT_TOP_Z - BASE_THICKNESS + 1.0,
        v(G.PIVOT.x, G.PIVOT.y, BASE_THICKNESS - 0.5),
    )
    support = support_outer.cut(support_inner)

    pivot = Part.makeCylinder(
        PIVOT_POST_RADIUS,
        PIVOT_POST_TOP_Z - BASE_THICKNESS,
        v(G.PIVOT.x, G.PIVOT.y, BASE_THICKNESS),
    )

    mount = DG.detent_mount_shape()

    sh = floor.fuse(support).fuse(pivot).fuse(mount).removeSplitter()
    sh = sh.cut(DG.detent_mount_holes_shape()).removeSplitter()
    require_single(sh, "DETENT_COUPON_BASE")
    return sh


def moving_cam():
    hub = Part.makeCylinder(
        ROTOR_HUB_RADIUS,
        ROTOR_THICKNESS,
        v(G.PIVOT.x, G.PIVOT.y, 0),
    )
    bore = Part.makeCylinder(
        ROTOR_BORE_RADIUS,
        ROTOR_THICKNESS + 2.0,
        v(G.PIVOT.x, G.PIVOT.y, -1.0),
    )
    hub = hub.cut(bore)

    spoke = radial_box(
        TRACK_SPOKE_R0,
        TRACK_SPOKE_R1,
        P.DETENT_HOME_ANGLE_DEG,
        TRACK_SPOKE_WIDTH,
        0.0,
        ROTOR_THICKNESS,
    )
    track = DG.rotor_detent_track_shape()

    handle = radial_box(
        HANDLE_R0,
        HANDLE_R1,
        HANDLE_ANGLE_DEG,
        HANDLE_WIDTH,
        0.0,
        ROTOR_THICKNESS,
    )
    a = math.radians(HANDLE_ANGLE_DEG)
    kx = G.PIVOT.x + HANDLE_R1 * math.cos(a)
    ky = G.PIVOT.y + HANDLE_R1 * math.sin(a)
    knob = Part.makeCylinder(
        HANDLE_KNOB_RADIUS,
        ROTOR_THICKNESS,
        v(kx, ky, 0),
    )

    sh = hub.fuse(spoke).fuse(track).fuse(handle).fuse(knob).removeSplitter()
    require_single(sh, "DETENT_COUPON_CAM")
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
        LinearDeflection=0.06,
        AngularDeflection=0.20,
        Relative=False,
    )
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "volume_mm3": round(float(shape.Volume),3),
        "size_mm": [round(bb.XLength,3),round(bb.YLength,3),round(bb.ZLength,3)],
        "facets": int(mesh.CountFacets),
    }


parts = {
    "detent_coupon_base": fixed_base(),
    "detent_coupon_cam": moving_cam(),
    "detent_coupon_pin": DG.detent_pin_shape(),
}
for t in P.DETENT_SPRING_THICKNESSES:
    suffix = int(round(t * 10))
    parts[f"detent_coupon_cassette_t{suffix:02d}"] = DG.detent_cassette_shape(t)

report = {
    "purpose": "physical zero-detent spring calibration before full stand print",
    "uses_exact_v5_geometry": True,
    "cassette_variants_mm": list(P.DETENT_SPRING_THICKNESSES),
    "assembly": {
        "cam_install_z_mm": P.DETENT_MOUNT_TOP_Z,
        "pins_required": 2,
        "instruction": (
            "Install one cassette with two pins, place cam at z=10 over pivot, "
            "and rotate gently through the center notch. Choose the lowest "
            "spring thickness that centers reliably without whitening or excessive torque."
        ),
    },
    "parts": {},
}

for name, sh in parts.items():
    report["parts"][name] = export_shape(name, sh)

with open(os.path.join(OUT, "DETENT_COUPON_REPORT.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
