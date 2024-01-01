self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False

text_gcodes = gcodetools.hersheyToGcode("Hello World!", "scripts")
for angle in range(0, 160, 30):
    self.grbl.write(gcodetools.rotate2D(text_gcodes, [-100, 0], angle))
