#!/usr/bin/env python3
"""Build Samsung_Stand v2 from the validated v1 STEP baseline.

v2 adds:
- one glide track per fixed side module;
- two rotor receiver sockets;
- one universal rotating INNER_ARM printed twice;
- a replaceable blank saddle insert;
- a transverse split-end snap lock pin for each rotor/arm joint.

The unresolved Samsung arm cross-section remains isolated to the small insert.
"""

from __future__ import annotations

import json
import math
import os

import FreeCAD as App
import Import
import MeshPart
import Part

import geometry_model as G
import v2_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_v2")
V1_STEP = os.path.join(ROOT, "cad", "v1", "STEP")
os.makedirs(OUT, exist_ok=True)


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def fuse_all(shapes):
    shapes = [s for s in shapes if s is not None]
    if not shapes:
        raise ValueError("No shapes to fuse")
    out = shapes[0]
    for sh in shapes[1:]:
        out = out.fuse(sh)
    return out.removeSplitter()


def require_single(shape, label):
    if shape.isNull():
        raise RuntimeError(label + ": null shape")
    if not shape.isValid():
        raise RuntimeError(label + ": invalid OCC shape")
    if len(shape.Solids) != 1:
        raise RuntimeError(f"{label}: expected one solid, got {len(shape.Solids)}")
    if shape.Volume <= 0:
        raise RuntimeError(label + ": non-positive volume")


def load_step(name):
    path = os.path.join(V1_STEP, name + ".step")
    if not os.path.isfile(path):
        raise RuntimeError("Missing validated v1 STEP input: " + path)
    doc = App.newDocument("import_" + name)
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = []
    for obj in doc.Objects:
        if hasattr(obj, "Shape") and not obj.Shape.isNull():
            shapes.append(obj.Shape.copy())
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No shape imported from " + path)
    sh = fuse_all(shapes)
    require_single(sh, "import " + name)
    return sh


def place_plan(shape, angle_deg, tx=0.0, ty=0.0):
    sh = shape.copy()
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle_deg)
    sh.translate(v(tx, ty, 0))
    return sh


def annular_sector(cx, cy, rmin, rmax, a0_deg, a1_deg, z0, height, n=40):
    pts = []
    for i in range(n + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        pts.append(v(cx + rmax * math.cos(a), cy + rmax * math.sin(a), z0))
    for i in range(n, -1, -1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / n)
        pts.append(v(cx + rmin * math.cos(a), cy + rmin * math.sin(a), z0))
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, 0, height))


def roof_prism_x(xmin, xmax, half_width, z_bottom, z_wall_top, z_apex):
    pts = [
        v(xmin, -half_width, z_bottom),
        v(xmin, +half_width, z_bottom),
        v(xmin, +half_width, z_wall_top),
        v(xmin, 0, z_apex),
        v(xmin, -half_width, z_wall_top),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(xmax - xmin, 0, 0))


def house_tunnel_y(x_center, y_length, x_half, z_bottom, z_wall_top, z_apex):
    y0 = -y_length / 2.0
    pts = [
        v(x_center - x_half, y0, z_bottom),
        v(x_center + x_half, y0, z_bottom),
        v(x_center + x_half, y0, z_wall_top),
        v(x_center, y0, z_apex),
        v(x_center - x_half, y0, z_wall_top),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, y_length, 0))


def center_v2():
    """Trim all fixed ribs above the bearing plane out of the rotating envelope."""
    sh = load_step("samsung_stand_v1_base_center")
    outer = Part.makeCylinder(
        P.ROTATING_CLEARANCE_RADIUS,
        P.ROTATING_CLEARANCE_HEIGHT,
        v(G.PIVOT.x, G.PIVOT.y, P.ROTATING_CLEARANCE_Z0),
    )
    inner = Part.makeCylinder(
        P.ROTATING_CLEARANCE_INNER_RADIUS,
        P.ROTATING_CLEARANCE_HEIGHT + 2.0,
        v(G.PIVOT.x, G.PIVOT.y, P.ROTATING_CLEARANCE_Z0 - 1.0),
    )
    rotating_clearance = outer.cut(inner)
    sh = sh.cut(rotating_clearance).removeSplitter()
    require_single(sh, "BASE_CENTER_V2")
    return sh


