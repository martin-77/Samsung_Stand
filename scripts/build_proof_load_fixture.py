#!/usr/bin/env python3
"""Build flat proof-load inserts for physical structural testing.

The inserts replace the final measured Samsung saddle inserts during proof-load
testing. They seat in the exact v8 INNER_ARM saddle pockets and present a flat,
slightly raised load surface so a rigid load-spreader board can apply force at
the two validated saddle stations without using the television.
"""

from __future__ import annotations

import json
import os

import FreeCAD as App
import MeshPart
import Part

import v2_params as V2


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_proof_load_fixture")
os.makedirs(OUT, exist_ok=True)

FIT_CLEARANCE = 0.30
PAD_LENGTH = V2.SADDLE_POCKET_LENGTH - 2.0 * FIT_CLEARANCE
PAD_WIDTH = V2.SADDLE_POCKET_WIDTH - 2.0 * FIT_CLEARANCE
PAD_HEIGHT = 11.0
POCKET_FLOOR_Z = V2.SADDLE_POCKET_FLOOR
ARM_TOP_Z = V2.INNER_TOTAL_HEIGHT
PROUD_HEIGHT = POCKET_FLOOR_Z + PAD_HEIGHT - ARM_TOP_Z

# Keep a flat top for a rigid spreader. A shallow underside relief avoids
# elephant-foot/high-spot seating at the pocket perimeter.
UNDERSIDE_RELIEF = 0.35
UNDERSIDE_RELIEF_MARGIN = 3.0


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def proof_pad():
    outer = Part.makeBox(
        PAD_LENGTH,
        PAD_WIDTH,
        PAD_HEIGHT,
        v(-PAD_LENGTH / 2.0, -PAD_WIDTH / 2.0, 0),
    )

    relief = Part.makeBox(
        PAD_LENGTH - 2.0 * UNDERSIDE_RELIEF_MARGIN,
        PAD_WIDTH - 2.0 * UNDERSIDE_RELIEF_MARGIN,
        UNDERSIDE_RELIEF + 0.1,
        v(
            -PAD_LENGTH / 2.0 + UNDERSIDE_RELIEF_MARGIN,
            -PAD_WIDTH / 2.0 + UNDERSIDE_RELIEF_MARGIN,
            -0.05,
        ),
    )

    # Four corner feet + perimeter band remain as deterministic seating surfaces.
    sh = outer.cut(relief).removeSplitter()
    if sh.isNull() or not sh.isValid() or len(sh.Solids) != 1:
        raise RuntimeError("invalid proof-load pad")
    return sh


def export_shape(name, shape):
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


pad = proof_pad()
name = "proof_load_saddle_pad"
part = export_shape(name, pad)

report = {
    "purpose": "physical proof-load fixture at validated saddle stations",
    "quantity": 2,
    "fit_clearance_each_side_mm": FIT_CLEARANCE,
    "pad_size_mm": [PAD_LENGTH, PAD_WIDTH, PAD_HEIGHT],
    "installed_proud_height_above_inner_arm_mm": PROUD_HEIGHT,
    "load_application": {
        "recommended": (
            "Use two pads, one per INNER_ARM. Place a rigid, flat spreader board "
            "across both pads and place a non-fragile test load on the board. "
            "Do not let the board contact OUTER_GUIDE, rotor, or fixed base."
        ),
        "support_surface": (
            "Rigid flat surrogate support under the complete adapter base; "
            "do not use the Magnat Sounddeck for the 500 N structural proof."
        ),
        "do_not_use_tv": True,
        "do_not_use_sounddeck_for_500n_proof": True,
        "target_load_source": "PHYSICAL_RELEASE_GATES.md",
    },
    "part": part,
}

with open(
    os.path.join(OUT, "PROOF_LOAD_FIXTURE_REPORT.json"),
    "w",
    encoding="utf-8",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
