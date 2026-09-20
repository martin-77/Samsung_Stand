#!/usr/bin/env python3
"""Generate the first printable Samsung_Stand v1 base/rotor CAD set.

Run with FreeCADCmd:
    FreeCADCmd -c "import sys; sys.path.insert(0,'scripts'); import build_v1"
"""

from __future__ import annotations

import json
import math
import os

import FreeCAD as App
import MeshPart
import Part

import geometry_model as G


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v1")
os.makedirs(OUT, exist_ok=True)


def v(x: float, y: float, z: float) -> App.Vector:
    return App.Vector(float(x), float(y), float(z))


def fuse_all(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes:
        raise ValueError("fuse_all() requires at least one shape")
    out = shapes[0]
    for sh in shapes[1:]:
        out = out.fuse(sh)
    return out.removeSplitter()


def require_single(shape, label: str):
    if shape.isNull():
        raise RuntimeError(f"{label}: null shape")
    if not shape.isValid():
        raise RuntimeError(f"{label}: invalid OCC shape")
    solids = len(shape.Solids)
    if solids != 1:
        raise RuntimeError(f"{label}: expected one solid, got {solids}")
    if shape.Volume <= 0:
        raise RuntimeError(f"{label}: non-positive volume")


def beam_xy(x1, y1, x2, y2, width, z0, height):
    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)
    if length <= 0:
        raise ValueError("zero-length beam")
    sh = Part.makeBox(length, width, height, v(0, -width / 2.0, z0))
    sh.rotate(v(0, 0, 0), v(0, 0, 1), math.degrees(math.atan2(dy, dx)))
    sh.translate(v(x1, y1, 0))
    return sh


