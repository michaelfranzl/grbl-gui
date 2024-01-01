self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False

self.grbl.write("F400")

self.grbl.write("G55")

self.grbl.write("G0 X20 Y20")
self.grbl.write("G1 X30")
self.grbl.write("G1 X40")
self.grbl.write("G1 X50")
self.grbl.write("G2 X60 Y30 I5 J5")

self.grbl.write("G54")

self.grbl.write("G0 X20 Y20")
self.grbl.write("G1 X30")
self.grbl.write("G1 X40")
self.grbl.write("G1 X50")
self.grbl.write("G2 X60 Y30 I5 J5")
