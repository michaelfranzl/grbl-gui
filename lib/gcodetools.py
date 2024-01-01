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

import logging
import re
import math

from scipy.interpolate import griddata

from . import hersheydata


def read(fname):
    with open(fname, 'r') as f:
        return [l.strip() for l in f.readlines()]

def write(fname, contents):
    with open(fname, 'w') as f:
        f.write(contents)

def to_origin(gcode):
    bb = bbox(gcode)
    xmin = bb[0][0]
    ymin = bb[1][0]
    translated_gcode = translate(gcode, [-xmin, -ymin, 0])
    return translated_gcode

def scale_into(gcode, width, height, depth, scale_zclear=False):
    bb = bbox(gcode)
    xmin = bb[0][0]
    xmax = bb[0][1]
    ymin = bb[1][0]
    ymax = bb[1][1]
    zmin = bb[2][0]
    zmax = bb[2][1]
    translated_gcode = translate(gcode, [-xmin, -ymin, 0])

    if width > 0:
        w = xmax - xmin
        fac_x = width / w
        fac_y = fac_x
        fac_z = fac_x

    if height > 0:
        h = ymax - ymin
        fac_y = height / h

    if depth > 0:
        d = zmax - zmin
        fac_z = depth / d

    scaled_gcode = scale_factor(translated_gcode, [fac_x, fac_y, fac_z], scale_zclear)
    return scaled_gcode

# returns string
def bbox_draw(gcode, move_z=False):
    result = ""

    bb = bbox(gcode)
    xmin = bb[0][0]
    xmax = bb[0][1]
    ymin = bb[1][0]
    ymax = bb[1][1]
    zmin = bb[2][0]
    zmax = bb[2][1]

    if move_z:
        pass

    result += "G0X{:0.1f}Y{:0.1f}\n".format(xmin, ymin)
    result += "M0\n"

    result += "G0X{:0.1f}\n".format(xmax)
    result += "M0\n"

    result += "G0Y{:0.1f}\n".format(ymax)
    result += "M0\n"

    result += "G0X{:0.1f}\n".format(xmin)
    result += "M0\n"

    result += "G0Y{:0.1f}\n".format(ymin)
    result += "M0\n"

    return result


# returns list
def translate(lines, offsets=[0, 0, 0]):
    logger = logging.getLogger('gerbil')

    result = []

    axes = ["X", "Y", "Z"]
    contains_regexps = []
    replace_regexps = []
    for i in range(0, 3):
        axis = axes[i]
        contains_regexps.append(re.compile(".*" + axis + "([-.\d]+)"))
        replace_regexps.append(re.compile(r"" + axis + "[-.\d]+"))

    for line in lines:

        if "G91" in line:
            logger.error("gcodetools.translate: It does not make sense to translate movements in G91 distance mode. Aborting at line {}".format(line))
            return

        for i in range(0, 3):
            axis = axes[i]
            cr = contains_regexps[i]
            rr = replace_regexps[i]
            ofst = offsets[i]

            m = re.match(cr, line)
            if m and offsets[i] != 0:
                a = float(m.group(1))
                a += ofst
                rep = "{}{:0.3f}".format(axis, a)
                rep = rep.rstrip("0").rstrip(".")
                line = re.sub(rr, rep, line)

        result.append(line)
    return result


def rotate2D(lines, anchor, angle):

    angle = math.radians(angle)

    result = []
    _re_motion_mode = re.compile("(G[0123])([^\d]|$)")
    _current_motion_mode = None

    re_allcomments_remove = re.compile(";.*")

    words = ["X", "Y", "I", "J"]
    contains_regexps = []
    replace_regexps = []
    for i in range(0, 3):
        word = words[i]
        contains_regexps.append(re.compile(".*" + word + "([-.\d]+)"))
        replace_regexps.append(re.compile(r"" + word + "[-.\d]+"))

    x = 0
    y = 0
    for line in lines:
        line = re.sub(re_allcomments_remove, "", line) # replace comments

        m = re.match(_re_motion_mode, line)
        if m:
            _current_motion_mode = m.group(1)

        match_x = re.match(contains_regexps[0], line)
        if match_x:
            x = float(match_x.group(1))

        match_y = re.match(contains_regexps[1], line)
        if match_y:
            y = float(match_y.group(1))

        rot_x = math.cos(angle) * (x-anchor[0]) - math.sin(angle) * (y-anchor[1]) + anchor[0]
        rot_y = math.sin(angle) * (x-anchor[0]) + math.cos(angle) * (y-anchor[1]) + anchor[1]

        rep_x = "X{:0.3f}".format(rot_x)
        rep_y = "Y{:0.3f}".format(rot_y)

        rep_x = rep_x.rstrip("0").rstrip(".")
        rep_y = rep_y.rstrip("0").rstrip(".")

        line = re.sub(replace_regexps[0], rep_x, line)
        line = re.sub(replace_regexps[1], rep_y, line)

        if not match_x: line += rep_x
        if not match_y: line += rep_y

        result.append(line)
    return result