def roof_key_prism(xmin, xmax, y_center, clearance=0.0):
    """Support-friendly pentagonal rail/cavity, extruded along +X."""
    hw = G.JOINT_KEY_HALF_WIDTH + clearance
    z0 = G.BASE_FLOOR_THICKNESS - clearance
    wall_top = G.JOINT_KEY_WALL_TOP_Z + clearance
    apex = G.JOINT_KEY_APEX_Z + clearance
    pts = [
        v(xmin, y_center - hw, z0),
        v(xmin, y_center + hw, z0),
        v(xmin, y_center + hw, wall_top),
        v(xmin, y_center, apex),
        v(xmin, y_center - hw, wall_top),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    face = Part.Face(wire)
    return face.extrude(v(xmax - xmin, 0, 0))


def retainer_hole(x_center, y_center):
    return Part.makeBox(
        G.RETAINER_HOLE_X,
        G.RETAINER_HOLE_Y,
        G.JOINT_RECEIVER_HEIGHT + 3.0,
        v(
            x_center - G.RETAINER_HOLE_X / 2.0,
            y_center - G.RETAINER_HOLE_Y / 2.0,
            -1.0,
        ),
    )


def center_base():
    floor = Part.makeBox(
        G.BASE_CENTER_WIDTH,
        G.BASE.depth,
        G.BASE_FLOOR_THICKNESS,
        v(-G.BASE_CENTER_WIDTH / 2.0, G.BASE.ymin, 0),
    )

    # Edge/radial stiffening. These sit on top of the 4 mm skin.
    ribs = [
        Part.makeBox(
            G.BASE_CENTER_WIDTH,
            8.0,
            G.BASE_RIB_HEIGHT,
            v(-G.BASE_CENTER_WIDTH / 2.0, G.BASE.ymin, G.BASE_FLOOR_THICKNESS),
        ),
        Part.makeBox(
            G.BASE_CENTER_WIDTH,
            8.0,
            G.BASE_RIB_HEIGHT,
            v(
                -G.BASE_CENTER_WIDTH / 2.0,
                G.BASE.ymax - 8.0,
                G.BASE_FLOOR_THICKNESS,
            ),
        ),
        beam_xy(
            G.PIVOT.x,
            G.PIVOT.y,
            G.PIVOT.x,
            G.BASE.ymin + 8.0,
            7.0,
            G.BASE_FLOOR_THICKNESS,
            G.BASE_RIB_HEIGHT,
        ),
        beam_xy(
            G.PIVOT.x,
            G.PIVOT.y,
            G.PIVOT.x,
            G.BASE.ymax - 8.0,
            7.0,
            G.BASE_FLOOR_THICKNESS,
            G.BASE_RIB_HEIGHT,
        ),
    ]

    receiver_blocks = []
    cavities = []
    holes = []
    seam_x = G.BASE_CENTER_WIDTH / 2.0
    x_hole_right = seam_x - G.RETAINER_HOLE_LOCAL_X
    x_hole_left = -x_hole_right

    for y0 in G.JOINT_Y_CENTERS:
        # RIGHT receiver: x = +85 .. +140 mm
        rx0 = seam_x - 55.0
        receiver_blocks.append(
            Part.makeBox(
                55.0,
                G.JOINT_RECEIVER_WIDTH,
                G.JOINT_RECEIVER_HEIGHT - G.BASE_FLOOR_THICKNESS,
                v(
                    rx0,
                    y0 - G.JOINT_RECEIVER_WIDTH / 2.0,
                    G.BASE_FLOOR_THICKNESS,
                ),
            )
        )
        cavities.append(
            roof_key_prism(
                seam_x - G.JOINT_OVERLAP - G.JOINT_CLEARANCE,
                seam_x + 2.0,
                y0,
                G.JOINT_CLEARANCE,
            )
        )
        holes.append(retainer_hole(x_hole_right, y0))

        # LEFT receiver: exact plan symmetry.
        lx0 = -seam_x
        receiver_blocks.append(
            Part.makeBox(
                55.0,
                G.JOINT_RECEIVER_WIDTH,
                G.JOINT_RECEIVER_HEIGHT - G.BASE_FLOOR_THICKNESS,
                v(
                    lx0,
                    y0 - G.JOINT_RECEIVER_WIDTH / 2.0,
                    G.BASE_FLOOR_THICKNESS,
                ),
            )
        )
        cavities.append(
            roof_key_prism(
                -seam_x - 2.0,
                -seam_x + G.JOINT_OVERLAP + G.JOINT_CLEARANCE,
                y0,
                G.JOINT_CLEARANCE,
            )
        )
        holes.append(retainer_hole(x_hole_left, y0))

        ribs.append(
            beam_xy(
                G.PIVOT.x,
                G.PIVOT.y,
                seam_x - 28.0,
                y0,
                7.0,
                G.BASE_FLOOR_THICKNESS,
                G.BASE_RIB_HEIGHT,
            )
        )
        ribs.append(
            beam_xy(
                G.PIVOT.x,
                G.PIVOT.y,
                -seam_x + 28.0,
                y0,
                7.0,
                G.BASE_FLOOR_THICKNESS,
                G.BASE_RIB_HEIGHT,
            )
        )

    # Primary annular vertical load path.
    bearing_outer = Part.makeCylinder(
        G.BEARING_OUTER_DIAMETER / 2.0,
        G.BEARING_HEIGHT,
        v(G.PIVOT.x, G.PIVOT.y, G.BASE_FLOOR_THICKNESS),
    )
    bearing_inner = Part.makeCylinder(
        G.BEARING_INNER_DIAMETER / 2.0,
        G.BEARING_HEIGHT + 1.0,
        v(G.PIVOT.x, G.PIVOT.y, G.BASE_FLOOR_THICKNESS - 0.5),
    )
    bearing = bearing_outer.cut(bearing_inner)

    # Pilot guides rotation. The narrowed neck receives a removable C-clip.
    stem = Part.makeCylinder(
        G.PIVOT_STEM_DIAMETER / 2.0,
        G.PIVOT_NECK_Z0 - G.BASE_FLOOR_THICKNESS,
        v(G.PIVOT.x, G.PIVOT.y, G.BASE_FLOOR_THICKNESS),
    )
    neck = Part.makeCylinder(
        G.PIVOT_NECK_DIAMETER / 2.0,
        G.PIVOT_NECK_HEIGHT,
        v(G.PIVOT.x, G.PIVOT.y, G.PIVOT_NECK_Z0),
    )

    sh = fuse_all([floor, bearing, stem, neck] + ribs + receiver_blocks)
    for cut in cavities + holes:
        sh = sh.cut(cut)
    sh = sh.removeSplitter()
    require_single(sh, "BASE_CENTER")
    return sh


def side_base(hand: str):
    if hand not in ("left", "right"):
        raise ValueError(hand)

    seam = G.BASE_CENTER_WIDTH / 2.0
    if hand == "right":
        floor_x = seam
        key_x0 = seam - G.JOINT_OVERLAP
        key_x1 = seam + G.JOINT_EMBED
        buttress_x = seam
        hole_x = seam - G.RETAINER_HOLE_LOCAL_X
        outer_x = G.BASE.xmax
    else:
        floor_x = G.BASE.xmin
        key_x0 = -seam - G.JOINT_EMBED
        key_x1 = -seam + G.JOINT_OVERLAP
        buttress_x = -seam - 25.0
        hole_x = -seam + G.RETAINER_HOLE_LOCAL_X
        outer_x = G.BASE.xmin

    floor = Part.makeBox(
        G.BASE_SIDE_WIDTH,
        G.BASE.depth,
        G.BASE_FLOOR_THICKNESS,
        v(floor_x, G.BASE.ymin, 0),
    )

    ribs = [
        Part.makeBox(
            G.BASE_SIDE_WIDTH,
            8.0,
            G.BASE_RIB_HEIGHT,
            v(floor_x, G.BASE.ymin, G.BASE_FLOOR_THICKNESS),
        ),
        Part.makeBox(
            G.BASE_SIDE_WIDTH,
            8.0,
            G.BASE_RIB_HEIGHT,
            v(floor_x, G.BASE.ymax - 8.0, G.BASE_FLOOR_THICKNESS),
        ),
    ]
    if hand == "right":
        ribs.append(
            Part.makeBox(
                8.0,
                G.BASE.depth,
                G.BASE_RIB_HEIGHT,
                v(G.BASE.xmax - 8.0, G.BASE.ymin, G.BASE_FLOOR_THICKNESS),
            )
        )
    else:
        ribs.append(
            Part.makeBox(
                8.0,
                G.BASE.depth,
                G.BASE_RIB_HEIGHT,
                v(G.BASE.xmin, G.BASE.ymin, G.BASE_FLOOR_THICKNESS),
            )
        )

    keys = []
    buttresses = []
    holes = []
    for y0 in G.JOINT_Y_CENTERS:
        keys.append(roof_key_prism(key_x0, key_x1, y0, 0.0))
        buttresses.append(
            Part.makeBox(
                25.0,
                G.JOINT_RECEIVER_WIDTH,
                G.JOINT_RECEIVER_HEIGHT - G.BASE_FLOOR_THICKNESS,
                v(
                    buttress_x,
                    y0 - G.JOINT_RECEIVER_WIDTH / 2.0,
                    G.BASE_FLOOR_THICKNESS,
                ),
            )
        )
        holes.append(retainer_hole(hole_x, y0))

        if hand == "right":
            target_x = G.BASE.xmax - 12.0
        else:
            target_x = G.BASE.xmin + 12.0

        ribs.append(
            beam_xy(
                seam if hand == "right" else -seam,
                y0,
                target_x,
                G.BASE.ymin + 15.0 if y0 < 0 else G.BASE.ymax - 15.0,
                7.0,
                G.BASE_FLOOR_THICKNESS,
                G.BASE_RIB_HEIGHT,
            )
        )

    sh = fuse_all([floor] + ribs + keys + buttresses)
    for hole in holes:
        sh = sh.cut(hole)
    sh = sh.removeSplitter()
    require_single(sh, "BASE_" + hand.upper())
    return sh


def rotor():
    outer = Part.makeCylinder(
        G.BEARING_OUTER_DIAMETER / 2.0,
        G.ROTOR_THICKNESS,
        v(G.PIVOT.x, G.PIVOT.y, 0),
    )
    bore = Part.makeCylinder(
        G.PIVOT_BORE_DIAMETER / 2.0,
        G.ROTOR_THICKNESS + 10.0,
        v(G.PIVOT.x, G.PIVOT.y, -1.0),
    )

    # Top ribs follow the reconstructed original stand arm directions and prepare
    # the rotor for the later INNER_LEFT / INNER_RIGHT slide-in modules.
    parts = [outer]
    for sx in (-1.0, 1.0):
        angle = math.atan2(G.STAND_TIP_Y, sx * G.STAND_HALF_WIDTH)
        x1 = G.PIVOT.x + math.cos(angle) * 18.0
        y1 = G.PIVOT.y + math.sin(angle) * 18.0
        x2 = G.PIVOT.x + math.cos(angle) * 68.0
        y2 = G.PIVOT.y + math.sin(angle) * 68.0
        parts.append(beam_xy(x1, y1, x2, y2, 30.0, G.ROTOR_THICKNESS, 8.0))

    hub_outer = Part.makeCylinder(
        30.0,
        8.0,
        v(G.PIVOT.x, G.PIVOT.y, G.ROTOR_THICKNESS),
    )
    parts.append(hub_outer)

    sh = fuse_all(parts).cut(bore).removeSplitter()
    require_single(sh, "ROTOR")
    return sh


def pivot_clip():
    outer = Part.makeCylinder(G.PIVOT_CLIP_OUTER_DIAMETER / 2.0, G.PIVOT_CLIP_THICKNESS)
    inner = Part.makeCylinder(
        G.PIVOT_CLIP_INNER_DIAMETER / 2.0,
        G.PIVOT_CLIP_THICKNESS + 1.0,
        v(0, 0, -0.5),
    )
    sh = outer.cut(inner)
    # C-opening. Rounded tips can be added after physical fit testing.
    gap = Part.makeBox(10.0, 24.0, 5.0, v(-5.0, 0.0, -1.0))
    sh = sh.cut(gap).removeSplitter()
    require_single(sh, "PIVOT_CLIP")
    return sh


def triangular_barb(side: int):
    if side not in (-1, 1):
        raise ValueError(side)
    x0 = 4.0 * side
    x1 = 4.6 * side
    pts = [
        v(x0, -6.0, 1.0),
        v(x1, -6.0, 4.0),
        v(x0, -6.0, 6.0),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, 12.0, 0))


