#!/usr/bin/env python3
"""Canonical geometry parameters and 2D transforms for Samsung_Stand."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Tuple


@dataclass(frozen=True)
class Point2:
    x: float
    y: float


@dataclass(frozen=True)
class Rect:
    width: float
    depth: float

    @property
    def xmin(self) -> float:
        return -self.width / 2.0

    @property
    def xmax(self) -> float:
        return self.width / 2.0

    @property
    def ymin(self) -> float:
        return -self.depth / 2.0

    @property
    def ymax(self) -> float:
        return self.depth / 2.0


SOUNDDECK = Rect(width=700.0, depth=340.0)
BASE = Rect(width=680.0, depth=295.0)

PRINTER_X = 300.0
PRINTER_Y = 300.0
PRINTER_Z = 330.0
PREFERRED_PART_XY = 295.0

STAND_WIDTH = 840.0
STAND_HALF_WIDTH = STAND_WIDTH / 2.0

# Reconstructed working geometry, not yet physical manufacturing truth.
STAND_TIP_Y = 208.0
STAND_REAR_Y = -80.0
ARM_SLOPE = STAND_TIP_Y / STAND_HALF_WIDTH

PIVOT = Point2(0.0, -64.0)
SWIVEL_LIMIT_DEG = 15.0

SADDLE_LOCAL_X = 250.0
SADDLE_LOCAL_Y = SADDLE_LOCAL_X * ARM_SLOPE
SADDLE_RADIUS = math.hypot(SADDLE_LOCAL_X, SADDLE_LOCAL_Y)

# Conservative half-size used for early support-footprint containment checks.
SADDLE_PAD_HALF_X = 20.0
SADDLE_PAD_HALF_Y = 20.0

# v1 fixed-base construction.
BASE_CENTER_WIDTH = 280.0
BASE_SIDE_WIDTH = (BASE.width - BASE_CENTER_WIDTH) / 2.0
BASE_FLOOR_THICKNESS = 4.0
BASE_RIB_HEIGHT = 10.0

# Each side module slides two long male roof-keys into matching center receivers.
# The snap pin retains withdrawal; it is not the primary vertical/bending load path.
JOINT_OVERLAP = 50.0
JOINT_EMBED = 8.0
JOINT_KEY_HALF_WIDTH = 12.0
JOINT_KEY_WALL_TOP_Z = 8.0
JOINT_KEY_APEX_Z = 20.0
JOINT_RECEIVER_HEIGHT = 24.0
JOINT_RECEIVER_WIDTH = 50.0
JOINT_Y_CENTERS = (-90.0, 90.0)
JOINT_CLEARANCE = 0.40

RETAINER_PIN_X = 8.0
RETAINER_PIN_Y = 12.0
RETAINER_HOLE_X = 8.6
RETAINER_HOLE_Y = 12.6
RETAINER_HOLE_LOCAL_X = 25.0  # measured inward from center/side seam

# Swivel bearing.
BEARING_OUTER_DIAMETER = 164.0
BEARING_INNER_DIAMETER = 104.0
BEARING_HEIGHT = 6.0
BEARING_TOP_Z = BASE_FLOOR_THICKNESS + BEARING_HEIGHT
ROTOR_THICKNESS = 8.0
PIVOT_STEM_DIAMETER = 29.0
PIVOT_BORE_DIAMETER = 30.6
PIVOT_NECK_DIAMETER = 25.0
PIVOT_NECK_Z0 = 19.0
PIVOT_NECK_HEIGHT = 4.0
PIVOT_CLIP_OUTER_DIAMETER = 38.0
PIVOT_CLIP_INNER_DIAMETER = 25.4
PIVOT_CLIP_THICKNESS = 3.0

DESIGN_VERTICAL_LOAD_N = 500.0


def annulus_area_mm2(outer_diameter: float, inner_diameter: float) -> float:
    return math.pi * (outer_diameter**2 - inner_diameter**2) / 4.0


BEARING_NOMINAL_AREA_MM2 = annulus_area_mm2(
    BEARING_OUTER_DIAMETER, BEARING_INNER_DIAMETER
)
BEARING_NOMINAL_PRESSURE_MPA = DESIGN_VERTICAL_LOAD_N / BEARING_NOMINAL_AREA_MM2

# Candidate printable envelopes (x, y, z) in mm.  Side modules include their
# 50 mm male joint overlap; the nominal 200 mm visible side width alone is not
# sufficient for a print-bed gate.
PRINT_MODULES = {
    "BASE_CENTER": (BASE_CENTER_WIDTH, BASE.depth, JOINT_RECEIVER_HEIGHT),
    "BASE_LEFT": (BASE_SIDE_WIDTH + JOINT_OVERLAP, BASE.depth, JOINT_RECEIVER_HEIGHT),
    "BASE_RIGHT": (BASE_SIDE_WIDTH + JOINT_OVERLAP, BASE.depth, JOINT_RECEIVER_HEIGHT),
    "ROTOR": (BEARING_OUTER_DIAMETER, BEARING_OUTER_DIAMETER, 16.0),
    "JOINT_RETAINER": (14.0, 18.0, 31.0),
    "PIVOT_CLIP": (PIVOT_CLIP_OUTER_DIAMETER, PIVOT_CLIP_OUTER_DIAMETER, PIVOT_CLIP_THICKNESS),
    "INNER_LEFT": (285.0, 120.0, 45.0),
    "INNER_RIGHT": (285.0, 120.0, 45.0),
    "OUTER_GUIDE_LEFT": (220.0, 80.0, 45.0),
    "OUTER_GUIDE_RIGHT": (220.0, 80.0, 45.0),
}


def rotate_local(point: Point2, angle_deg: float) -> Point2:
    """Rotate a point around local origin."""
    a = math.radians(angle_deg)
    c = math.cos(a)
    s = math.sin(a)
    return Point2(
        point.x * c - point.y * s,
        point.x * s + point.y * c,
    )


def local_to_sounddeck(point: Point2, angle_deg: float) -> Point2:
    """Rotate around swivel axis and translate into Sounddeck coordinates."""
    q = rotate_local(point, angle_deg)
    return Point2(q.x + PIVOT.x, q.y + PIVOT.y)


def saddle_centers(angle_deg: float) -> Tuple[Point2, Point2]:
    left = local_to_sounddeck(Point2(-SADDLE_LOCAL_X, SADDLE_LOCAL_Y), angle_deg)
    right = local_to_sounddeck(Point2(+SADDLE_LOCAL_X, SADDLE_LOCAL_Y), angle_deg)
    return left, right


def rect_contains_point(rect: Rect, p: Point2, margin: float = 0.0) -> bool:
    return (
        rect.xmin + margin <= p.x <= rect.xmax - margin
        and rect.ymin + margin <= p.y <= rect.ymax - margin
    )


def support_pad_inside_sounddeck(p: Point2) -> bool:
    return (
        SOUNDDECK.xmin <= p.x - SADDLE_PAD_HALF_X
        and p.x + SADDLE_PAD_HALF_X <= SOUNDDECK.xmax
        and SOUNDDECK.ymin <= p.y - SADDLE_PAD_HALF_Y
        and p.y + SADDLE_PAD_HALF_Y <= SOUNDDECK.ymax
    )


def sweep_angles(step_deg: float = 1.0) -> Iterable[float]:
    n = round((2.0 * SWIVEL_LIMIT_DEG) / step_deg)
    for i in range(n + 1):
        yield -SWIVEL_LIMIT_DEG + i * step_deg
