#!/usr/bin/env python3
"""Parameters for v5: replaceable zero-position detent calibration cassette."""

from __future__ import annotations

import math

import geometry_model as G
import v2_params as V2


# A dedicated flat rotor sector provides a circular cam surface.  The stationary
# spring nose is aligned at +5 deg to avoid the legacy base-joint receiver.
DETENT_HOME_ANGLE_DEG = 5.0
DETENT_TRACK_R_INNER = 72.0
DETENT_TRACK_R_OUTER = 100.0
DETENT_TRACK_HALF_ANGLE_DEG = 22.0
DETENT_TRACK_Z0 = 0.0
DETENT_TRACK_HEIGHT = 6.0

# V-notch in the rotor track.  At 0 deg swivel the spring relaxes into this
# notch.  At all other useful angles it rides on the constant-radius cam.
DETENT_NOTCH_DEPTH = 1.20
DETENT_NOTCH_HALF_ANGLE_DEG = 5.0
DETENT_NOTCH_ROOT_RADIUS = DETENT_TRACK_R_OUTER - DETENT_NOTCH_DEPTH

# Replaceable in-plane PETG spring cassette.
DETENT_NOSE_RADIUS = 1.50
DETENT_RELAXED_INNER_RADIUS = 98.90
DETENT_NOSE_CENTER_RADIUS = DETENT_RELAXED_INNER_RADIUS + DETENT_NOSE_RADIUS
DETENT_NORMAL_DEFLECTION = DETENT_TRACK_R_OUTER - DETENT_RELAXED_INNER_RADIUS
DETENT_CENTER_CLEARANCE = (
    DETENT_RELAXED_INNER_RADIUS - DETENT_NOTCH_ROOT_RADIUS
)

DETENT_SPRING_LENGTH = 34.0
DETENT_SPRING_HEIGHT = 6.0
DETENT_SPRING_THICKNESSES = (1.8, 2.2, 2.6)

# Cassette anchor footprint, expressed in local radial/tangential coordinates
# relative to the spring nose center.
DETENT_ANCHOR_X0 = -2.4
DETENT_ANCHOR_X1 = 13.6
DETENT_ANCHOR_Y0 = 32.0
DETENT_ANCHOR_Y1 = 50.0
DETENT_ANCHOR_HEIGHT = DETENT_SPRING_HEIGHT

# Fixed support platform: top is exactly the rotor installation plane (global
# z=10). The cassette is therefore printed flat and installed at global z=10.
DETENT_MOUNT_Z0 = G.BASE_FLOOR_THICKNESS - 0.20
DETENT_MOUNT_TOP_Z = V2.ROTOR_INSTALL_Z
DETENT_MOUNT_HEIGHT = DETENT_MOUNT_TOP_Z - DETENT_MOUNT_Z0

# Two simple removable locating pins. They only locate/retain the cassette;
# spring load remains in-plane and is reacted by the anchor walls/platform.
DETENT_PIN_LOCAL_X = (2.0, 9.6)
DETENT_PIN_LOCAL_Y = 41.0
DETENT_PIN_HOLE_SIZE = 4.4
DETENT_PIN_SHAFT_SIZE = 4.0
DETENT_PIN_SHAFT_HEIGHT = 12.4
DETENT_PIN_HEAD_SIZE = 7.0
DETENT_PIN_HEAD_HEIGHT = 2.0

# Approximate geometric strain for an in-plane cantilever with tip deflection.
# This does not claim a material fatigue life; it is a geometry sanity gate.
def cantilever_surface_strain(thickness: float, deflection: float) -> float:
    return 3.0 * thickness * deflection / (2.0 * DETENT_SPRING_LENGTH**2)


DETENT_STRAIN_ESTIMATES = {
    t: cantilever_surface_strain(t, DETENT_NORMAL_DEFLECTION)
    for t in DETENT_SPRING_THICKNESSES
}

# Force range is informational only, using a broad nominal PETG modulus range.
DETENT_E_MODULUS_RANGE_MPA = (1500.0, 2200.0)


def cantilever_force_n(thickness: float, modulus_mpa: float) -> float:
    inertia = DETENT_SPRING_HEIGHT * thickness**3 / 12.0
    return (
        3.0
        * modulus_mpa
        * inertia
        * DETENT_NORMAL_DEFLECTION
        / DETENT_SPRING_LENGTH**3
    )


DETENT_FORCE_RANGES_N = {
    t: (
        cantilever_force_n(t, DETENT_E_MODULUS_RANGE_MPA[0]),
        cantilever_force_n(t, DETENT_E_MODULUS_RANGE_MPA[1]),
    )
    for t in DETENT_SPRING_THICKNESSES
}

# Track sector must remain engaged at the stationary nose throughout +/-15 deg.
DETENT_REQUIRED_TRACK_HALF_ANGLE_DEG = (
    G.SWIVEL_LIMIT_DEG + DETENT_NOTCH_HALF_ANGLE_DEG + 2.0
)
