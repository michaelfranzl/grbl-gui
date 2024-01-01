"""
grbl-gui - Graphical User Interface for the "grbl" CNC controller
Copyright (C) 2015 Michael Franzl

This file is part of grbl-gui.

grbl-gui is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

grbl-gui is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyglpainter. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import re
import numpy as np

from pyglpainter.classes.painterwidget import PainterWidget

from OpenGL.GL import *


class SimulatorWidget(PainterWidget):
    def __init__(self, parent=None, refresh_rate=20):
        super().__init__(parent, refresh_rate)

        self.cs_offsets = {
            "G54": (0, 0, 0),
            "G55": (0, 0, 0),
            "G56": (0, 0, 0),
            "G57": (0, 0, 0),
            "G58": (0, 0, 0),
            "G59": (0, 0, 0)
        }

    def draw_heightmap(self, pos_col, dim, origin):
        if "myheightmap" in self.programs["heightmap"].items:
            # update
            i = self.programs["heightmap"].items["myheightmap"]
            i.set_data(pos_col)
            i.set_origin(origin)
            i.upload()
        else:
            # create
            i = self.item_create(
                "HeightMap",
                "myheightmap",
                "heightmap",
                dim[0],
                dim[1],
                pos_col,
                False,
                origin,
                1)

        self.dirty = True

    def remove_heightmap(self):
        self.item_remove("myheightmap")

    def initializeGL(self):
        super().initializeGL()

        path = os.path.dirname(os.path.realpath(__file__)) + "/shaders/"

        opts = {
            "uniforms": {
                "mat_m": "Matrix4fv",
                "mat_v": "Matrix4fv",
                "mat_p": "Matrix4fv",
            },
            "attributes": {
                "color": "vec4",
                "position": "vec3",
            }
        }
        self.program_create(
                "simple3d",
                path + "simple3d-vertex.c",
                path + "simple3d-fragment.c",
                opts)
        self.program_create(
                "simple2d",
                path + "simple2d-vertex.c",
                path + "simple2d-fragment.c",
                opts)

        opts = {
            "uniforms": {
                "mat_m": "Matrix4fv",
                "mat_v": "Matrix4fv",
                "mat_p": "Matrix4fv",
                "height_min": "1f",
                "height_max": "1f",
            },
            "attributes": {
                "position": "vec3",
            }
        }
        self.program_create(
            "heightmap",
            path + "heightmap-vertex.c",
            path + "heightmap-fragment.c",
            opts)

    def draw_stage(self, workarea_x, workarea_y):
        self.makeCurrent()
        self.item_create("CoordSystem", "csm", "simple3d", (0, 0, 0), 120, 5)

        self.item_remove("working_area_grid")
        self.item_create(
                "OrthoLineGrid",
                "working_area_grid",
                "simple3d",
                (0, 0),
                (workarea_x, workarea_y),
                10,
                (-workarea_x, -workarea_y, 0))

        self.item_create("Star", "buffermarker", "simple3d", (0, 0, 0), 2)
        self.dirty = True

    def cleanup_stage(self):
        self.makeCurrent()
        item_keys = self.programs["simple3d"].items.keys()

        keys_to_delete = []
        for key in item_keys:
            if not (re.match(".*csG5[4-9].*", key) or key == "csm" or key == "working_area_grid" or key == "tool" or key == "buffermarker"):
                keys_to_delete.append(key)

        print("cleanup_stage: removing items {}".format(keys_to_delete))
        for key in keys_to_delete:
            self.item_remove(key)

        self.dirty = True

    def draw_coordinate_system(self, key, tpl_origin):
        self.makeCurrent()
        self.cs_offsets[key] = tpl_origin
        cskey = "cs" + key

        if cskey in self.programs["simple3d"].items:
            self.programs["simple3d"].items[cskey].set_origin(tpl_origin)
        else:
            # create
            self.item_create("CoordSystem", cskey,
                             "simple3d", tpl_origin, 30, 2)

        txtkey = "txtcs" + key
        if txtkey in self.programs["simple3d"].items:
            self.programs["simple3d"].items[txtkey].set_origin(tpl_origin)
        else:
            # create
            text = self.item_create(
                "Text",
                txtkey,
                "simple3d",
                key,
                tpl_origin,
                2,
                1,
                (1, 1, 1, 0.2))
            text.billboard = True

        self.dirty = True

    def draw_gcode(self, gcode, cmpos, ccs, do_fractionize_arcs=True):
        self.makeCurrent()
        if "gcode" in self.programs["simple3d"].items:
            self.item_remove("gcode")

        # create a new one
        self.item_create(
                "GcodePath",
                "gcode",
                "simple3d",
                gcode,
                cmpos,
                ccs,
                self.cs_offsets,
                do_fractionize_arcs)
        self.dirty = True

    def put_buffer_marker_at_line(self, line_number):
        self.makeCurrent()
        if "gcode" in self.programs["simple3d"].items:
            if 2 * line_number <= self.programs["simple3d"].items["gcode"].vertexcount:
                bufferpos = self.programs["simple3d"].items["gcode"].vdata_pos_col["position"][2 * line_number]

                if "buffermarker" in self.programs["simple3d"].items:
                    self.programs["simple3d"].items["buffermarker"].set_origin(
                        tuple(bufferpos))

            self.dirty = True

    def get_buffer_marker_pos(self):
        self.makeCurrent()
        return self.programs["simple3d"].items["buffermarker"].origin

    def draw_tool(self, cmpos):
        self.makeCurrent()
        if "tool" in self.programs["simple3d"].items:
            # if tool was already created, simply move it to cmpos
            self.programs["simple3d"].items["tool"].set_origin(cmpos)
        else:
            # tool not yet created. create it and move it cmpos
            i = self.item_create(
                "Item",
                "tool",
                "simple3d",
                GL_LINES,
                7,
                (0, 0, 0),
                1,
                False,
                2)
            i.append_vertices([[(0, 0, 0), (1, 1, 1, .5)]])
            i.append_vertices([[(0, 0, 200), (1, 1, 1, .2)]])
            i.upload()
            i.set_origin(cmpos)

        if "tracer" in self.programs["simple3d"].items:
            # update existing
            tr = self.programs["simple3d"].items["tracer"]
            tr.append_vertices([[cmpos, (1, 1, 1, 0.2)]])
            # vertex_nr = tr.vertexcount
            # tr.substitute(vertex_nr, cmpos, )
        else:
            # create new
            tr = self.item_create(
                "Item",
                "tracer",
                "simple3d",
                GL_LINE_STRIP,
                1,
                (0, 0, 0),
                1,
                False,
                1000000)
            tr.append_vertices([[cmpos, (1, 1, 1, 0.2)]])
            tr.upload()

        self.dirty = True
