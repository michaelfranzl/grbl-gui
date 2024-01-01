# This script reads g-code from a file and
#   1. outputs it as is
#   2. creates a scaled copy of it and moves it so that the lower-left corner
#      of its bounding box is exactly at the origin

cat = gcodetools.read("examples/gcode/cat.ngc")

self.grbl.write(cat)
self.grbl.write(gcodetools.bbox_draw(cat))

scaled_origin_cat = gcodetools.to_origin(gcodetools.scale_factor(cat, [0.2, 0.2, 0]))
self.grbl.write(scaled_origin_cat)
self.grbl.write(gcodetools.bbox_draw(scaled_origin_cat))
