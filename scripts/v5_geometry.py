#!/usr/bin/env python3
"""Shared FreeCAD geometry for v5 zero-position detent calibration parts."""

from __future__ import annotations

import math

import FreeCAD as App
import Part

import geometry_model as G
import v5_params as P


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def place_local_frame(shape, radial_origin, angle_deg, z=0.0):
    sh = shape.copy()
    sh.translate(v(radial_origin, 0, z))
    sh.rotate(v(0, 0, z), v(0, 0, 1), angle_deg)
    sh.translate(v(G.PIVOT.x, G.PIVOT.y, 0))
    return sh


def annular_sector(r0, r1, a0_deg, a1_deg, z0, height, segments=72):
    pts = []
    for i in range(segments + 1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / segments)
        pts.append(v(G.PIVOT.x + r1 * math.cos(a), G.PIVOT.y + r1 * math.sin(a), z0))
    for i in range(segments, -1, -1):
        a = math.radians(a0_deg + (a1_deg - a0_deg) * i / segments)
        pts.append(v(G.PIVOT.x + r0 * math.cos(a), G.PIVOT.y + r0 * math.sin(a), z0))
    wire = Part.makePolygon(pts + [pts[0]])
    return Part.Face(wire).extrude(v(0, 0, height))


def rotor_detent_track_shape():
    track = annular_sector(
        P.DETENT_TRACK_R_INNER,
        P.DETENT_TRACK_R_OUTER,
        P.DETENT_HOME_ANGLE_DEG - P.DETENT_TRACK_HALF_ANGLE_DEG,
        P.DETENT_HOME_ANGLE_DEG + P.DETENT_TRACK_HALF_ANGLE_DEG,
        P.DETENT_TRACK_Z0,
        P.DETENT_TRACK_HEIGHT,
    )

    # Triangular V-notch cut through the outer cam edge.
    pts = []
    for angle, radius in (
        (
            P.DETENT_HOME_ANGLE_DEG - P.DETENT_NOTCH_HALF_ANGLE_DEG,
            P.DETENT_TRACK_R_OUTER + 1.0,
        ),
        (
            P.DETENT_HOME_ANGLE_DEG + P.DETENT_NOTCH_HALF_ANGLE_DEG,
            P.DETENT_TRACK_R_OUTER + 1.0,
        ),
        (P.DETENT_HOME_ANGLE_DEG, P.DETENT_NOTCH_ROOT_RADIUS),
    ):
        a = math.radians(angle)
        pts.append(v(
            G.PIVOT.x + radius * math.cos(a),
            G.PIVOT.y + radius * math.sin(a),
            P.DETENT_TRACK_Z0 - 1.0,
        ))
    wire = Part.makePolygon(pts + [pts[0]])
    notch = Part.Face(wire).extrude(v(0, 0, P.DETENT_TRACK_HEIGHT + 2.0))
    return track.cut(notch).removeSplitter()


def detent_mount_shape():
    # Platform coordinates are expressed relative to the spring-nose center.
    width_x = P.DETENT_ANCHOR_X1 - P.DETENT_ANCHOR_X0
    width_y = P.DETENT_ANCHOR_Y1 - P.DETENT_ANCHOR_Y0
    local = Part.makeBox(
        width_x,
        width_y,
        P.DETENT_MOUNT_HEIGHT,
        v(
            P.DETENT_ANCHOR_X0,
            P.DETENT_ANCHOR_Y0,
            P.DETENT_MOUNT_Z0,
        ),
    )

    for x in P.DETENT_PIN_LOCAL_X:
        hole = Part.makeBox(
            P.DETENT_PIN_HOLE_SIZE,
            P.DETENT_PIN_HOLE_SIZE,
            P.DETENT_MOUNT_HEIGHT + 3.0,
            v(
                x - P.DETENT_PIN_HOLE_SIZE / 2.0,
                P.DETENT_PIN_LOCAL_Y - P.DETENT_PIN_HOLE_SIZE / 2.0,
                P.DETENT_MOUNT_Z0 - 1.0,
            ),
        )
        local = local.cut(hole)

    return place_local_frame(
        local,
        P.DETENT_NOSE_CENTER_RADIUS,
        P.DETENT_HOME_ANGLE_DEG,
        0.0,
    ).removeSplitter()


