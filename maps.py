#!/usr/bin/python
# coding=utf8
# Copyright © 2014 Emily Maier
# Generates the maps of districts and election results.

import json
import mapnik
import multiprocessing
import ppygis
import psycopg2
import sys

# Set the correct bounding box for Alaska.
def normalize_alaska(bbox):
	bbox.rings[0].points[0].x = float(-163.5)
	bbox.rings[0].points[0].y = float(52.5)
	bbox.rings[0].points[2].x = float(-136)
	bbox.rings[0].points[2].y = float(71.5)
	return bbox

# Set the correct bounding box for Hawaii (and its 2nd district).
def normalize_hawaii(bbox):
	bbox.rings[0].points[0].x = float(-160.5)
	bbox.rings[0].points[0].y = float(18.75)
	bbox.rings[0].points[2].x = float(-154.5)
	bbox.rings[0].points[2].y = float(22.5)
	return bbox

# Prevent the aspect ratio of the map from exceeding the golden ratio.
def normalize_ratio(ratio):
	if ratio > 1.272:
		return 1.272
	if ratio < 0.786:
		return 0.786
	return ratio

# Finds the layer with the given name in the map and returns its index.
def layer_index(map, name):
	for index in range(len(map.layers)):
		if map.layers[index].name == name:
			return index
	return -1

