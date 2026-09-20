# Physical measurement input

This folder is the hand-off between the validated structural CAD and the real Samsung stand.

Do **not** fill missing values by estimation.

## Workflow

1. Copy `measurements/stand_measurements.template.json` to `measurements/stand_measurements.json`.
2. Keep `meta.measurement_kind = "physical"` and fill in the real measurer,
   ISO date and caliper resolution. Synthetic fixtures are rejected by the
   production workflow.
3. Enter measured global dimensions.
4. For each side of the inner saddle, measure **three sections** across the
   insert span: `root`, `center`, and `tip`. At every section record
   `center_xy_mm`, `lowest_point_height_mm`, and a 2D cross-section polygon
   looking along the stand arm axis.
5. For each outer-guide station (root/mid/tip), record the same three things:
   `center_xy_mm`, `lowest_point_height_mm`, and the measured cross-section
   polygon.
6. Run `python scripts/validate_measurements.py --require-physical measurements/stand_measurements.json`.
7. Only a complete, plausible **physical** measurement set unlocks the production v6 contact-part generator.

## Cross-section coordinates

Each `profile_points_mm` array contains points `[y,z]` in millimetres:

- y = lateral across the stand arm, with **y = 0 on the local arm centerline**;
- z = upward from the lowest physical point of that local cross-section;
- points ordered around the outside contour;
- no repeated final point is required;
- use enough points to represent radii/chamfers/ribs that matter for contact.

The profile is the **physical Samsung arm**, not desired clearance.

The CAD generator applies its own explicit geometric clearance. The current
project is PETG-only: `contact_pad.used` must remain `false` and compressed
pad thickness must remain `0.0`.


## Station center coordinates

Each measured station also contains `center_xy_mm: [x,y]`.

Use the swivel pivot as the origin:

- +X = right side of the television/stand;
- -X = left side;
- +Y = toward the front stand tips;
- values describe the center of the measured arm cross-section.

`station_radius_mm` is retained as an independent cross-check. The validator
rejects a radius that disagrees with `center_xy_mm` by more than 1.5 mm.

The generator projects these coordinates into the fixed v8 arm frames. Small
real lateral deviations therefore modify only the replaceable saddle inserts
and guide rails. They do **not** silently move the structural v8 arms.


## Common vertical datum

Every station requires `lowest_point_height_mm`.

Use one **unchanged flat reference plane for the complete stand**. The value is
the vertical distance from that plane to the lowest physical point of the
cross-section at the measurement station.

This is different from the local polygon coordinate:

- `profile_points_mm[*][1]` uses local z with the lowest point of that
  individual cross-section normalized to z = 0;
- `lowest_point_height_mm` says where that local z = 0 actually lies relative
  to the common reference plane.

Do not re-zero the height gauge separately at each station. Doing so would erase
the longitudinal rise/fall of the real Samsung arm and could hide an unintended
OUTER_GUIDE floor contact.

The generator uses the mean of the two **center** saddle-section
`lowest_point_height_mm` values as the vertical reference. The complete
root/center/tip saddle loft preserves measured relative height, lateral offset
and cross-section shape along the insert. Every outer-guide station is likewise
checked at its own measured relative Z position.


## Provenance gate

The metadata is part of the manufacturing input, not documentation only.

Required fields include:

- `measurement_kind`: `physical` for production or `synthetic` for CI only;
- `model`: exactly `Samsung UE55J6250`;
- `stand_part`: currently accepted `BN96-38964A`;
- `measured_by`: non-empty;
- `date`: ISO `YYYY-MM-DD`;
- `caliper_resolution_mm`: positive and no worse than 0.2 mm.

A synthetic file can still exercise the CAD pipeline, but it cannot pass the
production provenance gate or the production builder.

## Saddle sampling density

For the load-bearing saddle, root/center/tip are not merely labels. After
projection into the structural arm frame, adjacent measured sections may be no
more than **25 mm apart**, and the nearest root/tip section may be no more than
**8 mm** from the corresponding insert end.

These gates limit how much of the load-bearing insert is based on interpolation.
They do not replace the physical dry-fit check between stations.
