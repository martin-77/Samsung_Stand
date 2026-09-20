# Physical release gates

The generated CAD is test-driven for geometry, assembly, print envelope and
collision behavior. That is not the same as a verified structural release for
a television.

A version may be marked **printable candidate**, but not **physically released**,
until all gates below are completed on the real hardware and recorded.

## 1. Real Samsung stand geometry

Still required:

- stand-arm cross-sections at inner-saddle root / center / tip on both sides;
- stand-arm cross-section / side profile at outer-guide root / mid / tip;
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

### Measured-contact dry fit

Before any proof load, install the **real original Samsung stand** into the
generated PETG contact parts without the television and verify the complete
contact path.

For each left/right saddle insert:

1. confirm seating/contact at the measured **root, center and tip** sections;
2. check that the stand does not rock when alternately pressed near the root and
   tip of the saddle region;
3. check for a local high spot that prevents another measured section from
   seating;
4. inspect the unmeasured intervals between the three sections for unexpected
   bosses, ribs or curvature that the loft could not know from the measurements.

For each OUTER_GUIDE:

1. confirm all four side rails sit fully down on the guide floor before the
   original stand is inserted;
2. confirm the side rails guide the real arm without binding;
3. confirm visible/free vertical clearance below the arm;
4. specifically verify that the arm does **not** touch the structural guide
   floor anywhere through the guide span.

These observations are separate fields in the physical release record. A generic
"dry fit passed" is not sufficient by itself.

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

Minimum test sequence on the rigid surrogate support:

1. preload / settle the assembly;
2. apply the full 500 N load in center position;
3. apply the full 500 N load at -15 degrees;
4. apply the full 500 N load at +15 degrees;
5. test the left saddle branch alone at at least 250 N;
6. test the right saddle branch alone at at least 250 N;
7. hold every test case for the declared minimum dwell time;
8. unload and inspect after each case;
9. repeat the swivel cycle and check that the zero detent and positive end stops
   still behave normally.

The two one-side cases are intentional. They verify each nominal 250 N branch
independently and can expose asymmetric print, seating or assembly defects that
a symmetric spreader-board test could hide.

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
- whether the replaceable wear inserts remain seated;
- whether any V6 OUTER_GUIDE side rail has lifted from its seat;
- whether any V6 OUTER_GUIDE side rail has moved axially past its intended
  root/tip capture position.

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

## 6. Static stability characterization and anti-tip restraint

The UE55J6250 Quick Guide BN68-07177M-00 warns that pulling or pushing the TV can
cause it to tip and describes a wall anti-fall restraint for added stability.
This project adds a raised, rotating support underneath the complete original
stand, so the physical release is intentionally stricter: an anti-tip restraint
is required for the final installation.

This is **not** a claim that Samsung specifies a numeric horizontal test force
for this adapter. No such value is invented here.

### Sounddeck flat-area measurement

Before interpreting the 680 × 295 mm base as the real support polygon, measure
the actually flat top surface of the Sounddeck:

- usable flat width;
- usable flat front-to-rear depth;
- whether every point of the printed base is supported by the flat region;
- whether any base edge sits on a radius, chamfer or rounded cabinet edge.

The current 20 mm nominal top-edge margin is a project assumption, not a Magnat
load-rating requirement. These measurements determine whether a future deeper
base is physically possible.

### Fore/aft centre-of-gravity characterization

Use two rigid transverse load-spreading bars or equivalent full-width reaction
lines underneath the **complete final TV + adapter assembly** on a rigid test
surface. Do not perform this measurement on two isolated point supports that can
twist the base.

Record the Y position of the rear and front reaction lines relative to base
centre, then record rear/front reaction force at:

1. -15°;
2. 0°;
3. +15°.

Also record the vertical reference height at which an idealized horizontal force
is to be characterized. The validator calculates:

- total measured reaction;
- projected Y centre of gravity;
- static distance to rear and front base edges;
- idealized horizontal force at the chosen height that would balance the static
  gravity moment about each edge.

The last values are **characterization only**. They are not a certified tipping
load and do not create an acceptance threshold. The validator does require
positive reactions, a centre-of-gravity projection inside the base, and less
than 5% change in total measured reaction between swivel positions so gross
measurement/setup errors are caught.

### Anti-tip restraint

Use the anti-fall concept described in Samsung Quick Guide BN68-07177M-00 with
hardware and wall anchorage appropriate to the actual wall. The release record
requires confirmation that:

- the restraint is installed;
- wall anchorage is verified;
- TV-side attachment is verified;
- the complete -15° to +15° swivel range works without binding or forcing the
  restraint;
- the restraint is not loose, damaged or interfering with normal swivel.

This is an additional safety layer; it does not compensate for a geometrically
unstable base.

## 7. Sounddeck interface / anti-slip gate

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

## 8. Creep / dwell gate

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

## 9. Release criterion

A physically released version needs all of the following:

- CAD design gates green;
- measured Sounddeck flat area fully supports the fixed base;
- final assembly stability characterized at -15° / 0° / +15°;
- anti-tip restraint installed and verified through the full swivel range;
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
