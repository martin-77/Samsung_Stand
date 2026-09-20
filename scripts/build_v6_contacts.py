#!/usr/bin/env python3
"""Build measurement-driven v6 Samsung contact parts.

This script never guesses missing Samsung geometry. It requires a complete
measurement JSON accepted by measurement_model.py.

Generated parts:
- side-specific INNER saddle inserts with a measured underside support envelope;
- side-specific OUTER guide liners that preserve the v3 structural guide and
  add only lateral contact surfaces.

Usage with FreeCADCmd:
    FreeCADCmd -c "import sys; sys.path.insert(0,'scripts'); import build_v6_contacts as B; B.main('measurements/stand_measurements.json','build_v6_contacts')"
"""

from __future__ import annotations

import json
import math
import os

import FreeCAD as App
import MeshPart
import Part

import measurement_model as M
import v2_params as V2
import v3_params as V3


SADDLE_BASE_THICKNESS = 4.0
SADDLE_NOMINAL_LOWEST_CONTACT_Z = V2.SADDLE_INSERT_HEIGHT
SADDLE_PROFILE_SAMPLES = 41
SADDLE_ENDPOINT_DISTANCE_MAX_MM = 8.0
SADDLE_SECTION_SPACING_MAX_MM = 25.0

GUIDE_LATERAL_CLEARANCE = 0.50
GUIDE_ROOT_AXIAL_CLEARANCE = 2.0
GUIDE_TIP_AXIAL_CLEARANCE = 4.0
GUIDE_LINER_X0 = (
    V3.OUTER_ROOT_TIE_LENGTH + GUIDE_ROOT_AXIAL_CLEARANCE
)
GUIDE_LINER_X1 = (
    V3.OUTER_VISIBLE_LENGTH
    - V3.OUTER_TIP_TIE_LENGTH
    - GUIDE_TIP_AXIAL_CLEARANCE
)
GUIDE_LINER_Z0_IN_GUIDE = V3.OUTER_FLOOR_THICKNESS
GUIDE_LINER_HEIGHT = V3.OUTER_WALL_HEIGHT - GUIDE_LINER_Z0_IN_GUIDE
GUIDE_CHANNEL_HALF_WIDTH = V3.OUTER_CHANNEL_PLACEHOLDER_WIDTH / 2.0
GUIDE_ENDPOINT_DISTANCE_MAX_MM = 15.0


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def require_single(shape, label):
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise RuntimeError(
            f"{label}: invalid/null/non-single shape "
            f"(solids={len(shape.Solids)}, volume={shape.Volume})"
        )


def fuse_all(shapes):
    out = shapes[0]
    for sh in shapes[1:]:
        out = out.fuse(sh)
    return out.removeSplitter()


def _structural_arm_angle(assembly_side: str) -> float:
    if assembly_side == "left":
        return V2.LEFT_ARM_ANGLE_DEG
    if assembly_side == "right":
        return V2.RIGHT_ARM_ANGLE_DEG
    raise ValueError(assembly_side)


def station_frame(station: M.Station, assembly_side: str) -> tuple[float, float]:
    return M.station_arm_frame(
        station,
        _structural_arm_angle(assembly_side),
    )


def _saddle_normalized_y_grid(stations) -> tuple[float, ...]:
    """Common loft grid that preserves every measured profile vertex."""
    us = {
        i / (SADDLE_PROFILE_SAMPLES - 1)
        for i in range(SADDLE_PROFILE_SAMPLES)
    }
    for st in stations:
        width = st.profile.width
        for y, _z in st.profile.points:
            us.add((y - st.profile.ymin) / width)
    return tuple(sorted(us))


