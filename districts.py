#!/usr/bin/python

import json
import mapnik
import multiprocessing
import ppygis
import psycopg2
import sys

json_input = open("stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()

def map_thread(queue):
	map_small = mapnik.Map(600, 600)
	mapnik.load_map(map_small, "map-small.xml")
	map_large = mapnik.Map(2000, 2000)
	mapnik.load_map(map_large, "map-large.xml")

	pg_conn = psycopg2.connect(database="gis")
	pg_cursor = pg_conn.cursor()

	while True:
		current_task = queue.get()
		congress = current_task[0]
		state = current_task[1]
		district = current_task[2]
		district_gis = current_task[3]
		quit = current_task[4]
		if quit:
			sys.exit(0)

		map_small.layers[5].datasource = mapnik.PostGIS(dbname="gis", table="districts%d" % congress) # districts
		map_large.layers[5].datasource = mapnik.PostGIS(dbname="gis", table="districts%d" % congress)
		state_datasource = mapnik.PostGIS(dbname="gis", table="(select ST_Intersection(wkb_geometry, !bbox!) as wkb_geometry, name from simplified where name != '%s') multipolygon" % state, srid=4269)
		map_small.layers[8].datasource = state_datasource # state labels
		map_large.layers[8].datasource = state_datasource
		district_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d where statename = '%s' and district = '%s') multipolygon" % (congress, state, district_gis))
		map_small.layers[7].datasource = district_datasource # current district
		map_large.layers[7].datasource = district_datasource

		pg_cursor.execute("select ST_Envelope(wkb_geometry) from districts%d where statename = '%s' and district = '%s'" % (congress, state, district_gis))
		pg_record = pg_cursor.fetchone()
		pg_conn.rollback()
		district_bbox = ppygis.Geometry.read_ewkb(pg_record[0])
		if state == "Alaska":
			district_bbox.rings[0].points[0].x = float(-163.5)
			district_bbox.rings[0].points[0].y = float(52.5)
			district_bbox.rings[0].points[2].x = float(-136)
			district_bbox.rings[0].points[2].y = float(71.5)
		if state == "Hawaii" and district == 2:
			district_bbox.rings[0].points[0].x = float(-160.5)
			district_bbox.rings[0].points[0].y = float(18.75)
			district_bbox.rings[0].points[2].x = float(-154.5)
			district_bbox.rings[0].points[2].y = float(22.5)
		district_width = district_bbox.rings[0].points[2].x - district_bbox.rings[0].points[0].x
		district_height = district_bbox.rings[0].points[2].y - district_bbox.rings[0].points[0].y
		district_ratio = district_width / district_height
		if state != "Alaska":
			# golden ratio
			if district_ratio > 1.272:
				district_ratio = 1.272
			if district_ratio < 0.786:
				district_ratio = 0.786

		map_small.resize(int(600 * district_ratio), int(600 / district_ratio))
		map_small.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
		if state != "Alaska" and (state != "Hawaii" or district != 2):
			map_small.zoom(-1.5)
		if map_small.scale() < 0.0006:
			map_small.zoom(-0.0006 / map_small.scale())
		filename = "districts/%d%s%d-small.jpeg" % (congress, str(state), district)
		mapnik.render_to_file(map_small, filename, "jpeg")
		print filename

		map_large.resize(int(2000 * district_ratio), int(2000 / district_ratio))
		map_large.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
		if state != "Alaska" and (state != "Hawaii" or district != 2):
			map_large.zoom(-1.5)
		if map_large.scale() < 0.0006:
			map_large.zoom(-0.0006 / map_large.scale())
		filename = "districts/%d%s%d.jpeg" % (congress, str(state), district)
		mapnik.render_to_file(map_large, filename, "jpeg")
		print filename

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
			queue.put((congress, state, district, district_gis, False))

for i in range(4):
	queue.put((0, "", 0, "", True))
