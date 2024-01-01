# This script demonstrates that relative-distance CW and CCW circles,
# in R as well as O mode, can be scaled via the gcodetools module.

# ===== THE SOURCE GCODE PROGRAM ======

# --- this first part will use Absolute distance mode
self.grbl.preprocessor.do_fractionize_arcs = False

self.grbl.write("F1000")
self.grbl.write("G0 X0 Y0")  # select arcs in XY plane
self.grbl.write("G17")  # select arcs in XY plane

circles = []
circles.append("G91")  # select relative distance mode
circles.append("G3 X15 Y40 R90")  # Radius mode, less than 180 deg.
circles.append("G2 X-10 Y-10 R10")  # Radius mode, more than 180 deg.
circles.append("G2 X-20 Y10 R-12")  # Radius mode, more than 180 deg.
circles.append("G90")  # reset to absolute distance mode

for i in range(1, 10):
    factor = 1 / i
    self.grbl.write(gcodetools.scale_factor(circles, [factor, factor, factor]))
