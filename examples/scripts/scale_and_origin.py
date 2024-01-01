# (c) 2015 Michael Franzl
# This script reads g-code from a file and
#   1. outputs it as it is
#   2. creates a scaled copy of it and moves it so that the lower-left corner
#      of its bounding box is exactly at the origin

grbl = self.grbl
t = gcodetools

self.new_job()

cat = t.read("examples/gcode/cat.ngc")

grbl.write(cat)
grbl.write(t.bbox_draw(cat))

scaled_origin_cat = t.to_origin(t.scale_factor(cat, [0.2, 0.2, 0]))

grbl.write(scaled_origin_cat)
grbl.write(t.bbox_draw(scaled_origin_cat))

grbl.preprocessor.vars = {"1": 0}
self.set_target("simulator")
grbl.job_run()
