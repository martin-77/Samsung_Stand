#!/usr/bin/env python3
"""Assembly validation for measurement-driven v6 contact parts.

The validator checks both interfaces:
1. generated contact parts against the validated v8 structural parts;
2. the measured Samsung arm profiles against the generated contact parts.

This prevents a geometrically valid insert from silently violating the intended
load path or the requested fit clearance.
"""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import
import Part

import build_v6_contacts as B
import measurement_model as M
import v2_params as V2
import v3_params as V3


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
V8_STEP = os.path.join(ROOT, "cad", "v8", "STEP")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(path):
    if not os.path.isfile(path):
        raise RuntimeError("Missing STEP: " + path)
    doc = App.newDocument("asm_" + os.path.basename(path).replace(".", "_"))
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = [
        obj.Shape.copy()
        for obj in doc.Objects
        if hasattr(obj, "Shape") and not obj.Shape.isNull()
    ]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No shape in " + path)
    sh = shapes[0]
    for other in shapes[1:]:
        sh = sh.fuse(other)
    return sh.removeSplitter()


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def profile_prism(
    profile: M.Profile,
    x_center: float,
    length: float,
    z0: float,
    lateral_offset: float = 0.0,
):
    """Extrude a measured YZ cross-section along local structural-arm X."""
    x0 = x_center - length / 2.0
    pts = [
        v(x0, y + lateral_offset, z0 + z)
        for y, z in profile.points
    ]
    wire = Part.makePolygon(pts + [pts[0]])
    face = Part.Face(wire)
    sh = face.extrude(v(length, 0, 0)).removeSplitter()
    if sh.isNull() or not sh.isValid() or len(sh.Solids) != 1:
        raise RuntimeError("invalid measured profile prism")
    return sh


def station_frame(station: M.Station, side: str) -> tuple[float, float]:
    return B.station_frame(station, side)


def liner_station_x(station: M.Station, side: str) -> float:
    along, _lateral = station_frame(station, side)
    raw = along - V3.OUTER_R0
    return min(max(raw, B.GUIDE_LINER_X0), B.GUIDE_LINER_X1)


