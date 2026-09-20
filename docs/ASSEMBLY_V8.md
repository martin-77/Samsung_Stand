# V8 assembly sequence

> Status: geometry-candidate assembly sequence. Do not mount the television until
> all applicable gates in `PHYSICAL_RELEASE_GATES.md` have passed.

## Before the large prints

Print and physically evaluate:

1. roof-key fit coupons;
2. v8 retainer coupons;
3. zero-detent calibration rig;
4. final measured Samsung contact inserts / liners when available.

Use the same printer, PETG, nozzle, layer height and relevant slicer settings
planned for the structural parts.

## Printed structural quantities

Core v8:

- 1 × BASE_CENTER
- 1 × BASE_LEFT
- 1 × BASE_RIGHT
- 1 × ROTOR
- 2 × INNER_ARM
- 2 × OUTER_GUIDE
- 1 × center wear ring
- 2 × side-track wear arcs
- 6 × compact joint lock pins
  - 4 for BASE ↔ CENTER
  - 2 for ROTOR ↔ INNER_ARM
- 2 × long OUTER lock pins
- 1 × pivot lock pin
- 2 × detent pins
- 1 × selected detent cassette
- 2 × measured saddle inserts
- 4 × measured OUTER_GUIDE side rails (2 per guide)

The legacy vertical base retainers, legacy pivot C-clip and legacy v2 arm lock
pin are not part of the v8 assembly.

## 1. Assemble the fixed base

1. Inspect all roof keys and receivers for elephant-foot, stringing or damaged
   snap surfaces.
2. Slide BASE_LEFT and BASE_RIGHT into BASE_CENTER through the long form-locking
   roof-key joints. Do not hammer the parts together.
3. Verify all three base modules sit on one common underside plane.
4. Install the four horizontal compact lock pins.

The front and rear pins are deliberately mirrored:

- rear joint at y = -90 mm: pin shaft runs toward +Y;
- front joint at y = +90 mm: pin shaft runs toward -Y.

This keeps the expanded snap barbs clear of the asymmetric center-base
reinforcement ribs.

The pins retain the joint against withdrawal. The roof-key overlap remains the
primary structural load path.

## 2. Install replaceable wear surfaces

1. Drop the center wear ring into the shallow annular BASE_CENTER recess.
2. Install one side-track wear arc in BASE_LEFT and one in BASE_RIGHT.
3. Verify all wear pieces sit fully down in their recesses without rocking.

Installed top planes must remain:

- center wear ring: z = 10 mm;
- side wear arcs: z = 18 mm.

Do not glue the wear pieces during fit validation. They are intended to remain
replaceable.

## 3. Install and calibrate the zero detent

1. Install the physically selected detent cassette on the fixed base.
2. Retain it with the two detent pins.
3. Verify the spring nose moves freely and is not pre-whitened.

The detent is positional only. It is not an end stop.

## 4. Place the rotor

1. Lower ROTOR over the extended central pivot post.
2. Seat it on the center wear ring.
3. Verify it rotates freely through the available range before installing the
   remaining rotating carrier parts.
4. Confirm the open central counterbore is accessible from above.

## 5. Install the pivot cross-pin

This step must occur before the INNER_ARM parts obstruct access to the central
assembly area.

1. Place the pivot lock pin horizontally into the top-open Ø61 mm rotor
   counterbore.
2. Align it with the support-friendly transverse tunnel in the fixed Ø25 mm
   pivot post.
3. Slide the pin through the post until the split-end barbs have passed the far
   side and expanded.
4. Verify the pin head and barb ends remain fully inside the circular rotor
   counterbore.
5. Rotate the rotor gently through the complete +/-15 degree range.

The rotor intentionally has approximately 0.7 mm axial lift clearance before
its counterbore shoulder reaches the fixed cross-pin. The pin is an accidental
lift retainer; normal TV weight is carried by the annular wear ring and the two
side-track supports, not by the pivot pin.

## 6. Install INNER_ARM left/right

For each side:

1. slide the inward roof key into the rotor receiver;
2. seat the flat root landing on the rotor support plane;
3. verify the outer saddle region simultaneously sits on the appropriate side
   wear arc;
4. insert one compact joint lock pin transversely through the rotor receiver and
   INNER_ARM tongue.

The lock pin retains withdrawal. It is not the primary bending support.

## 7. Install OUTER_GUIDE left/right

For each side:

1. slide the OUTER_GUIDE male roof key into the INNER_ARM receiver;
2. verify the U-guide remains clear of the fixed base;
3. insert the long v8 outer lock pin through the fully opened transverse tunnel.

V8 intentionally re-opens this tunnel through the complete 58 mm saddle region.
The earlier 50 mm tunnel was geometrically enclosed by the saddle and was not a
satisfactory real insertion path.

## 8. Install measured saddle contact parts

Only use contact parts generated from validated physical measurements.

1. place the left/right measured saddle inserts in the INNER_ARM pockets;
2. verify both inserts sit fully in their pockets without rocking or forcing an
   INNER_ARM out of its validated position.

Do **not** install the OUTER_GUIDE side rails yet. They are deliberately separate
lateral-only rails and are installed around the real stand arm in the next step.
Reconstructed stand dimensions are not a substitute for these measurements.

## 9. Dry-fit the original Samsung stand and install lateral guide rails

Before adding the television:

1. place the original Samsung stand in the two measured saddle inserts;
2. for each OUTER_GUIDE, slide the measured negative-Y and positive-Y side rail
   down from above between the Samsung arm and the corresponding guide wall;
3. verify all four side rails sit on the guide floor and remain on their own
   side of the arm centerline;
4. verify the arm is not vertically supported by any side rail. The generated
   V6 validation report must show at least 5 mm measured vertical clearance from
   every root/mid/tip cross-section to the structural OUTER_GUIDE floor;
5. rotate slowly from center to -15 degrees and +15 degrees;
6. verify:
   - vertical load remains on the inner supports;
   - outer guides and measured side rails only guide laterally;
   - positive mechanical end stops engage at +/-15 degrees;
   - the fixed base does not move on the Sounddeck;
   - no retainer walks out;
   - no PETG whitening appears.

## 10. Physical release testing

Proceed with a non-fragile substitute load, not the TV, and complete
`PHYSICAL_RELEASE_GATES.md`.

Only after measurement validation, fit coupons, static proof loading, creep
dwell, swivel/end-stop cycling and the Sounddeck anti-slip/surface gate have
passed should the real TV be mounted.
