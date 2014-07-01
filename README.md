# Debug utils for OSRM

## RTree

Export the bounding boxes and geometries of an rtree to geojson and display them on leaflet.

Requires Python 3.

	./rtree2geojson.py data.fileIndex data.ramIndex data.nodes input.json

Open main.html to display the data.

## FileGuard

*WARNING* This runs osrm-datastore which might interfere with running OSRM instances!

Runs all osrm tools and checks all files that are touched against a whitelist.

This guards against debugging files that could blow up the production servers.

