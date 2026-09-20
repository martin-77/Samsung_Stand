#!/usr/bin/env python3
"""Parameters for v3: modular outer Samsung stand guide rails."""

from __future__ import annotations

import math

import geometry_model as G
import v2_params as V2


STAND_TIP_RADIUS = math.hypot(G.STAND_HALF_WIDTH, G.STAND_TIP_Y)

# v2 INNER_ARM starts at radius 85 and has 225 mm structural length.
OUTER_R0 = V2.INNER_R0 + V2.INNER_LENGTH
OUTER_VISIBLE_LENGTH = 170.0
OUTER_TIP_RADIUS = OUTER_R0 + OUTER_VISIBLE_LENGTH

# Form-locking outer joint. The tongue is intentionally lifted above the guide
# floor / glide-track plane so OUTER_GUIDE cannot become a normal vertical load
# path into the fixed base.
OUTER_KEY_OVERLAP = 45.0
OUTER_KEY_EMBED = 8.0
OUTER_KEY_HALF_WIDTH = 8.0
OUTER_KEY_BOTTOM_Z = 2.60
OUTER_KEY_WALL_TOP_Z = 5.50
OUTER_KEY_APEX_Z = 10.50
OUTER_KEY_CLEARANCE = 0.40
OUTER_KEY_UNDERSIDE_CLEARANCE = 0.20

OUTER_RECEIVER_START_X = V2.INNER_LENGTH - OUTER_KEY_OVERLAP
OUTER_RECEIVER_END_X = V2.INNER_LENGTH + 2.0
OUTER_RECEIVER_CAVITY_BOTTOM_Z = (
    OUTER_KEY_BOTTOM_Z - OUTER_KEY_UNDERSIDE_CLEARANCE
)
OUTER_RECEIVER_CAVITY_WALL_TOP_Z = OUTER_KEY_WALL_TOP_Z + OUTER_KEY_CLEARANCE
OUTER_RECEIVER_CAVITY_APEX_Z = OUTER_KEY_APEX_Z + OUTER_KEY_CLEARANCE

# Transverse replaceable snap pin. Reuse the same printable v2 lock-pin part.
OUTER_LOCK_CENTER_X = V2.INNER_LENGTH - 22.0
OUTER_LOCK_HOLE_WIDTH = 7.0
OUTER_LOCK_HOLE_BOTTOM_Z = 4.0
OUTER_LOCK_HOLE_WALL_TOP_Z = 8.0
OUTER_LOCK_HOLE_APEX_Z = 11.5
OUTER_LOCK_HOLE_LENGTH = 50.0

# U-shaped guide rail. It is deliberately oversized until the physical Samsung
# arm width/side profile is measured. The low central floor is ~9 mm below the
# current blank saddle contact plane, so it does not carry normal vertical load.
OUTER_BODY_WIDTH = 68.0
OUTER_FLOOR_THICKNESS = 5.0
OUTER_WALL_THICKNESS = 4.0
OUTER_WALL_HEIGHT = 22.0
OUTER_CHANNEL_PLACEHOLDER_WIDTH = OUTER_BODY_WIDTH - 2.0 * OUTER_WALL_THICKNESS

STAND_CONTACT_PLANE_GLOBAL_Z = (
    V2.TRACK_TOP_Z + V2.SADDLE_POCKET_FLOOR + V2.SADDLE_INSERT_HEIGHT
)
OUTER_FLOOR_TOP_GLOBAL_Z = V2.TRACK_TOP_Z + OUTER_FLOOR_THICKNESS
NORMAL_VERTICAL_CLEARANCE_TO_GUIDE_FLOOR = (
    STAND_CONTACT_PLANE_GLOBAL_Z - OUTER_FLOOR_TOP_GLOBAL_Z
)

OUTER_PRINT_LENGTH = OUTER_VISIBLE_LENGTH + OUTER_KEY_OVERLAP
OUTER_PRINT_WIDTH = OUTER_BODY_WIDTH
OUTER_PRINT_HEIGHT = OUTER_WALL_HEIGHT

# Small safety gap between fixed glide track outer radius and the first
# full-bottom surface of OUTER_GUIDE. Only the lifted key overlaps radially.
TRACK_OUTER_RADIUS = V2.TRACK_RADIUS + V2.TRACK_RADIAL_WIDTH / 2.0
OUTER_BODY_RADIAL_GAP_TO_TRACK = OUTER_R0 - TRACK_OUTER_RADIUS