def joint_retainer():
    stem = Part.makeBox(
        G.RETAINER_PIN_X,
        G.RETAINER_PIN_Y,
        28.0,
        v(-G.RETAINER_PIN_X / 2.0, -G.RETAINER_PIN_Y / 2.0, 0.0),
    )
    # Split the lower end into two flexible PETG legs.
    relief = Part.makeBox(2.4, 14.0, 14.0, v(-1.2, -7.0, 0.0))
    stem = stem.cut(relief)
    head = Part.makeBox(14.0, 18.0, 3.0, v(-7.0, -9.0, 28.0))
    sh = fuse_all([stem, head, triangular_barb(-1), triangular_barb(1)])
    require_single(sh, "JOINT_RETAINER")
    return sh


def export_shape(name: str, shape):
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
        LinearDeflection=0.08,
        AngularDeflection=0.25,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ": empty tessellation")
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "name": name,
        "volume_mm3": round(float(shape.Volume), 3),
        "bbox_mm": [
            round(bb.XMin, 3),
            round(bb.XMax, 3),
            round(bb.YMin, 3),
            round(bb.YMax, 3),
            round(bb.ZMin, 3),
            round(bb.ZMax, 3),
        ],
        "size_mm": [round(bb.XLength, 3), round(bb.YLength, 3), round(bb.ZLength, 3)],
        "facets": int(mesh.CountFacets),
    }


