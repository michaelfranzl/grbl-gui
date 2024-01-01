# Draws a single line with alternating pixels for speed test

self.grbl.write("F10000")
self.grbl.write("G0X0Y0")

dist = 1000
ppmm = 1
i = 0
for i in range(0, dist * ppmm):
    feed = 255 if i == 0 else 0
    self.grbl.write("X{:.1f}S{:d}".format(i / ppmm, feed))
