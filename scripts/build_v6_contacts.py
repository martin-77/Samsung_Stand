#!/usr/bin/env python3
"""Build measurement-driven v6 Samsung contact parts.

This script never guesses missing Samsung geometry. It requires a complete
measurement JSON accepted by measurement_model.py.

Generated parts:
- side-specific INNER saddle inserts with a measured underside support envelope;
- side-specific OUTER guide liners that preserve the v3 structural guide and
  add only lateral contact surfaces.

Usage with FreeCADCmd:
    FreeCADCmd -c "import sys; sys.path.insert(0,'scripts'); import build_v6_contacts as B; B.main('measurements/stand_measurements.json','build_v6_contacts')"
"""

from __future__ import annotations

import json
import math
import os

import FreeCAD as App
import MeshPart
import Part

import measurement_model as M
import v2_params as V2
import v3_params as V3


SADDLE_BASE_THICKNESS = 4.0
SADDLE_NOMINAL_LOWEST_CONTACT_Z = V2.SADDLE_INSERT_HEIGHT
SADDLE_PROFILE_SAMPLES = 41

GUIDE_LATERAL_CLEARANCE = 0.50
GUIDE_LINER_X0 = 12.0
GUIDE_LINER_X1 = V3.OUTER_VISIBLE_LENGTH - 12.0
GUIDE_LINER_Z0_IN_GUIDE = V3.OUTER_FLOOR_THICKNESS
GUIDE_LINER_HEIGHT = V3.OUTER_WALL_HEIGHT - GUIDE_LINER_Z0_IN_GUIDE
GUIDE_CHANNEL_HALF_WIDTH = V3.OUTER_CHANNEL_PLACEHOLDER_WIDTH / 2.0
GUIDE_CROSSBAR_HEIGHT = 2.0
GUIDE_CROSSBAR_LENGTH = 5.0
GUIDE_CROSSBAR_X = (20.0, 85.0, 150.0)


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def require_single(shape, label):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def fuse_all(shapes):
    out = shapes[0]
    for sh in shapes[1:]:
        out = out.fuse(sh)
    return out.removeSplitter()


def saddle_insert(profile: M.Profile, pad_thickness: float):
    env = M.lower_envelope(profile, SADDLE_PROFILE_SAMPLES)
    contact_low = SADDLE_NOMINAL_LOWEST_CONTACT_Z - pad_thickness
    if contact_low <= SADDLE_BASE_THICKNESS + 1.0:
        raise RuntimeError("contact pad leaves insufficient saddle insert thickness")

    pocket_half_y = V2.SADDLE_INSERT_WIDTH / 2.0
    if profile.ymin < -pocket_half_y + 0.5 or profile.ymax > pocket_half_y - 0.5:
        raise RuntimeError(
            "measured saddle profile is too wide for existing v5 insert pocket: "
            f"profile [{profile.ymin:.3f},{profile.ymax:.3f}], "
            f"insert half-width {pocket_half_y:.3f}"
        )

    base = Part.makeBox(
        V2.SADDLE_INSERT_LENGTH,
        V2.SADDLE_INSERT_WIDTH,
        SADDLE_BASE_THICKNESS,
        v(
            -V2.SADDLE_INSERT_LENGTH / 2.0,
            -V2.SADDLE_INSERT_WIDTH / 2.0,
            0,
        ),
    )

    # YZ section: bottom is fused into the flat base; top follows the measured
    # lower envelope. Lowest physical stand point remains at the v5 contact plane.
    yz = [(env[0][0], SADDLE_BASE_THICKNESS)]
    yz += [(y, contact_low + z) for y, z in env]
    yz += [(env[-1][0], SADDLE_BASE_THICKNESS)]

    pts = [v(-V2.SADDLE_INSERT_LENGTH / 2.0, y, z) for y, z in yz]
    wire = Part.makePolygon(pts + [pts[0]])
    cap = Part.Face(wire).extrude(v(V2.SADDLE_INSERT_LENGTH, 0, 0))

    sh = base.fuse(cap).removeSplitter()
    require_single(sh, "SADDLE_INSERT")
    return sh


def _side_surface(profile: M.Profile, side: str) -> float:
    if side == "left":
        return profile.ymin - GUIDE_LATERAL_CLEARANCE
    if side == "right":
        return profile.ymax + GUIDE_LATERAL_CLEARANCE
    raise ValueError(side)


