# my cnctoolbox script!
#
t = gcodetools
grbl = self.grbl


focus_range = 50
width = 200
line_spacing = 0.5

self.new_job()
gcodes = []
gcodes.append("G91") # relative distances

# turn laser off
gcodes.append("S0")
gcodes.append("M3")

dir = 1
for feed in range(6000, 100, -500):
    gcodes.append("G1 X{} Z{} F{} S255".format(width * dir, focus_range * dir, feed))
    gcodes.append("G0 Y{} S0".format(line_spacing))
    dir *= -1

# turn laser off
gcodes.append("S0")
gcodes.append("M3")

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.write(gcodes)

self.set_target("simulator")
self.job_run()













