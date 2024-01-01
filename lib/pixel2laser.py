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

from PIL import Image
import math
import logging

def find_row_ranges(pix, width, height):
    '''
    Scans each pixel row and finds the index of the first and last
    non-white pixel as counted from the left and the right edge.
    It returns those indices and row direction in a list

    [[x_start1, x_end1, 1], [x_start2, x_end2, -1], ...]

    direction=1 means ltr, and -1 means rtl
    '''

    result = []

    # The direction alternates between -1 and 1 for each row.
    # We start going left to right
    direction = 1


    for cy in range(height):
        # bitmap origin is top left, but CNC origin is bottom left
        # so we scan the bitmap beginning with the last row
        y = height - cy - 1

        # by default we assume the row to be empty
        start_x = None
        end_x = None

        if direction == 1:
            # we are going ltr
            rng_start = range(0, width, 1)
            rng_end = range(width - 1, -1, -1)
        else:
            # we are going rtl
            rng_start = range(width - 1, -1, -1)
            rng_end = range(0, width, 1)

        # look for the first non-white start pixel
        for i in rng_start:
            if pix[i, y] != 255:
                start_x = i
                break

        # look for the first non-white end pixel
        for i in rng_end:
            if pix[i, y] != 255:
                end_x = i
                break

        if start_x is not None and end_x is not None:
            # increment/decrement start and end points by one
            start_x += -direction
            end_x += direction

            # limit start_x and end_x to the maximal extents of the bitmap
            if direction == 1:
                start_x = 0 if start_x < 0 else start_x
                end_x = width if end_x > width else end_x
            else:
                start_x = (width-1) if start_x > (width-1) else start_x
                end_x = -1 if end_x < -1 else end_x

        # alternate direction for next row
        direction *= -1

        #logging.info("Row range of row %s: start_x=%s end_x=%s direction=%i", cy, start_x, end_x, -direction)
        result.append([start_x, end_x, -direction])

    return result




