// Samsung_Stand v1 validation preview.
// Generated STL parts are already in global XY assembly coordinates.
// Rotor is lifted onto the annular bearing for the installed preview.

$fn = 120;

module sounddeck_reference() {
    color([0.15,0.15,0.15,0.20])
        translate([-350,-170,-12]) cube([700,340,12]);
}

module base_parts() {
    color([0.18,0.18,0.20])
        import("../build_v1/samsung_stand_v1_base_center.stl", convexity=20);
    color([0.22,0.22,0.24])
        import("../build_v1/samsung_stand_v1_base_left.stl", convexity=20);
    color([0.22,0.22,0.24])
        import("../build_v1/samsung_stand_v1_base_right.stl", convexity=20);
}

module rotor() {
    color([0.10,0.10,0.12])
        translate([0,0,10])
            import("../build_v1/samsung_stand_v1_rotor.stl", convexity=20);
}

module reconstructed_stand_reference() {
    // Visual reference only: 840 mm reconstructed stand planform.
    // It is deliberately not used as manufacturing geometry.
    color([0.25,0.25,0.27,0.55]) {
        translate([0,-64,31]) {
            hull() {
                translate([0,0,0]) cylinder(d=34,h=8);
                translate([420,208,0]) cylinder(d=26,h=8);
            }
            hull() {
                translate([0,0,0]) cylinder(d=34,h=8);
                translate([-420,208,0]) cylinder(d=26,h=8);
            }
        }
    }
}

sounddeck_reference();
base_parts();
rotor();
reconstructed_stand_reference();
