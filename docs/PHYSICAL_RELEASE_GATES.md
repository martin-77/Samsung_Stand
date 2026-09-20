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
- the outer U-guide remains an oversized structural guide until four
  lateral-only side rails (negative-Y and positive-Y per guide) are generated
  from physical measurements. No generated outer contact part may bridge below
  the Samsung arm or become a normal vertical support.

Do not convert reconstructed dimensions into manufacturing truth by assumption.

## 2. Fit coupons before full print

Print small fit coupons before the large structural modules:

1. base roof-key + receiver clearance coupon;
2. rotor/INNER_ARM roof-key + cross-pin coupon;
3. INNER_ARM/OUTER_GUIDE roof-key + cross-pin coupon;
4. final Samsung saddle insert;
5. final measured OUTER_GUIDE side-rail fit (all four rails);
6. selected zero-detent spring cassette;
7. v8 base-joint transverse retainer coupon;
8. v8 long INNER_ARM/OUTER_GUIDE retainer coupon;
9. v8 pivot-post / cross-pin retainer coupon.

Record printer, material, nozzle, layer height and actual measured clearances.

## 3. Static proof loading

The geometry model uses a 500 N vertical engineering design load. The verified
Samsung UE55J6250 mass with original stand is 16.7 kg, corresponding to about
163.8 N static service load. Thus 500 N is roughly 3.05 times the real static
TV load. This remains an internal development target, not a certified load
rating or safety factor.

Before mounting the TV, assemble the complete adapter on a **rigid, flat
surrogate support**, not on the Magnat Sounddeck, and apply a non-fragile
substitute load at the real Samsung support locations.

The repository provides `cad/proof_load_fixture/proof_load_saddle_pad`.
Print two pads and place one in each INNER_ARM saddle pocket. A rigid flat
spreader board may then bridge only those two pads so the substitute load enters
at the validated saddle stations without using the television or the
OUTER_GUIDE parts as load supports.

Do **not** use the real Sounddeck as the 500 N proof fixture. The 500 N value is
an adapter development load. Magnat's manual states that the Sounddeck is
intended to carry a small-to-medium television but does not provide a numeric
maximum load in the manual. The Sounddeck interface is tested separately at
approximately the verified real TV service load.

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
- any base movement on the Sounddeck;
- visible marking / indentation of the Sounddeck top surface;
- whether the replaceable wear inserts remain seated.

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

## 6. Sounddeck interface / anti-slip gate

The adapter is intentionally all-PETG at this stage. That means sufficient
friction against the real Magnat top surface must be **measured**, not assumed.

Before mounting the TV:

1. place the complete unloaded adapter on the real Sounddeck;
2. mark its centered position;
3. apply the expected hand torque needed to move through the detent and the
   complete +/-15 degree swivel range;
4. add a non-fragile substitute load of at least the verified TV service load
   (16.7 kg with stand, approximately 163.8 N) but no more than 110% of that
   load for this interface test;
5. repeat the swivel / detent operation;
6. verify that the rotating assembly moves while the fixed 680 x 295 mm base
   does not translate or yaw on the Sounddeck;
7. inspect the Sounddeck finish for scratches, pressure marks or local
   indentation.

The 500 N structural proof belongs on the rigid surrogate support, not here.

If the fixed base moves, the all-PETG interface is not released. Do not simply
increase detent force. The correction must reduce required swivel torque or add
a separately justified locating / friction concept without concentrating the TV
load onto small points.

## 7. Creep / dwell gate

Short OCC/static checks do not validate long-term PETG creep.

Before final release, the complete printed load path must be held under a
representative sustained substitute load long enough to detect meaningful
settling at:

- the center wear ring;
- both side wear arcs;
- INNER_ARM root landings;
- saddle inserts;
- form-locking base joints;
- pivot post / cross-pin retention.

Record initial and final heights / gaps at defined reference points and repeat
the swivel test after unloading. Any progressive permanent set, growing joint
play or whitening is a failed gate.

## 8. Release criterion

A physically released version needs all of the following:

- CAD design gates green;
- final STL mesh gates green;
- installed OCC assembly gates green;
- real stand geometry measured and final contact inserts generated;
- roof-key, retainer and detent fit coupons passed on the target printer/material;
- full assembly printed;
- Sounddeck anti-slip / surface-protection gate passed;
- physical static proof test passed;
- sustained creep / dwell gate passed;
- swivel/end-stop cycling passed;
- chosen detent cassette passed physical calibration;
- photographs and measured results committed under a release-validation folder.

Record the physical result in a copy of
`release_validation/physical_release.template.json` named
`release_validation/physical_release.json`. The declared dwell durations and
cycle counts must be chosen before the test and explained in the record. CI then
runs `scripts/validate_physical_release.py` and checks the recorded outcomes
against those declared criteria. The 500 N development load remains the only
hard-coded proof-load floor; passing the validator is not a certification or
independent safety approval.

Until then, the newest CAD version is a validated **geometry candidate**, not a
verified structural product.
