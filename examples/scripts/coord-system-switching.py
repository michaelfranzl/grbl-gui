# my cnctoolbox script!
#
grbl = self.grbl

gcodes = []

gcodes.append("F400")

gcodes.append("G55")

gcodes.append("G0 X20 Y20")
gcodes.append("G1 X30")
gcodes.append("G1 X40")
gcodes.append("G1 X50")
gcodes.append("G2 X60 Y30 I5 J5")

gcodes.append("G54")

gcodes.append("G0 X20 Y20")
gcodes.append("G1 X30")
gcodes.append("G1 X40")
gcodes.append("G1 X50")
gcodes.append("G2 X60 Y30 I5 J5")

self.new_job()

self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.write(gcodes)

self.set_target("simulator")
self.job_run()
