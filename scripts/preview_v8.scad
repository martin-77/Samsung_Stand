// Samsung_Stand v8 retention preview.
// Replacement lock pins are rendered lighter than structural parts.

$fn=140;
pivot_y=-64;
right_angle=26.346366;
left_angle=153.653634;
inner_r0=85;
outer_r0=310;
inner_pin_r=60;
outer_pin_r=288;

module base() {
  color([0.20,0.20,0.22])
    import("../build_v8/samsung_stand_v8_base_center.stl",convexity=40);
  color([0.23,0.23,0.25])
    import("../build_v8/samsung_stand_v8_base_left.stl",convexity=40);
  color([0.23,0.23,0.25])
    import("../build_v8/samsung_stand_v8_base_right.stl",convexity=40);
}

module radial_part(file,r,a,z,c=[0.10,0.10,0.12]) {
  color(c)
    translate([0,pivot_y,z])
      rotate([0,0,a])
        translate([r,0,0])
          import(file,convexity=30);
}

module base_pin(x,y) {
  color([0.62,0.62,0.66])
    if (y < 0)
      translate([x,y-26,8.25])
        rotate([0,0,90])
          import("../build_v8/samsung_stand_v8_joint_lock_pin.stl",convexity=20);
    else
      translate([x,y+26,8.25])
        rotate([0,0,-90])
          import("../build_v8/samsung_stand_v8_joint_lock_pin.stl",convexity=20);
}

module inner_pin(a) {
  color([0.62,0.62,0.66])
    translate([0,pivot_y,0])
      rotate([0,0,a])
        translate([inner_pin_r,-23,19.25])
          rotate([0,0,90])
            import("../build_v8/samsung_stand_v8_joint_lock_pin.stl",convexity=20);
}

module outer_pin(a) {
  color([0.70,0.70,0.73])
    translate([0,pivot_y,0])
      rotate([0,0,a])
        translate([outer_pin_r,-32,22.25])
          rotate([0,0,90])
            import("../build_v8/samsung_stand_v8_outer_lock_pin.stl",convexity=20);
}

base();

color([0.55,0.55,0.58])
  translate([0,pivot_y,8.8])
    import("../build_v8/samsung_stand_v8_center_wear_ring.stl",convexity=30);

color([0.08,0.08,0.10])
  translate([0,0,10])
    import("../build_v8/samsung_stand_v8_rotor.stl",convexity=40);

radial_part("../build_v8/samsung_stand_v8_inner_arm.stl",inner_r0,right_angle,18);
radial_part("../build_v8/samsung_stand_v8_inner_arm.stl",inner_r0,left_angle,18);
radial_part("../build_v8/samsung_stand_v8_outer_guide.stl",outer_r0,right_angle,18,[0.16,0.16,0.18]);
radial_part("../build_v8/samsung_stand_v8_outer_guide.stl",outer_r0,left_angle,18,[0.16,0.16,0.18]);

base_pin(-100,-90);
base_pin(-100,90);
base_pin(100,-90);
base_pin(100,90);

inner_pin(right_angle);
inner_pin(left_angle);
outer_pin(right_angle);
outer_pin(left_angle);

color([0.78,0.78,0.81])
  translate([-18,pivot_y,21.7])
    import("../build_v8/samsung_stand_v8_pivot_lock_pin.stl",convexity=20);
