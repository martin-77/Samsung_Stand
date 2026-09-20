# Physical measurement input

This folder is the hand-off between the validated structural CAD and the real Samsung stand.

Do **not** fill missing values by estimation.

## Workflow

1. Copy `measurements/stand_measurements.template.json` to `measurements/stand_measurements.json`.
2. Enter measured global dimensions.
3. For each inner saddle station, record its `center_xy_mm`, its
   `lowest_point_height_mm` above the common reference plane, and a 2D
   cross-section polygon looking along the stand arm axis.
4. For each outer-guide station (root/mid/tip), record the same three things:
   `center_xy_mm`, `lowest_point_height_mm`, and the measured cross-section
   polygon.
5. Run `python scripts/validate_measurements.py measurements/stand_measurements.json`.
6. Only a complete, symmetric/plausible measurement set unlocks the v6 contact-part generator.

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

The generator uses the mean of the two measured inner-saddle lowest-point
heights as the vertical reference. Left/right saddle inserts preserve their
measured relative height, and every outer-guide station is checked at its own
measured relative Z position.