# returns list
def scale_factor(lines, facts=[1, 1, 1], scale_zclear=False):
    result = []

    logger = logging.getLogger('gerbil')

    if facts[0] != facts[1] or facts[0] != facts[2] or facts[1] != facts[2]:
        logger.warning("gcodetools.scale_factor: Circles will stay circles even with inhomogeous scale factor ".format(facts))

    _re_motion_mode = re.compile("(G[0123])([^\d]|$)")
    _current_motion_mode = None

    words = ["X", "Y", "Z", "I", "J", "K", "R"]
    contains_regexps = []
    replace_regexps = []
    for i in range(0, 7):
        word = words[i]
        contains_regexps.append(re.compile(".*" + word + "([-.\d]+)"))
        replace_regexps.append(re.compile(r"" + word + "[-.\d]+"))

    for line in lines:
        for i in range(0, 7):
            m = re.match(_re_motion_mode, line)
            if m:
                _current_motion_mode = m.group(1)

            word = words[i]
            cr = contains_regexps[i]
            rr = replace_regexps[i]
            factor = facts[(i % 3)]

            m = re.match(cr, line)
            if m and facts[i % 3] != 0 and not ("_zclear" in line and scale_zclear == False):
                val = float(m.group(1))
                val *= factor
                rep = "{}{:0.3f}".format(word, val)
                rep = rep.rstrip("0").rstrip(".")
                line = re.sub(rr, rep, line)

        result.append(line)
    return result


# returns list
def bbox(gcode):
    bb = []

    axes = ["X", "Y", "Z"]
    contains_regexps = []

    for i in range(0, 3):
        axis = axes[i]
        contains_regexps.append(re.compile(".*" + axis + "([-.\d]+)"))
        bb.append([9999, -9999])

    for line in gcode:
        for i in range(0, 3):
            axis = axes[i]
            cr = contains_regexps[i]
            m = re.match(cr, line)
            if m:
                a = float(m.group(1))
                min = bb[i][0]
                max = bb[i][1]
                min = a if a < min else min
                max = a if a > max else max
                bb[i][0] = min
                bb[i][1] = max
    return bb



def bumpify(gcode_list, cwpos, probe_points, probe_values):
    print("bumpify start")
    logger = logging.getLogger('gerbil')

    position = list(cwpos)

    axes = ["X", "Y", "Z"]
    re_allcomments_remove = re.compile(";.*")
    re_axis_values = []
    re_axis_replace = []

    # precompile regular expressions for speed increase
    for i in range(0, 3):
        axis = axes[i]
        re_axis_values.append(re.compile(".*" + axis + "([-.\d]+)"))
        re_axis_replace.append(re.compile(r"" + axis + "[-.\d]+"))

    # first, collect xy coords per line, because all of them will be interpolated at once
    coords_xy = [None]*len(gcode_list)
    for nr in range(0, len(gcode_list)):
        line = gcode_list[nr]
        line = re.sub(re_allcomments_remove, "", line) # replace comments

        if "G91" in line:
            logger.error("gcodetools.bumpify: G91 distance mode is not supported. Aborting at line {}".format(line))
            return

        if re.match("G(5[4-9]).*", line):
            logger.error("gcodetools.bumpify: Switching coordinate systems is not supported. Aborting at line {}".format(line))
            return

        for i in range(0, 2): # only loop over x and y
            axis = axes[i]
            rv = re_axis_values[i]
            m = re.match(rv, line)
            if m:
                a = float(m.group(1))
                position[i] = a

        coords_xy[nr] = [position[0], position[1]]

    #print("parsed coords", coords_xy)


    print("bumpify interpol")

    # see http://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.griddata.html
    interpolated_z = griddata(
        probe_points,
        probe_values,
        coords_xy,
        method='cubic')

    z_at_xy_origin = griddata(
        probe_points,
        probe_values,
        [0,0],
        method='cubic')[0]

    #print("interpolated", interpolated_z)

    # next add/substitute Z values
    current_z = cwpos[2]
    for nr in range(0, len(gcode_list)):
        line = gcode_list[nr]
        line = re.sub(re_allcomments_remove, "", line) # remove comments

        axis = axes[2]
        rv = re_axis_values[2]
        rr = re_axis_replace[2]
        m = re.match(rv, line)
        if m:
            # contains Z, replace
            current_z = float(m.group(1))
            new_z = current_z + interpolated_z[nr] - z_at_xy_origin
            rep = "{}{:0.3f}".format(axis, new_z)
            rep = rep.rstrip("0").rstrip(".")
            line = re.sub(rr, rep, line)
        elif "X" in line or "Y" in line:
            # add Z
            new_z = current_z + interpolated_z[nr] - z_at_xy_origin
            line += "{}{:0.3f}".format(axis, new_z)

        gcode_list[nr] = line

    #print("FINI", gcode_list)
    print("bumpify done")
    return gcode_list



