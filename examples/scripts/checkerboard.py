# Read arbitrary G-Code from a file and create a checkerboard array of 8 x 8

t = gcodetools
grbl = self.grbl

self.new_job()

cat = t.read("examples/gcode/cat.ngc")

scaled_origin_cat = t.to_origin(t.scale_factor(cat, [0.2, 0.2, 0]))


for i in range(0,200,25):
    for j in range(0, 200, 25):
        x = 1 if j % 2 == 0 else 0
        if i % 2 == x:
            gcode = t.translate(scaled_origin_cat, [i, j, 0])
            print("\nProcessing", i, j)
            grbl.write("\n".join(gcode))


grbl.preprocessor.vars = {"1":0}
self.set_target("simulator")
grbl.job_run()