json_input = open("stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()
state_fips = dict(zip(config_data["states"], config_data["fips"]))

# Subprocess that generates district and state maps. Receives tasks giving a
# state and election year to generate.
def map_thread(queue):
	map_state_small = mapnik.Map(600, 600)
	mapnik.load_map(map_state_small, "map-config/state-small.xml")
	map_state_large = mapnik.Map(2000, 2000)
	mapnik.load_map(map_state_large, "map-config/state-large.xml")
	map_small = mapnik.Map(600, 600)
	mapnik.load_map(map_small, "map-config/district-small.xml")
	map_large = mapnik.Map(2000, 2000)
	mapnik.load_map(map_large, "map-config/district-large.xml")

	pg_conn = psycopg2.connect(database="gis")
	pg_cursor = pg_conn.cursor()

	while True:
		current_task = queue.get()
		congress = current_task[0]
		state = current_task[1]
		district_count = current_task[2]
		quit = current_task[3]
		if quit:
			sys.exit(0)

		# set the datasources needed for this state
		districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d join results on parse_district(districts%d.district) = results.district and districts%d.statename = '%s' and results.year = %d and results.state = '%s' and results.winner = 'Republican') multipolygon" % (congress, congress, congress, state, congress * 2 + 1786, state))
		dr_index = layer_index(map_state_small, "districts republican")
		map_state_small.layers[dr_index].datasource = districts_datasource
		map_state_large.layers[dr_index].datasource = districts_datasource
		districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d join results on parse_district(districts%d.district) = results.district and districts%d.statename = '%s' and results.year = %d and results.state = '%s' and results.winner = 'Democrat') multipolygon" % (congress, congress, congress, state, congress * 2 + 1786, state))
		dd_index = layer_index(map_state_small, "districts democrat")
		map_state_small.layers[dd_index].datasource = districts_datasource
		map_state_large.layers[dd_index].datasource = districts_datasource
		districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d join results on parse_district(districts%d.district) = results.district and districts%d.statename = '%s' and results.year = %d and results.state = '%s' and results.winner != 'Republican' and results.winner != 'Democrat') multipolygon" % (congress, congress, congress, state, congress * 2 + 1786, state))
		di_index = layer_index(map_state_small, "districts independent")
		map_state_small.layers[di_index].datasource = districts_datasource
		map_state_large.layers[di_index].datasource = districts_datasource
		districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d where statename = '%s') multipolygon" % (congress, state))
		d_index = layer_index(map_small, "districts")
		map_small.layers[d_index].datasource = districts_datasource
		map_large.layers[d_index].datasource = districts_datasource
		state_datasource = mapnik.PostGIS(dbname="gis", table="(select ST_Intersection(wkb_geometry, !bbox!) as wkb_geometry, name from simplified where name != '%s') multipolygon" % state, srid=4269)
		s_index = layer_index(map_state_small, "state labels")
		map_state_small.layers[s_index].datasource = state_datasource
		map_state_large.layers[s_index].datasource = state_datasource
		s_index = layer_index(map_small, "state labels")
		map_small.layers[s_index].datasource = state_datasource
		map_large.layers[s_index].datasource = state_datasource
		place_datasource = mapnik.PostGIS(dbname="gis", table="(select wkb_geometry, name from places where pcicbsa = 'Y' and statefp = '%s' order by aland desc limit 3) multipolygon" % state_fips[state])
		cp_index = layer_index(map_state_small, "city polygons")
		map_state_small.layers[cp_index].datasource = place_datasource
		cl_index = layer_index(map_state_small, "city labels")
		map_state_small.layers[cl_index].datasource = place_datasource

		# generate the state maps
		pg_cursor.execute("select ST_Envelope(wkb_geometry) from states where name = '%s'" % state)
		pg_record = pg_cursor.fetchone()
		pg_conn.rollback()
		state_bbox = ppygis.Geometry.read_ewkb(pg_record[0])
		if state == "Alaska":
			state_bbox = normalize_alaska(state_bbox)
		if state == "Hawaii":
			state_bbox = normalize_hawaii(state_bbox)
		state_width = state_bbox.rings[0].points[2].x - state_bbox.rings[0].points[0].x
		state_height = state_bbox.rings[0].points[2].y - state_bbox.rings[0].points[0].y
		state_ratio = state_width / state_height
		if state != "Alaska":
			state_ratio = normalize_ratio(state_ratio)

		map_state_small.resize(int(600 * state_ratio), int(600 / state_ratio))
		map_state_small.zoom_to_box(mapnik.Box2d(state_bbox.rings[0].points[0].x, state_bbox.rings[0].points[0].y, state_bbox.rings[0].points[2].x, state_bbox.rings[0].points[2].y))
		if state != "Alaska" and state != "Hawaii":
			map_state_small.zoom(-1.5)
		filename = "/var/lib/house/%d%s-small.jpeg" % (congress, str(state))
		mapnik.render_to_file(map_state_small, filename, "jpeg")
		print filename

		map_state_large.resize(int(2000 * state_ratio), int(2000 / state_ratio))
		map_state_large.zoom_to_box(mapnik.Box2d(state_bbox.rings[0].points[0].x, state_bbox.rings[0].points[0].y, state_bbox.rings[0].points[2].x, state_bbox.rings[0].points[2].y))
		if state != "Alaska" and state != "Hawaii":
			map_state_large.zoom(-1.5)
		filename = "/var/lib/house/%d%s.jpeg" % (congress, str(state))
		mapnik.render_to_file(map_state_large, filename, "jpeg")
		print filename

		# begin district maps here
		for district in range(1, district_count + 1):
			if congress == 113:
				if district_count == 1:
					district_gis = '00'
				else:
					district_gis = '%02d' % district
			else:
				if district_count == 1:
					district_gis = '0'
				else:
					district_gis = '%d' % district

			district_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d where statename = '%s' and district = '%s') multipolygon" % (congress, state, district_gis))
			d_index = layer_index(map_small, "current district")
			map_small.layers[d_index].datasource = district_datasource
			map_large.layers[d_index].datasource = district_datasource

			pg_cursor.execute("select ST_Envelope(wkb_geometry) from districts%d where statename = '%s' and district = '%s'" % (congress, state, district_gis))
			pg_record = pg_cursor.fetchone()
			pg_conn.rollback()
			district_bbox = ppygis.Geometry.read_ewkb(pg_record[0])
			if state == "Alaska":
				district_bbox = normalize_alaska(district_bbox)
			if state == "Hawaii" and district == 2:
				district_bbox = normalize_hawaii(district_bbox)
			district_width = district_bbox.rings[0].points[2].x - district_bbox.rings[0].points[0].x
			district_height = district_bbox.rings[0].points[2].y - district_bbox.rings[0].points[0].y
			district_ratio = district_width / district_height
			if state != "Alaska":
				district_ratio = normalize_ratio(district_ratio)

			map_small.resize(int(600 * district_ratio), int(600 / district_ratio))
			map_small.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
			if state != "Alaska" and (state != "Hawaii" or district != 2):
				map_small.zoom(-1.5)
			if map_small.scale() < 0.0006:
				map_small.zoom(-0.0006 / map_small.scale())
			filename = "/var/lib/house/%d%s%d-small.jpeg" % (congress, str(state), district)
			mapnik.render_to_file(map_small, filename, "jpeg")
			print filename

			map_large.resize(int(2000 * district_ratio), int(2000 / district_ratio))
			map_large.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
			if state != "Alaska" and (state != "Hawaii" or district != 2):
				map_large.zoom(-1.5)
			if map_large.scale() < 0.0006:
				map_large.zoom(-0.0006 / map_large.scale())
			filename = "/var/lib/house/%d%s%d.jpeg" % (congress, str(state), district)
			mapnik.render_to_file(map_large, filename, "jpeg")
			print filename

