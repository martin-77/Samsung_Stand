# Samsung_Stand

Parametric, test-driven CAD project for a modular PETG adapter that reuses the original Samsung UE55J6250 stand on a Magnat Sounddeck 150 and adds limited swivel.

## Design targets

- Reuse the original Samsung stand assembly.
- Magnat Sounddeck 150 footprint: **700 × 340 mm**.
- Working Samsung stand footprint: **840 mm width**; depth currently treated as a reconstructed/working value and must remain explicitly marked as such until physically verified.
- Printer target: **Prusa CORE One L, 300 × 300 × 330 mm**.
- Material target: PETG.
- Modular printed construction with form-locking joints; snap tabs are retention only, never primary structural load paths.
- Large fixed base on the Sounddeck.
- Central swivel with limited range, initially **±15°**.
- Inner saddle/support points carry vertical load inside the Sounddeck footprint.
- Outer printed rails guide the original Samsung stand but should not become long vertical-load cantilevers.
- No CAD change is considered valid until geometry/layout checks pass.

## Engineering approach

This repository follows the test-driven CAD approach used in `martin-77/eurobox`:

1. Keep dimensional truth in code.
2. Validate global assembly geometry independently from local CAD construction.
3. Hard-gate print-bed limits, support-point position, swivel sweep, clearances and exported meshes.
4. Generate CAD/STL only from the validated parameter set.
5. Treat inferred dimensions separately from verified dimensions.

## Current baseline

Initial working geometry:

- Sounddeck: 700 × 340 mm
- Fixed base target: 680 × 295 mm
- Samsung stand width: 840 mm
- Samsung stand reconstructed depth: ~288 mm
- Pivot offset: 64 mm rearward from Sounddeck center
- Inner load/saddle stations: x ≈ ±250 mm along the reconstructed arm geometry
- Saddle orbit radius: ~279 mm
- Swivel target: −15° / 0° / +15°

See `docs/DESIGN_BASELINE.md` and the geometry validation scripts before changing these values.

## Current status

The repository has progressed to **v5** as the validated structural geometry candidate, plus a validated **v6 contact-generation pipeline**:

- v1: modular three-piece fixed base and central annular swivel bearing;
- v2: dual-load-path INNER_ARM with rotor root landing and side glide tracks;
- v3: modular OUTER_GUIDE rails, intentionally non-load-bearing vertically;
- v4: calibrated positive mechanical +/-15 degree end stops plus complete carrier sweep clearance;
- v5: replaceable zero-position PETG detent cassette with 1.8 / 2.2 / 2.6 mm calibration variants;
- v6 contact pipeline: strict physical-measurement model plus side-specific saddle inserts and outer-guide liners generated only from validated real measurements.

For v5 the parameter gates, FreeCAD build, watertight-mesh checks and installed
OCC collision/contact checks are green. The +/-15 degree end stops remain
structural; the center detent is positional only.

The v6 measurement-to-CAD path is also green against a synthetic CI fixture:
measurement validation, FreeCAD generation, watertight-mesh gates and installed
contact-part checks against the real v5 structural STEP geometry all pass.
Production v6 contact parts remain intentionally unpublished until
`measurements/stand_measurements.json` contains complete physical measurements.

This is **not yet a physical structural release for mounting the TV**.  The
Samsung arm contact geometry is still based partly on reconstruction and must be
measured before final saddle/guide inserts are generated.  A real fit-coupon
sequence and non-fragile proof-load test are required before TV use.

See:

- `cad/v5/` for the newest validated CAD candidate;
- `cad/fit_coupons/` for published structural joint clearance coupons;
- `measurements/` and `docs/REQUIRED_MEASUREMENTS.md` for the remaining physical dimensions and profile capture;
- `docs/PHYSICAL_RELEASE_GATES.md` for the required fit and proof tests.
