#!/usr/bin/python3

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

def scatter_parties_year(figure, r_expected, r_actual, d_expected, d_actual, filename):
	i = 0
	for year in range(1998, 2014, 2):
		pyplot.plot(r_expected[i], r_actual[i], "ro", figure=figure, markersize=6.0)[0].set_gid("r_" + str(year))
		pyplot.plot(d_expected[i], d_actual[i], "bo", figure=figure, markersize=6.0)[0].set_gid("d_" + str(year))
		i += 1
	r_regression = numpy.poly1d(numpy.polyfit(r_expected, r_actual, 1))
	d_regression = numpy.poly1d(numpy.polyfit(d_expected, d_actual, 1))
	pyplot.plot(r_expected, r_regression(r_expected), "r:", figure=figure)
	pyplot.plot(d_expected, d_regression(d_expected), "b:", figure=figure)

	output = io.StringIO()
	figure.savefig(output, format="svg")
	pyplot.close(figure)
	tree, xmlid = ElementTree.XMLID(output.getvalue())
	for year in range(1998, 2014, 2):
		r_element = xmlid["r_%d" % year]
		cloned_r_element = copy.deepcopy(r_element)
		r_element.clear()
		r_element.tag = "a"
		r_element.set("xlink:href", "/%d" % year)
		r_element.set("target", "_top")
		r_element.insert(0, cloned_r_element)

		d_element = xmlid["d_%d" % year]
		cloned_d_element = copy.deepcopy(d_element)
		d_element.clear()
		d_element.tag = "a"
		d_element.set("xlink:href", "/%d" % year)
		d_element.set("target", "_top")
		d_element.insert(0, cloned_d_element)
	ElementTree.ElementTree(tree).write(filename)

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
	pyplot.plot(r_expected_list, r_regression(r_expected_list), "r:", figure=figure)
	pyplot.plot(d_expected_list, d_regression(d_expected_list), "b:", figure=figure)

	output = io.StringIO()
	figure.savefig(output, format="svg")
	pyplot.close(figure)
	tree, xmlid = ElementTree.XMLID(output.getvalue())
	for state_name in config_data["states"]:
		if "r_%s" % state_name in xmlid:
			r_element = xmlid["r_%s" % state_name]
			cloned_r_element = copy.deepcopy(r_element)
			r_element.clear()
			r_element.tag = "a"
			r_element.set("xlink:href", "/%d/%s" % (year, state_name))
			r_element.set("target", "_top")
			r_element.insert(0, cloned_r_element)

		if "d_%s" % state_name in xmlid:
			d_element = xmlid["d_%s" % state_name]
			cloned_d_element = copy.deepcopy(d_element)
			d_element.clear()
			d_element.tag = "a"
			d_element.set("xlink:href", "/%d/%s" % (year, state_name))
			d_element.set("target", "_top")
			d_element.insert(0, cloned_d_element)
	ElementTree.ElementTree(tree).write(filename)

def scatter_parties(figure, r_expected, r_actual, d_expected, d_actual, filename):
	pyplot.plot(r_expected, r_actual, "ro", figure=figure, markersize=6.0)
	pyplot.plot(d_expected, d_actual, "bo", figure=figure, markersize=6.0)
	r_regression = numpy.poly1d(numpy.polyfit(r_expected, r_actual, 1))
	d_regression = numpy.poly1d(numpy.polyfit(d_expected, d_actual, 1))
	pyplot.plot(r_expected, r_regression(r_expected), "r:", figure=figure)
	pyplot.plot(d_expected, d_regression(d_expected), "d:", figure=figure)
	figure.savefig(filename)
	pyplot.close(figure)

results_file = open("results.json", "r")
results = json.loads(results_file.read())
results_file.close()

f1 = pyplot.figure()
f1.suptitle("Actual Versus Expected Seats by Party")
f1.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats (National Popular Vote)", ylabel="Actual Seats")
r_expected = []
r_actual = []
d_expected = []
d_actual = []
for year in range(1998, 2014, 2):
	for party in results[str(year)]["parties"]:
		if party["name"] == "Republican":
			r_expected.append(party["expectedSeats"]["national"])
			r_actual.append(party["seatCount"])
		elif party["name"] == "Democrat":
			d_expected.append(party["expectedSeats"]["national"])
			d_actual.append(party["seatCount"])
scatter_parties_year(f1, r_expected, r_actual, d_expected, d_actual, "static/seats_national.svg")

f2 = pyplot.figure()
f2.suptitle("Actual Versus Expected Seats by Party")
f2.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats (National Popular Vote Without 1-District States)", ylabel="Actual Seats")
r_expected = []
d_expected = []
for year in range(1998, 2014, 2):
	for party in results[str(year)]["parties"]:
		if party["name"] == "Republican":
			r_expected.append(party["expectedSeats"]["nationalWithout1"])
		elif party["name"] == "Democrat":
			d_expected.append(party["expectedSeats"]["nationalWithout1"])
scatter_parties_year(f2, r_expected, r_actual, d_expected, d_actual, "static/seats_national_without_1.svg")

f3 = pyplot.figure()
f3.suptitle("Actual Versus Expected Seats by Party")
f3.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats (State Popular Votes)", ylabel="Actual Seats")
r_expected = []
d_expected = []
for year in range(1998, 2014, 2):
	for party in results[str(year)]["parties"]:
		if party["name"] == "Republican":
			r_expected.append(party["expectedSeats"]["state"])
		elif party["name"] == "Democrat":
			d_expected.append(party["expectedSeats"]["state"])
scatter_parties_year(f3, r_expected, r_actual, d_expected, d_actual, "static/seats_state.svg")

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
	for state_name, state in results[str(year)]["states"].items():
		for party in state["parties"]:
			if party["name"] == "Republican":
				r_expected.append(party["expectedSeats"]["national"])
				r_actual.append(party["seatCount"])
				r_expected_year[state_name] = party["expectedSeats"]["national"]
				r_actual_year[state_name] = party["seatCount"]
			elif party["name"] == "Democrat":
				d_expected.append(party["expectedSeats"]["national"])
				d_actual.append(party["seatCount"])
				d_expected_year[state_name] = party["expectedSeats"]["national"]
				d_actual_year[state_name] = party["seatCount"]
	f_state = pyplot.figure()
	f_state.suptitle("Actual versus Expected Seats per State by Party — " + str(year))
	f_state.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats", ylabel="Actual Seats")
	scatter_parties_state(f_state, r_expected_year, r_actual_year, d_expected_year, d_actual_year, year, "static/seats_" + str(year) + ".svg")
	district_margins = []
	for state in results[str(year)]["states"].values():
		for district in state["districts"]:
			if district["winner"] == "Republican":
				district_margins.append(district["margin"])
			elif district["winner"] == "Democrat":
				district_margins.append(-district["margin"])
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
	f_district.savefig("static/margin_" + str(year) + ".svg")
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
f4.savefig("static/margin.svg")
pyplot.close(f4)
f5 = pyplot.figure()
f5.suptitle("Actual versus Expected Seats per State by Party")
f5.add_axes([0.1, 0.1, 0.8, 0.8], xlabel="Expected Seats", ylabel="Actual Seats")
scatter_parties(f5, r_expected, r_actual, d_expected, d_actual, "static/seats.svg")