"""
Fonts available in hershedata.py:

standard    Standard

futural     Sans 1-stroke
futuram     Sans bold

gothiceng   Gothic English
gothicger   Gothic German
gothicita   Gothic Italian

greek       Greek 1-stroke
timesg      Greek medium
japanese    Japanese
cyrillic    Cyrillic

astrology   Astrology
markers     Markers
mathlow     Math (lower)
mathupp     Math (upper)
meteorology Meteorology
music       Music
symbolic    Symbolic

cursive     Script 1-stroke (alt)
scriptc     Script medium
scripts     Script 1-stroke

timesi      Serif medium italic
timesib     Serif bold italic
timesr      Serif medium
timesrb     Serif bold
"""

def hersheyToGcode(string, font='standard', z_depth=0, z_safe=3):
    fontdata = eval('hersheydata.' + font)

    #regexp = re.compile("([ML].+?)")

    letter_vals = [ord(q) - 32 for q in string]

    gcodelist = []
    offset_x = 0

    for i in letter_vals:
        # Ignore unavailable Letters except german umlaute
        #if (q == 164 or q == 182 or q == 188 or q == 191 or q == 196 or q == 214 or q == 220 or 0 <= q < 93):
        char_path = fontdata[i]

        size_match = re.match('^([-0-9.]+) ([-0-9.]+)', char_path)
        size1 = float(size_match.groups(0)[0])
        size2 = float(size_match.groups(0)[1])
        print("SIZE", size1, size2)


        offset_x -= size1

        parts = re.findall('[ML][-0-9. ]+', char_path)
        current_motion_mode = None
        for cmd in parts:
            gcode = ""

            m = re.match('([ML]) ([-0-9.]+) ([-0-9.]+)', cmd)
            print(m, m.groups(0))
            mm = m.groups(0)[0]
            x = float(m.groups(0)[1])
            y = float(m.groups(0)[2])

            if mm == "M":
                if current_motion_mode != 0:
                    if z_depth != 0:
                        g_z_safe = "G0S0Z{}; z_safe".format(z_safe)
                        gcodelist.append(g_z_safe)

                    gcode += "G0S0"
                current_motion_mode = 0

            else:
                if current_motion_mode != 1:
                    if z_depth != 0:
                        g_plunge = "G1Z{}; plunge".format(z_depth)
                        gcodelist.append(g_plunge)

                    gcode += "G1S255"
                current_motion_mode = 1

            mv_x = "X{:0.3f}".format(x + offset_x)
            mv_x = mv_x.rstrip("0").rstrip(".")
            gcode += mv_x

            mv_y = "Y{:0.3f}".format(-y)
            mv_y = mv_y.rstrip("0").rstrip(".")
            gcode += mv_y

            gcodelist.append(gcode)

        offset_x += size2
    return gcodelist



if __name__ == "__main__":
    rotated = []
    gcode = ["G0X0Y0", "G1X100", "G1Y20"]
    for angle in range(0, 95, 5):
        rotated += rotate2D(gcode, [20,10], math.radians(angle))
    with open('/tmp/test.ngc', 'w') as f: f.write("\n".join(rotated))


