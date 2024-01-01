# This script tests if the fractionization of arcs and lines (break
# down into small linear segments) by gcode-machine's preprocessor
# matches the actually traced path by the Grbl firmware (reality check).

# Fractionization of long lines or arcs into small line segments is useful for
# faster feed adjustment times, as well as quicker response when stream is
# paused.

# In the following, we test arcs in both Offset mode as well as Radius mode,
# for both Absolute G90 distances as well as Relative G91 distances,
# in all combinations.

# The result will be rendered into the simulator window, and success
# can be determined by "eyeballing". The actual factorization algorithms
# were ported directly from Grbl's C source code, so an exact match
# should not be surprising.

# ===== THE SOURCE GCODE PROGRAM ======

# --- this first part will use Absolute distance mode
self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.preprocessor.do_fractionize_arcs = False

self.grbl.write("G90")  # use absolute distances

self.grbl.write("F2000")  # set feed
self.grbl.write("G0 X0 Y0")  # return to origin
self.grbl.write("G1 X20 Y20 F100")  # draw a line

self.grbl.write("G17")  # select arcs in XY plane
self.grbl.write("G2 X30 Y30 I5 J5 F200")  # draw clockwise circle in Offset mode

self.grbl.write("G18")  # select arcs in XZ plane
self.grbl.write("G2 X30 Z30 I15 K15")  # draw clockwise circle in Offset mode

self.grbl.write("G0 Y40")  # draw line

self.grbl.write("G19")  # select arcs in YZ plane
self.grbl.write("G2 Y40 Z30 J15 K15")  # draw clockwise circle in Offset mode

self.grbl.write("G1 X0")  # draw line

self.grbl.write("G17")  # select arcs in XY plane
# draw counterclockwise helical movement down
self.grbl.write("G3 X0 Y40 Z0 I5 J5")

self.grbl.write("G1 X-30")  # draw line

self.grbl.write("G3 X-40Y50 R-8")  # draw circle in Radius mode, larger than 180°
self.grbl.write("G3 X-50Y60 R20")  # draw circle in Radius mode, smaller than 180°


# ---- this second part will use relative distances -----
self.grbl.write("F1000")
self.grbl.write("G0 X0 Y0")  # return to origin
self.grbl.write("G91")  # select relative distance mode
self.grbl.write("G1 X-50 Y-20")  # draw relative line
self.grbl.write("G1 X-5 Y-5")  # draw another relative line
self.grbl.write("G2 X10 Y10 I5 J5")  # draw clockwise circle in Offset mode
self.grbl.write("G2 X10 Y10 I5 J5")  # same
self.grbl.write("G3 X10 Y10 I5 J5")  # same but counter clockwise
self.grbl.write("G3 X-50 Y-10 R90")  # Radius mode, less than 180 deg.
self.grbl.write("G3 X-10 Y-10 R-10")  # Radius mode, more than 180 deg.

self.grbl.write("G90")  # reset to absolute distance mode