def side_with_track(side):
    if side == "right":
        upstream = load_step("samsung_stand_v1_base_right")
        angles = P.RIGHT_TRACK_ANGLE_RANGE
    elif side == "left":
        upstream = load_step("samsung_stand_v1_base_left")
        angles = P.LEFT_TRACK_ANGLE_RANGE
    else:
        raise ValueError(side)

    rmin = P.TRACK_RADIUS - P.TRACK_RADIAL_WIDTH / 2.0
    rmax = P.TRACK_RADIUS + P.TRACK_RADIAL_WIDTH / 2.0
    # 0.2 mm overlap into the base skin avoids face-only fuse ambiguity.
    z0 = P.TRACK_Z0 - 0.2
    track = annular_sector(
        G.PIVOT.x,
        G.PIVOT.y,
        rmin,
        rmax,
        angles[0],
        angles[1],
        z0,
        P.TRACK_TOP_Z - z0,
    )
    sh = upstream.fuse(track).removeSplitter()
    require_single(sh, "BASE_" + side.upper() + "_TRACK")
    return sh


def rotor_v2():
    sh = load_step("samsung_stand_v1_rotor")
    receiver_blocks = []
    root_landings = []
    cavities = []
    tunnels = []

    cavity_z_bottom = P.ROTOR_KEY_CAVITY_BOTTOM_Z
    cavity_wall_top = (
        P.TRACK_TOP_Z + P.ARM_KEY_WALL_TOP_Z - G.BEARING_TOP_Z
        + P.ARM_KEY_CLEARANCE
    )
    cavity_apex = (
        P.TRACK_TOP_Z + P.ARM_KEY_APEX_Z - G.BEARING_TOP_Z
        + P.ARM_KEY_CLEARANCE
    )

    for angle in (P.RIGHT_ARM_ANGLE_DEG, P.LEFT_ARM_ANGLE_DEG):
        block_local = Part.makeBox(
            P.ROTOR_RECEIVER_R_OUTER - P.ROTOR_RECEIVER_R_INNER,
            P.ROTOR_RECEIVER_WIDTH,
            P.ROTOR_RECEIVER_TOP_Z - P.ROTOR_RECEIVER_Z0,
            v(
                P.ROTOR_RECEIVER_R_INNER,
                -P.ROTOR_RECEIVER_WIDTH / 2.0,
                P.ROTOR_RECEIVER_Z0,
            ),
        )
        receiver_blocks.append(
            place_plan(block_local, angle, G.PIVOT.x, G.PIVOT.y)
        )

        landing_local = Part.makeBox(
            P.ROOT_LANDING_R1 - P.ROOT_LANDING_R0,
            P.ROOT_LANDING_WIDTH,
            P.ROOT_LANDING_TOP_Z - P.ROOT_LANDING_Z0,
            v(
                P.ROOT_LANDING_R0,
                -P.ROOT_LANDING_WIDTH / 2.0,
                P.ROOT_LANDING_Z0,
            ),
        )
        root_landings.append(
            place_plan(landing_local, angle, G.PIVOT.x, G.PIVOT.y)
        )

        cavity_local = roof_prism_x(
            P.INNER_R0 - P.INNER_MALE_OVERLAP - P.ARM_KEY_CLEARANCE,
            P.INNER_R0 + 2.0,
            P.ARM_KEY_HALF_WIDTH + P.ARM_KEY_CLEARANCE,
            cavity_z_bottom,
            cavity_wall_top,
            cavity_apex,
        )
        cavities.append(place_plan(cavity_local, angle, G.PIVOT.x, G.PIVOT.y))

        tunnel_local = house_tunnel_y(
            P.ARM_RETAINER_RADIUS,
            P.ARM_LOCK_HOLE_TRANSVERSE_LENGTH,
            P.ARM_LOCK_HOLE_RADIAL_WIDTH / 2.0,
            P.ARM_LOCK_HOLE_BOTTOM_Z_ROTOR,
            P.ARM_LOCK_HOLE_WALL_TOP_Z_ROTOR,
            P.ARM_LOCK_HOLE_APEX_Z_ROTOR,
        )
        tunnels.append(place_plan(tunnel_local, angle, G.PIVOT.x, G.PIVOT.y))

    sh = fuse_all([sh] + receiver_blocks + root_landings)
    for cut in cavities + tunnels:
        sh = sh.cut(cut)
    sh = sh.removeSplitter()
    require_single(sh, "ROTOR_V2")
    return sh


