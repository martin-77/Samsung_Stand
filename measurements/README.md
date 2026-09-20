# Physical measurement input

This folder is the hand-off between the validated structural CAD and the real Samsung stand.

Do **not** fill missing values by estimation.

## Workflow

1. Copy `docs/stand_measurements.template.json` to `measurements/stand_measurements.json`.
2. Enter measured global dimensions.
3. For each inner saddle station, enter a 2D cross-section polygon looking along the stand arm axis.
4. For each outer-guide station (root/mid/tip), enter the measured cross-section polygon.
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
