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

place_datasource_small = mapnik.PostGIS(dbname="gis", table="(select wkb_geometry, name from places where pcicbsa = 'Y' order by aland desc) multipolygon")
place_datasource_large = mapnik.PostGIS(dbname="gis", table="(select wkb_geometry, name from places where pcicbsa = 'Y' or aland >= 30000000 order by aland desc) multipolygon")
water_datasource = mapnik.PostGIS(dbname="gis", table="(select wkb_geometry from water where awater >= 500000) multipolygon")
road_datasource = mapnik.PostGIS(dbname="gis", table="(select wkb_geometry, fullname from roads where fullname ~ 'I- \\d+') multiline")
state_datasource = mapnik.PostGIS(dbname="gis", table="states")

map = mapnik.Map(600, 600)
map.background = mapnik.Color("white")

city_point_style = mapnik.Style()
city_point_rule = mapnik.Rule()
city_point_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("yellow"))
city_point_rule.symbols.append(city_point_symbolizer)
city_point_style.rules.append(city_point_rule)
map.append_style("City Point Style", city_point_style)

city_point_layer = mapnik.Layer("City Points")
city_point_layer.styles.append("City Point Style")
map.layers.append(city_point_layer) # 0

water_style = mapnik.Style()
water_rule = mapnik.Rule()
water_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("blue"))
water_rule.symbols.append(water_symbolizer)
water_style.rules.append(water_rule)
map.append_style("Water Style", water_style)

water_layer = mapnik.Layer("Water")
water_layer.datasource = water_datasource
water_layer.styles.append("Water Style")
map.layers.append(water_layer) # 1

road_style = mapnik.Style()
road_rule = mapnik.Rule()
road_symbolizer = mapnik.LineSymbolizer(mapnik.Color("#ff0000"), 0.8)
road_rule.symbols.append(road_symbolizer)
road_style.rules.append(road_rule)
map.append_style("Road Style", road_style)

road_layer = mapnik.Layer("Roads")
road_layer.datasource = road_datasource
road_layer.styles.append("Road Style")
map.layers.append(road_layer) # 2

districts_style = mapnik.Style()
districts_rule = mapnik.Rule()
districts_symbolizer = mapnik.LineSymbolizer(mapnik.Color("rgb(50%,50%,50%)"), 0.3)
districts_rule.symbols.append(districts_symbolizer)
districts_style.rules.append(districts_rule)
map.append_style("Districts Style", districts_style)

districts_layer = mapnik.Layer("Districts")
districts_layer.styles.append("Districts Style")
map.layers.append(districts_layer) # 3

state_boundary_style = mapnik.Style()
state_boundary_rule = mapnik.Rule()
state_boundary_symbolizer = mapnik.LineSymbolizer(mapnik.Color("black"), 0.3)
state_boundary_rule.symbols.append(state_boundary_symbolizer)
state_boundary_style.rules.append(state_boundary_rule)
map.append_style("State Boundary Style", state_boundary_style)

state_boundary_layer = mapnik.Layer("State Boundaries")
state_boundary_layer.datasource = state_datasource
state_boundary_layer.styles.append("State Boundary Style")
map.layers.append(state_boundary_layer) # 4

district_style = mapnik.Style()
district_rule = mapnik.Rule()
district_symbolizer = mapnik.LineSymbolizer(mapnik.Color("rgb(0%,0%,0%)"), 2)
district_rule.symbols.append(district_symbolizer)
district_style.rules.append(district_rule)
map.append_style("District Style", district_style)

district_layer = mapnik.Layer("District")
district_layer.styles.append("District Style")
map.layers.append(district_layer) # 5

state_label_style = mapnik.Style()
state_label_rule = mapnik.Rule()
state_label_symbolizer = mapnik.TextSymbolizer(mapnik.Expression("[name]"), "DejaVu Sans Book", 22, mapnik.Color("black"))
state_label_symbolizer.halo_fill = mapnik.Color("white")
state_label_symbolizer.halo_radius = 3
state_label_symbolizer.minimum_padding = 10
state_label_symbolizer.placement = mapnik.marker_placement.INTERIOR_PLACEMENT
state_label_rule.symbols.append(state_label_symbolizer)
state_label_style.rules.append(state_label_rule)
map.append_style("State Label Style", state_label_style)

