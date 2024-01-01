#!/usr/bin/env python

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

import argparse
import logging
import sys
import time

from classes.session import Session
from classes.svg import SVG

from grbl_streamer import GrblStreamer

from lib import stipple
from lib import pixel2laser as p2l
from lib import gcodetools
from lib import utility

from classes.window import Ui_MainWindow
#from gi.repository import Gtk

from PyQt5.QtWidgets import (QApplication, QHBoxLayout, QMessageBox, QSlider, QWidget, QDialog, QMainWindow)

from classes.window import MainWindow


def main():
    '''
    This function does nothing else than parsing command line arguments.
    It delegates to library functions accordingly.
    '''
    #log_format = '%(asctime)s %(levelname)s %(message)s'
    #logging.basicConfig(level=logging.INFO, format=log_format)
    logger = logging.getLogger('grbl_gui')
    logger.setLevel(5)

    parser = argparse.ArgumentParser(description='This program is a box full of useful CNC tools')

    # Set up sub-commands like git uses them
    subparsers = parser.add_subparsers(help="Available subcommands")

    # define arguments for the 'stipple' subcommand
    stipple_parser = subparsers.add_parser(
        "stipple",
        help="Creates stippling art for laser-engraving based on files created by third-party C++ programs voronoi_stippler and concorde.",
        epilog="EXAMPLE: python ./grbl_gui.py stipple ./data/grace.crd ./data/grace.sol out.svg --weight ./data/grace.wgt"
        )
    stipple_parser.add_argument(
        'crd_file',
        metavar='COORD_FILE',
        help='File containing point coordinates in concorde format. Use modified voronoi_stippler to generate it.'
        )
    stipple_parser.add_argument(
        'idx_file',
        metavar='INDEX_FILE',
        help='File containing TSP indices in concorde format. Use concorde to solve the TSP problem.'
        )
    stipple_parser.add_argument(
        'out_file',
        metavar='OUT_FILE',
        help='File to write the result to. Currently only .svg output is supported. Gcode output will be supported soon.'
        )
    stipple_parser.add_argument(
        '--weight',
        metavar='WEIGHT_FILE',
        help='File containing weights for ealogger_ch point. Use modified voronoi_stippler to generate it.'
        )

    # define arguments for the 'p2l' (pixel2laser) subcommand
    p2l_parser = subparsers.add_parser(
        "pixel2laser",
        help="Generate optimized Gcode from PNG for laser.",
        epilog="EXAMPLE: python ./grbl_gui.py p2l ./data/pixel2laser.png p2l.ngc"
        )
    p2l_parser.add_argument(
        'in_file',
        metavar='IN_FILE',
        help='PNG file to be read. Other file formats have not been tested.'
        )
    p2l_parser.add_argument(
        'out_file',
        metavar='OUT_FILE',
        help='File to write the result to.'
        )

    # define arguments for the 'stream' subcommand
    stream_parser = subparsers.add_parser("stream", help="Streams a gcode file to GRBL.")
    stream_parser.add_argument(
        'dev_node',
        metavar='DEV_NODE',
        help='Interface node in /dev file system. E.g. /dev/ttyACM0'
        )
    stream_parser.add_argument(
        'gcodefile',
        metavar='GCODE_FILE',
        help='File to stream'
        )

    # define arguments for the 'bbox' subcommand
    bbox_parser = subparsers.add_parser("bbox", help="Calculates the bounding box of a gcode file")
    bbox_parser.add_argument(
        'gcodefile',
        metavar='GCODE_FILE',
        help='File to find the bounding box for'
        )


    # This parent parser provides args for infile and outfile for less repetition
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        'infile',
        metavar='GCODE_INFILE',
        help='File to read from'
        )
    parent_parser.add_argument(
        'outfile',
        metavar='GCODE_OUTFILE',
        help='File to write results to'
        )

    # define arguments for the 'translate' subcommand
    translate_parser = subparsers.add_parser("translate", help="Translates gcode by X, Y, Z offsets", parents=[parent_parser])
    translate_parser.add_argument(
        'offset_x',
        metavar='OFFSET_X',
        help='offset x'
        )
    translate_parser.add_argument(
        'offset_y',
        metavar='OFFSET_Y',
        help='offset y'
        )
    translate_parser.add_argument(
        'offset_z',
        metavar='OFFSET_Z',
        help='offset z'
        )


    # define arguments for the 'scale_factor' subcommand
    scalefactor_parser = subparsers.add_parser("scale_factor", help="Scales gcode by X, Y, Z factors", parents=[parent_parser])
    scalefactor_parser.add_argument(
        'scale_x',
        metavar='SCALE_X',
        help='scale x'
        )
    scalefactor_parser.add_argument(
        'scale_y',
        metavar='SCALE_Y',
        help='scale y'
        )
    scalefactor_parser.add_argument(
        'scale_z',
        metavar='SCALE_Z',
        help='scale z'
        )


    # define arguments for the 'scale_factor' subcommand
    scaleinto_parser = subparsers.add_parser("scale_into", help="Scales and translates gcode into a bbox specified by (0,0,-,width,height,depth)", parents=[parent_parser])
    scaleinto_parser.add_argument(
        'width',
        metavar='WIDTH',
        help='width in mm'
        )
    scaleinto_parser.add_argument(
        'height',
        metavar='HEIGHT',
        help='height mm'
        )
    scaleinto_parser.add_argument(
        'depth',
        metavar='DEPTH',
        help='depth in mm'
        )


    # define arguments for the 'scale' subcommand
    to_origin_parser = subparsers.add_parser("2origin", help="Moves bottom left extremity of gcode to (0,0), z remains unaffected", parents=[parent_parser])

    # define arguments for the 'gui' subcommand
    gui_parser = subparsers.add_parser("gui", help="Start GUI")
    gui_parser.add_argument(
        '--path',
        metavar='PATH',
        default='/dev/ttyACM0',
        help='e.g. /dev/ttyACM0'
        )

    gui_parser.add_argument(
        '--baud',
        metavar='BAUD',
        help='e.g. 9600',
        default=115200
        )

    args = parser.parse_args()

    if len(sys.argv) < 2:
        print("Please use the -h flag to see help")
        raise SystemExit

    subcmd = sys.argv[1]

    # after all arguments have been parsed, delegate
    if subcmd == "stipple":
        stipple.do(args.crd_file, args.idx_file, args.weight, args.out_file)

    elif subcmd == "pixel2laser":
        gcode = p2l.do(args.in_file)
        f = open(args.out_file, 'w')
        f.write(gcode)
        f.close()

    elif subcmd == "stream":
        grbl = GrblStreamer("grbl1", args.dev_node)
        grbl.cnect()
        time.sleep(1)
        src = "out.ngc"
        grbl.send(src)

    elif subcmd == "bbox":
        lines = utility.read_file_to_linearray(args.gcodefile)

        bbox = gcodetools.get_bbox(lines)
        print("BBOX: {}".format(bbox))

    elif subcmd == "translate":
        lines = utility.read_file_to_linearray(args.infile)
        result = gcodetools.translate(lines, [float(args.offset_x), float(args.offset_y), float(args.offset_z)])
        utility.write_file_from_linearray(result, args.outfile)

    elif subcmd == "scale_factor":
        lines = utility.read_file_to_linearray(args.infile)
        result = gcodetools.scale_factor(lines, [float(args.scale_x), float(args.scale_y), float(args.scale_z)], False)
        utility.write_file_from_linearray(result, args.outfile)

    elif subcmd == "scale_into":
        lines = utility.read_file_to_linearray(args.infile)
        result = gcodetools.scale_into(lines, float(args.width), float(args.height), float(args.depth), False)
        utility.write_file_from_linearray(result, args.outfile)

    elif subcmd == "2origin":
        lines = utility.read_file_to_linearray(args.infile)
        result = gcodetools.move_to_origin(lines)
        utility.write_file_from_linearray(result, args.outfile)

    elif subcmd == "gui":
        app = QApplication(sys.argv)
        #styles = [line.strip() for line in open("stylesheet.css")]
        #styles = " ".join(styles)
        #app.setStyleSheet(styles)
        window = MainWindow(args.path, int(args.baud))
        #ui = Ui_MainWindow()
        #ui.setupUi(window)
        #window = Window()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
