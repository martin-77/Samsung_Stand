#!/usr/bin/env python3
"""Shared FreeCAD geometry for v8 locking pins and tunnels."""

from __future__ import annotations

import FreeCAD as App
import Part

import geometry_model as G
import v8_params as P


def v(x,y,z):
    return App.Vector(float(x),float(y),float(z))


def fuse_all(shapes):
    out=shapes[0]
    for sh in shapes[1:]:
        out=out.fuse(sh)
    return out.removeSplitter()


def house_tunnel_y(x_center,y_center,length,x_half,z_bottom,z_wall_top,z_apex):
    y0=y_center-length/2.0
    pts=[
        v(x_center-x_half,y0,z_bottom),
        v(x_center+x_half,y0,z_bottom),
        v(x_center+x_half,y0,z_wall_top),
        v(x_center,y0,z_apex),
        v(x_center-x_half,y0,z_wall_top),
    ]
    wire=Part.makePolygon(pts+[pts[0]])
    return Part.Face(wire).extrude(v(0,length,0))


def house_tunnel_x(x_center,y_center,length,y_half,z_bottom,z_wall_top,z_apex):
    x0=x_center-length/2.0
    pts=[
        v(x0,y_center-y_half,z_bottom),
        v(x0,y_center+y_half,z_bottom),
        v(x0,y_center+y_half,z_wall_top),
        v(x0,y_center,z_apex),
        v(x0,y_center-y_half,z_wall_top),
    ]
    wire=Part.makePolygon(pts+[pts[0]])
    return Part.Face(wire).extrude(v(length,0,0))


def _snap_barb(axis_x0,axis_x1,axis_peak,shaft_half,peak_half,height,side):
    y0=shaft_half*side
    yp=peak_half*side
    pts=[
        v(axis_x0,y0,0),
        v(axis_peak,yp,0),
        v(axis_x1,y0,0),
    ]
    wire=Part.makePolygon(pts+[pts[0]])
    return Part.Face(wire).extrude(v(0,0,height))


def joint_lock_pin():
    shaft=Part.makeBox(
        P.JOINT_PIN_LENGTH,
        P.JOINT_PIN_WIDTH,
        P.JOINT_PIN_HEIGHT,
        v(0,-P.JOINT_PIN_WIDTH/2.0,0),
    )
    split=Part.makeBox(
        P.JOINT_PIN_SPLIT_LENGTH,
        P.JOINT_PIN_SPLIT_WIDTH,
        P.JOINT_PIN_HEIGHT+2.0,
        v(
            P.JOINT_PIN_LENGTH-P.JOINT_PIN_SPLIT_LENGTH,
            -P.JOINT_PIN_SPLIT_WIDTH/2.0,
            -1.0,
        ),
    )
    shaft=shaft.cut(split)

    head=Part.makeBox(
        P.JOINT_PIN_HEAD_LENGTH,
        P.JOINT_PIN_HEAD_WIDTH,
        P.JOINT_PIN_HEAD_HEIGHT,
        v(
            -P.JOINT_PIN_HEAD_LENGTH,
            -P.JOINT_PIN_HEAD_WIDTH/2.0,
            0,
        ),
    )

    barb0=P.JOINT_PIN_BARB_START_X
    barb1=P.JOINT_PIN_LENGTH-0.5
    b1=_snap_barb(
        barb0,barb1,P.JOINT_PIN_BARB_PEAK_X,
        P.JOINT_PIN_WIDTH/2.0,
        P.JOINT_PIN_BARB_HALF_WIDTH,
        P.JOINT_PIN_HEIGHT,
        +1,
    )
    b2=_snap_barb(
        barb0,barb1,P.JOINT_PIN_BARB_PEAK_X,
        P.JOINT_PIN_WIDTH/2.0,
        P.JOINT_PIN_BARB_HALF_WIDTH,
        P.JOINT_PIN_HEIGHT,
        -1,
    )
    return fuse_all([shaft,head,b1,b2])


def pivot_lock_pin():
    shaft=Part.makeBox(
        P.PIVOT_PIN_LENGTH,
        P.PIVOT_PIN_WIDTH,
        P.PIVOT_PIN_HEIGHT,
        v(0,-P.PIVOT_PIN_WIDTH/2.0,0),
    )
    split=Part.makeBox(
        P.PIVOT_PIN_SPLIT_LENGTH,
        P.PIVOT_PIN_SPLIT_WIDTH,
        P.PIVOT_PIN_HEIGHT+2.0,
        v(
            P.PIVOT_PIN_LENGTH-P.PIVOT_PIN_SPLIT_LENGTH,
            -P.PIVOT_PIN_SPLIT_WIDTH/2.0,
            -1.0,
        ),
    )
    shaft=shaft.cut(split)

    head=Part.makeBox(
        P.PIVOT_PIN_HEAD_LENGTH,
        P.PIVOT_PIN_HEAD_WIDTH,
        P.PIVOT_PIN_HEAD_HEIGHT,
        v(
            -P.PIVOT_PIN_HEAD_LENGTH,
            -P.PIVOT_PIN_HEAD_WIDTH/2.0,
            0,
        ),
    )

    barb0=P.PIVOT_PIN_BARB_START_X
    barb1=P.PIVOT_PIN_LENGTH-0.5
    b1=_snap_barb(
        barb0,barb1,P.PIVOT_PIN_BARB_PEAK_X,
        P.PIVOT_PIN_WIDTH/2.0,
        P.PIVOT_PIN_BARB_HALF_WIDTH,
        P.PIVOT_PIN_HEIGHT,
        +1,
    )
    b2=_snap_barb(
        barb0,barb1,P.PIVOT_PIN_BARB_PEAK_X,
        P.PIVOT_PIN_WIDTH/2.0,
        P.PIVOT_PIN_BARB_HALF_WIDTH,
        P.PIVOT_PIN_HEIGHT,
        -1,
    )
    return fuse_all([shaft,head,b1,b2])


