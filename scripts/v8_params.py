#!/usr/bin/env python3
"""v8 parameters: fully above-base joint locking and positive pivot retention."""

from __future__ import annotations

import math

import geometry_model as G
import v2_params as V2


# ---------------------------------------------------------------------------
# Universal structural joint lock pin
# Used for BASE<->CENTER (4x), ROTOR<->INNER_ARM (2x) and
# INNER_ARM<->OUTER_GUIDE (2x).
# ---------------------------------------------------------------------------
JOINT_PIN_LENGTH = 58.0
JOINT_PIN_WIDTH = 6.0
JOINT_PIN_HEIGHT = 3.5
JOINT_PIN_HEAD_LENGTH = 3.0
JOINT_PIN_HEAD_WIDTH = 10.0
JOINT_PIN_HEAD_HEIGHT = 6.0
JOINT_PIN_SPLIT_LENGTH = 12.0
JOINT_PIN_SPLIT_WIDTH = 1.6
JOINT_PIN_BARB_PEAK_X = 55.5
JOINT_PIN_BARB_HALF_WIDTH = 3.8

BASE_LOCK_X_ABS = 100.0
BASE_LOCK_TUNNEL_LENGTH = 52.0
BASE_LOCK_HOLE_WIDTH = 7.0
BASE_LOCK_HOLE_BOTTOM_Z = 8.0
BASE_LOCK_HOLE_WALL_TOP_Z = 12.2
BASE_LOCK_HOLE_APEX_Z = 16.2
BASE_LOCK_PIN_INSTALL_Z = 8.25

# Body starts exactly at the near receiver face after +90 deg rotation.
BASE_LOCK_PIN_AXIS_START = -BASE_LOCK_TUNNEL_LENGTH / 2.0

LEGACY_VERTICAL_LOCK_X_ABS = (
    G.BASE_CENTER_WIDTH / 2.0 - G.RETAINER_HOLE_LOCAL_X
)


# ---------------------------------------------------------------------------
# Pivot retention
# Fixed post is extended upward. A horizontal snap pin lives entirely inside a
# circular rotor counterbore. Rotor can rotate around the fixed pin; lifting the
# rotor makes its counterbore shoulder contact the pin.
# ---------------------------------------------------------------------------
PIVOT_POST_DIAMETER = G.PIVOT_NECK_DIAMETER
PIVOT_POST_TOP_Z = 34.0

PIVOT_COUNTERBORE_RADIUS = 23.5
PIVOT_COUNTERBORE_GLOBAL_Z0 = 21.0
PIVOT_COUNTERBORE_LOCAL_Z0 = PIVOT_COUNTERBORE_GLOBAL_Z0 - V2.ROTOR_INSTALL_Z
PIVOT_COUNTERBORE_HEIGHT = 30.0

PIVOT_PIN_HOLE_AXIS_LENGTH = 30.0
PIVOT_PIN_HOLE_WIDTH = 8.6
PIVOT_PIN_HOLE_BOTTOM_Z = 21.4
PIVOT_PIN_HOLE_WALL_TOP_Z = 27.8
PIVOT_PIN_HOLE_APEX_Z = 33.0

PIVOT_PIN_LENGTH = 36.0
PIVOT_PIN_WIDTH = 8.0
PIVOT_PIN_HEIGHT = 6.0
PIVOT_PIN_HEAD_LENGTH = 3.0
PIVOT_PIN_HEAD_WIDTH = 12.0
PIVOT_PIN_HEAD_HEIGHT = 8.0
PIVOT_PIN_SPLIT_LENGTH = 12.0
PIVOT_PIN_SPLIT_WIDTH = 1.8
PIVOT_PIN_BARB_PEAK_X = 31.0
PIVOT_PIN_BARB_HALF_WIDTH = 4.7

PIVOT_PIN_INSTALL_X0 = -18.0
PIVOT_PIN_INSTALL_Z = 21.7

PIVOT_ROTOR_LIFT_CLEARANCE = (
    PIVOT_PIN_INSTALL_Z - PIVOT_COUNTERBORE_GLOBAL_Z0
)

# Rough development-only bending check for an accidental 500 N lift shared by
# the two pin ends. This is not a certified material calculation.
PIVOT_PIN_CONTACT_LEVER_MM = (
    G.PIVOT_BORE_DIAMETER / 2.0 - PIVOT_POST_DIAMETER / 2.0
)
PIVOT_PIN_SECTION_MODULUS_MM3 = (
    PIVOT_PIN_WIDTH * PIVOT_PIN_HEIGHT**2 / 6.0
)
PIVOT_PIN_BENDING_STRESS_MPA_AT_500N = (
    (G.DESIGN_VERTICAL_LOAD_N / 2.0)
    * PIVOT_PIN_CONTACT_LEVER_MM
    / PIVOT_PIN_SECTION_MODULUS_MM3
)


# Dedicated OUTER_GUIDE lock: the inherited v3 50 mm tunnel sits inside the
# 58 mm saddle platform and is not externally accessible. V8 re-cuts a full
# transverse opening and uses a longer replaceable snap pin.
OUTER_LOCK_TUNNEL_LENGTH = 64.0
OUTER_LOCK_HOLE_WIDTH = 7.0
OUTER_LOCK_HOLE_BOTTOM_Z = 4.0
OUTER_LOCK_HOLE_WALL_TOP_Z = 8.2
OUTER_LOCK_HOLE_APEX_Z = 12.2

OUTER_PIN_LENGTH = 70.0
OUTER_PIN_WIDTH = 6.0
OUTER_PIN_HEIGHT = 3.5
OUTER_PIN_HEAD_LENGTH = 3.0
OUTER_PIN_HEAD_WIDTH = 10.0
OUTER_PIN_HEAD_HEIGHT = 6.0
OUTER_PIN_SPLIT_LENGTH = 12.0
OUTER_PIN_SPLIT_WIDTH = 1.6
OUTER_PIN_BARB_PEAK_X = 67.5
OUTER_PIN_BARB_HALF_WIDTH = 3.8
OUTER_PIN_INSTALL_AXIS_START = -OUTER_LOCK_TUNNEL_LENGTH / 2.0
OUTER_PIN_INSTALL_Z = 4.25
