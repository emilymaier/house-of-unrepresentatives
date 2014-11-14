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

map = mapnik.Map(600, 600)
map.background = mapnik.Color("white")

city_point_style = mapnik.Style()
city_point_rule = mapnik.Rule()
city_point_symbolizer = mapnik.PolygonSymbolizer(mapnik.Color("yellow"))
city_point_rule.symbols.append(city_point_symbolizer)
city_point_style.rules.append(city_point_rule)

city_point_layer = mapnik.Layer("City Points")
city_point_layer.styles.append("City Point Style")
map.layers.append(city_point_layer)

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

city_label_style = mapnik.Style()
city_label_rule = mapnik.Rule()
city_label_symbolizer = mapnik.TextSymbolizer(mapnik.Expression("[NAME]"), "DejaVu Sans Book", 13, mapnik.Color("black"))
city_label_symbolizer.minimum_padding = 10
city_label_symbolizer.minimum_distance = 10
city_label_symbolizer.halo_fill = mapnik.Color("white")
city_label_symbolizer.halo_radius = 2
city_label_rule.symbols.append(city_label_symbolizer)
city_label_style.rules.append(city_label_rule)

city_label_layer = mapnik.Layer("City Labels")
city_label_layer.styles.append("City Label Style")
map.layers.append(city_label_layer)

road_label_style = mapnik.Style()
road_label_rule = mapnik.Rule()
road_label_rule.filter = mapnik.Expression("[FULLNAME].match('I- \\d+')")
road_label_symbolizer = mapnik.ShieldSymbolizer(mapnik.Expression("[FULLNAME].replace('I- ', '')"), "DejaVu Sans Book", 18, mapnik.Color("white"), mapnik.PathExpression("I-blank.svg"))
road_label_symbolizer.label_placement = mapnik.label_placement.LINE_PLACEMENT
road_label_symbolizer.minimum_padding = 50
road_label_symbolizer.transform = "scale(0.07)"
road_label_rule.symbols.append(road_label_symbolizer)
road_label_style.rules.append(road_label_rule)

road_label_layer = mapnik.Layer("Road Labels")
road_label_layer.datasource = road_datasource
road_label_layer.styles.append("Road Label Style")
map.layers.append(road_label_layer)

for congress in range(106, 114):
	shape_data = shapefile.Reader("districtShapes/districts%d" % congress)
	shape_records = shape_data.shapeRecords()

	map.layers[2].datasource = district_datasources.pop(0) # districts_layer
	i = 0
	for state in config_data["states"]:
		map.layers[0].datasource = place_datasources[i] # city_point_layer
		map.layers[3].datasource = place_datasources[i] # city_label_layer
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
			if state == "Alaska":
				district_bbox[2] = -130

			city_point_style.rules[0].filter = mapnik.Filter("[PCICBSA] = 'Y' or ([LSAD] = '25' and [ALAND] >= 100000000)")
			map.append_style("City Point Style", city_point_style)
			city_label_style.rules[0].filter = mapnik.Filter("[PCICBSA] = 'Y' or ([LSAD] = '25' and [ALAND] >= 100000000)")
			map.append_style("City Label Style", city_label_style)
			road_label_style.rules[0].symbols[0].minimum_distance = 200
			map.append_style("Road Label Style", road_label_style)

			map.resize(600, int(600 * (district_bbox[3] - district_bbox[1]) / (district_bbox[2] - district_bbox[0])))
			map.zoom_to_box(mapnik.Box2d(district_bbox[0], district_bbox[1], district_bbox[2], district_bbox[3]))
			map.zoom(-1.5)
			filename = "districts/%d%s%d-small.png" % (congress, str(state), district)
			mapnik.render_to_file(map, filename, "png")
			map.remove_style("City Point Style")
			map.remove_style("City Label Style")
			map.remove_style("Road Label Style")
			print filename

			city_point_style.rules[0].filter = mapnik.Filter("[PCICBSA] = 'Y' or (([LSAD] = '21' or [LSAD] = '25' or [LSAD] = '43') and [ALAND] >= 30000000)")
			map.append_style("City Point Style", city_point_style)
			city_label_style.rules[0].filter = mapnik.Filter("[PCICBSA] = 'Y' or (([LSAD] = '21' or [LSAD] = '25' or [LSAD] = '43') and [ALAND] >= 30000000)")
			map.append_style("City Label Style", city_label_style)
			road_label_style.rules[0].symbols[0].minimum_distance = 600
			map.append_style("Road Label Style", road_label_style)

			map.resize(2000, int(2000 * (district_bbox[3] - district_bbox[1]) / (district_bbox[2] - district_bbox[0])))
			map.zoom_to_box(mapnik.Box2d(district_bbox[0], district_bbox[1], district_bbox[2], district_bbox[3]))
			map.zoom(-1.5)
			filename = "districts/%d%s%d.png" % (congress, str(state), district)
			mapnik.render_to_file(map, filename, "png")
			map.remove_style("City Point Style")
			map.remove_style("City Label Style")
			map.remove_style("Road Label Style")
			print filename

			map.remove_style("Districts Style")
