#!/usr/bin/env python3
"""Parameters for v2: side glide tracks and modular rotating inner arms."""

from __future__ import annotations

import math

import geometry_model as G


# The rotating carrier underside is intentionally coplanar at two load paths:
# rotor top at the center and glide-track top near each saddle.
TRACK_TOP_Z = G.BEARING_TOP_Z + G.ROTOR_THICKNESS
TRACK_Z0 = G.BASE_FLOOR_THICKNESS
TRACK_HEIGHT = TRACK_TOP_Z - TRACK_Z0
TRACK_RADIUS = G.SADDLE_RADIUS
TRACK_RADIAL_WIDTH = 52.0
TRACK_ANGLE_MARGIN_DEG = 2.0

RIGHT_ARM_ANGLE_DEG = math.degrees(math.atan2(G.STAND_TIP_Y, G.STAND_HALF_WIDTH))
LEFT_ARM_ANGLE_DEG = 180.0 - RIGHT_ARM_ANGLE_DEG

# Rotating inner arm: local +X points outward along the original stand arm.
INNER_R0 = 85.0
INNER_LENGTH = 225.0
INNER_MALE_OVERLAP = 50.0
INNER_MALE_EMBED = 8.0
INNER_BEAM_WIDTH = 44.0
INNER_FLOOR_THICKNESS = 5.0
INNER_TOTAL_HEIGHT = 15.0

SADDLE_U = G.SADDLE_RADIUS - INNER_R0
SADDLE_PLATFORM_LENGTH = 56.0
SADDLE_PLATFORM_WIDTH = 58.0
SADDLE_POCKET_LENGTH = 50.0
SADDLE_POCKET_WIDTH = 48.0
SADDLE_POCKET_FLOOR = 7.0
SADDLE_INSERT_CLEARANCE = 0.30
SADDLE_INSERT_HEIGHT = 7.0

# Dedicated smaller form-locking arm connector.
ARM_KEY_HALF_WIDTH = 10.0
ARM_KEY_BOTTOM_Z = 0.40
ARM_KEY_UNDERSIDE_CLEARANCE = 0.20
ARM_KEY_WALL_TOP_Z = 5.0
ARM_KEY_APEX_Z = 15.0
ARM_KEY_CLEARANCE = 0.40

# Receiver sits on top of the rotor disk. Rotor itself is installed +10 mm
# above the base; inner arm is installed +18 mm, so these profiles coincide.
ROTOR_RECEIVER_R_INNER = 31.0
ROTOR_RECEIVER_R_OUTER = INNER_R0
ROTOR_RECEIVER_WIDTH = 40.0
ROTOR_INSTALL_Z = G.BEARING_TOP_Z
ROTOR_RECEIVER_Z0 = 7.80
ROTOR_RECEIVER_TOP_Z = 27.0

# Flat root landing: top is rotor-local z=8, therefore global z=18 after
# installation. That is exactly coplanar with TRACK_TOP_Z. The key tongue starts
# 0.4 mm above the arm underside and keeps 0.2 mm free space over the receiver
# floor, so guidance and vertical support are intentionally separated.
ROOT_LANDING_R0 = 83.0
ROOT_LANDING_R1 = 97.0
ROOT_LANDING_WIDTH = 36.0
ROOT_LANDING_Z0 = 5.80
ROOT_LANDING_TOP_Z = G.ROTOR_THICKNESS

ARM_KEY_INSTALLED_BOTTOM_ROTOR_Z = (
    TRACK_TOP_Z - ROTOR_INSTALL_Z + ARM_KEY_BOTTOM_Z
)
ROTOR_KEY_CAVITY_BOTTOM_Z = (
    ARM_KEY_INSTALLED_BOTTOM_ROTOR_Z - ARM_KEY_UNDERSIDE_CLEARANCE
)
ARM_RETAINER_RADIUS = 60.0

# Replaceable transverse snap pin: slides tangentially through rotor receiver and
# arm tongue. The tunnel has a printable roof; the pin carries withdrawal shear,
# while its split-end barbs only retain the pin.
ARM_LOCK_PIN_LENGTH = 48.0
ARM_LOCK_PIN_RADIAL_WIDTH = 6.0
ARM_LOCK_PIN_HEIGHT = 3.5
ARM_LOCK_HOLE_RADIAL_WIDTH = 7.0
ARM_LOCK_HOLE_BOTTOM_Z_ROTOR = 9.0
ARM_LOCK_HOLE_WALL_TOP_Z_ROTOR = 13.0
ARM_LOCK_HOLE_APEX_Z_ROTOR = 16.5
ARM_LOCK_HOLE_TRANSVERSE_LENGTH = 46.0

# Reuse v1 replaceable snap-pin envelope.
ARM_RETAINER_HOLE_X = G.RETAINER_HOLE_X
ARM_RETAINER_HOLE_Y = G.RETAINER_HOLE_Y

# The main inner arm plus its inward male tongue must still fit comfortably.
INNER_PRINT_LENGTH = INNER_LENGTH + INNER_MALE_OVERLAP
INNER_PRINT_WIDTH = SADDLE_PLATFORM_WIDTH
INNER_PRINT_HEIGHT = INNER_TOTAL_HEIGHT

# Blank insert is intentionally not the final Samsung-contact profile.
SADDLE_INSERT_LENGTH = SADDLE_POCKET_LENGTH - 2.0 * SADDLE_INSERT_CLEARANCE
SADDLE_INSERT_WIDTH = SADDLE_POCKET_WIDTH - 2.0 * SADDLE_INSERT_CLEARANCE


def track_angle_range(center_deg: float) -> tuple[float, float]:
    half = G.SWIVEL_LIMIT_DEG + TRACK_ANGLE_MARGIN_DEG
    return center_deg - half, center_deg + half


RIGHT_TRACK_ANGLE_RANGE = track_angle_range(RIGHT_ARM_ANGLE_DEG)
LEFT_TRACK_ANGLE_RANGE = track_angle_range(LEFT_ARM_ANGLE_DEG)