def _saddle_section_wire(
    x: float,
    profile: M.Profile,
    lateral_offset: float,
    vertical_offset: float,
    pad_thickness: float,
    normalized_us,
):
    contact_low = (
        SADDLE_NOMINAL_LOWEST_CONTACT_Z
        - pad_thickness
        + vertical_offset
    )
    if contact_low <= SADDLE_BASE_THICKNESS + 1.0:
        raise RuntimeError(
            "measured saddle vertical offset leaves insufficient "
            "insert thickness"
        )

    pocket_half_y = V2.SADDLE_INSERT_WIDTH / 2.0
    shifted_ymin = profile.ymin + lateral_offset
    shifted_ymax = profile.ymax + lateral_offset
    if (
        shifted_ymin < -pocket_half_y + 0.5
        or shifted_ymax > pocket_half_y - 0.5
    ):
        raise RuntimeError(
            "measured saddle profile plus centerline offset does not fit "
            "existing insert pocket: "
            f"shifted profile [{shifted_ymin:.3f},{shifted_ymax:.3f}], "
            f"insert half-width {pocket_half_y:.3f}"
        )

    upper = []
    for u in normalized_us:
        y = profile.ymin + profile.width * u
        z = M.lower_profile_z_at_y(profile, y)
        upper.append(
            (
                y + lateral_offset,
                contact_low + z,
            )
        )

    yz = [(upper[0][0], SADDLE_BASE_THICKNESS)]
    yz.extend(upper)
    yz.append((upper[-1][0], SADDLE_BASE_THICKNESS))

    pts = [v(x, y, z) for y, z in yz]
    return Part.makePolygon(pts + [pts[0]])


def saddle_station_frames(stations, assembly_side: str):
    saddle_center_radius = V2.INNER_R0 + V2.SADDLE_U
    return tuple(
        (
            station_frame(st, assembly_side)[0] - saddle_center_radius,
            station_frame(st, assembly_side)[1],
            st,
        )
        for st in stations
    )


def saddle_insert(
    stations,
    assembly_side: str,
    ms: M.MeasurementSet,
    pad_thickness: float,
):
    """Loft the load-bearing insert surface through root/center/tip measurements."""
    half_length = V2.SADDLE_INSERT_LENGTH / 2.0
    frames = sorted(
        saddle_station_frames(stations, assembly_side),
        key=lambda item: item[0],
    )

    xs = [item[0] for item in frames]
    if not (xs[0] < xs[1] < xs[2]):
        raise RuntimeError(
            f"{assembly_side} saddle stations do not increase along insert X"
        )

    spacings = [
        xs[i + 1] - xs[i]
        for i in range(len(xs) - 1)
    ]
    if max(spacings) > SADDLE_SECTION_SPACING_MAX_MM:
        raise RuntimeError(
            f"{assembly_side} saddle measured-section spacing "
            f"{max(spacings):.3f} mm exceeds "
            f"{SADDLE_SECTION_SPACING_MAX_MM:.1f} mm"
        )

    root_delta = abs(xs[0] + half_length)
    tip_delta = abs(xs[-1] - half_length)
    if root_delta > SADDLE_ENDPOINT_DISTANCE_MAX_MM:
        raise RuntimeError(
            f"{assembly_side} saddle root section is {root_delta:.3f} mm "
            f"from insert root; max {SADDLE_ENDPOINT_DISTANCE_MAX_MM:.1f} mm"
        )
    if tip_delta > SADDLE_ENDPOINT_DISTANCE_MAX_MM:
        raise RuntimeError(
            f"{assembly_side} saddle tip section is {tip_delta:.3f} mm "
            f"from insert tip; max {SADDLE_ENDPOINT_DISTANCE_MAX_MM:.1f} mm"
        )

    # Use measured sections inside the insert and bounded nearest-section
    # extrapolation only for the short unmeasured end strips.
    sections_src = [
        item for item in frames
        if -half_length <= item[0] <= half_length
    ]
    if not sections_src:
        raise RuntimeError(f"{assembly_side} has no saddle section inside insert")

    first = frames[0]
    if sections_src[0][0] > -half_length + 1e-9:
        sections_src.insert(
            0,
            (-half_length, first[1], first[2]),
        )
    elif first[0] < -half_length:
        sections_src.insert(
            0,
            (-half_length, first[1], first[2]),
        )

    last = frames[-1]
    if sections_src[-1][0] < half_length - 1e-9:
        sections_src.append(
            (half_length, last[1], last[2])
        )
    elif last[0] > half_length:
        sections_src.append(
            (half_length, last[1], last[2])
        )

    deduped = []
    for item in sections_src:
        if deduped and abs(item[0] - deduped[-1][0]) < 1e-9:
            deduped[-1] = item
        else:
            deduped.append(item)

    normalized_us = _saddle_normalized_y_grid(stations)
    wires = []
    for x, lateral_offset, st in deduped:
        wires.append(
            _saddle_section_wire(
                x,
                st.profile,
                lateral_offset,
                M.station_vertical_offset_mm(st, ms),
                pad_thickness,
                normalized_us,
            )
        )

    cap = Part.makeLoft(wires, True, False)
    require_single(cap, "SADDLE_INSERT_LOFT")

    base = Part.makeBox(
        V2.SADDLE_INSERT_LENGTH,
        V2.SADDLE_INSERT_WIDTH,
        SADDLE_BASE_THICKNESS,
        v(
            -half_length,
            -V2.SADDLE_INSERT_WIDTH / 2.0,
            0,
        ),
    )

    sh = base.fuse(cap).removeSplitter()
    require_single(sh, "SADDLE_INSERT")
    return sh
