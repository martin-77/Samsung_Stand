// Samsung_Stand v2 installed-orientation validation preview.
// Original Samsung stand is reconstructed reference geometry only.

$fn = 120;

pivot_y = -64;
right_angle = 26.344;
left_angle = 153.656;
inner_r0 = 85;
saddle_u = 193.99;

module sounddeck_reference() {
    color([0.15,0.15,0.15,0.18])
        translate([-350,-170,-12]) cube([700,340,12]);
}

module fixed_base() {
    color([0.19,0.19,0.21])
        import("../build_v2/samsung_stand_v2_base_center.stl", convexity=20);
    color([0.23,0.23,0.25])
        import("../build_v2/samsung_stand_v2_base_left.stl", convexity=20);
    color([0.23,0.23,0.25])
        import("../build_v2/samsung_stand_v2_base_right.stl", convexity=20);
}

module rotor() {
    color([0.09,0.09,0.11])
        translate([0,0,10])
            import("../build_v2/samsung_stand_v2_rotor.stl", convexity=20);
}

module inner_arm_at(a) {
    color([0.11,0.11,0.13])
        translate([0,pivot_y,18])
            rotate([0,0,a])
                translate([inner_r0,0,0])
                    import("../build_v2/samsung_stand_v2_inner_arm.stl", convexity=20);

    // Blank saddle insert shown separately for clarity.
    color([0.32,0.32,0.35])
        translate([0,pivot_y,18+7])
            rotate([0,0,a])
                translate([inner_r0+saddle_u,0,0])
                    import("../build_v2/samsung_stand_v2_saddle_insert_blank.stl", convexity=20);
}

module reconstructed_stand_reference() {
    color([0.35,0.35,0.38,0.38])
        translate([0,pivot_y,39]) {
            hull() {
                cylinder(d=36,h=7);
                translate([420,208,0]) cylinder(d=26,h=7);
            }
            hull() {
                cylinder(d=36,h=7);
                translate([-420,208,0]) cylinder(d=26,h=7);
            }
        }
}

sounddeck_reference();
fixed_base();
rotor();
inner_arm_at(right_angle);
inner_arm_at(left_angle);
reconstructed_stand_reference();
