self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.preprocessor.do_fractionize_arcs = False

self.grbl.write("S0")  # laser min
self.grbl.write("M3")  # laser on

i = 0
gcode = pixel2laser.do("examples/patterntest.png", 10, 20, 0)
for feed in range(6000, 0, -1000):
    self.grbl.write("F{}".format(feed))
    self.grbl.write(gcodetools.translate(gcode, [0, i * 1.8, 0]))
    i += 1

self.grbl.write("S0")  # laser min
self.grbl.write("M5")  # laser off
