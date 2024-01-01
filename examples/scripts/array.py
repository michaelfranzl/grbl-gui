# Read a simple square G-Code from a file and create an array of 10 x 10 of the same square

sq = gcodetools.read("examples/gcode/square_offset.ngc")

for i in range(0, 200, 20):
    for j in range(0, 200, 20):
        self.grbl.write(gcodetools.translate(sq, [i, j, 0]))
