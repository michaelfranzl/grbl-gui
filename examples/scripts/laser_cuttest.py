# Read a simple square G-Code from a file and create an array of 10 x 10 of the same square

thickness = 1
steps = 10
feed = 750

self.grbl.preprocessor.do_fractionize_arcs = True
self.grbl.preprocessor.do_fractionize_lines = True

self.grbl.write("G91")

self.grbl.write("S0")
self.grbl.write("M3")
self.grbl.write("F{}".format(feed))

self.grbl.write("G0 X10 Y5")
for step in range(0, steps):
    z_inc = thickness/steps
    self.grbl.write("G2 X0 Y0 I0 J5 S255")
    self.grbl.write("G0 Z{} S0".format(-z_inc))

self.grbl.write("G0 X-10 Y-5 Z{}".format(thickness))

square = ["G1 X20 S255", "G1 Y20", "G1 X-20", "G1 Y-20"]
for step in range(0, steps):
    self.grbl.write(square)
    z_inc = thickness/steps
    self.grbl.write("G0 Z{} S0".format(-z_inc))
