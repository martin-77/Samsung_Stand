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

## Status

Repository bootstrap / geometry-validation phase. No printable release yet.
