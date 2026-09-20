# Samsung Stand v4

v4 extends the validated v3 assembly with positive mechanical +/-15 degree swivel end stops.

Stop architecture:
- a flat-printable spoke and broad stop tab are fused into the rotor;
- two broad fixed stop towers are fused into BASE_CENTER;
- BASE_CENTER has a narrow sweep-clearance corridor above the bearing plane so the stop can start at rotor-local Z=0 without support;
- the mechanical stop carries end-stop load. A later detent, if added, is positional only.

Validation contract:
- at +/-14 degrees the stop must remain free;
- at +/-15 degrees the stop must be surface contact without meaningful penetration;
- at +/-15.5 degrees the stop must show solid interference, proving positive blocking;
- the full rotating carrier is collision-checked against the fixed base through representative sweep positions.

The Samsung arm contact channel remains a measured-fit TODO; v4 does not change the v3 placeholder fit claim.
