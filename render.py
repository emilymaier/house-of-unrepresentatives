#!/usr/bin/python3
# Copyright © 2014 Emily Maier
# Creates the results graphs.

import copy
import io
import json
from matplotlib import pyplot
import numpy
from xml.etree import ElementTree

json_input = open("stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()

ElementTree.register_namespace("", "http://www.w3.org/2000/svg")
ElementTree.register_namespace("xlink", "http://www.w3.org/1999/xlink")

# Generates the party scatter plot for the entire election year.
def scatter_parties_year(figure, r_expected, r_actual, d_expected, d_actual, filename):
	i = 0
	for year in range(1998, 2014, 2):
		pyplot.plot(r_expected[i], r_actual[i], "ro", figure=figure, markersize=6.0)[0].set_gid("r_" + str(year))
		pyplot.plot(d_expected[i], d_actual[i], "bo", figure=figure, markersize=6.0)[0].set_gid("d_" + str(year))
		i += 1
	r_regression = numpy.poly1d(numpy.polyfit(r_expected, r_actual, 1))
	d_regression = numpy.poly1d(numpy.polyfit(d_expected, d_actual, 1))
	min_x = min(r_expected + d_expected)
	max_x = max(r_expected + d_expected)
	pyplot.plot([min_x, max_x], r_regression([min_x, max_x]), "r--", figure=figure)
	pyplot.plot([min_x, max_x], d_regression([min_x, max_x]), "b--", figure=figure)

	output = io.StringIO()
	figure.savefig(output, format="svg")
	pyplot.close(figure)
	tree, xmlid = ElementTree.XMLID(output.getvalue())
	i = 0
	for year in range(1998, 2014, 2):
		r_element = xmlid["r_%d" % year]
		cloned_r_element = copy.deepcopy(r_element)
		tooltip = ElementTree.Element("title")
		tooltip.text = "Republicans — %d\nExpected: %.1f\nActual: %d" % (year, r_expected[i], r_actual[i])
		cloned_r_element.insert(0, tooltip)
		r_element.clear()
		r_element.tag = "a"
		r_element.set("xlink:href", "./%d" % year)
		r_element.insert(0, cloned_r_element)

		d_element = xmlid["d_%d" % year]
		cloned_d_element = copy.deepcopy(d_element)
		tooltip = ElementTree.Element("title")
		tooltip.text = "Democrats — %d\nExpected: %.1f\nActual: %d" % (year, d_expected[i], d_actual[i])
		cloned_d_element.insert(0, tooltip)
		d_element.clear()
		d_element.tag = "a"
		d_element.set("xlink:href", "./%d" % year)
		d_element.insert(0, cloned_d_element)

		i += 1
	ElementTree.ElementTree(tree).write(filename)

# Generates the party scatter plot for a single state.
def scatter_parties_state(figure, r_expected, r_actual, d_expected, d_actual, year, filename):
	i = 0
	r_expected_list = []
	r_actual_list = []
	d_expected_list = []
	d_actual_list = []
	for state_name in config_data["states"]:
		if state_name in r_expected:
			pyplot.plot(r_expected[state_name], r_actual[state_name], "ro", figure=figure, markersize=6.0)[0].set_gid("r_%s" % state_name)
			r_expected_list.append(r_expected[state_name])
			r_actual_list.append(r_actual[state_name])
		if state_name in d_expected:
			pyplot.plot(d_expected[state_name], d_actual[state_name], "bo", figure=figure, markersize=6.0)[0].set_gid("d_%s" % state_name)
			d_expected_list.append(d_expected[state_name])
			d_actual_list.append(d_actual[state_name])
	r_regression = numpy.poly1d(numpy.polyfit(r_expected_list, r_actual_list, 1))
	d_regression = numpy.poly1d(numpy.polyfit(d_expected_list, d_actual_list, 1))
	min_x = min(r_expected_list + d_expected_list)
	max_x = max(r_expected_list + d_expected_list)
	pyplot.plot([min_x, max_x], r_regression([min_x, max_x]), "r--", figure=figure)
	pyplot.plot([min_x, max_x], d_regression([min_x, max_x]), "b--", figure=figure)

	output = io.StringIO()
	figure.savefig(output, format="svg")
	pyplot.close(figure)
	tree, xmlid = ElementTree.XMLID(output.getvalue())
	for state_name in config_data["states"]:
		if "r_%s" % state_name in xmlid:
			r_element = xmlid["r_%s" % state_name]
			cloned_r_element = copy.deepcopy(r_element)
			tooltip = ElementTree.Element("title")
			tooltip.text = "Republicans — %s\nExpected: %.1f\nActual: %d" % (state_name, r_expected[state_name], r_actual[state_name])
			cloned_r_element.insert(0, tooltip)
			r_element.clear()
			r_element.tag = "a"
			r_element.set("xlink:href", "./%s" % state_name)
			r_element.insert(0, cloned_r_element)

		if "d_%s" % state_name in xmlid:
			d_element = xmlid["d_%s" % state_name]
			cloned_d_element = copy.deepcopy(d_element)
			tooltip = ElementTree.Element("title")
			tooltip.text = "Democrats — %s\nExpected: %.1f\nActual: %d" % (state_name, d_expected[state_name], d_actual[state_name])
			cloned_d_element.insert(0, tooltip)
			d_element.clear()
			d_element.tag = "a"
			d_element.set("xlink:href", "./%s" % state_name)
			d_element.insert(0, cloned_d_element)
	ElementTree.ElementTree(tree).write(filename)

# Generic function to generate a scatter plot. Used for the overall scatter plot
# for all elections in the data set.
def scatter_parties(figure, r_expected, r_actual, d_expected, d_actual, filename):
	pyplot.plot(r_expected, r_actual, "ro", figure=figure, markersize=6.0)
	pyplot.plot(d_expected, d_actual, "bo", figure=figure, markersize=6.0)
	r_regression = numpy.poly1d(numpy.polyfit(r_expected, r_actual, 1))
	d_regression = numpy.poly1d(numpy.polyfit(d_expected, d_actual, 1))
	min_x = min(r_expected + d_expected)
	max_x = max(r_expected + d_expected)
	pyplot.plot([min_x, max_x], r_regression([min_x, max_x]), "r--", figure=figure)
	pyplot.plot([min_x, max_x], d_regression([min_x, max_x]), "b--", figure=figure)
	figure.savefig(filename)
	pyplot.close(figure)

tree = ElementTree.parse("/var/lib/house/output/results.xml")
results = tree.getroot()

f1 = pyplot.figure()
f1.suptitle("Actual Versus Expected Seats by Party")
f1.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats (National Popular Vote)", ylabel="Actual Seats")
r_expected = []
r_actual = []
d_expected = []
d_actual = []
for year in range(1998, 2014, 2):
	for party in results.findall("./year[@year='%d']/yearParty" % year):
		if party.attrib["name"] == "Republican":
			r_expected.append(float(party.find("expectedSeats").attrib["national"]))
			r_actual.append(int(party.attrib["seatCount"]))
		elif party.attrib["name"] == "Democrat":
			d_expected.append(float(party.find("expectedSeats").attrib["national"]))
			d_actual.append(int(party.attrib["seatCount"]))
scatter_parties_year(f1, r_expected, r_actual, d_expected, d_actual, "/var/lib/house/output/seats_national.svg")

f2 = pyplot.figure()
f2.suptitle("Actual Versus Expected Seats by Party")
f2.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats (National Popular Vote Without 1-District States)", ylabel="Actual Seats")
r_expected = []
d_expected = []
for year in range(1998, 2014, 2):
	for party in results.findall("./year[@year='%d']/yearParty" % year):
		if party.attrib["name"] == "Republican":
			r_expected.append(float(party.find("expectedSeats").attrib["nationalWithout1"]))
		elif party.attrib["name"] == "Democrat":
			d_expected.append(float(party.find("expectedSeats").attrib["nationalWithout1"]))
scatter_parties_year(f2, r_expected, r_actual, d_expected, d_actual, "/var/lib/house/output/seats_national_without_1.svg")

f3 = pyplot.figure()
f3.suptitle("Actual Versus Expected Seats by Party")
f3.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats (State Popular Votes)", ylabel="Actual Seats")
r_expected = []
d_expected = []
for year in range(1998, 2014, 2):
	for party in results.findall("./year[@year='%d']/yearParty" % year):
		if party.attrib["name"] == "Republican":
			r_expected.append(float(party.find("expectedSeats").attrib["state"]))
		elif party.attrib["name"] == "Democrat":
			d_expected.append(float(party.find("expectedSeats").attrib["state"]))
scatter_parties_year(f3, r_expected, r_actual, d_expected, d_actual, "/var/lib/house/output/seats_state.svg")

r_expected = []
r_actual = []
d_expected = []
d_actual = []
all_numbers = []
all_margins = []
for year in range(1998, 2014, 2):
	r_expected_year = {}
	r_actual_year = {}
	d_expected_year = {}
	d_actual_year = {}
	for state in results.findall("./year[@year='%d']/state" % year):
		for party in state.findall("./stateParty"):
			if party.attrib["name"] == "Republican":
				r_expected.append(float(party.attrib["expectedSeats"]))
				r_actual.append(int(party.attrib["seatCount"]))
				r_expected_year[state.attrib["name"]] = float(party.attrib["expectedSeats"])
				r_actual_year[state.attrib["name"]] = int(party.attrib["seatCount"])
			elif party.attrib["name"] == "Democrat":
				d_expected.append(float(party.attrib["expectedSeats"]))
				d_actual.append(int(party.attrib["seatCount"]))
				d_expected_year[state.attrib["name"]] = float(party.attrib["expectedSeats"])
				d_actual_year[state.attrib["name"]] = int(party.attrib["seatCount"])
	f_state = pyplot.figure()
	f_state.suptitle("Actual versus Expected Seats per State by Party — " + str(year))
	f_state.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats", ylabel="Actual Seats")
	scatter_parties_state(f_state, r_expected_year, r_actual_year, d_expected_year, d_actual_year, year, "/var/lib/house/output/seats_" + str(year) + ".svg")
	district_margins = []
	for state in results.findall("./year[@year='%d']/state" % year):
		for district in state.findall("./district"):
			if district.attrib["winner"] == "Republican":
				district_margins.append(float(district.attrib["margin"]))
			elif district.attrib["winner"] == "Democrat":
				district_margins.append(-float(district.attrib["margin"]))
	district_margins.sort()
	district_numbers = []
	i = 0
	for margin in district_margins:
		district_numbers.append(i)
		i += 1
	all_numbers.append(district_numbers)
	all_margins.append(district_margins)
	f_district = pyplot.figure()
	f_district.suptitle("Vote Margin by District — " + str(year))
	f_district.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Republican Margin", ylabel="Cumulative Districts")
	if year > 1998:
		pyplot.plot(all_margins[-2], all_numbers[-2], figure=f_district, label=str(year - 2))
	pyplot.plot(district_margins, district_numbers, figure=f_district, label=str(year))
	if year > 1998:
		pyplot.figure(f_district.number)
		pyplot.legend(loc="lower right")
	f_district.savefig("/var/lib/house/output/margin_" + str(year) + ".svg")
	pyplot.close(f_district)
f4 = pyplot.figure()
f4.suptitle("Vote Margin by District")
f4.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Republican Margin", ylabel="Cumulative Districts")
i = 0
year = 1998
for numbers in all_numbers:
	pyplot.plot(all_margins[i], numbers, figure=f4, label=str(year))
	i += 1
	year += 2
pyplot.figure(f4.number)
pyplot.legend(loc="lower right")
f4.savefig("/var/lib/house/output/margin.svg")
pyplot.close(f4)
f5 = pyplot.figure()
f5.suptitle("Actual versus Expected Seats per State by Party")
f5.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats", ylabel="Actual Seats")
scatter_parties(f5, r_expected, r_actual, d_expected, d_actual, "/var/lib/house/output/seats.svg")
