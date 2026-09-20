#!/usr/bin/env python3
"""Physical Samsung stand measurement model for v6 contact parts."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any


class MeasurementError(ValueError):
    pass


@dataclass(frozen=True)
class Profile:
    points: tuple[tuple[float, float], ...]

    @property
    def ymin(self) -> float:
        return min(p[0] for p in self.points)

    @property
    def ymax(self) -> float:
        return max(p[0] for p in self.points)

    @property
    def zmin(self) -> float:
        return min(p[1] for p in self.points)

    @property
    def zmax(self) -> float:
        return max(p[1] for p in self.points)

    @property
    def width(self) -> float:
        return self.ymax - self.ymin

    @property
    def height(self) -> float:
        return self.zmax - self.zmin

    @property
    def signed_area(self) -> float:
        pts = self.points
        return 0.5 * sum(
            pts[i][0] * pts[(i + 1) % len(pts)][1]
            - pts[(i + 1) % len(pts)][0] * pts[i][1]
            for i in range(len(pts))
        )

    @property
    def area(self) -> float:
        return abs(self.signed_area)


def _is_number(v: Any) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def _require_number(v: Any, path: str, *, positive: bool = False) -> float:
    if not _is_number(v):
        raise MeasurementError(f"{path}: expected finite number, got {v!r}")
    x = float(v)
    if positive and x <= 0.0:
        raise MeasurementError(f"{path}: expected > 0, got {x}")
    return x


def _orientation(a, b, c) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _on_segment(a, b, p, eps=1e-9) -> bool:
    return (
        min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps
        and min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps
        and abs(_orientation(a, b, p)) <= eps
    )


def _segments_intersect(a, b, c, d, eps=1e-9) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)

    if ((o1 > eps and o2 < -eps) or (o1 < -eps and o2 > eps)) and (
        (o3 > eps and o4 < -eps) or (o3 < -eps and o4 > eps)
    ):
        return True

    return (
        abs(o1) <= eps and _on_segment(a, b, c, eps)
        or abs(o2) <= eps and _on_segment(a, b, d, eps)
        or abs(o3) <= eps and _on_segment(c, d, a, eps)
        or abs(o4) <= eps and _on_segment(c, d, b, eps)
    )


def _self_intersects(points: tuple[tuple[float, float], ...]) -> bool:
    n = len(points)
    for i in range(n):
        a = points[i]
        b = points[(i + 1) % n]
        for j in range(i + 1, n):
            # Adjacent edges share an endpoint and are allowed.
            if j == i or j == (i + 1) % n or (j + 1) % n == i:
                continue
            # First and last are adjacent in the closed polygon.
            if i == 0 and j == n - 1:
                continue
            c = points[j]
            d = points[(j + 1) % n]
            if _segments_intersect(a, b, c, d):
                return True
    return False


def parse_profile(raw: Any, path: str) -> Profile:
    if not isinstance(raw, list) or len(raw) < 4:
        raise MeasurementError(f"{path}: need at least 4 [y,z] profile points")

    pts = []
    for i, item in enumerate(raw):
        if not isinstance(item, list) or len(item) != 2:
            raise MeasurementError(f"{path}[{i}]: expected [y,z]")
        pts.append(
            (
                _require_number(item[0], f"{path}[{i}][0]"),
                _require_number(item[1], f"{path}[{i}][1]"),
            )
        )

    # Consecutive duplicate vertices make later CAD offsets/lofts fragile.
    for i, p in enumerate(pts):
        if p == pts[(i + 1) % len(pts)]:
            raise MeasurementError(f"{path}: duplicate consecutive point {p}")

    profile = Profile(tuple(pts))
    if profile.width < 3.0:
        raise MeasurementError(f"{path}: implausible profile width {profile.width:.3f} mm")
    if not (profile.ymin < 0.0 < profile.ymax):
        raise MeasurementError(
            f"{path}: profile must straddle y=0 local arm centerline"
        )
    if profile.height < 2.0:
        raise MeasurementError(f"{path}: implausible profile height {profile.height:.3f} mm")
    if profile.area < 10.0:
        raise MeasurementError(f"{path}: implausible polygon area {profile.area:.3f} mm²")
    if _self_intersects(profile.points):
        raise MeasurementError(f"{path}: polygon self-intersects")

    return profile


STATION_RADIUS_COORD_TOLERANCE_MM = 1.5


@dataclass(frozen=True)
class Station:
    radius: float
    center_xy: tuple[float, float]
    profile: Profile

    @property
    def coordinate_radius(self) -> float:
        return math.hypot(*self.center_xy)

    @property
    def coordinate_angle_deg(self) -> float:
        return math.degrees(math.atan2(self.center_xy[1], self.center_xy[0]))


@dataclass(frozen=True)
class MeasurementSet:
    raw: dict[str, Any]
    stand_width: float
    stand_depth: float
    pivot_to_rear: float
    left_tip_xy: tuple[float, float]
    right_tip_xy: tuple[float, float]
    inner_left: Station
    inner_right: Station
    outer_left: tuple[Station, Station, Station]
    outer_right: tuple[Station, Station, Station]
    pad_used: bool
    pad_thickness: float


def _tip_xy(raw: Any, path: str) -> tuple[float, float]:
    if not isinstance(raw, list) or len(raw) != 2:
        raise MeasurementError(f"{path}: expected [x,y]")
    return (
        _require_number(raw[0], path + "[0]"),
        _require_number(raw[1], path + "[1]"),
    )


def _station(raw: Any, path: str) -> Station:
    if not isinstance(raw, dict):
        raise MeasurementError(f"{path}: expected object")

    center_xy = _tip_xy(raw.get("center_xy_mm"), path + ".center_xy_mm")
    station = Station(
        radius=_require_number(
            raw.get("station_radius_mm"),
            path + ".station_radius_mm",
            positive=True,
        ),
        center_xy=center_xy,
        profile=parse_profile(
            raw.get("profile_points_mm"),
            path + ".profile_points_mm",
        ),
    )

    radius_delta = abs(station.radius - station.coordinate_radius)
    if radius_delta > STATION_RADIUS_COORD_TOLERANCE_MM:
        raise MeasurementError(
            f"{path}: station_radius_mm and center_xy_mm disagree by "
            f"{radius_delta:.3f} mm (max "
            f"{STATION_RADIUS_COORD_TOLERANCE_MM:.3f} mm)"
        )

    return station


def load_measurements(path: str | Path) -> MeasurementSet:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))

    g = data.get("global")
    if not isinstance(g, dict):
        raise MeasurementError("global: expected object")

    inner = data.get("inner_saddle")
    outer = data.get("outer_guide")
    pad = data.get("contact_pad")
    if not isinstance(inner, dict):
        raise MeasurementError("inner_saddle: expected object")
    if not isinstance(outer, dict):
        raise MeasurementError("outer_guide: expected object")
    if not isinstance(pad, dict):
        raise MeasurementError("contact_pad: expected object")

    pad_used = pad.get("used")
    if not isinstance(pad_used, bool):
        raise MeasurementError("contact_pad.used: expected boolean")
    pad_t = _require_number(
        pad.get("compressed_thickness_mm"),
        "contact_pad.compressed_thickness_mm",
    )
    if pad_t < 0.0 or pad_t > 5.0:
        raise MeasurementError("contact_pad.compressed_thickness_mm: expected 0..5 mm")
    if pad_used:
        raise MeasurementError(
            "contact_pad.used: this project is PETG-only; external contact "
            "pads/layers are not permitted by the current design constraint"
        )
    if abs(pad_t) > 1e-9:
        raise MeasurementError(
            "contact_pad.compressed_thickness_mm must be 0 for PETG-only build"
        )

    def outer_side(side: str) -> tuple[Station, Station, Station]:
        obj = outer.get(side)
        if not isinstance(obj, dict):
            raise MeasurementError(f"outer_guide.{side}: expected object")
        return tuple(
            _station(obj.get(name), f"outer_guide.{side}.{name}")
            for name in ("root", "mid", "tip")
        )

    ms = MeasurementSet(
        raw=data,
        stand_width=_require_number(g.get("stand_width_mm"), "global.stand_width_mm", positive=True),
        stand_depth=_require_number(g.get("stand_depth_mm"), "global.stand_depth_mm", positive=True),
        pivot_to_rear=_require_number(g.get("pivot_to_rear_mm"), "global.pivot_to_rear_mm", positive=True),
        left_tip_xy=_tip_xy(g.get("left_tip_xy_mm"), "global.left_tip_xy_mm"),
        right_tip_xy=_tip_xy(g.get("right_tip_xy_mm"), "global.right_tip_xy_mm"),
        inner_left=_station(inner.get("left"), "inner_saddle.left"),
        inner_right=_station(inner.get("right"), "inner_saddle.right"),
        outer_left=outer_side("left"),
        outer_right=outer_side("right"),
        pad_used=pad_used,
        pad_thickness=pad_t,
    )

    validate_global_plausibility(ms)
    return ms


def validate_global_plausibility(ms: MeasurementSet) -> None:
    if not 750.0 <= ms.stand_width <= 950.0:
        raise MeasurementError(f"global.stand_width_mm: implausible {ms.stand_width:.3f}")
    if not 240.0 <= ms.stand_depth <= 340.0:
        raise MeasurementError(f"global.stand_depth_mm: implausible {ms.stand_depth:.3f}")
    if not 40.0 <= ms.pivot_to_rear <= 130.0:
        raise MeasurementError(f"global.pivot_to_rear_mm: implausible {ms.pivot_to_rear:.3f}")

    for name, st in (("inner_left", ms.inner_left), ("inner_right", ms.inner_right)):
        if not 240.0 <= st.radius <= 310.0:
            raise MeasurementError(
                f"{name}.station_radius_mm: implausible {st.radius:.3f}"
            )

    for side, stations in (("left", ms.outer_left), ("right", ms.outer_right)):
        radii = [x.radius for x in stations]
        if not all(300.0 <= r <= 500.0 for r in radii):
            raise MeasurementError(
                f"outer_guide.{side}: station radius outside 300..500 mm"
            )
        if not (radii[0] < radii[1] < radii[2]):
            raise MeasurementError(
                f"outer_guide.{side}: radii must increase root < mid < tip"
            )

    # Global sign convention: left arm is -X, right arm is +X, both extend
    # forward (+Y) from the pivot.
    for name, st in (
        ("inner_saddle.left", ms.inner_left),
        ("outer_guide.left.root", ms.outer_left[0]),
        ("outer_guide.left.mid", ms.outer_left[1]),
        ("outer_guide.left.tip", ms.outer_left[2]),
    ):
        if not (st.center_xy[0] < 0.0 and st.center_xy[1] > 0.0):
            raise MeasurementError(
                f"{name}.center_xy_mm: expected left/front quadrant (-X,+Y)"
            )

    for name, st in (
        ("inner_saddle.right", ms.inner_right),
        ("outer_guide.right.root", ms.outer_right[0]),
        ("outer_guide.right.mid", ms.outer_right[1]),
        ("outer_guide.right.tip", ms.outer_right[2]),
    ):
        if not (st.center_xy[0] > 0.0 and st.center_xy[1] > 0.0):
            raise MeasurementError(
                f"{name}.center_xy_mm: expected right/front quadrant (+X,+Y)"
            )


def symmetry_report(ms: MeasurementSet) -> dict[str, float]:
    return {
        "tip_x_magnitude_delta_mm": abs(abs(ms.left_tip_xy[0]) - abs(ms.right_tip_xy[0])),
        "tip_y_delta_mm": abs(ms.left_tip_xy[1] - ms.right_tip_xy[1]),
        "inner_radius_delta_mm": abs(ms.inner_left.radius - ms.inner_right.radius),
        "inner_centerline_angle_delta_deg": abs(
            (180.0 - ms.inner_left.coordinate_angle_deg)
            - ms.inner_right.coordinate_angle_deg
        ),
        "inner_profile_width_delta_mm": abs(ms.inner_left.profile.width - ms.inner_right.profile.width),
        "inner_profile_height_delta_mm": abs(ms.inner_left.profile.height - ms.inner_right.profile.height),
        "outer_root_width_delta_mm": abs(ms.outer_left[0].profile.width - ms.outer_right[0].profile.width),
        "outer_mid_width_delta_mm": abs(ms.outer_left[1].profile.width - ms.outer_right[1].profile.width),
        "outer_tip_width_delta_mm": abs(ms.outer_left[2].profile.width - ms.outer_right[2].profile.width),
    }


def _profile_z_intersections_at_y(
    profile: Profile,
    y: float,
) -> tuple[float, ...]:
    """Return all boundary intersections with a vertical line at local Y."""
    zs = []
    pts = profile.points
    n = len(pts)

    for i in range(n):
        y1, z1 = pts[i]
        y2, z2 = pts[(i + 1) % n]

        if abs(y2 - y1) < 1e-12:
            if abs(y - y1) < 1e-9:
                zs.extend((z1, z2))
            continue

        lo = min(y1, y2)
        hi = max(y1, y2)
        if y < lo - 1e-9 or y > hi + 1e-9:
            continue

        t = (y - y1) / (y2 - y1)
        if -1e-9 <= t <= 1.0 + 1e-9:
            zs.append(z1 + t * (z2 - z1))

    return tuple(zs)


def lower_envelope(
    profile: Profile,
    samples: int = 31,
) -> tuple[tuple[float, float], ...]:
    """Return a vertex-exact lower Z boundary of a closed measured profile.

    Every measured vertex Y is included exactly. Optional uniform samples only
    densify the piecewise-linear contour; they can never replace or smooth over
    a real measured kink. This matters for load-bearing saddle inserts, where a
    missed lower-profile vertex would otherwise create small solid penetration.
    """
    if samples < 3:
        raise ValueError("samples must be >= 3")

    uniform_ys = {
        profile.ymin
        + (profile.ymax - profile.ymin) * i / (samples - 1)
        for i in range(samples)
    }
    vertex_ys = {y for y, _z in profile.points}
    ys = sorted(uniform_ys | vertex_ys)

    out = []
    for y in ys:
        zs = _profile_z_intersections_at_y(profile, y)
        if not zs:
            raise MeasurementError(
                f"cannot derive lower envelope at y={y:.6f} from profile"
            )
        out.append((y, min(zs)))

    # Normalize against the actual measured minimum, not the sampled minimum.
    # This preserves the physical datum even if a uniform sample would miss it.
    return tuple((y, z - profile.zmin) for y, z in out)


def project_xy_to_arm_frame(
    xy: tuple[float, float],
    arm_angle_deg: float,
) -> tuple[float, float]:
    """Project global stand-local XY into a structural arm frame.

    local +X: from pivot outward along the structural arm centerline.
    local +Y: 90 degrees counter-clockwise from local +X.
    """
    a = math.radians(arm_angle_deg)
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    x, y = xy
    along = x * ux + y * uy
    lateral = x * nx + y * ny
    return along, lateral


def station_arm_frame(
    station: Station,
    arm_angle_deg: float,
) -> tuple[float, float]:
    return project_xy_to_arm_frame(station.center_xy, arm_angle_deg)
