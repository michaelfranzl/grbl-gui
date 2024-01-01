# Read a simple square G-Code from a file and create an array of 10 x 10 of the same square

t = gcodetools
grbl = self.grbl

thickness = 1
steps = 10
feed = 750

self.new_job()

gcode = []
gcode.append("G91")

gcode.append("S0")
gcode.append("M3")
gcode.append("F{}".format(feed))

gcode.append("G0 X10 Y5")
for step in range(0,steps):
    z_inc = thickness/steps
    gcode.append("G2 X0 Y0 I0 J5 S255")
    gcode.append("G0 Z{} S0".format(-z_inc))

gcode.append("G0 X-10 Y-5 Z{}".format(thickness))

square = ["G1 X20 S255", "G1 Y20", "G1 X-20", "G1 Y-20"]
for step in range(0,steps):
    gcode += square
    z_inc = thickness/steps
    gcode.append("G0 Z{} S0".format(-z_inc))


grbl.preprocessor.do_fractionize_arcs = True
grbl.preprocessor.do_fractionize_lines = True
grbl.write(gcode)


# Send the result straight to the simulator window
grbl.target = "simulator"
grbl.job_run()







