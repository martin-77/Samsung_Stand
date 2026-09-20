// Samsung_Stand v3 installed preview.
// Gray Samsung V-arms are reconstructed reference only.

$fn=120;
pivot_y=-64;
right_angle=26.346366;
left_angle=153.653634;
inner_r0=85;
outer_r0=310;
saddle_u=193.978;

module sounddeck() {
  color([0.15,0.15,0.15,0.16]) translate([-350,-170,-12]) cube([700,340,12]);
}
module base() {
  color([0.2,0.2,0.22]) import("../build_v3/samsung_stand_v3_base_center.stl",convexity=20);
  color([0.23,0.23,0.25]) import("../build_v3/samsung_stand_v3_base_left.stl",convexity=20);
  color([0.23,0.23,0.25]) import("../build_v3/samsung_stand_v3_base_right.stl",convexity=20);
}
module radial_part(file,r,a,z,c=[0.1,0.1,0.12]) {
  color(c) translate([0,pivot_y,z]) rotate([0,0,a]) translate([r,0,0])
    import(file,convexity=20);
}
module stand_reference() {
  color([0.38,0.38,0.4,0.34]) translate([0,pivot_y,39]) {
    hull(){ cylinder(d=36,h=7); translate([420,208,0]) cylinder(d=26,h=7); }
    hull(){ cylinder(d=36,h=7); translate([-420,208,0]) cylinder(d=26,h=7); }
  }
}

sounddeck();
base();
color([0.08,0.08,0.1]) translate([0,0,10])
  import("../build_v3/samsung_stand_v3_rotor.stl",convexity=20);
radial_part("../build_v3/samsung_stand_v3_inner_arm.stl",inner_r0,right_angle,18);
radial_part("../build_v3/samsung_stand_v3_inner_arm.stl",inner_r0,left_angle,18);
radial_part("../build_v3/samsung_stand_v3_outer_guide.stl",outer_r0,right_angle,18,[0.16,0.16,0.18]);
radial_part("../build_v3/samsung_stand_v3_outer_guide.stl",outer_r0,left_angle,18,[0.16,0.16,0.18]);
stand_reference();
