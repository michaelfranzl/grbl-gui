# Read arbitrary G-Code from a file and create a checkerboard array of 8 x 8

cat = gcodetools.read("examples/gcode/cat.ngc")

scaled_origin_cat = gcodetools.to_origin(gcodetools.scale_factor(cat, [0.2, 0.2, 0]))

for i in range(0, 200, 25):
    for j in range(0, 200, 25):
        x = 1 if j % 2 == 0 else 0
        if i % 2 == x:
            self.grbl.write(gcodetools.translate(scaled_origin_cat, [i, j, 0]))
