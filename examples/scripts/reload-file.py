# Read a G-Code file and create a scaled copy of it at the origin

self.grbl.preprocessor.do_fractionize_lines = False
self.grbl.preprocessor.do_fractionize_arcs = False
self.grbl.load_file("/tmp/test.ngc")