def pivot_post_extension():
    overlap = 0.30
    z0 = G.PIVOT_NECK_Z0 + G.PIVOT_NECK_HEIGHT - overlap
    return Part.makeCylinder(
        P.PIVOT_POST_DIAMETER/2.0,
        P.PIVOT_POST_TOP_Z-z0,
        v(G.PIVOT.x,G.PIVOT.y,z0),
    )


def pivot_post_tunnel():
    return house_tunnel_x(
        G.PIVOT.x,
        G.PIVOT.y,
        P.PIVOT_PIN_HOLE_AXIS_LENGTH,
        P.PIVOT_PIN_HOLE_WIDTH/2.0,
        P.PIVOT_PIN_HOLE_BOTTOM_Z,
        P.PIVOT_PIN_HOLE_WALL_TOP_Z,
        P.PIVOT_PIN_HOLE_APEX_Z,
    )


def rotor_counterbore():
    return Part.makeCylinder(
        P.PIVOT_COUNTERBORE_RADIUS,
        P.PIVOT_COUNTERBORE_HEIGHT,
        v(
            G.PIVOT.x,
            G.PIVOT.y,
            P.PIVOT_COUNTERBORE_LOCAL_Z0,
        ),
    )


def base_lock_tunnel(x_center,y_center):
    return house_tunnel_y(
        x_center,
        y_center,
        P.BASE_LOCK_TUNNEL_LENGTH,
        P.BASE_LOCK_HOLE_WIDTH/2.0,
        P.BASE_LOCK_HOLE_BOTTOM_Z,
        P.BASE_LOCK_HOLE_WALL_TOP_Z,
        P.BASE_LOCK_HOLE_APEX_Z,
    )


def outer_lock_tunnel(x_center):
    return house_tunnel_y(
        x_center,
        0.0,
        P.OUTER_LOCK_TUNNEL_LENGTH,
        P.OUTER_LOCK_HOLE_WIDTH/2.0,
        P.OUTER_LOCK_HOLE_BOTTOM_Z,
        P.OUTER_LOCK_HOLE_WALL_TOP_Z,
        P.OUTER_LOCK_HOLE_APEX_Z,
    )


def outer_lock_pin():
    shaft=Part.makeBox(
        P.OUTER_PIN_LENGTH,
        P.OUTER_PIN_WIDTH,
        P.OUTER_PIN_HEIGHT,
        v(0,-P.OUTER_PIN_WIDTH/2.0,0),
    )
    split=Part.makeBox(
        P.OUTER_PIN_SPLIT_LENGTH,
        P.OUTER_PIN_SPLIT_WIDTH,
        P.OUTER_PIN_HEIGHT+2.0,
        v(
            P.OUTER_PIN_LENGTH-P.OUTER_PIN_SPLIT_LENGTH,
            -P.OUTER_PIN_SPLIT_WIDTH/2.0,
            -1.0,
        ),
    )
    shaft=shaft.cut(split)
    head=Part.makeBox(
        P.OUTER_PIN_HEAD_LENGTH,
        P.OUTER_PIN_HEAD_WIDTH,
        P.OUTER_PIN_HEAD_HEIGHT,
        v(
            -P.OUTER_PIN_HEAD_LENGTH,
            -P.OUTER_PIN_HEAD_WIDTH/2.0,
            0,
        ),
    )
    barb0=P.OUTER_PIN_LENGTH-P.OUTER_PIN_SPLIT_LENGTH+1.0
    barb1=P.OUTER_PIN_LENGTH-0.5
    b1=_snap_barb(
        barb0,barb1,P.OUTER_PIN_BARB_PEAK_X,
        P.OUTER_PIN_WIDTH/2.0,
        P.OUTER_PIN_BARB_HALF_WIDTH,
        P.OUTER_PIN_HEIGHT,+1,
    )
    b2=_snap_barb(
        barb0,barb1,P.OUTER_PIN_BARB_PEAK_X,
        P.OUTER_PIN_WIDTH/2.0,
        P.OUTER_PIN_BARB_HALF_WIDTH,
        P.OUTER_PIN_HEIGHT,-1,
    )
    return fuse_all([shaft,head,b1,b2])


def front_base_barb_relief(x_center):
    return Part.makeBox(
        2.0 * P.FRONT_BASE_BARB_RELIEF_HALF_X,
        P.FRONT_BASE_BARB_RELIEF_Y1 - P.FRONT_BASE_BARB_RELIEF_Y0,
        P.FRONT_BASE_BARB_RELIEF_Z1 - P.FRONT_BASE_BARB_RELIEF_Z0,
        v(
            x_center - P.FRONT_BASE_BARB_RELIEF_HALF_X,
            P.FRONT_BASE_BARB_RELIEF_Y0,
            P.FRONT_BASE_BARB_RELIEF_Z0,
        ),
    )
