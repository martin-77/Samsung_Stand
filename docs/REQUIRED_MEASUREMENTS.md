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

## B. Inner saddle station

Target measurement station is the current support orbit at approximately
279 mm radius from the swivel axis.

For both left and right stand arms measure:

- arm width across Y-like / lateral direction;
- arm total thickness / height;
- underside shape;
- top shape;
- corner radii or chamfers;
- local arm angle / twist if the cross-section is not level;
- any rubber foot, boss, screw, rib or protrusion in the contact zone.

Also record at least one photograph looking exactly along the arm axis so the
cross-section can be reconstructed.

The final part affected by these values is the replaceable saddle insert.  The
INNER_ARM itself should not need to be reworked unless the real contact station
is materially different from the reconstructed orbit.

## C. Outer guide region

The OUTER_GUIDE starts at about 310 mm radius and extends outward about 170 mm.
The current inside channel is deliberately oversized.

Measure arm width and height at three stations per side:

1. near the outer-guide root;
2. near the middle;
3. near the stand tip.

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

A measurement set is complete when it can fill a record equivalent to:

```json
{
  "global": {
    "stand_width_mm": null,
    "stand_depth_mm": null,
    "pivot_to_rear_mm": null,
    "left_tip_xy_mm": [null, null],
    "right_tip_xy_mm": [null, null]
  },
  "inner_saddle": {
    "left": {
      "width_mm": null,
      "height_mm": null,
      "corner_radius_mm": null,
      "notes": ""
    },
    "right": {
      "width_mm": null,
      "height_mm": null,
      "corner_radius_mm": null,
      "notes": ""
    }
  },
  "outer_guide": {
    "left": {
      "root_width_mm": null,
      "mid_width_mm": null,
      "tip_width_mm": null,
      "root_height_mm": null,
      "mid_height_mm": null,
      "tip_height_mm": null,
      "notes": ""
    },
    "right": {
      "root_width_mm": null,
      "mid_width_mm": null,
      "tip_width_mm": null,
      "root_height_mm": null,
      "mid_height_mm": null,
      "tip_height_mm": null,
      "notes": ""
    }
  },
  "contact_pad": {
    "used": false,
    "compressed_thickness_mm": 0.0,
    "notes": "PETG-only project constraint"
  }
}
```

Do not enter guessed values to make the record complete.  Missing physical
measurements should remain null until measured.
