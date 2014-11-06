#!/usr/bin/python3

import json
from matplotlib import pyplot
import numpy

results_file = open("results.json", "r")
results = json.loads(results_file.read())
results_file.close()

pyplot.title("Actual Versus Expected Seats by Party")
pyplot.xlabel("Expected Seats (National Popular Vote)")
pyplot.ylabel("Actual Seats")
republican_expected = []
republican_actual = []
democrat_expected = []
democrat_actual = []
for year in range(1998, 2014, 2):
	for party in results[str(year)]["parties"]:
		if party["name"] == "Republican":
			republican_expected.append(party["expectedSeats"]["national"])
			republican_actual.append(party["seatCount"])
		elif party["name"] == "Democrat":
			democrat_expected.append(party["expectedSeats"]["national"])
			democrat_actual.append(party["seatCount"])
pyplot.plot(republican_expected, republican_actual, "ro", markersize=4.0)
pyplot.plot(democrat_expected, democrat_actual, "bo", markersize=4.0)
republican_regression = numpy.poly1d(numpy.polyfit(republican_expected, republican_actual, 1))
democrat_regression = numpy.poly1d(numpy.polyfit(democrat_expected, democrat_actual, 1))
pyplot.plot(republican_expected, republican_regression(republican_expected), "r:")
pyplot.plot(democrat_expected, democrat_regression(democrat_expected), "b:")
pyplot.savefig("static/seats_national.svg")
pyplot.clf()
pyplot.cla()
pyplot.close()

pyplot.title("Actual Versus Expected Seats by Party")
pyplot.xlabel("Expected Seats (National Popular Vote Without 1-District States)")
pyplot.ylabel("Actual Seats")
republican_expected = []
democrat_expected = []
for year in range(1998, 2014, 2):
	for party in results[str(year)]["parties"]:
		if party["name"] == "Republican":
			republican_expected.append(party["expectedSeats"]["nationalWithout1"])
		elif party["name"] == "Democrat":
			democrat_expected.append(party["expectedSeats"]["nationalWithout1"])
pyplot.plot(republican_expected, republican_actual, "ro", markersize=4.0)
pyplot.plot(democrat_expected, democrat_actual, "bo", markersize=4.0)
republican_regression = numpy.poly1d(numpy.polyfit(republican_expected, republican_actual, 1))
democrat_regression = numpy.poly1d(numpy.polyfit(democrat_expected, democrat_actual, 1))
pyplot.plot(republican_expected, republican_regression(republican_expected), "r:")
pyplot.plot(democrat_expected, democrat_regression(democrat_expected), "b:")
pyplot.savefig("static/seats_national_without_1.svg")
pyplot.clf()
pyplot.cla()
pyplot.close()

pyplot.title("Actual Versus Expected Seats by Party")
pyplot.xlabel("Expected Seats (State Popular Votes)")
pyplot.ylabel("Actual Seats")
republican_expected = []
democrat_expected = []
for year in range(1998, 2014, 2):
	for party in results[str(year)]["parties"]:
		if party["name"] == "Republican":
			republican_expected.append(party["expectedSeats"]["state"])
		elif party["name"] == "Democrat":
			democrat_expected.append(party["expectedSeats"]["state"])
pyplot.plot(republican_expected, republican_actual, "ro", markersize=4.0)
pyplot.plot(democrat_expected, democrat_actual, "bo", markersize=4.0)
republican_regression = numpy.poly1d(numpy.polyfit(republican_expected, republican_actual, 1))
democrat_regression = numpy.poly1d(numpy.polyfit(democrat_expected, democrat_actual, 1))
pyplot.plot(republican_expected, republican_regression(republican_expected), "r:")
pyplot.plot(democrat_expected, democrat_regression(democrat_expected), "b:")
pyplot.savefig("static/seats_state.svg")
pyplot.clf()
pyplot.cla()
pyplot.close()

republican_expected = []
republican_actual = []
democrat_expected = []
democrat_actual = []
for year in range(1998, 2014, 2):
	republican_expected_year = []
	republican_actual_year = []
	democrat_expected_year = []
	democrat_actual_year = []
	for state in results[str(year)]["states"].values():
		for party in state["parties"]:
			if party["name"] == "Republican":
				republican_expected.append(party["expectedSeats"]["national"])
				republican_actual.append(party["seatCount"])
				republican_expected_year.append(party["expectedSeats"]["national"])
				republican_actual_year.append(party["seatCount"])
			elif party["name"] == "Democrat":
				democrat_expected.append(party["expectedSeats"]["national"])
				democrat_actual.append(party["seatCount"])
				democrat_expected_year.append(party["expectedSeats"]["national"])
				democrat_actual_year.append(party["seatCount"])
	pyplot.title("Actual versus Expected Seats per State by Party — " + str(year))
	pyplot.xlabel("Expected Seats")
	pyplot.ylabel("Actual Seats")
	pyplot.plot(republican_expected_year, republican_actual_year, "ro", markersize=4.0)
	pyplot.plot(democrat_expected_year, democrat_actual_year, "bo", markersize=4.0)
	republican_regression = numpy.poly1d(numpy.polyfit(republican_expected_year, republican_actual_year, 1))
	democrat_regression = numpy.poly1d(numpy.polyfit(democrat_expected_year, democrat_actual_year, 1))
	pyplot.plot(republican_expected_year, republican_regression(republican_expected_year), "r:")
	pyplot.plot(democrat_expected_year, democrat_regression(democrat_expected_year), "b:")
	pyplot.savefig("static/seats_" + str(year) + ".svg")
	pyplot.clf()
	pyplot.cla()
	pyplot.close()
pyplot.title("Actual versus Expected Seats per State by Party")
pyplot.xlabel("Expected Seats")
pyplot.ylabel("Actual Seats")
pyplot.plot(republican_expected, republican_actual, "ro", markersize=4.0)
pyplot.plot(democrat_expected, democrat_actual, "bo", markersize=4.0)
republican_regression = numpy.poly1d(numpy.polyfit(republican_expected, republican_actual, 1))
democrat_regression = numpy.poly1d(numpy.polyfit(democrat_expected, democrat_actual, 1))
pyplot.plot(republican_expected, republican_regression(republican_expected), "r:")
pyplot.plot(democrat_expected, democrat_regression(democrat_expected), "b:")
pyplot.savefig("static/seats_state_individual.svg")
