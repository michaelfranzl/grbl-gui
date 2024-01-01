import xml.etree.ElementTree as ET
import svgwrite
import logging

class SVG:
    def __init__(self, name="", path=""):
        self.name = name
        self.path = path
        self.drawing = svgwrite.Drawing(path, profile='tiny')
        #self.tree = ET.parse(path)
        
    def draw_from_data(self, data, draw_circles):
        logging.info("SVG: draw_from_data")
        pathcmds = "M "
        for idx, val in enumerate(data):
            x = val[0]
            y = val[1]
            r = val[2]

            if idx > 0:
              pathcmds += " L "
            pathcmds += str(x) + "," + str(y) + " "
            
            if True or draw_circles:
                self.drawing.add(self.drawing.circle((x, y), r))
        pathcmds += " z"
        self.drawing.add(self.drawing.path(d=pathcmds, fill="none", stroke="red", stroke_width="2px"))

        
    def save(self):
        logging.info("SVG: save")
        self.drawing.save()