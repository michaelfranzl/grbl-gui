# my cnctoolbox script!
#
t = gcodetools
grbl = self.grbl

import math

thickness = 1
steps = 20

gcodes = []

gcodes.append("M3")
gcodes.append("S0")

gcodes.append("G0X0Y0")

gcodes.append("F500")

gcodes.append("G1")


self.new_job()

def spiral(cx, cy, r1, r2, windings, direction):
    gcode = []
    steps_per_winding = 100

    if direction == 1:
        r = r1
    else:
        r = r2

    r_inc = direction * (r2 - r1) / windings / steps_per_winding

    for anglestep in range(0, steps_per_winding * windings):
        r += r_inc
        angle = (direction + direction * anglestep) * 2 * math.pi / steps_per_winding
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        print(angle)
        gcode.append("X{:.3f} Y{:.3f} S255".format(x, y))
    return gcode


self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False

dir = 1
for z in range(1, steps):
    gcodes += spiral(0, 0, 2, 30, 4, dir)
    gcodes.append("G91")
    gcodes.append("G0 Z{} S0".format(-thickness/steps))
    gcodes.append("G90")
    dir *= -1


self.grbl.write(gcodes)

self.set_target("simulator")
self.job_run()
