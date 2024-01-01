#!/usr/bin/python

import logging
from classes.svg import SVG

def do(crd_file, idx_file, wgt_file, out_file):
    coords_unsorted = read_coords(crd_file)
    sort_indices = read_sort_indices(idx_file)
    if wgt_file:
        weights_unsorted = read_weights(wgt_file)
        
    data = merge_and_sort_data(sort_indices, coords_unsorted, weights_unsorted)
        
    if ".svg" in out_file:
        svg = SVG("mysvg", out_file)
        svg.draw_from_data(data, False)
        svg.save()
    elif ".ngc" in out_file:
        render_gcode_from_data(data, out_file)
    else:
        print("Only supporting .svg output at the moment")


def render_gcode_from_data(data, out_file):
    logging.info("NGC: draw_from_data")
    with open(out_file, "w") as f:
        f.write("G90 ; absolute positioning\n")
        f.write("F400; _globalfeed\n")
        f.write("G0 Z0.5 ; _zclear\n")
        for idx, val in enumerate(data):
            x = val[0]
            y = val[1]
            r = val[2]
            f.write("G0 X{:0.2f} Y{:0.2f}\n".format(x, 3000 - y)) # position
            f.write("G1 Z-{:0.2f}\n".format(r))
            f.write("G0 Z0.5 ; _zclear\n")
    
def merge_and_sort_data(sort_indices, coords_unsorted, weights_unsorted):
    logging.info("Sorting coords")
    data = []
    for i in sort_indices:
        data.append(coords_unsorted[i] + (weights_unsorted[i],))
    return data


def read_sort_indices(filename_solution):
    logging.info("Reading solution file %s", filename_solution)
    sort_indices = []
    with open(filename_solution) as f:
        next(f) # skip the first line which contains the index length
        for line in f:
            indices = map(int, line.strip().split(" "))
            sort_indices.append(indices)
        
    return [item for sublist in sort_indices for item in sublist]


def read_weights(filename_weights):
    logging.info("Reading weight file %s", filename_weights)
    f = open(filename_weights)
    weights = []
    for line in f:
        idx, w = line.strip().split(' ')
        weights.append(float(w))
        
    return weights
    
    
def read_coords(filename_coord):
    '''
    read the coordinates from file
    coords are stored in concorde format
    '''
    logging.info("Reading coord file %s", filename_coord)
    f = open(filename_coord)
    
    coords=[]
    state_coords = False
    for line in f:
        if "NODE_COORD_SECTION" in line:
          state_coords = True
          continue
        if "EOF" in line:
          state_coords = False
        if state_coords == True:
          i, x, y = line.strip().split(' ')
          coords.append((float(x), float(y)))
    return coords