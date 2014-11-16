#!/usr/bin/python

import json
import mapnik
import ppygis
import psycopg2

json_input = open("stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()

pg_conn = psycopg2.connect(database="gis")
pg_cursor = pg_conn.cursor()

map_small = mapnik.Map(600, 600)
mapnik.load_map(map_small, "map-small.xml")
map_large = mapnik.Map(2000, 2000)
mapnik.load_map(map_large, "map-large.xml")

for congress in range(113, 114):
#for congress in range(106, 114):
	map_small.layers[3].datasource = mapnik.PostGIS(dbname="gis", table="districts%d" % congress) # districts
	map_large.layers[3].datasource = mapnik.PostGIS(dbname="gis", table="districts%d" % congress)

	i = 0
	for state in config_data["states"]:
		state_datasource = mapnik.PostGIS(dbname="gis", table="(select ST_Intersection(wkb_geometry, !bbox!) as wkb_geometry, name from simplified where name != '%s') multipolygon" % state, srid=4269)
		map_small.layers[6].datasource = state_datasource # state labels
		map_large.layers[6].datasource = state_datasource

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
			district_datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d where statename = '%s' and district = '%s') multipolygon" % (congress, state, district_gis))
			map_small.layers[5].datasource = district_datasource # current district
			map_large.layers[5].datasource = district_datasource

			pg_cursor.execute("select ST_Envelope(wkb_geometry) from districts%d where statename = '%s' and district = '%s'" % (congress, state, district_gis))
			pg_record = pg_cursor.fetchone()
			pg_conn.rollback()
			district_bbox = ppygis.Geometry.read_ewkb(pg_record[0])
			if state == "Alaska":
				district_bbox.rings[0].points[2].x = -130
			district_width = district_bbox.rings[0].points[2].x - district_bbox.rings[0].points[0].x
			district_height = district_bbox.rings[0].points[2].y - district_bbox.rings[0].points[0].y
			district_ratio = district_width / district_height
			if district_ratio > 1.4:
				district_ratio = 1.4
			if district_ratio < 0.714:
				district_ratio = 0.714

			map_small.resize(int(600 * district_ratio), int(600 / district_ratio))
			map_small.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
			map_small.zoom(-1.5)
			filename = "districts/%d%s%d-small.png" % (congress, str(state), district)
			mapnik.render_to_file(map_small, filename, "png")
			print filename

			map_large.resize(int(2000 * district_ratio), int(2000 / district_ratio))
			map_large.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
			map_large.zoom(-1.5)
			filename = "districts/%d%s%d.png" % (congress, str(state), district)
			mapnik.render_to_file(map_large, filename, "png")
			print filename