def _loft_side_rail(stations, wall_side: str):
    sections = []
    # Map measured radial station to local OUTER_GUIDE X.
    measured = [(st.radius - V3.OUTER_R0, st.profile) for st in stations]
    measured.sort(key=lambda x: x[0])

    if measured[0][0] > GUIDE_LINER_X0:
        measured.insert(0, (GUIDE_LINER_X0, measured[0][1]))
    else:
        measured[0] = (GUIDE_LINER_X0, measured[0][1])

    if measured[-1][0] < GUIDE_LINER_X1:
        measured.append((GUIDE_LINER_X1, measured[-1][1]))
    else:
        measured[-1] = (GUIDE_LINER_X1, measured[-1][1])

    for x, profile in measured:
        if x < GUIDE_LINER_X0 - 1e-6 or x > GUIDE_LINER_X1 + 1e-6:
            raise RuntimeError(
                f"outer measurement station x={x:.3f} lies outside liner span "
                f"{GUIDE_LINER_X0:.3f}..{GUIDE_LINER_X1:.3f}"
            )

        if wall_side == "left":
            y0 = -GUIDE_CHANNEL_HALF_WIDTH
            y1 = _side_surface(profile, "left")
            if y1 <= y0 + 1.0:
                raise RuntimeError("left guide liner would be thinner than 1 mm")
        else:
            y0 = _side_surface(profile, "right")
            y1 = GUIDE_CHANNEL_HALF_WIDTH
            if y1 <= y0 + 1.0:
                raise RuntimeError("right guide liner would be thinner than 1 mm")

        z0 = 0.0
        z1 = GUIDE_LINER_HEIGHT
        pts = [
            v(x, y0, z0),
            v(x, y1, z0),
            v(x, y1, z1),
            v(x, y0, z1),
        ]
        sections.append(Part.makePolygon(pts + [pts[0]]))

    sh = Part.makeLoft(sections, True, False)
    require_single(sh, "GUIDE_" + wall_side.upper() + "_RAIL")
    return sh


def outer_guide_liner(stations):
    left = _loft_side_rail(stations, "left")
    right = _loft_side_rail(stations, "right")

    bars = []
    for x in GUIDE_CROSSBAR_X:
        if GUIDE_LINER_X0 <= x <= GUIDE_LINER_X1 - GUIDE_CROSSBAR_LENGTH:
            bars.append(
                Part.makeBox(
                    GUIDE_CROSSBAR_LENGTH,
                    2.0 * GUIDE_CHANNEL_HALF_WIDTH,
                    GUIDE_CROSSBAR_HEIGHT,
                    v(x, -GUIDE_CHANNEL_HALF_WIDTH, 0),
                )
            )

    sh = fuse_all([left, right] + bars)
    require_single(sh, "OUTER_GUIDE_LINER")
    return sh


def export_shape(out_dir, name, shape):
    require_single(shape, name)
    os.makedirs(out_dir, exist_ok=True)

    step = os.path.join(out_dir, name + ".step")
    fcstd = os.path.join(out_dir, name + ".FCStd")
    stl = os.path.join(out_dir, name + ".stl")

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
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ": empty tessellation")
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "volume_mm3": round(float(shape.Volume), 3),
        "size_mm": [round(bb.XLength,3), round(bb.YLength,3), round(bb.ZLength,3)],
        "bbox_mm": [
            round(bb.XMin,3), round(bb.XMax,3),
            round(bb.YMin,3), round(bb.YMax,3),
            round(bb.ZMin,3), round(bb.ZMax,3),
        ],
        "facets": int(mesh.CountFacets),
    }


def main(measurement_path: str, out_dir: str = "build_v6_contacts"):
    ms = M.load_measurements(measurement_path)
    pad = ms.pad_thickness if ms.pad_used else 0.0

    parts = {
        "samsung_stand_v6_saddle_insert_left": saddle_insert(ms.inner_left.profile, pad),
        "samsung_stand_v6_saddle_insert_right": saddle_insert(ms.inner_right.profile, pad),
        "samsung_stand_v6_outer_liner_left": outer_guide_liner(ms.outer_left),
        "samsung_stand_v6_outer_liner_right": outer_guide_liner(ms.outer_right),
    }

    report = {
        "version": "v6-contact-parts",
        "measurement_path": measurement_path,
        "measurement_symmetry": {
            k: round(vv,4) for k,vv in M.symmetry_report(ms).items()
        },
        "design_clearances": {
            "outer_lateral_each_side_mm": GUIDE_LATERAL_CLEARANCE,
            "contact_pad_compressed_mm": pad,
            "saddle_lowest_printed_contact_z_mm": (
                SADDLE_NOMINAL_LOWEST_CONTACT_Z - pad
            ),
        },
        "structural_note": (
            "These parts change only Samsung-contact geometry. V8 structural "
            "load path, outer guide shell, end stops and detent remain upstream."
        ),
        "parts": {},
    }

    for name, shape in parts.items():
        report["parts"][name] = export_shape(out_dir, name, shape)

    with open(os.path.join(out_dir, "VALIDATION_v6_contacts_source.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("measurement_path")
    ap.add_argument("--out", default="build_v6_contacts")
    ns = ap.parse_args()
    main(ns.measurement_path, ns.out)
