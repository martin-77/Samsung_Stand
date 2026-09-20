# Physical release gates

The generated CAD is test-driven for geometry, assembly, print envelope and
collision behavior. That is not the same as a verified structural release for
a television.

A version may be marked **printable candidate**, but not **physically released**,
until all gates below are completed on the real hardware and recorded.

## 1. Real Samsung stand geometry

Still required:

- stand-arm cross-section at the inner saddle station;
- stand-arm cross-section / side profile inside the outer guide;
- actual stand depth and rear contour;
- verification that the reconstructed pivot/arm centerline matches the physical
  stand closely enough over the complete +/-15 degree sweep.

The structural CAD deliberately isolates these unknowns:

- the inner support uses a replaceable saddle insert;
- the outer U-guide remains an oversized structural guide until side-contact
  shims / inserts are generated from physical measurements.

Do not convert reconstructed dimensions into manufacturing truth by assumption.

## 2. Fit coupons before full print

Print small fit coupons before the large structural modules:

1. base roof-key + receiver clearance coupon;
2. rotor/INNER_ARM roof-key + cross-pin coupon;
3. INNER_ARM/OUTER_GUIDE roof-key + cross-pin coupon;
4. final Samsung saddle insert;
5. final outer-guide side-contact shim;
6. selected zero-detent spring cassette.

Record printer, material, nozzle, layer height and actual measured clearances.

## 3. Static proof loading

The geometry model uses a 500 N vertical engineering design load. This is an
internal development target, not a certified load rating and not a substitute
for a physical proof test.

Before mounting the TV, assemble the complete adapter on the real Sounddeck and
apply a non-fragile substitute load at the real Samsung support locations.

Minimum test sequence:

1. preload / settle the assembly;
2. load center position;
3. load at -15 degrees;
4. load at +15 degrees;
5. hold each test position long enough to reveal gross creep / seating;
6. unload and inspect;
7. repeat the swivel cycle and check that the zero detent and positive end stops
   still behave normally.

Record:

- applied load;
- duration;
- permanent deformation after unload;
- cracks / whitening / layer separation;
- loosened retaining pins;
- change in swivel friction;
- change in detent feel;
- any base movement on the Sounddeck.

The eventual proof-load magnitude and duration must be chosen deliberately
before calling the design structurally released. The current CAD repository does
not claim a certified safety factor.

## 4. End-stop verification

The v4+ CAD has positive mechanical +/-15 degree end stops. OCC validation proves
geometric contact behavior, but the printed stop must also be checked for:

- no brittle impact damage;
- no layer splitting at the rotor stop spoke;
- no deformation of the fixed stop towers;
- continued operation after repeated gentle end-stop contacts.

Do not use the detent cassette as an end stop.

## 5. Detent calibration

The v5 detent is intentionally replaceable. The 1.8 / 2.2 / 2.6 mm spring
variants are calibration choices, not validated force specifications.

Select the lowest spring force that reliably centers the stand without causing:

- excessive breakaway torque;
- visible spring whitening;
- permanent set;
- noisy stick-slip;
- accelerated wear on the rotor cam.

## 6. Release criterion

A physically released version needs all of the following:

- CAD design gates green;
- final STL mesh gates green;
- installed OCC assembly gates green;
- real stand geometry measured and final contact inserts generated;
- fit coupons passed on the target printer/material;
- full assembly printed;
- physical static proof test passed;
- swivel/end-stop cycling passed;
- chosen detent cassette passed physical calibration;
- photographs and measured results committed under a release-validation folder.

Until then, the newest CAD version is a validated **geometry candidate**, not a
verified structural product.
