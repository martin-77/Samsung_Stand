# Design baseline

## Scope

Adapter system for a Samsung UE55J6250 using the original wide Samsung stand on a Magnat Sounddeck 150.

The design must be printable on a Prusa CORE One L and assembled from multiple PETG parts using form-locking joints plus replaceable snap retainers.

## Confidence levels

### Verified / high confidence

- Samsung UE55J6250 weight with stand: 16.7 kg.
- Samsung UE55J6250 complete envelope with stand: 1230.6 × 770.6 × 310.5 mm.
- Samsung UE55J6250 body depth without stand: 64.0 mm.
- Samsung's specified stand swivel: 0°.
- Magnat Sounddeck 150 footprint: 700 × 340 mm.
- Samsung stand family/base width used as working source dimension: 840 mm.
- Prusa CORE One L build volume: 300 × 300 × 330 mm.

### Reconstructed / must be physically verified before final release

- Pure stand-only depth: approximately 288–290 mm as a reconstruction only.
  Samsung's verified 310.5 mm value is the **complete TV+stand depth**, so it
  cannot be substituted for this stand-only measurement.
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


## Magnat Sounddeck interface constraints

Manufacturer documentation explicitly describes the Sounddeck 150 as suitable
for placement directly below a television and states that the enclosure is
designed to carry a small-to-medium TV. The front speaker systems and display are
on the front face; the subwoofer is down-firing. The rear amplifier cooling
plate / cooling openings must remain unobstructed.

Project consequences:

- the adapter remains entirely on the 700 × 340 mm top surface;
- the 680 × 295 mm fixed base is centered and therefore leaves 22.5 mm top-edge
  margin at both front and rear;
- future base-depth changes must preserve at least 20 mm front/rear top-edge
  margin;
- no printed part may wrap around or cover the rear amplifier/cooling panel;
- the Sounddeck must itself remain on the solid, level support required for the
  down-firing subwoofer.

Primary source:
- Magnat Sounddeck 150 manual, installation/safety section and illustrations.


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

## Samsung envelope versus reconstructed stand planform

Samsung's model-specific Quick Guide BN68-07177M-00 specifies the complete
UE55J6250 assembly with stand at **1230.6 × 770.6 × 310.5 mm** and lists
**Stand Swivel (Left / Right): 0°**. The TV body itself is only 64.0 mm deep.

Consequences:

- 310.5 mm is a hard external-envelope reference for the original assembled TV;
- it is **not** a direct measurement of the stand-only footprint;
- the current ~288 mm stand-only reconstruction therefore remains an assumption
  until the real stand is measured;
- our ±15° mechanism rotates the complete TV + original stand together beneath
  the OEM stand, so it does not twist Samsung's non-swivelling TV-to-stand
  connection.

Primary source: Samsung Quick Start Guide BN68-07177M-00
(`UJ6250-ZG_BN68-07177M-00L04-0331.pdf`), UE55J6250 / UE55J6270
specification table.

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


## Verified service load

Samsung's Quick Start Guide BN68-07177M-00 lists the UE55J6250 at 16.7 kg with
its original stand. Using standard gravity, the static service load is therefore
approximately 163.8 N.

The project's 500 N vertical design load is an internal adapter-development
load, approximately 3.05 times the real static TV weight. It is **not** a
certified safety factor and must not be interpreted as permission to place a
500 N proof load on the Magnat Sounddeck itself.

Physical release therefore separates:

- adapter structural proof: 500 N on a rigid flat surrogate support;
- real Sounddeck interface test: approximately the real 163.8 N TV service
  load, with a validator ceiling of 110% for the interface test.

Source: Samsung Quick Start Guide BN68-07177M-00, model table for
UE55J6250 / UE55J6270.
