# (c) 2015 Michael Franzl

# This script tests if the fractionization of arcs and lines (break
# down into small linear segments) by gerbil's preprocessor
# matches the actually traced path by the Grbl firmware (reality check).

# Fractionization of long lines or arcs into small line segments is useful for faster feed adjustment times, as well as quicker response when stream is paused.

# In the following, we test arcs in both Offset mode as well as Radius mode, for both Absolute G90 distances as well as Relative G91 distances, in all combinations.

# The result will be rendered into the simulator window, and success can be determined by "eyeballing". The actual factorization algorithms were ported directly from Grbl's C source code, so an exact match should not be surprising.

grbl = self.grbl


# ===== THE SOURCE GCODE PROGRAM ======

# --- this first part will use Absolute distance mode
input = []
input.append("G90") # use absolute distances

input.append("F2000") # set feed
input.append("G0 X0 Y0") # return to origin
input.append("G1 X20 Y20 F100") # draw a line

input.append("G17") # select arcs in XY plane
input.append("G2 X30 Y30 I5 J5 F200") # draw clockwise circle in Offset mode

input.append("G18") # select arcs in XZ plane
input.append("G2 X30 Z30 I15 K15") # draw clockwise circle in Offset mode

input.append("G0 Y40") # draw line

input.append("G19") # select arcs in YZ plane
input.append("G2 Y40 Z30 J15 K15") # draw clockwise circle in Offset mode

input.append("G1 X0") # draw line

input.append("G17") # select arcs in XY plane
input.append("G3 X0 Y40 Z0 I5 J5") # draw counterclockwise helical movement down

input.append("G1 X-30") # draw line

input.append("G3 X-40Y50 R-8") # draw circle in Radius mode, larger than 180°
input.append("G3 X-50Y60 R20") # draw circle in Radius mode, smaller than 180°


# ---- this second part will use relative distances -----
input.append("F1000")
input.append("G0 X0 Y0") # return to origin
input.append("G91") # select relative distance mode
input.append("G1 X-50 Y-20") # draw relative line
input.append("G1 X-5 Y-5") # draw another relative line
input.append("G2 X10 Y10 I5 J5") # draw clockwise circle in Offset mode
input.append("G2 X10 Y10 I5 J5") # same
input.append("G3 X10 Y10 I5 J5") # same but counter clockwise
input.append("G3 X-50 Y-10 R90") # Radius mode, less than 180 deg.
input.append("G3 X-10 Y-10 R-10") # Radius mode, more than 180 deg.

input.append("G90") # reset to absolute distance mode



# fractionize above G-Codes and render the line segments in the simulator
self.set_target("simulator")
grbl.job_new()
grbl.preprocessor.do_fractionize_lines = False
grbl.preprocessor.do_fractionize_arcs = False
grbl.write(input)
grbl.job_run()