def _side_surface(
    profile: M.Profile,
    side: str,
    lateral_offset: float,
) -> float:
    if side == "left":
        return (
            profile.ymin
            + lateral_offset
            - GUIDE_LATERAL_CLEARANCE
        )
    if side == "right":
        return (
            profile.ymax
            + lateral_offset
            + GUIDE_LATERAL_CLEARANCE
        )
    raise ValueError(side)


def _loft_side_rail(
    stations,
    wall_side: str,
    assembly_side: str,
):
    sections = []

    measured = []
    for st in stations:
        along, lateral = station_frame(st, assembly_side)
        measured.append(
            (
                along - V3.OUTER_R0,
                st.profile,
                lateral,
            )
        )
    measured.sort(key=lambda item: item[0])

    first_x = measured[0][0]
    last_x = measured[-1][0]
    first_endpoint_delta = abs(first_x - GUIDE_LINER_X0)
    last_endpoint_delta = abs(last_x - GUIDE_LINER_X1)
    if first_endpoint_delta > GUIDE_ENDPOINT_DISTANCE_MAX_MM:
        raise RuntimeError(
            f"first outer station projected x={first_x:.3f} mm is "
            f"{first_endpoint_delta:.3f} mm from liner start; max allowed "
            f"is {GUIDE_ENDPOINT_DISTANCE_MAX_MM:.1f} mm"
        )
    if last_endpoint_delta > GUIDE_ENDPOINT_DISTANCE_MAX_MM:
        raise RuntimeError(
            f"last outer station projected x={last_x:.3f} mm is "
            f"{last_endpoint_delta:.3f} mm from liner end; max allowed "
            f"is {GUIDE_ENDPOINT_DISTANCE_MAX_MM:.1f} mm"
        )

    # Keep only physically sampled sections that lie inside the printable rail
    # span. If the nearest measured station lies just outside an endpoint, use
    # that exact measured profile/centerline offset at the endpoint. This is a
    # bounded extrapolation, not an arbitrary clamp.
    sections_src = [
        item
        for item in measured
        if GUIDE_LINER_X0 <= item[0] <= GUIDE_LINER_X1
    ]

    first = measured[0]
    if not sections_src or sections_src[0][0] > GUIDE_LINER_X0 + 1e-9:
        sections_src.insert(
            0,
            (GUIDE_LINER_X0, first[1], first[2]),
        )
    elif first[0] < GUIDE_LINER_X0:
        sections_src.insert(
            0,
            (GUIDE_LINER_X0, first[1], first[2]),
        )

    last = measured[-1]
    if sections_src[-1][0] < GUIDE_LINER_X1 - 1e-9:
        sections_src.append(
            (GUIDE_LINER_X1, last[1], last[2])
        )
    elif last[0] > GUIDE_LINER_X1:
        sections_src.append(
            (GUIDE_LINER_X1, last[1], last[2])
        )

    # Remove duplicate endpoint sections while preserving measured order.
    deduped = []
    for item in sections_src:
        if deduped and abs(item[0] - deduped[-1][0]) < 1e-9:
            deduped[-1] = item
        else:
            deduped.append(item)

    for x, profile, lateral_offset in deduped:

        if wall_side == "left":
            y0 = -GUIDE_CHANNEL_HALF_WIDTH
            y1 = _side_surface(
                profile,
                "left",
                lateral_offset,
            )
            if y1 <= y0 + 1.0:
                raise RuntimeError("left guide liner would be thinner than 1 mm")
        else:
            y0 = _side_surface(
                profile,
                "right",
                lateral_offset,
            )
            y1 = GUIDE_CHANNEL_HALF_WIDTH
            if y1 <= y0 + 1.0:
                raise RuntimeError("right guide liner would be thinner than 1 mm")

        z0 = 0.0
        z1 = GUIDE_LINER_HEIGHT
        pts = [
            v(x, y0, z0),
            v(x, y1, z0),
            v(x, y1, z1),
            v(x, y0, z1),
        ]
        sections.append(Part.makePolygon(pts + [pts[0]]))

    sh = Part.makeLoft(sections, True, False)
    require_single(sh, "GUIDE_" + wall_side.upper() + "_RAIL")
    return sh


