# Structural fit coupons

These small coupons calibrate the three form-locking roof-key joints before large PETG parts are printed.

Families:
- base: BASE_LEFT/RIGHT into BASE_CENTER;
- inner: INNER_ARM into ROTOR;
- outer: OUTER_GUIDE into INNER_ARM.

For each family print:
- one male probe;
- c030 receiver: 0.30 mm nominal clearance;
- c040 receiver: 0.40 mm nominal clearance;
- c050 receiver: 0.50 mm nominal clearance.

The current production CAD uses 0.40 mm nominal side/roof clearance.

Selection rule:
use the smallest receiver that slides fully onto the probe without force, binding or visible PETG whitening, while still avoiding obvious rocking.

These coupons test cross-sectional printer/material fit. They do not replace the later full-joint or proof-load test.
