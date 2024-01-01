focus_range = 50
width = 30
point_distance = 3

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False

self.grbl.write("G91")  # relative distances

# turn laser off
self.grbl.write("S0")
self.grbl.write("M3")

dir = 1
points_per_line = int(width/point_distance)
# first row = 10 ms, each row plus 100ms
for dwell in range(100, 10000, 1000):
    self.grbl.write("S255")
    self.grbl.write("G4 P{:0.2f}".format(dwell / 10000))
    self.grbl.write("S0")
    for x in range(1, points_per_line + 1):
        z_inc = focus_range / points_per_line
        self.grbl.write("G0 X{} Z{}".format(point_distance * dir, z_inc * dir))
        self.grbl.write("S255")
        self.grbl.write("G4 P{:0.2f}".format(dwell / 10000))
        self.grbl.write("S0")
    self.grbl.write("G0 Y{}".format(point_distance))
    dir *= -1

# turn laser off
self.grbl.write("S0")
self.grbl.write("M3")
