# my cnctoolbox script!
#
t = gcodetools
grbl = self.grbl

self.new_job()

sq = t.read("examples/gcode/square_offset.ngc")

for i in range(0, 200, 20):
    for j in range(0, 200, 20):
        gcode = t.translate(sq, [i, j, 0])
        grbl.write("\n".join(gcode))

probe_points = [[0, 0], [300, 0], [300, 300], [0, 300]]
probe_values = [1, 200, 3, 100]

# probe_points = self.probe_points
# probe_values = self.probe_values

grbl.buffer = t.bumpify(grbl.buffer, self.wpos, probe_points, probe_values)

self.set_target("simulator")
grbl.job_run()
