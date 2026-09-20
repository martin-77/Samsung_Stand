# Required physical Samsung stand measurements

The structural geometry is now isolated from the still-unverified Samsung contact
geometry.  The remaining measurements should therefore change only small contact
parts, not the complete load-bearing adapter.

Use a digital caliper where practical.  Record actual values rather than rounded
nominal guesses.  Photos with a ruler/caliper in the frame are useful for
cross-checking interpretation.

## A. Global stand geometry

Record with the original stand assembled exactly as it will be used:

- total left-to-right stand width;
- total front-to-back stand depth;
- pivot / neck center to rear-most contour;
- pivot / neck center to both front stand tips;
- X/Y location of both stand tips relative to the pivot;
- whether left and right geometry is measurably symmetric.

These measurements verify the reconstructed 840 mm / ~288–290 mm planform and
the current (0, -64 mm) swivel-axis placement.

## B. Inner saddle region

The replaceable saddle insert spans about 49 mm along each arm. One center
cross-section is not enough to prove the complete contact surface.

For **both left and right arms**, measure three cross-sections:

1. **root** — near the inboard end of the insert;
2. **center** — near the current support orbit at approximately 279 mm radius;
3. **tip** — near the outboard end of the insert.

At every root/center/tip section record:

- `station_radius_mm` from the swivel pivot;
- `center_xy_mm` relative to the swivel pivot;
- `lowest_point_height_mm` from one unchanged common flat reference plane;
- the complete `profile_points_mm` cross-section polygon;
- relevant radii/chamfers, ribs, bosses or protrusions.

The root and tip sections should be measured close enough to the insert ends
that only a short bounded extrapolation remains. The generator rejects a nearest
measured saddle section more than 8 mm from the corresponding insert end and
rejects adjacent measured saddle sections more than 25 mm apart.

Use photographs looking along the arm axis at all three sections where possible.
The generated saddle insert is a loft through the measured sections; the
INNER_ARM structural part remains unchanged.

## C. Outer guide region

The OUTER_GUIDE starts at about 310 mm radius and extends outward about 170 mm.
The current inside channel is deliberately oversized.

Measure the arm at three stations per side:

1. near the outer-guide root;
2. near the middle;
3. near the stand tip.

At every station record the cross-section polygon, its `center_xy_mm`
relative to the swivel pivot, and `lowest_point_height_mm` from the same
common flat reference plane used for the inner saddle measurements. This allows
the contact parts to follow both plan-view centerline deviations and real
vertical rise/fall of the arm.

Also record:

- taper in plan view;
- taper in height;
- side-wall angle;
- corner radii/chamfers;
- any local protrusions;
- whether a constant shim profile is possible or a tapered shim is required.

Preferred design outcome: keep the structural OUTER_GUIDE and generate small
replaceable side-contact shims/inserts instead of reprinting the 215 mm rail.

## D. Contact material / protection

Current project constraint: **all contact parts remain PETG-only**.

The original Samsung stand therefore touches printed PETG directly. External
protective pads, foam, TPU, rubber or adhesive layers are not part of the current
design and are rejected by the measurement validator.

Keep:

- `contact_pad.used = false`
- `contact_pad.compressed_thickness_mm = 0.0`

If this constraint is ever changed deliberately, the measurement schema,
generator and physical-release gates must be revised together rather than
silently adding another material.

## E. Values to return to CAD

Use **only** the canonical template:

`measurements/stand_measurements.template.json`

Copy it to:

`measurements/stand_measurements.json`

The current generator does **not** accept width/height-only approximations for
the Samsung contact geometry. Each relevant cross-section must be represented by
`profile_points_mm` as an ordered polygon of `[y,z]` points.

Minimal structural form:

```json
{
  "meta": {
    "measurement_kind": "physical",
    "model": "Samsung UE55J6250",
    "stand_part": "BN96-38964A",
    "measured_by": null,
    "date": null,
    "caliper_resolution_mm": null
  },
  "global": {
    "stand_width_mm": null,
    "stand_depth_mm": null,
    "pivot_to_rear_mm": null,
    "left_tip_xy_mm": [null, null],
    "right_tip_xy_mm": [null, null]
  },
  "inner_saddle": {
    "left": {
      "root": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "center": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "tip": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      }
    },
    "right": {
      "root": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "center": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "tip": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      }
    }
  },
  "outer_guide": {
    "left": {
      "root": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "mid": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "tip": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      }
    },
    "right": {
      "root": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "mid": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      },
      "tip": {
        "station_radius_mm": null,
        "center_xy_mm": [null, null],
        "lowest_point_height_mm": null,
        "profile_points_mm": null
      }
    }
  },
  "contact_pad": {
    "used": false,
    "compressed_thickness_mm": 0.0
  }
}
```

Coordinate convention for every profile:

- `y = 0` is the local arm centerline;
- `z = 0` is the lowest physical point of that measured cross-section;
- points run around the complete outer contour;
- real kinks/chamfers/radii that affect fit must be represented rather than
  smoothed away.

The validator rejects incomplete, self-intersecting, off-center or implausible
profiles. Do not enter guessed values simply to make the record complete.


## F. Provenance

Production contact CAD is generated only from a file whose
`meta.measurement_kind` is `physical`. The CI fixture is explicitly marked
`synthetic` and is intentionally rejected when the validator is called with
`--require-physical`.

The model, accepted stand part, measurer, date and caliper resolution are also
validated. This prevents a geometrically plausible test fixture or measurement
set for a different stand from being silently published as manufacturing CAD.
