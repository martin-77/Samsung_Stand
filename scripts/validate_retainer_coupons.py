#!/usr/bin/env python3
"""OCC assembly validation for v8 retainer coupons."""

from __future__ import annotations

import json
import os

import FreeCAD as App
import Import

import v8_params as P


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "build_retainer_coupons")


def v(x, y, z):
    return App.Vector(float(x), float(y), float(z))


def load_step(name):
    path = os.path.join(OUT, name + ".step")
    doc = App.newDocument("asm_" + name)
    Import.insert(path, doc.Name)
    doc.recompute()
    shapes = [
        o.Shape.copy()
        for o in doc.Objects
        if hasattr(o, "Shape") and not o.Shape.isNull()
    ]
    App.closeDocument(doc.Name)
    if not shapes:
        raise RuntimeError("No STEP shape: " + path)
    sh = shapes[0]
    for other in shapes[1:]:
        sh = sh.fuse(other)
    return sh.removeSplitter()


def common_volume(a, b):
    return float(a.common(b).Volume)


def distance(a, b):
    return float(a.distToShape(b)[0])


def main():
    failures = []
    result = {"version": "retainer-coupons", "families": {}}

    # Base pin: receiver spans y=-25..+25. Mirror orientation is irrelevant for
    # this coupon; use rear/base production direction.
    receiver = load_step("retainer_coupon_base_receiver")
    pin = load_step("retainer_coupon_joint_pin")
    pin.rotate(v(0, 0, 0), v(0, 0, 1), 90.0)
    pin.translate(
        v(
            0,
            P.BASE_LOCK_PIN_AXIS_START,
            P.BASE_LOCK_PIN_INSTALL_Z,
        )
    )
    vol = common_volume(pin, receiver)
    result["families"]["base_joint"] = {
        "common_volume_mm3": round(vol, 6),
        "distance_mm": round(distance(pin, receiver), 6),
    }
    if vol > 0.05:
        failures.append(f"base coupon final pin interference {vol:.6f} mm3")

    receiver = load_step("retainer_coupon_outer_receiver")
    pin = load_step("retainer_coupon_outer_pin")
    pin.rotate(v(0, 0, 0), v(0, 0, 1), 90.0)
    pin.translate(
        v(
            0,
            P.OUTER_PIN_INSTALL_AXIS_START,
            P.OUTER_PIN_INSTALL_Z,
        )
    )
    vol = common_volume(pin, receiver)
    result["families"]["outer_joint"] = {
        "common_volume_mm3": round(vol, 6),
        "distance_mm": round(distance(pin, receiver), 6),
    }
    if vol > 0.05:
        failures.append(f"outer coupon final pin interference {vol:.6f} mm3")

    receiver = load_step("retainer_coupon_pivot_post")
    pin = load_step("retainer_coupon_pivot_pin")
    pin.translate(
        v(
            P.PIVOT_PIN_INSTALL_X0,
            0,
            P.PIVOT_PIN_INSTALL_Z,
        )
    )
    vol = common_volume(pin, receiver)
    result["families"]["pivot"] = {
        "common_volume_mm3": round(vol, 6),
        "distance_mm": round(distance(pin, receiver), 6),
    }
    if vol > 0.05:
        failures.append(f"pivot coupon final pin interference {vol:.6f} mm3")

    result["failed"] = failures
    with open(
        os.path.join(OUT, "RETAINER_COUPON_ASSEMBLY_VALIDATION.json"),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(
            "RETAINER COUPON ASSEMBLY FAILED: " + " | ".join(failures)
        )


if __name__ == "__main__":
    main()
