# Design baseline

## Scope

Adapter system for a Samsung UE55J6250 using the original wide Samsung stand on a Magnat Sounddeck 150.

The design must be printable on a Prusa CORE One L and assembled from multiple PETG parts using form-locking joints plus replaceable snap retainers.

## Confidence levels

### Verified / high confidence

- Samsung UE55J6250 weight with stand: about 16.7 kg.
- Magnat Sounddeck 150 footprint: 700 × 340 mm.
- Samsung stand family/base width used as working source dimension: 840 mm.
- Prusa CORE One L build volume: 300 × 300 × 330 mm.

### Reconstructed / must be physically verified before final release

- Pure stand depth: approximately 288–290 mm.
- Stand-arm planform and arm centerline.
- Pivot-to-rear stand contour: approximately 80 mm.
- Pivot-to-front stand tip: approximately 208 mm in Y with ±420 mm X tip coordinates.
- Stand-arm cross-section along the guide rails.

These inferred values may be used for layout and collision exploration, but **must not silently become manufacturing truth**.

## Coordinate system

- X: left/right, Sounddeck center at x = 0.
- Y: front/back, positive Y = front.
- Z: upward.
- Sounddeck geometric center = (0, 0).
- Initial swivel axis = (0, -64 mm), i.e. 64 mm rearward from Sounddeck center.

## Fixed base

Target fixed base footprint:

- width: 680 mm
- depth: 295 mm
- centered in X
- kept fully inside the 700 × 340 mm Sounddeck footprint

The base will be split into printable modules. The central swivel-bearing region must remain on one unbroken center module.

## Load path

Nominal static weight force:

- 16.7 kg × 9.81 m/s² ≈ 164 N

Initial engineering design load for geometry and structural development:

- 500 N vertical

This is an internal design target, not a certified safety factor.

Primary vertical load path:

1. original Samsung stand
2. two broad inner PETG saddles
3. upper rotating carrier
4. broad glide/support pads on circular paths
5. fixed base
6. Magnat Sounddeck

The outer rails primarily provide lateral guidance and anti-twist support.

They must **not** be treated as long primary vertical-load cantilevers.

## Reconstructed stand planform

Current working tip coordinates relative to swivel axis:

- left tip: (-420, +208) mm
- right tip: (+420, +208) mm
- approximate rear contour: y = -80 mm

This corresponds to an arm centerline slope of 208 / 420.

## Inner saddles

Initial support station:

- x = ±250 mm
- y = 250 × (208 / 420) ≈ 123.8 mm relative to swivel axis
- support orbit radius ≈ 279 mm

The saddle/support pad footprint must remain inside the Sounddeck at all allowed swivel angles.

## Swivel

Initial allowed range:

- -15°
- 0°
- +15°

The outer Samsung stand tips are allowed to overhang the Sounddeck.

The **load supports are not**.

Future CAD must include:

- positive end stops
- center detent
- optional ±15° detents
- cable-safe limited rotation
- large-area PETG-on-PETG bearing surfaces
- central axis used primarily for guidance, not as the only vertical load path

## Modular print architecture

Target module classes:

- BASE_CENTER
- BASE_LEFT
- BASE_RIGHT
- ROTOR
- INNER_LEFT
- INNER_RIGHT
- OUTER_GUIDE_LEFT
- OUTER_GUIDE_RIGHT
- replaceable RETAINER clips

Rules:

- no structural module may exceed the 300 × 300 mm XY build limit
- preferred maximum XY envelope for large parts: 295 × 295 mm
- snap tabs retain joints; they do not carry the primary bending/shear load
- structural joints use long overlap / dovetail / trapezoidal form locking
- retainers should be replaceable without reprinting a major module

## Required hard gates before printable release

- global dimensions are internally consistent
- fixed base remains within Sounddeck footprint
- support points remain within Sounddeck footprint across full swivel range
- support pads retain edge margin across full swivel range
- all printable modules fit the printer build volume
- exported meshes are watertight and have positive volume
- assembled left/right geometry is mirrored correctly
- no accidental load path through only snap tabs
- guide rails have explicit clearance and do not unintentionally preload the original stand