def main(
    contact_dir: str = "build_v6_contacts",
    measurement_path: str = "tests/fixtures/stand_measurements.synthetic.json",
):
    ms = M.load_measurements(measurement_path)

    inner = load_step(os.path.join(V8_STEP, "samsung_stand_v8_inner_arm.step"))
    guide = load_step(os.path.join(V8_STEP, "samsung_stand_v8_outer_guide.step"))

    failures = []
    result = {
        "version": "v6-contact-parts",
        "measurement_path": measurement_path,
        "saddles": {},
        "liners": {},
        "measured_profile_fit": {
            "saddles": {},
            "outer_guides": {},
        },
    }

    # ------------------------------------------------------------------
    # Inner saddle inserts: structural seating + all three measured sections.
    # ------------------------------------------------------------------
    inner_sets = {
        "left": ms.inner_left,
        "right": ms.inner_right,
    }
    stand_low_z_inner_nominal = (
        V2.SADDLE_POCKET_FLOOR + V2.SADDLE_INSERT_HEIGHT
    )
    vertical_reference = M.inner_vertical_reference_mm(ms)

    for side in ("left", "right"):
        saddle = load_step(
            os.path.join(
                contact_dir,
                f"samsung_stand_v6_saddle_insert_{side}.step",
            )
        )
        saddle.translate(v(V2.SADDLE_U, 0, V2.SADDLE_POCKET_FLOOR))

        vol = common_volume(saddle, inner)
        gap = distance(saddle, inner)
        bb = saddle.BoundBox

        result["saddles"][side] = {
            "common_volume_mm3": round(vol, 6),
            "distance_to_inner_arm_mm": round(gap, 6),
            "installed_bbox_mm": [
                round(bb.XMin, 3), round(bb.XMax, 3),
                round(bb.YMin, 3), round(bb.YMax, 3),
                round(bb.ZMin, 3), round(bb.ZMax, 3),
            ],
        }

        if vol > 0.05:
            failures.append(
                f"{side} saddle penetrates INNER_ARM: {vol:.6f} mm3"
            )
        if gap > 0.05:
            failures.append(
                f"{side} saddle is not seated in INNER_ARM pocket: "
                f"{gap:.6f} mm"
            )

        result["measured_profile_fit"]["saddles"][side] = {}
        for station_name, station in zip(
            ("root", "center", "tip"),
            inner_sets[side],
        ):
            inner_along, inner_lateral = station_frame(
                station,
                side,
            )
            vertical_offset = M.station_vertical_offset_mm(
                station,
                ms,
            )
            stand_low_z_inner = (
                stand_low_z_inner_nominal + vertical_offset
            )
            stand = profile_prism(
                station.profile,
                inner_along - V2.INNER_R0,
                0.8,
                stand_low_z_inner,
                lateral_offset=inner_lateral,
            )
            stand_saddle_vol = common_volume(stand, saddle)
            stand_saddle_gap = distance(stand, saddle)
            stand_inner_vol = common_volume(stand, inner)

            result["measured_profile_fit"]["saddles"][side][
                station_name
            ] = {
                "stand_saddle_common_volume_mm3": round(
                    stand_saddle_vol, 6
                ),
                "stand_saddle_distance_mm": round(
                    stand_saddle_gap, 6
                ),
                "stand_inner_structure_common_volume_mm3": round(
                    stand_inner_vol, 6
                ),
                "measured_lateral_offset_mm": round(
                    inner_lateral, 6
                ),
                "measured_lowest_point_height_mm": round(
                    station.lowest_point_height_mm, 6
                ),
                "vertical_reference_height_mm": round(
                    vertical_reference, 6
                ),
                "relative_vertical_offset_mm": round(
                    vertical_offset, 6
                ),
                "installed_lowest_point_z_mm": round(
                    stand_low_z_inner, 6
                ),
                "expected": (
                    "surface contact to lofted saddle insert; no "
                    "penetration into insert or structural INNER_ARM"
                ),
            }

            if stand_saddle_vol > 0.05:
                failures.append(
                    f"{side}/{station_name} measured saddle profile "
                    f"penetrates insert: {stand_saddle_vol:.6f} mm3"
                )
            if stand_saddle_gap > 0.05:
                failures.append(
                    f"{side}/{station_name} measured saddle profile is "
                    f"not supported by insert: gap "
                    f"{stand_saddle_gap:.6f} mm"
                )
            if stand_inner_vol > 0.05:
                failures.append(
                    f"{side}/{station_name} measured saddle profile "
                    f"penetrates structural INNER_ARM: "
                    f"{stand_inner_vol:.6f} mm3"
                )

    # ------------------------------------------------------------------
    # Outer guides: lateral-only rails + measured 0.5 mm side clearance.
    # ------------------------------------------------------------------
    outer_sets = {
        "left": ms.outer_left,
        "right": ms.outer_right,
    }
    stand_low_z_outer_nominal = (
        V3.STAND_CONTACT_PLANE_GLOBAL_Z - V2.TRACK_TOP_Z
    )
    outer_floor_clearances = []

    for side in ("left", "right"):
        result["liners"][side] = {}
        installed_rails = {}

        for wall_side in ("neg_y", "pos_y"):
            liner = load_step(
                os.path.join(
                    contact_dir,
                    (
                        f"samsung_stand_v6_outer_liner_{side}_"
                        f"{wall_side}.step"
                    ),
                )
            )
            liner.translate(v(0, 0, V3.OUTER_FLOOR_THICKNESS))
            installed_rails[wall_side] = liner

            vol = common_volume(liner, guide)
            gap = distance(liner, guide)
            bb = liner.BoundBox

            row = {
                "common_volume_mm3": round(vol, 6),
                "distance_to_outer_guide_mm": round(gap, 6),
                "installed_bbox_mm": [
                    round(bb.XMin, 3), round(bb.XMax, 3),
                    round(bb.YMin, 3), round(bb.YMax, 3),
                    round(bb.ZMin, 3), round(bb.ZMax, 3),
                ],
                "top_matches_guide_wall_mm": round(
                    V3.OUTER_WALL_HEIGHT - bb.ZMax, 6
                ),
                "crosses_arm_centerline": bool(
                    bb.YMin <= 0.0 <= bb.YMax
                ),
            }
            result["liners"][side][wall_side] = row

            if vol > 0.05:
                failures.append(
                    f"{side}/{wall_side} liner penetrates OUTER_GUIDE: "
                    f"{vol:.6f} mm3"
                )
            if gap > 0.05:
                failures.append(
                    f"{side}/{wall_side} liner is not seated in OUTER_GUIDE: "
                    f"{gap:.6f} mm"
                )
            if bb.ZMax > V3.OUTER_WALL_HEIGHT + 0.05:
                failures.append(
                    f"{side}/{wall_side} liner exceeds OUTER_GUIDE wall "
                    f"height: zmax={bb.ZMax:.3f}"
                )
            if bb.YMin <= 0.0 <= bb.YMax:
                failures.append(
                    f"{side}/{wall_side} liner crosses arm centerline and "
                    "could create an unintended vertical floor bridge"
                )

        result["measured_profile_fit"]["outer_guides"][side] = {}
        for station_name, station in zip(
            ("root", "mid", "tip"),
            outer_sets[side],
        ):
            x = liner_station_x(station, side)
            _along, lateral = station_frame(station, side)
            vertical_offset = M.station_vertical_offset_mm(
                station,
                ms,
            )
            stand_low_z_outer = (
                stand_low_z_outer_nominal + vertical_offset
            )
            floor_vertical_clearance = (
                stand_low_z_outer - V3.OUTER_FLOOR_THICKNESS
            )
            outer_floor_clearances.append(
                floor_vertical_clearance
            )
            stand = profile_prism(
                station.profile,
                x,
                0.8,
                stand_low_z_outer,
                lateral_offset=lateral,
            )

            neg = installed_rails["neg_y"]
            pos = installed_rails["pos_y"]

            neg_gap = distance(stand, neg)
            pos_gap = distance(stand, pos)
            neg_vol = common_volume(stand, neg)
            pos_vol = common_volume(stand, pos)
            structural_vol = common_volume(stand, guide)

            row = {
                "liner_x_mm": round(x, 4),
                "measured_lateral_offset_mm": round(lateral, 6),
                "measured_lowest_point_height_mm": round(
                    station.lowest_point_height_mm, 6
                ),
                "relative_vertical_offset_mm": round(
                    vertical_offset, 6
                ),
                "installed_lowest_point_z_mm": round(
                    stand_low_z_outer, 6
                ),
                "neg_y_clearance_mm": round(neg_gap, 6),
                "pos_y_clearance_mm": round(pos_gap, 6),
                "neg_y_common_volume_mm3": round(neg_vol, 6),
                "pos_y_common_volume_mm3": round(pos_vol, 6),
                "stand_guide_structure_common_volume_mm3": round(
                    structural_vol, 6
                ),
                "vertical_clearance_above_guide_floor_mm": round(
                    floor_vertical_clearance, 6
                ),
            }
            result["measured_profile_fit"]["outer_guides"][side][
                station_name
            ] = row

            for wall_side, measured_gap, measured_vol in (
                ("neg_y", neg_gap, neg_vol),
                ("pos_y", pos_gap, pos_vol),
            ):
                if measured_vol > 0.05:
                    failures.append(
                        f"{side}/{station_name}/{wall_side} measured stand "
                        f"profile penetrates liner: {measured_vol:.6f} mm3"
                    )
                if abs(
                    measured_gap - B.GUIDE_LATERAL_CLEARANCE
                ) > 0.08:
                    failures.append(
                        f"{side}/{station_name}/{wall_side} clearance "
                        f"{measured_gap:.6f} mm differs from target "
                        f"{B.GUIDE_LATERAL_CLEARANCE:.3f} mm"
                    )

            if structural_vol > 0.05:
                failures.append(
                    f"{side}/{station_name} measured stand profile "
                    f"penetrates structural OUTER_GUIDE: "
                    f"{structural_vol:.6f} mm3"
                )
            if floor_vertical_clearance < 5.0:
                failures.append(
                    f"{side}/{station_name} measured outer guide vertical "
                    f"floor clearance fell below 5 mm: "
                    f"{floor_vertical_clearance:.3f} mm"
                )

    minimum_floor_vertical_clearance = min(
        outer_floor_clearances
    )

    root_axial_free = B.GUIDE_LINER_X0 - V3.OUTER_ROOT_TIE_LENGTH
    tip_tie_x0 = V3.OUTER_VISIBLE_LENGTH - V3.OUTER_TIP_TIE_LENGTH
    tip_axial_free = tip_tie_x0 - B.GUIDE_LINER_X1
    tie_vertical_overlap = (
        V3.OUTER_TIE_HEIGHT - V3.OUTER_FLOOR_THICKNESS
    )

    if not 1.0 <= root_axial_free <= 5.0:
        failures.append(
            f"root rail axial capture gap invalid: {root_axial_free:.3f} mm"
        )
    if not 1.0 <= tip_axial_free <= 5.0:
        failures.append(
            f"tip rail axial capture gap invalid: {tip_axial_free:.3f} mm"
        )
    if tie_vertical_overlap < 2.0:
        failures.append(
            "OUTER_GUIDE cross-ties do not overlap installed side rails "
            f"enough for passive axial capture: {tie_vertical_overlap:.3f} mm"
        )

    result["outer_guide_load_path_contract"] = {
        "lateral_only": True,
        "generated_floor_bridge": False,
        "target_lateral_clearance_mm": B.GUIDE_LATERAL_CLEARANCE,
        "minimum_vertical_floor_clearance_mm": round(
            minimum_floor_vertical_clearance, 6
        ),
        "vertical_reference_height_mm": round(
            vertical_reference, 6
        ),
        "passive_axial_capture": {
            "root_free_travel_mm": round(root_axial_free, 6),
            "tip_free_travel_mm": round(tip_axial_free, 6),
            "tie_vertical_overlap_mm": round(tie_vertical_overlap, 6),
        },
        "note": (
            "Each OUTER_GUIDE uses two independent side rails. Measured "
            "root/mid/tip profiles are OCC-checked against those rails. "
            "No V6 contact part exists underneath the Samsung arm."
        ),
    }
    result["failed"] = failures

    os.makedirs(contact_dir, exist_ok=True)
    with open(
        os.path.join(
            contact_dir,
            "ASSEMBLY_VALIDATION_v6_contacts.json",
        ),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(
            "V6 CONTACT ASSEMBLY FAILED: " + " | ".join(failures)
        )


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--contacts", default="build_v6_contacts")
    ap.add_argument(
        "--measurements",
        default="tests/fixtures/stand_measurements.synthetic.json",
    )
    ns = ap.parse_args()
    main(ns.contacts, ns.measurements)