def outer_guide_liners(stations, assembly_side: str):
    """Return two independent lateral-only guide rails.

    Deliberately do not bridge across the guide floor. A floor bridge could
    become an unintended vertical support under the Samsung arm and violate the
    v3/v8 load-path contract that OUTER_GUIDE is lateral guidance only.
    """
    neg_y = _loft_side_rail(
        stations,
        "left",
        assembly_side,
    )
    pos_y = _loft_side_rail(
        stations,
        "right",
        assembly_side,
    )
    return {"neg_y": neg_y, "pos_y": pos_y}


def export_shape(out_dir, name, shape):
    require_single(shape, name)
    os.makedirs(out_dir, exist_ok=True)

    step = os.path.join(out_dir, name + ".step")
    fcstd = os.path.join(out_dir, name + ".FCStd")
    stl = os.path.join(out_dir, name + ".stl")

    shape.exportStep(step)

    doc = App.newDocument("export_" + name)
    obj = doc.addObject("Part::Feature", name)
    obj.Shape = shape.copy()
    doc.recompute()
    doc.saveAs(fcstd)
    App.closeDocument(doc.Name)

    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=0.06,
        AngularDeflection=0.20,
        Relative=False,
    )
    if mesh.CountFacets <= 0:
        raise RuntimeError(name + ": empty tessellation")
    mesh.write(stl)

    bb = shape.BoundBox
    return {
        "volume_mm3": round(float(shape.Volume), 3),
        "size_mm": [round(bb.XLength,3), round(bb.YLength,3), round(bb.ZLength,3)],
        "bbox_mm": [
            round(bb.XMin,3), round(bb.XMax,3),
            round(bb.YMin,3), round(bb.YMax,3),
            round(bb.ZMin,3), round(bb.ZMax,3),
        ],
        "facets": int(mesh.CountFacets),
    }


