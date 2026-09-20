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

# Candidate large-part envelopes (x, y, z) in mm.
PRINT_MODULES = {
    "BASE_CENTER": (280.0, 295.0, 40.0),
    "BASE_LEFT": (200.0, 295.0, 40.0),
    "BASE_RIGHT": (200.0, 295.0, 40.0),
    "ROTOR": (190.0, 190.0, 35.0),
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