parts = {
    "samsung_stand_v1_base_center": center_base(),
    "samsung_stand_v1_base_left": side_base("left"),
    "samsung_stand_v1_base_right": side_base("right"),
    "samsung_stand_v1_rotor": rotor(),
    "samsung_stand_v1_joint_retainer": joint_retainer(),
    "samsung_stand_v1_pivot_clip": pivot_clip(),
}

report = {
    "version": "v1",
    "freecad_version": App.Version(),
    "parameters": {
        "base_mm": [G.BASE.width, G.BASE.depth],
        "center_width_mm": G.BASE_CENTER_WIDTH,
        "side_visible_width_mm": G.BASE_SIDE_WIDTH,
        "joint_overlap_mm": G.JOINT_OVERLAP,
        "joint_clearance_mm": G.JOINT_CLEARANCE,
        "bearing_od_id_mm": [G.BEARING_OUTER_DIAMETER, G.BEARING_INNER_DIAMETER],
        "pivot_xy_mm": [G.PIVOT.x, G.PIVOT.y],
        "bearing_pressure_mpa_at_500N": round(G.BEARING_NOMINAL_PRESSURE_MPA, 5),
    },
    "parts": {},
}

for name, sh in parts.items():
    report["parts"][name] = export_shape(name, sh)

with open(os.path.join(OUT, "VALIDATION_v1_source.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

with open(os.path.join(OUT, "README_BUILD_v1.txt"), "w", encoding="utf-8") as f:
    f.write(
        "Samsung_Stand v1 generated base/rotor set\n"
        "Primary vertical path: annular bearing, not central pilot.\n"
        "Side joints: two 50 mm roof-keys per side plus replaceable snap retainer pins.\n"
        "Retainer barbs retain the pin only; structural withdrawal load is carried by the pin stem.\n"
        "Outer guide rails / inner saddle carriers are intentionally not part of this first CAD increment.\n"
    )

print(json.dumps(report, indent=2))
