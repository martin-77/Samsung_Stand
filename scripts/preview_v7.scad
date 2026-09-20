// Samsung_Stand v7 preview with replaceable PETG wear surfaces highlighted.

$fn=140;
pivot_y=-64;
right_angle=26.346366;
left_angle=153.653634;
inner_r0=85;
outer_r0=310;

module base() {
  color([0.20,0.20,0.22])
    import("../build_v7/samsung_stand_v7_base_center.stl",convexity=30);
  color([0.23,0.23,0.25])
    import("../build_v7/samsung_stand_v7_base_left.stl",convexity=30);
  color([0.23,0.23,0.25])
    import("../build_v7/samsung_stand_v7_base_right.stl",convexity=30);
}

module radial(file,r,a,z,c=[0.10,0.10,0.12]) {
  color(c)
    translate([0,pivot_y,z])
      rotate([0,0,a])
        translate([r,0,0])
          import(file,convexity=30);
}

module wear_arc(a) {
  color([0.55,0.55,0.58])
    translate([0,pivot_y,16.8])
      rotate([0,0,a])
        import("../build_v7/samsung_stand_v7_track_wear_arc.stl",convexity=30);
}

base();

color([0.60,0.60,0.64])
  translate([0,pivot_y,8.8])
    import("../build_v7/samsung_stand_v7_center_wear_ring.stl",convexity=30);

wear_arc(right_angle);
wear_arc(left_angle);

color([0.08,0.08,0.10])
  translate([0,0,10])
    import("../build_v7/samsung_stand_v7_rotor.stl",convexity=30);

radial("../build_v7/samsung_stand_v7_inner_arm.stl",inner_r0,right_angle,18);
radial("../build_v7/samsung_stand_v7_inner_arm.stl",inner_r0,left_angle,18);
radial("../build_v7/samsung_stand_v7_outer_guide.stl",outer_r0,right_angle,18,[0.16,0.16,0.18]);
radial("../build_v7/samsung_stand_v7_outer_guide.stl",outer_r0,left_angle,18,[0.16,0.16,0.18]);
