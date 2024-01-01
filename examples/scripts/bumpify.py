sq = gcodetools.read("examples/gcode/square_offset.ngc")

for i in range(0, 200, 20):
    for j in range(0, 200, 20):
        gcode = gcodetools.translate(sq, [i, j, 0])
        self.grbl.write(gcode)

probe_points = [[0, 0], [300, 0], [300, 300], [0, 300]]
probe_values = [1, 200, 3, 100]

# probe_points = self.probe_points
# probe_values = self.probe_values

self.grbl.buffer = gcodetools.bumpify(self.grbl.buffer, self.wpos, probe_points, probe_values)
