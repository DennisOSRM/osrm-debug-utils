#!/usr/bin/env python3

import json
import struct
import sys
import random

LEAF_NODE_SIZE   = 1024
BRANCHING_FACTOR = 64
COORDINATE_PRECISION = 1000000.0;
NUM_SAMPLES = 0

edgedata = "4I I 4i I H ??"
edgesize = struct.calcsize(edgedata)
leafnode = "I %is" % (edgesize * LEAF_NODE_SIZE)
leafsize = struct.calcsize(leafnode)
nodeinfo = "iiI"
nodeinfosize = struct.calcsize(nodeinfo)
treenode = "iiiiI%iI" % BRANCHING_FACTOR
treenodesize = struct.calcsize(treenode)
print(treenodesize)

def parseLeaf(leaf, num_edges):
    offset = 0
    edges = []
    for i in range(num_edges):
        subdata = leaf[offset:offset+edgesize]
        edge = struct.unpack(edgedata, subdata)
        edges.append((edge[2], edge[3]))
        offset += edgesize
    return edges

def readLeaves(data):
    num_elements = struct.unpack("Q", data[0:8])[0]
    print("Number of elements: %i " % num_elements)
    num_leaves = num_elements // LEAF_NODE_SIZE
    if num_elements % LEAF_NODE_SIZE != 0:
        num_leaves += 1
    print("Number of leaves: %i " % num_leaves)
    leaves = []
    offset = 8
    for i in range(num_leaves):
        subdata = data[offset:offset+leafsize]
        leaf = struct.unpack(leafnode, subdata)
        leaves.append(parseLeaf(leaf[1], leaf[0]))
        offset += leafsize
    return leaves

def readNodes(data):
    num_nodes = struct.unpack("I", data[0:4])[0]
    offset = 4
    nodes = []
    for i in range(num_nodes):
        subdata = data[offset:offset+nodeinfosize]
        node = struct.unpack(nodeinfo, subdata)
        nodes.append((node[1]/COORDINATE_PRECISION, node[0]/COORDINATE_PRECISION))
        offset += nodeinfosize
    return nodes

def readBoundingBoxes(data):
    num_bb = struct.unpack("I", data[0:4])[0]
    print(num_bb)
    offset = 4
    bbs = []
    for i in range(num_bb):
        subdata = data[offset:offset+treenodesize]
        t = struct.unpack(treenode, subdata)
        num_children = t[4]
        is_leaf_bb = (num_children & 0x80000000) != 0
        num_children = num_children & 0x7FFFFFFF
        if is_leaf_bb:
            num_children += 1
        children = t[5:5+num_children]
        min_lon, max_lon, min_lat, max_lat = [c / COORDINATE_PRECISION for c in t[:4]]
        bb = [[min_lon, min_lat], [max_lon, min_lat], [max_lon, max_lat], [min_lon, max_lat]]
        bbs.append((i, is_leaf_bb, children, bb))
        offset += treenodesize
    return bbs

def toGeoJSON(leaves, nodes, bbs):
    j = {'type': "FeatureCollection"}
    features = []
    for i, l in enumerate(leaves):
        for u, v in random.sample(l, min(NUM_SAMPLES, len(l))):
            f = {'type': "Feature",
                 'geometry': {
                 'type': "LineString",
                 'coordinates': [nodes[u], nodes[v]]
                 },
                'properties': {'leaf_id': i, 'is_data': True, 'edge': [u, v]},
               }
            features.append(f)
    for bb in bbs:
        f = {'type': "Feature",
             'geometry': {
             'type': "Polygon",
             'coordinates': [bb[3]]
             },
             'properties': {
                'id': bb[0],
                'is_leaf': bb[1],
                'children': bb[2]
             }
            }
        features.append(f)
    j['features'] = features
    geojson = "var geojson = " + json.dumps(j) + ";"
    return geojson

leaves_filename = sys.argv[1]
leaves = []
with open(leaves_filename, "rb") as f:
    data = f.read()
    leaves = readLeaves(data)

nodes_filename = sys.argv[2]
nodes = []
with open(nodes_filename, "rb") as f:
    data = f.read()
    nodes = readNodes(data)

bbs_filename = sys.argv[3]
bbs = []
with open(bbs_filename, "rb") as f:
    data = f.read()
    bbs = readBoundingBoxes(data)

geojson = toGeoJSON(leaves, nodes, bbs)
output_filename = sys.argv[4]
with open(output_filename, "w+") as f:
    f.write(geojson)
