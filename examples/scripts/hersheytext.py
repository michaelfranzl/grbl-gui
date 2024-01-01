# my cnctoolbox script!
#
t = gcodetools
grbl = self.grbl

text_gcodes = t.hersheyToGcode("Hello World!", "scripts")


rotated_gcodes = []
for angle in range(0, 160, 30):
    rotated_gcodes += t.rotate2D(text_gcodes, [-100, 0], angle)

self.new_job()

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.write(rotated_gcodes)

self.set_target("simulator")
self.job_run()