state_label_layer = mapnik.Layer("State Labels")
state_label_layer.styles.append("State Label Style")
map.layers.append(state_label_layer) # 6

city_label_style = mapnik.Style()
city_label_rule = mapnik.Rule()
city_label_symbolizer = mapnik.TextSymbolizer(mapnik.Expression("[name]"), "DejaVu Sans Book", 13, mapnik.Color("black"))
city_label_symbolizer.minimum_padding = 10
city_label_symbolizer.minimum_distance = 10
city_label_symbolizer.halo_fill = mapnik.Color("white")
city_label_symbolizer.halo_radius = 2
city_label_rule.symbols.append(city_label_symbolizer)
city_label_style.rules.append(city_label_rule)
map.append_style("City Label Style", city_label_style)

city_label_layer = mapnik.Layer("City Labels")
city_label_layer.styles.append("City Label Style")
map.layers.append(city_label_layer) # 7

road_label_style = mapnik.Style()
road_label_rule = mapnik.Rule()
road_label_symbolizer = mapnik.ShieldSymbolizer(mapnik.Expression("[fullname].replace('I- ', '')"), "DejaVu Sans Book", 12, mapnik.Color("white"), mapnik.PathExpression("I-blank.svg"))
road_label_symbolizer.label_placement = mapnik.label_placement.LINE_PLACEMENT
road_label_symbolizer.minimum_padding = 50
road_label_symbolizer.transform = "scale(0.04)"
road_label_rule.symbols.append(road_label_symbolizer)
road_label_style.rules.append(road_label_rule)

road_label_layer = mapnik.Layer("Road Labels")
road_label_layer.datasource = road_datasource
road_label_layer.styles.append("Road Label Style")
map.layers.append(road_label_layer) # 8

for congress in range(106, 114):
	map.layers[3].datasource = mapnik.PostGIS(dbname="gis", table="districts%d" % congress) # districts_layer

	i = 0
	for state in config_data["states"]:
		map.layers[6].datasource = mapnik.PostGIS(dbname="gis", table="(select ST_Intersection(wkb_geometry, !bbox!) as wkb_geometry, name from simplified where name != '%s') multipolygon" % state, srid=4269) # state_label_layer

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
			map.layers[5].datasource = mapnik.PostGIS(dbname="gis", table="(select * from districts%d where statename = '%s' and district = '%s') multipolygon" % (congress, state, district_gis)) # district_layer

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

			road_label_style.rules[0].symbols[0].minimum_distance = 200
			map.append_style("Road Label Style", road_label_style)
			map.layers[0].datasource = place_datasource_small # city_point_layer
			map.layers[7].datasource = place_datasource_small # city_label_layer

			map.resize(int(600 * district_ratio), int(600 / district_ratio))
			map.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
			map.zoom(-1.5)
			filename = "districts/%d%s%d-small.png" % (congress, str(state), district)
			mapnik.render_to_file(map, filename, "png")
			map.remove_style("Road Label Style")
			print filename

			road_label_style.rules[0].symbols[0].minimum_distance = 600
			map.append_style("Road Label Style", road_label_style)
			map.layers[0].datasource = place_datasource_large # city_point_layer
			map.layers[7].datasource = place_datasource_large # city_label_layer

			map.resize(int(2000 * district_ratio), int(2000 / district_ratio))
			map.zoom_to_box(mapnik.Box2d(district_bbox.rings[0].points[0].x, district_bbox.rings[0].points[0].y, district_bbox.rings[0].points[2].x, district_bbox.rings[0].points[2].y))
			map.zoom(-1.5)
			filename = "districts/%d%s%d.png" % (congress, str(state), district)
			mapnik.render_to_file(map, filename, "png")
			map.remove_style("Road Label Style")
			print filename
