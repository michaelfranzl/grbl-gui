import math

thickness = 1
steps = 20

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False

self.grbl.write("M3")
self.grbl.write("S0")
self.grbl.write("G0X0Y0")
self.grbl.write("F500")
self.grbl.write("G1")


def spiral(cx, cy, r1, r2, windings, direction):
    gcode = []
    steps_per_winding = 100

    r = r1 if direction == 1 else r2

    r_inc = direction * (r2 - r1) / windings / steps_per_winding

    for anglestep in range(0, steps_per_winding * windings):
        r += r_inc
        angle = (direction + direction * anglestep) * 2 * math.pi / steps_per_winding
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        gcode.append("X{:.3f} Y{:.3f} S255".format(x, y))
    return gcode

dir = 1
for z in range(1, steps):
    self.grbl.write(spiral(0, 0, 2, 30, 4, dir))
    self.grbl.write("G91")
    self.grbl.write("G0 Z{} S0".format(-thickness/steps))
    self.grbl.write("G90")
    dir *= -1
