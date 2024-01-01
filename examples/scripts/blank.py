self.grbl.preprocessor.do_fractionize_arcs = True
self.grbl.preprocessor.do_fractionize_lines = True
self.grbl.write(";blah")
self.grbl.write("G0 X0 Y0 Z0 ; nice command")
self.grbl.write("G1 X10 Y30 F100")
self.grbl.write("G4 P2")
self.grbl.write("G2 X20 Y40 I5 J5")
