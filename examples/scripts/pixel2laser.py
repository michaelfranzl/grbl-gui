# (c) 2015 Michael Franzl

# This script reads a PNG image, translates it into G-Code
# and writes the resulting file to the tmp directory

p2l = pixel2laser
t = gcodetools

grbl = self.grbl
grbl.buffer = []

self.new_job()

gcode = p2l.do("examples/patterntest.png", 10, 20, 0)
#gcode = p2l.do("examples/gradient.png", 10, 20, 0)

grbl.preprocessor.do_fractionize_lines = False
grbl.preprocessor.do_fractionize_arcs = False

grbl.write("S0") # laser min
grbl.write("M3") # laser on
grbl.write(gcode)

self.set_target("simulator")
grbl.job_run()

