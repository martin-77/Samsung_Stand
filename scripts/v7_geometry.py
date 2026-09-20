#!/usr/bin/env python3
"""Shared FreeCAD geometry for v7 flush wear inserts/recesses."""

from __future__ import annotations

import math

import FreeCAD as App
import Part

import geometry_model as G
import v2_params as V2
import v7_params as P


def v(x,y,z):
    return App.Vector(float(x),float(y),float(z))


def annular_sector(cx,cy,r0,r1,a0_deg,a1_deg,z0,height,segments=72):
    pts=[]
    for i in range(segments+1):
        a=math.radians(a0_deg+(a1_deg-a0_deg)*i/segments)
        pts.append(v(cx+r1*math.cos(a),cy+r1*math.sin(a),z0))
    for i in range(segments,-1,-1):
        a=math.radians(a0_deg+(a1_deg-a0_deg)*i/segments)
        pts.append(v(cx+r0*math.cos(a),cy+r0*math.sin(a),z0))
    wire=Part.makePolygon(pts+[pts[0]])
    return Part.Face(wire).extrude(v(0,0,height))


def center_recess():
    outer=Part.makeCylinder(
        P.CENTER_RECESS_R_OUTER,
        P.CENTER_RECESS_HEIGHT,
        v(G.PIVOT.x,G.PIVOT.y,P.CENTER_RECESS_Z0),
    )
    inner=Part.makeCylinder(
        P.CENTER_RECESS_R_INNER,
        P.CENTER_RECESS_HEIGHT+0.2,
        v(G.PIVOT.x,G.PIVOT.y,P.CENTER_RECESS_Z0-0.1),
    )
    return outer.cut(inner)


def center_wear_ring():
    outer=Part.makeCylinder(P.CENTER_INSERT_R_OUTER,P.WEAR_THICKNESS)
    inner=Part.makeCylinder(
        P.CENTER_INSERT_R_INNER,
        P.WEAR_THICKNESS+0.2,
        v(0,0,-0.1),
    )
    return outer.cut(inner).removeSplitter()


def track_recess(side):
    if side=="right":
        center=V2.RIGHT_ARM_ANGLE_DEG
    elif side=="left":
        center=V2.LEFT_ARM_ANGLE_DEG
    else:
        raise ValueError(side)
    return annular_sector(
        G.PIVOT.x,G.PIVOT.y,
        P.TRACK_RECESS_R_INNER,P.TRACK_RECESS_R_OUTER,
        center-P.TRACK_RECESS_HALF_ANGLE_DEG,
        center+P.TRACK_RECESS_HALF_ANGLE_DEG,
        P.TRACK_RECESS_Z0,P.TRACK_RECESS_HEIGHT,
    )


def universal_track_wear_arc():
    return annular_sector(
        0,0,
        P.TRACK_INSERT_R_INNER,P.TRACK_INSERT_R_OUTER,
        -P.TRACK_INSERT_HALF_ANGLE_DEG,
        +P.TRACK_INSERT_HALF_ANGLE_DEG,
        0,P.WEAR_THICKNESS,
    ).removeSplitter()