def detent_mount_holes_shape():
    holes = []
    for x in P.DETENT_PIN_LOCAL_X:
        local = Part.makeBox(
            P.DETENT_PIN_HOLE_SIZE,
            P.DETENT_PIN_HOLE_SIZE,
            13.5,
            v(
                x - P.DETENT_PIN_HOLE_SIZE / 2.0,
                P.DETENT_PIN_LOCAL_Y - P.DETENT_PIN_HOLE_SIZE / 2.0,
                3.5,
            ),
        )
        holes.append(
            place_local_frame(
                local,
                P.DETENT_NOSE_CENTER_RADIUS,
                P.DETENT_HOME_ANGLE_DEG,
                0.0,
            )
        )
    return holes[0].fuse(holes[1])


def detent_nose_shape():
    return Part.makeCylinder(
        P.DETENT_NOSE_RADIUS,
        P.DETENT_SPRING_HEIGHT,
        v(0, 0, 0),
    )


def detent_cassette_body_shape(thickness):
    beam = Part.makeBox(
        thickness,
        P.DETENT_SPRING_LENGTH,
        P.DETENT_SPRING_HEIGHT,
        v(0, 0, 0),
    )
    anchor = Part.makeBox(
        P.DETENT_ANCHOR_X1 - P.DETENT_ANCHOR_X0,
        P.DETENT_ANCHOR_Y1 - P.DETENT_ANCHOR_Y0,
        P.DETENT_ANCHOR_HEIGHT,
        v(P.DETENT_ANCHOR_X0, P.DETENT_ANCHOR_Y0, 0),
    )

    sh = beam.fuse(anchor)
    for x in P.DETENT_PIN_LOCAL_X:
        hole = Part.makeBox(
            P.DETENT_PIN_HOLE_SIZE,
            P.DETENT_PIN_HOLE_SIZE,
            P.DETENT_ANCHOR_HEIGHT + 2.0,
            v(
                x - P.DETENT_PIN_HOLE_SIZE / 2.0,
                P.DETENT_PIN_LOCAL_Y - P.DETENT_PIN_HOLE_SIZE / 2.0,
                -1.0,
            ),
        )
        sh = sh.cut(hole)
    return sh.removeSplitter()


def detent_cassette_shape(thickness):
    body = detent_cassette_body_shape(thickness)
    return body.fuse(detent_nose_shape()).removeSplitter()


def detent_pin_shape():
    shaft = Part.makeBox(
        P.DETENT_PIN_SHAFT_SIZE,
        P.DETENT_PIN_SHAFT_SIZE,
        P.DETENT_PIN_SHAFT_HEIGHT,
        v(
            -P.DETENT_PIN_SHAFT_SIZE / 2.0,
            -P.DETENT_PIN_SHAFT_SIZE / 2.0,
            0,
        ),
    )
    head = Part.makeBox(
        P.DETENT_PIN_HEAD_SIZE,
        P.DETENT_PIN_HEAD_SIZE,
        P.DETENT_PIN_HEAD_HEIGHT,
        v(
            -P.DETENT_PIN_HEAD_SIZE / 2.0,
            -P.DETENT_PIN_HEAD_SIZE / 2.0,
            P.DETENT_PIN_SHAFT_HEIGHT,
        ),
    )
    return shaft.fuse(head).removeSplitter()


def install_cassette(shape):
    return place_local_frame(
        shape,
        P.DETENT_NOSE_CENTER_RADIUS,
        P.DETENT_HOME_ANGLE_DEG,
        P.DETENT_MOUNT_TOP_Z,
    )