def main(
    measurement_path: str,
    out_dir: str = "build_v6_contacts",
    require_physical: bool = False,
):
    ms = M.load_measurements(measurement_path)
    if require_physical and ms.measurement_kind != "physical":
        raise RuntimeError(
            "physical measurement input required for production contact CAD; "
            f"got {ms.measurement_kind!r}"
        )
    pad = ms.pad_thickness if ms.pad_used else 0.0

    vertical_reference = M.inner_vertical_reference_mm(ms)
    inner_sets = {
        "left": ms.inner_left,
        "right": ms.inner_right,
    }
    inner_station_frames = {
        side: saddle_station_frames(stations, side)
        for side, stations in inner_sets.items()
    }

    parts = {
        "samsung_stand_v6_saddle_insert_left": saddle_insert(
            ms.inner_left,
            "left",
            ms,
            pad,
        ),
        "samsung_stand_v6_saddle_insert_right": saddle_insert(
            ms.inner_right,
            "right",
            ms,
            pad,
        ),
    }

    for assembly_side, stations in (
        ("left", ms.outer_left),
        ("right", ms.outer_right),
    ):
        rails = outer_guide_liners(
            stations,
            assembly_side,
        )
        for wall_side, shape in rails.items():
            parts[
                f"samsung_stand_v6_outer_liner_{assembly_side}_{wall_side}"
            ] = shape

    report = {
        "version": "v6-contact-parts",
        "measurement_path": measurement_path,
        "measurement_meta": {
            "measurement_kind": ms.measurement_kind,
            "model": ms.model,
            "stand_part": ms.stand_part,
            "measured_by": ms.measured_by,
            "date": ms.measurement_date,
            "caliper_resolution_mm": ms.caliper_resolution_mm,
        },
        "measurement_symmetry": {
            k: round(vv,4)
            for k,vv in M.symmetry_report(ms).items()
        },
        "measured_vertical_datum": {
            "inner_reference_height_mm": round(vertical_reference, 4),
            "inner_saddle": {
                side: [
                    {
                        "station": name,
                        "measured_lowest_point_height_mm": round(
                            st.lowest_point_height_mm, 4
                        ),
                        "relative_vertical_offset_mm": round(
                            M.station_vertical_offset_mm(st, ms), 4
                        ),
                    }
                    for name, st in zip(
                        ("root", "center", "tip"),
                        stations,
                    )
                ]
                for side, stations in inner_sets.items()
            },
            "outer_guide": {
                side: [
                    {
                        "measured_lowest_point_height_mm": round(
                            st.lowest_point_height_mm, 4
                        ),
                        "relative_vertical_offset_mm": round(
                            M.station_vertical_offset_mm(st, ms), 4
                        ),
                    }
                    for st in stations
                ]
                for side, stations in (
                    ("left", ms.outer_left),
                    ("right", ms.outer_right),
                )
            },
        },
        "measured_centerline_projection": {
            "inner_saddle": {
                side: [
                    {
                        "station": name,
                        "insert_x_mm": round(frame[0], 4),
                        "lateral_mm": round(frame[1], 4),
                    }
                    for name, frame in zip(
                        ("root", "center", "tip"),
                        frames,
                    )
                ]
                for side, frames in inner_station_frames.items()
            },
            "outer_guide": {
                side: [
                    {
                        "along_mm": round(
                            station_frame(st, side)[0], 4
                        ),
                        "lateral_mm": round(
                            station_frame(st, side)[1], 4
                        ),
                    }
                    for st in stations
                ]
                for side, stations in (
                    ("left", ms.outer_left),
                    ("right", ms.outer_right),
                )
            },
        },
        "design_clearances": {
            "outer_lateral_each_side_mm": GUIDE_LATERAL_CLEARANCE,
            "outer_root_axial_free_travel_mm": GUIDE_ROOT_AXIAL_CLEARANCE,
            "outer_tip_axial_free_travel_mm": GUIDE_TIP_AXIAL_CLEARANCE,
            "outer_tie_vertical_capture_overlap_mm": (
                V3.OUTER_TIE_HEIGHT - V3.OUTER_FLOOR_THICKNESS
            ),
            "outer_endpoint_distance_max_mm": (
                GUIDE_ENDPOINT_DISTANCE_MAX_MM
            ),
            "contact_pad_compressed_mm": pad,
            "saddle_nominal_lowest_contact_z_mm": (
                SADDLE_NOMINAL_LOWEST_CONTACT_Z - pad
            ),
            "saddle_endpoint_distance_max_mm": (
                SADDLE_ENDPOINT_DISTANCE_MAX_MM
            ),
            "saddle_section_spacing_max_mm": (
                SADDLE_SECTION_SPACING_MAX_MM
            ),
            "saddle_measured_section_spacing_mm": {
                side: [
                    round(
                        frames[i + 1][0] - frames[i][0],
                        4,
                    )
                    for i in range(len(frames) - 1)
                ]
                for side, frames in inner_station_frames.items()
            },
            "saddle_lowest_contact_z_mm": {
                side: [
                    round(
                        SADDLE_NOMINAL_LOWEST_CONTACT_Z
                        - pad
                        + M.station_vertical_offset_mm(st, ms),
                        4,
                    )
                    for st in stations
                ]
                for side, stations in inner_sets.items()
            },
        },
        "structural_note": (
            "These parts change only Samsung-contact geometry. V8 structural "
            "load path, outer guide shell, end stops and detent remain upstream."
        ),
        "outer_guide_load_path_contract": (
            "Each physical OUTER_GUIDE receives two independent side rails. "
            "There is intentionally no printed V6 bridge or floor surface under "
            "the Samsung arm, so measured contact parts cannot create a normal "
            "vertical load path at the outer guide."
        ),
        "parts": {},
    }

    for name, shape in parts.items():
        report["parts"][name] = export_shape(out_dir, name, shape)

    with open(os.path.join(out_dir, "VALIDATION_v6_contacts_source.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("measurement_path")
    ap.add_argument("--out", default="build_v6_contacts")
    ns = ap.parse_args()
    main(ns.measurement_path, ns.out)