national_ratio = 1.525
map_national_small = mapnik.Map(int(600 * national_ratio), int(600 / national_ratio))
mapnik.load_map(map_national_small, "map-config/national.xml")
map_national_large = mapnik.Map(int(2000 * national_ratio), int(2000 / national_ratio))
mapnik.load_map(map_national_large, "map-config/national.xml")
national_box = mapnik.Box2d(-125, 29, -66.5, 45)
map_national_small.zoom_to_box(national_box)
map_national_large.zoom_to_box(national_box)

queue = multiprocessing.Queue()

threads = []
for i in range(4):
	threads.append(multiprocessing.Process(target=map_thread, args=(queue,)))
	threads[i].start()

for congress in range(106, 114):
	i = 0
	for state in config_data["states"]:
		if congress == 106 or congress == 107:
			district_count = config_data["apportionment_1992"][i]
		elif congress >= 108 and congress < 113:
			district_count = config_data["apportionment_2002"][i]
		else:
			district_count = config_data["apportionment_2012"][i]
		i += 1
		queue.put((congress, state, district_count, False))

	# the main process generates the national maps itself
	districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d join results on parse_district(districts%d.district) = results.district and districts%d.statename = results.state and results.year = %d and results.winner = 'Republican') multipolygon" % (congress, congress, congress, congress * 2 + 1786))
	dr_index = layer_index(map_national_small, "districts republican")
	map_national_small.layers[dr_index].datasource = districts_datasource
	map_national_large.layers[dr_index].datasource = districts_datasource
	districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d join results on parse_district(districts%d.district) = results.district and districts%d.statename = results.state and results.year = %d and results.winner = 'Democrat') multipolygon" % (congress, congress, congress, congress * 2 + 1786))
	dd_index = layer_index(map_national_small, "districts democrat")
	map_national_small.layers[dd_index].datasource = districts_datasource
	map_national_large.layers[dd_index].datasource = districts_datasource
	districts_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d join results on parse_district(districts%d.district) = results.district and districts%d.statename = results.state and results.year = %d and results.winner != 'Republican' and results.winner != 'Democrat') multipolygon" % (congress, congress, congress, congress * 2 + 1786))
	di_index = layer_index(map_national_small, "districts independent")
	map_national_small.layers[di_index].datasource = districts_datasource
	map_national_large.layers[di_index].datasource = districts_datasource
	filename = "/var/lib/house/%d-small.jpeg" % congress
	mapnik.render_to_file(map_national_small, filename)
	print filename
	filename = "/var/lib/house/%s.jpeg" % congress
	mapnik.render_to_file(map_national_large, filename)
	print filename

# kill the subprocesses
for i in range(4):
	queue.put((0, "", 0, True))
