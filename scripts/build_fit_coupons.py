#!/usr/bin/env python3
"""Generate support-free vertical fit coupons for structural roof-key joints.

The coupon axis is rotated to print vertically.  This tests the exact key/socket
cross-section and FDM clearance without spending material on the full modules.
"""

from __future__ import annotations

import json
import os

import FreeCAD as App
import MeshPart
import Part

import fit_coupon_params as C


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_fit_coupons")
os.makedirs(OUT, exist_ok=True)


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def polygon_face(points):
    pts = [v(x, y, 0) for x, y in points]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire)


def male_profile(family):
    return [
        (-family.half_width, 0.0),
        (+family.half_width, 0.0),
        (+family.half_width, family.wall_top_from_bottom),
        (0.0, family.apex_from_bottom),
        (-family.half_width, family.wall_top_from_bottom),
    ]


def receiver_profile(family, clearance):
    underside = clearance * family.underside_factor
    return [
        (-family.half_width - clearance, -underside),
        (+family.half_width + clearance, -underside),
        (
            +family.half_width + clearance,
            family.wall_top_from_bottom + clearance,
        ),
        (0.0, family.apex_from_bottom + clearance),
        (
            -family.half_width - clearance,
            family.wall_top_from_bottom + clearance,
        ),
    ]


def male_probe(family):
    profile = polygon_face(male_profile(family))
    shaft = profile.extrude(v(0, 0, C.PROBE_HEIGHT))

    # Broad print flange only at the bottom; insertion uses the free top end.
    max_w = 2.0 * family.half_width + 10.0
    max_d = family.apex_from_bottom + 10.0
    flange = Part.makeBox(
        max_w,
        max_d,
        C.PROBE_FLANGE_HEIGHT,
        v(-max_w / 2.0, -5.0, 0.0),
    )
    return shaft.fuse(flange).removeSplitter()


def receiver_socket(family, clearance):
    cavity_pts = receiver_profile(family, clearance)
    xs = [p[0] for p in cavity_pts]
    ys = [p[1] for p in cavity_pts]

    xmin = min(xs) - C.SOCKET_WALL
    xmax = max(xs) + C.SOCKET_WALL
    ymin = min(ys) - C.SOCKET_WALL
    ymax = max(ys) + C.SOCKET_WALL

    block = Part.makeBox(
        xmax - xmin,
        ymax - ymin,
        C.SOCKET_HEIGHT,
        v(xmin, ymin, 0.0),
    )
    cavity = polygon_face(cavity_pts).extrude(v(0, 0, C.SOCKET_HEIGHT + 2.0))
    cavity.translate(v(0, 0, -1.0))
    return block.cut(cavity).removeSplitter()


def export_shape(name, shape):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(f"{name}: invalid coupon shape")

    step = os.path.join(OUT, name + ".step")
    stl = os.path.join(OUT, name + ".stl")
    fcstd = os.path.join(OUT, name + ".FCStd")

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


report = {
    "purpose": "structural roof-key cross-section calibration",
    "clearances_mm": list(C.CLEARANCES_MM),
    "instructions": (
        "Print the male probe and the three receiver sockets for the joint family. "
        "Use the smallest receiver that slides fully without force, binding or "
        "visible wall whitening. Nominal production clearance is currently 0.40 mm."
    ),
    "families": {},
    "parts": {},
}

for family in C.FAMILIES:
    family_report = {
        "nominal_production_clearance_mm": family.nominal_clearance,
        "underside_clearance_factor": family.underside_factor,
        "male_profile": male_profile(family),
        "receivers": {},
    }

    male_name = f"fit_{family.name}_male_probe"
    report["parts"][male_name] = export_shape(male_name, male_probe(family))

    for clearance in C.CLEARANCES_MM:
        suffix = int(round(clearance * 100.0))
        name = f"fit_{family.name}_receiver_c{suffix:03d}"
        family_report["receivers"][str(clearance)] = receiver_profile(
            family, clearance
        )
        report["parts"][name] = export_shape(
            name, receiver_socket(family, clearance)
        )

    report["families"][family.name] = family_report

with open(
    os.path.join(OUT, "FIT_COUPON_REPORT.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