def inner_arm():
    # Local +X points outward; assembly origin is radius INNER_R0 from pivot.
    floor = Part.makeBox(
        P.INNER_LENGTH,
        P.INNER_BEAM_WIDTH,
        P.INNER_FLOOR_THICKNESS,
        v(0, -P.INNER_BEAM_WIDTH / 2.0, 0),
    )
    edge_ribs = [
        Part.makeBox(
            P.INNER_LENGTH,
            5.0,
            P.INNER_TOTAL_HEIGHT - P.INNER_FLOOR_THICKNESS,
            v(0, -P.INNER_BEAM_WIDTH / 2.0, P.INNER_FLOOR_THICKNESS),
        ),
        Part.makeBox(
            P.INNER_LENGTH,
            5.0,
            P.INNER_TOTAL_HEIGHT - P.INNER_FLOOR_THICKNESS,
            v(
                0,
                P.INNER_BEAM_WIDTH / 2.0 - 5.0,
                P.INNER_FLOOR_THICKNESS,
            ),
        ),
    ]

    root = Part.makeBox(28.0, 40.0, P.INNER_TOTAL_HEIGHT, v(0, -20.0, 0))

    male = roof_prism_x(
        -P.INNER_MALE_OVERLAP,
        P.INNER_MALE_EMBED,
        P.ARM_KEY_HALF_WIDTH,
        P.ARM_KEY_BOTTOM_Z,
        P.ARM_KEY_WALL_TOP_Z,
        P.ARM_KEY_APEX_Z,
    )

    saddle_x0 = P.SADDLE_U - P.SADDLE_PLATFORM_LENGTH / 2.0
    saddle = Part.makeBox(
        P.SADDLE_PLATFORM_LENGTH,
        P.SADDLE_PLATFORM_WIDTH,
        P.INNER_TOTAL_HEIGHT,
        v(saddle_x0, -P.SADDLE_PLATFORM_WIDTH / 2.0, 0),
    )

    sh = fuse_all([floor, root, male, saddle] + edge_ribs)

    # Replaceable contact insert pocket: only this small insert must eventually
    # encode the exact Samsung arm underside/cross-section.
    pocket = Part.makeBox(
        P.SADDLE_POCKET_LENGTH,
        P.SADDLE_POCKET_WIDTH,
        P.INNER_TOTAL_HEIGHT - P.SADDLE_POCKET_FLOOR + 2.0,
        v(
            P.SADDLE_U - P.SADDLE_POCKET_LENGTH / 2.0,
            -P.SADDLE_POCKET_WIDTH / 2.0,
            P.SADDLE_POCKET_FLOOR,
        ),
    )
    sh = sh.cut(pocket)

    # Transverse support-friendly lock tunnel through the inward male tongue.
    local_pin_u = P.ARM_RETAINER_RADIUS - P.INNER_R0
    inner_tunnel = house_tunnel_y(
        local_pin_u,
        24.0,
        P.ARM_LOCK_HOLE_RADIAL_WIDTH / 2.0,
        P.ARM_LOCK_HOLE_BOTTOM_Z_ROTOR + G.BEARING_TOP_Z - P.TRACK_TOP_Z,
        P.ARM_LOCK_HOLE_WALL_TOP_Z_ROTOR + G.BEARING_TOP_Z - P.TRACK_TOP_Z,
        P.ARM_LOCK_HOLE_APEX_Z_ROTOR + G.BEARING_TOP_Z - P.TRACK_TOP_Z,
    )
    sh = sh.cut(inner_tunnel).removeSplitter()
    require_single(sh, "INNER_ARM")
    return sh


