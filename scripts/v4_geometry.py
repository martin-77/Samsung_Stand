#!/usr/bin/env python3
"""Shared FreeCAD geometry for v4 positive swivel end stops.

This module is the single source for both production CAD and OCC validation.
"""

from __future__ import annotations

import math

import FreeCAD as App
import Part

import geometry_model as G
import v2_params as V2
import v4_params as P


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def place_plan(shape, angle_deg):
    sh = shape.copy()
    sh.rotate(v(0, 0, 0), v(0, 0, 1), angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, 0))
    return sh


def oriented_rect_prism(
    radius: float,
    angle_deg: float,
    radial_length: float,
    tangential_width: float,
    z0: float,
    height: float,
):
    """Rectangle centered at polar radius/angle, extruded in +Z."""
    local = Part.makeBox(
        radial_length,
        tangential_width,
        height,
        v(
            radius - radial_length / 2.0,
            -tangential_width / 2.0,
            z0,
        ),
    )
    return place_plan(local, angle_deg)


def radial_spoke(
    r0: float,
    r1: float,
    angle_deg: float,
    width: float,
    z0: float,
    height: float,
):
    local = Part.makeBox(
        r1 - r0,
        width,
        height,
        v(r0, -width / 2.0, z0),
    )
    return place_plan(local, angle_deg)


def annular_sector(
    r0: float,
    r1: float,
    a0_deg: float,
    a1_deg: float,
    z0: float,
    height: float,
    segments: int = 72,
):
    pts = []
    for i in range(segments + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / segments)
        pts.append(v(G.PIVOT.x + r1 * math.cos(a), G.PIVOT.y + r1 * math.sin(a), z0))
    for i in range(segments, -1, -1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / segments)
        pts.append(v(G.PIVOT.x + r0 * math.cos(a), G.PIVOT.y + r0 * math.sin(a), z0))
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, 0, height))


def stop_sweep_clearance_shape():
    return annular_sector(
        P.STOP_CLEARANCE_R0,
        P.STOP_CLEARANCE_R1,
        P.ROTOR_STOP_HOME_ANGLE_DEG - P.STOP_CLEARANCE_HALF_ANGLE_DEG,
        P.ROTOR_STOP_HOME_ANGLE_DEG + P.STOP_CLEARANCE_HALF_ANGLE_DEG,
        P.STOP_CLEARANCE_Z0,
        P.STOP_CLEARANCE_HEIGHT,
    )


def arm_sweep_clearance_shape(side: str):
    if side == "right":
        a0, a1 = P.RIGHT_ARM_SWEEP_RANGE_DEG
    elif side == "left":
        a0, a1 = P.LEFT_ARM_SWEEP_RANGE_DEG
    else:
        raise ValueError(side)

    return annular_sector(
        P.ARM_SWEEP_CLEARANCE_R0,
        P.ARM_SWEEP_CLEARANCE_R1,
        a0,
        a1,
        P.ARM_SWEEP_CLEARANCE_Z0,
        P.ARM_SWEEP_CLEARANCE_HEIGHT,
    )


def rotor_stop_shape():
    """Stop hardware in rotor-local Z and home-angle XY coordinates."""
    spoke = radial_spoke(
        P.ROTOR_STOP_SPOKE_R0,
        P.ROTOR_STOP_SPOKE_R1,
        P.ROTOR_STOP_HOME_ANGLE_DEG,
        P.ROTOR_STOP_SPOKE_WIDTH,
        P.ROTOR_STOP_SPOKE_Z0,
        P.ROTOR_STOP_SPOKE_HEIGHT,
    )
    tab = oriented_rect_prism(
        P.STOP_RADIUS,
        P.ROTOR_STOP_HOME_ANGLE_DEG,
        P.ROTOR_STOP_TAB_RADIAL_LENGTH,
        P.ROTOR_STOP_TAB_TANGENTIAL_WIDTH,
        P.ROTOR_STOP_TAB_Z0,
        P.ROTOR_STOP_TAB_HEIGHT,
    )
    return spoke.fuse(tab).removeSplitter()


def fixed_stop_tower(angle_deg: float):
    return oriented_rect_prism(
        P.STOP_RADIUS,
        angle_deg,
        P.FIXED_STOP_RADIAL_LENGTH,
        P.FIXED_STOP_TANGENTIAL_WIDTH,
        P.FIXED_STOP_Z0,
        P.FIXED_STOP_HEIGHT,
    )


def fixed_stop_pair_shape():
    a = fixed_stop_tower(P.FIXED_STOP_ANGLE_NEG_DEG)
    b = fixed_stop_tower(P.FIXED_STOP_ANGLE_POS_DEG)
    # The pair is intentionally two solids before it is fused into BASE_CENTER.
    return a.fuse(b)


def rotate_about_pivot(shape, angle_deg: float):
    sh = shape.copy()
    sh.rotate(
        v(G.PIVOT.x, G.PIVOT.y, 0),
        v(0, 0, 1),
        angle_deg,
    )
    return sh
