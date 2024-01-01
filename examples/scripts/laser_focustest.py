focus_range = 50
width = 200
line_spacing = 0.5

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False

self.grbl.write("G91")  # relative distances

# turn laser off
self.grbl.write("S0")
self.grbl.write("M3")

dir = 1
for feed in range(6000, 100, -500):
    self.grbl.write("G1 X{} Z{} F{} S255".format(width * dir, focus_range * dir, feed))
    self.grbl.write("G0 Y{} S0".format(line_spacing))
    dir *= -1

# turn laser off
self.grbl.write("S0")
self.grbl.write("M3")