def saddle_insert_blank():
    # Calibration placeholder only; final contact profile is intentionally absent.
    return Part.makeBox(
        P.SADDLE_INSERT_LENGTH,
        P.SADDLE_INSERT_WIDTH,
        P.SADDLE_INSERT_HEIGHT,
        v(
            -P.SADDLE_INSERT_LENGTH / 2.0,
            -P.SADDLE_INSERT_WIDTH / 2.0,
            0,
        ),
    )


def lock_barb(side):
    # Pin axis = local +X. Split-end legs flex in +/-Y.
    y0 = (P.ARM_LOCK_PIN_RADIAL_WIDTH / 2.0) * side
    y1 = (P.ARM_LOCK_PIN_RADIAL_WIDTH / 2.0 + 0.6) * side
    pts = [
        v(P.ARM_LOCK_PIN_LENGTH - 12.0, y0, 0),
        v(P.ARM_LOCK_PIN_LENGTH - 7.0, y1, 0),
        v(P.ARM_LOCK_PIN_LENGTH - 2.0, y0, 0),
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, 0, P.ARM_LOCK_PIN_HEIGHT))


def arm_lock_pin():
    body = Part.makeBox(
        P.ARM_LOCK_PIN_LENGTH,
        P.ARM_LOCK_PIN_RADIAL_WIDTH,
        P.ARM_LOCK_PIN_HEIGHT,
        v(0, -P.ARM_LOCK_PIN_RADIAL_WIDTH / 2.0, 0),
    )
    # Split the far end into two flexible legs.
    split = Part.makeBox(
        13.0,
        1.6,
        P.ARM_LOCK_PIN_HEIGHT + 2.0,
        v(
            P.ARM_LOCK_PIN_LENGTH - 13.0,
            -0.8,
            -1.0,
        ),
    )
    body = body.cut(split)
    head = Part.makeBox(
        3.0,
        10.0,
        6.0,
        v(-3.0, -5.0, 0.0),
    )
    sh = fuse_all([body, head, lock_barb(-1), lock_barb(1)])
    require_single(sh, "ARM_LOCK_PIN")
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
        LinearDeflection=0.08,
        AngularDeflection=0.25,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ": empty tessellation")
    mesh.write(stl)

    bb = shape.BoundBox
    return {
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
    "samsung_stand_v2_base_center": center_v2(),
    "samsung_stand_v2_base_left": side_with_track("left"),
    "samsung_stand_v2_base_right": side_with_track("right"),
    "samsung_stand_v2_rotor": rotor_v2(),
    "samsung_stand_v2_inner_arm": inner_arm(),
    "samsung_stand_v2_saddle_insert_blank": saddle_insert_blank(),
    "samsung_stand_v2_arm_lock_pin": arm_lock_pin(),
}

report = {
    "version": "v2",
    "freecad_version": App.Version(),
    "upstream": "validated cad/v1/STEP",
    "parameters": {
        "track_top_z_mm": P.TRACK_TOP_Z,
        "track_radius_mm": round(P.TRACK_RADIUS, 3),
        "track_radial_width_mm": P.TRACK_RADIAL_WIDTH,
        "inner_arm_r0_mm": P.INNER_R0,
        "inner_arm_length_mm": P.INNER_LENGTH,
        "inner_arm_print_length_mm": P.INNER_PRINT_LENGTH,
        "saddle_u_mm": round(P.SADDLE_U, 3),
        "contact_profile_status": "blank insert - real Samsung arm cross-section still required",
    },
    "parts": {},
}

for name, sh in parts.items():
    report["parts"][name] = export_shape(name, sh)

with open(os.path.join(OUT, "VALIDATION_v2_source.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
