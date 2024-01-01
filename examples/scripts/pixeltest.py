# Draws a single line with alternating pixels for speed test

p2l = pixel2laser
t = gcodetools

grbl = self.grbl

self.new_job()

gcode = "F10000\n"
gcode += "G0X0Y0\n"
dist = 1000
ppmm = 1
i = 0
for i in range(0, dist * ppmm):
    feed = 255 if i == 0 else 0
    gcode += "X{:.1f}S{:d}\n".format(i/ppmm, feed)

grbl.write(gcode)

self.set_target("simulator")
grbl.job_run()

