#!/usr/bin/env python3
"""Canonical fit-coupon parameters for the three structural roof-key families."""

from __future__ import annotations

from dataclasses import dataclass

import geometry_model as G
import v2_params as V2
import v3_params as V3


CLEARANCES_MM = (0.30, 0.40, 0.50)
PROBE_HEIGHT = 28.0
PROBE_FLANGE_HEIGHT = 3.0
SOCKET_HEIGHT = 20.0
SOCKET_WALL = 5.0


@dataclass(frozen=True)
class KeyFamily:
    name: str
    half_width: float
    wall_top_from_bottom: float
    apex_from_bottom: float
    nominal_clearance: float
    underside_factor: float


FAMILIES = (
    KeyFamily(
        name="base",
        half_width=G.JOINT_KEY_HALF_WIDTH,
        wall_top_from_bottom=G.JOINT_KEY_WALL_TOP_Z - G.BASE_FLOOR_THICKNESS,
        apex_from_bottom=G.JOINT_KEY_APEX_Z - G.BASE_FLOOR_THICKNESS,
        nominal_clearance=G.JOINT_CLEARANCE,
        underside_factor=1.0,
    ),
    KeyFamily(
        name="inner",
        half_width=V2.ARM_KEY_HALF_WIDTH,
        wall_top_from_bottom=V2.ARM_KEY_WALL_TOP_Z - V2.ARM_KEY_BOTTOM_Z,
        apex_from_bottom=V2.ARM_KEY_APEX_Z - V2.ARM_KEY_BOTTOM_Z,
        nominal_clearance=V2.ARM_KEY_CLEARANCE,
        underside_factor=0.5,
    ),
    KeyFamily(
        name="outer",
        half_width=V3.OUTER_KEY_HALF_WIDTH,
        wall_top_from_bottom=V3.OUTER_KEY_WALL_TOP_Z - V3.OUTER_KEY_BOTTOM_Z,
        apex_from_bottom=V3.OUTER_KEY_APEX_Z - V3.OUTER_KEY_BOTTOM_Z,
        nominal_clearance=V3.OUTER_KEY_CLEARANCE,
        underside_factor=0.5,
    ),
)