def do(filename_in, dpmm=1, x_bleed=10, xcorr=0):
    # 300 dpi = 11.8 dpmm
    # 254 dpi = 10 dpmm (100µm pixels)
    # 127 dpi = 5 dpmm (200µm pixels)
    # 76.2 dpi = 3 dpmm (333µm pixels)
    logging.info("Opening image %s", filename_in)

    unit_length = 1 / dpmm

    # read bitmap and convert into grayscale ('L')
    im = Image.open(filename_in).convert('L')

    # contains grayscale values depending on pixel coordinates, lazy-loaded
    pix = im.load()

    width = im.size[0]
    height = im.size[1]
    logging.info("Image is %ix%i", width, height)

    row_ranges = find_row_ranges(pix, width, height)

    result = ""

    first_x = None
    first_y = None
    first_direction = None
    # find first x and y
    for j in range(len(row_ranges)):
        first_x = row_ranges[j][0]
        first_y = j
        first_direction = row_ranges[j][2]
        if first_x != None: break

    result += "S0\n"
    result += "G0 X{:f} Y{:f}\n".format(first_x * unit_length - first_direction * x_bleed, first_y * unit_length)
    result += "G0\n"
    result += "X{:f}\n".format(first_x * unit_length + xcorr * first_direction)

    last_x = first_x
    last_y = first_y
    last_z = 0
    last_s = 0

    for cy in range(height):
        start_x, end_x, direction = row_ranges[cy]

        # bitmap origin is top left, but CNC origin is bottom left
        # so we scan the bitmap beginning with the last row
        y = height - cy - 1

        # when going rtl we have to shift pixels by one
        x_shift = 1 if direction == 1 else 0

        if start_x is None and end_x is None:
            # this row only contains white pixels, nothing to do for this row
            continue

        #print("\n\n==========\nProcessing line", y, "start_x", start_x, "end_x", end_x, "direction", direction)

        for cx in range(start_x, end_x, direction):
            s = pix[cx, y] # get intensity from pixel
            s = 255 - s # invert, black pixels (0) are highest intensity (255) for laser

            #print(" Pixel", cx, pix[cx, y], 255 - pix[cx, y])

            if cx > 0 and cx < (width - 1) and pix[cx, y] == pix[cx + direction, y]:
                # This is gcode optimzation for consecutive pixels of the
                # same intensity. This reduces gcode lines, because gcode coordinates
                # remain in the state machine of the CNC controller.
                continue

            x = cx + x_shift

            new_x = x
            new_y = cy
            new_z = 0
            new_s = s

            gcodeline = ""
            # Only write changes to coords
            x2 = new_x * unit_length + direction * xcorr
            y2 = new_y * unit_length
            z2 = new_z * unit_length
            if last_x != new_x: gcodeline += "X{:g} ".format(x2)
            if last_y != new_y: gcodeline += "Y{:g} ".format(y2)
            if last_z != new_z: gcodeline += "Z{:g} ".format(z2)
            if last_s != new_s: gcodeline += "S{:g} ".format(new_s)
            gcodeline += "\n"
            result += gcodeline

            last_x = new_x
            last_y = new_y
            last_z = new_z
            last_s = new_s

        # After lasering the last pixel, continue going into the same direction for
        # the distance of x_bleed, so that GRBL's inertia control doesn't slow down
        # the movement. Lasering should be done at constant speed for constant
        # burning (non-distorted grayscale) of material.
        # For this, we have to look ahead at the x_start and x_end of the next row.
        nxs = None # next x_start
        nxe = None # next x_end
        ny = None # next y
        nd = None # next direction

        for j in range(cy + 1, height):
            # find the next non-empty row
            nxs, nxe, dctn = row_ranges[j]
            if nxs is not None and nxe is not None:
                # found next y!
                ny = j
                ndir = dctn
                break

        if nxs is None and nxe is None:
            # no non-empty lines were found, so nothing more to do
            continue

        # which line has the furthest x coordinate? current row or the next row?
        if direction == 1:
            furthest_x = nxs if nxs > last_x else last_x
        else:
            furthest_x = nxs if nxs < last_x else last_x

        middle_y = last_y + (ny - last_y) / 2

        x_clear = unit_length * furthest_x + (direction * x_bleed)

        # below we are going to draw approximately tangential circles to ease out the current X movement without any significant y movement at the beginning of the circle.

        arcmode = 3 if direction == 1 else 2

        # The following code is based on trial-and-error which leads to good results
        # in the GRBL simulator. Circles could be made exactly tangential to the
        # pixel rows, but I require more arc gcode studying.
        radius_factor = 7
        if direction == 1:
            arc_radius_out = radius_factor * (x_clear - last_x) * unit_length
            arc_radius_in = radius_factor * (x_clear - nxs) * unit_length
        else:
            arc_radius_out = radius_factor * (last_x - x_clear) * unit_length
            arc_radius_in = radius_factor * (nxs - x_clear) * unit_length

        #result += "G{:g} X{:g} Y{:g} R{:f} S0\n".format(arcmode, x_clear, middle_y * unit_length, arc_radius_out * unit_length)
        #result += "G{:g} X{:g} Y{:g} R{:f} S0\n".format(arcmode, (nxs + direction) * unit_length, ny * unit_length, arc_radius_in * unit_length)
        result += ";_gerbil bleed begin\n"
        result += "G0 X{:g} Y{:g} S0\n".format(x_clear, middle_y * unit_length)
        offset = 1 if direction == 1 else 0
        result += "G0 X{:g} Y{:g} S0\n".format(direction * xcorr + (nxs + offset) * unit_length, ny * unit_length)
        result += ";_gerbil bleed end\n"

        last_s = None # invalidate last S for next row processing
        last_x = None # invalidate last X for next row processing

        result += "G1\n"


    # gcode postamble
    out_x = float(unit_length * last_x + direction * x_bleed)
    result += "G0 X{:f} S0\n".format(out_x) # last easing out movement

    return result.split('\n')
