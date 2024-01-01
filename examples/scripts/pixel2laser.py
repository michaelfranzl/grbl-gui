self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.preprocessor.do_fractionize_arcs = False

self.grbl.write("S0")  # laser min
self.grbl.write("M3")  # laser on
self.grbl.write(pixel2laser.do("examples/patterntest.png", 10, 20, 0))
