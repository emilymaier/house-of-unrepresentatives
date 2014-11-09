#!/usr/bin/python

import json
import mapnik
import shapefile

json_input = open("stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()

place_datasources = []
for i in range(0, 50):
	place_datasources.append(mapnik.Shapefile(file="TIGER/tl_2014_%s_place.shp" % config_data["fips"][i]))
road_datasource = mapnik.Shapefile(file="TIGER/roads_merged.shp")
district_datasources = []
for congress in range(106, 114):
	district_datasources.append(mapnik.Shapefile(file="districtShapes/districts%d.shp" % congress))

map = mapnik.Map(1500, 1500)
map.background = mapnik.Color("white")

city_style = mapnik.Style()
city_rule = mapnik.Rule()
city_rule.filter = mapnik.Filter("[LSAD] = '25' and [ALAND] >= 30000000")

city_point_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("yellow"))
city_rule.symbols.append(city_point_symbolizer)

city_label_symbolizer = mapnik.TextSymbolizer(mapnik.Expression("[NAME]"), "DejaVu Sans Book", 20, mapnik.Color("black"))
city_label_symbolizer.displacement = (0, 12)
city_rule.symbols.append(city_label_symbolizer)

city_style.rules.append(city_rule)
map.append_style("City Style", city_style)

place_layer = mapnik.Layer("Places")
place_layer.styles.append("City Style")
map.layers.append(place_layer)

road_style = mapnik.Style()
road_rule = mapnik.Rule()
road_symbolizer = mapnik.LineSymbolizer(mapnik.Color("#ff0000"), 0.8)
road_rule.symbols.append(road_symbolizer)
road_style.rules.append(road_rule)
map.append_style("Road Style", road_style)

road_layer = mapnik.Layer("Roads")
road_layer.datasource = road_datasource
road_layer.styles.append("Road Style")
map.layers.append(road_layer)

districts_layer = mapnik.Layer("Districts")
districts_layer.styles.append("Districts Style")
map.layers.append(districts_layer)

road_label_style = mapnik.Style()
road_label_rule = mapnik.Rule()
road_label_rule.filter = mapnik.Expression("[FULLNAME].match('I- \\d+')")
road_label_symbolizer = mapnik.ShieldSymbolizer(mapnik.Expression("[FULLNAME].replace('I- ', '')"), "DejaVu Sans Book", 18, mapnik.Color("white"), mapnik.PathExpression("I-blank.svg"))
road_label_symbolizer.label_placement = mapnik.label_placement.LINE_PLACEMENT
road_label_symbolizer.minimum_distance = 150
road_label_symbolizer.minimum_padding = 50
road_label_symbolizer.transform = "scale(0.07)"
road_label_rule.symbols.append(road_label_symbolizer)
road_label_style.rules.append(road_label_rule)
map.append_style("Road Label Style", road_label_style)

road_label_layer = mapnik.Layer("Road Labels")
road_label_layer.datasource = road_datasource
road_label_layer.styles.append("Road Label Style")
map.layers.append(road_label_layer)

for congress in range(106, 114):
	shape_data = shapefile.Reader("districtShapes/districts%d" % congress)
	shape_records = shape_data.shapeRecords()

	map.layers[2].datasource = district_datasources.pop(0)
	i = 0
	for state in config_data["states"]:
		map.layers[0].datasource = place_datasources[i]
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

			districts_style = mapnik.Style()
			districts_rule = mapnik.Rule()
			districts_symbolizer = mapnik.LineSymbolizer(mapnik.Color("rgb(50%,50%,50%)"), 0.5)
			districts_rule.symbols.append(districts_symbolizer)
			districts_style.rules.append(districts_rule)
			district_symbolizer = mapnik.LineSymbolizer(mapnik.Color("rgb(0%,0%,0%)"), 1.6)
			district_rule = mapnik.Rule()
			district_rule.filter = mapnik.Filter("[STATENAME] = '%s' and [DISTRICT] = '%s'" % (str(state), str(district_gis)))
			district_rule.symbols.append(district_symbolizer)
			districts_style.rules.append(district_rule)
			map.append_style("Districts Style", districts_style)

			for shape_record in shape_records:
				if shape_record.record[0] == state and shape_record.record[2] == district_gis:
					district_bbox = shape_record.shape.bbox
					break
			map.resize(1500, int(1500 * (district_bbox[3] - district_bbox[1]) / (district_bbox[2] - district_bbox[0])))
			map.zoom_to_box(mapnik.Box2d(district_bbox[0], district_bbox[1], district_bbox[2], district_bbox[3]))
			map.zoom(-1.5)
			mapnik.render_to_file(map, "districts/%d%s%d.png" % (congress, str(state), district), "png")
			map.remove_style("Districts Style")
