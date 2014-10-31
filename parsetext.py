#!/usr/bin/python3
#XXX: Redistricting notes cause multiple districts to be parsed together

import re
import sys
import time

election_file = open(sys.argv[1], "r")
election_string = election_file.read()

state_regex = re.compile("STATES REPRESENTATIVE1?\n")
states = re.split(state_regex, election_string)

all_districts = []
for state_raw in states[1:51]:
	state = state_raw.split("\nRecapitulation of Votes Cast in")[0].split("Total ..........")[0].split("\n..........")[0].split("\nPresidential electors ..........")[0].split("\n\u000c..........")[0]
	candidates = []
	votes = []
	district = []
	districts = []

	for line in state.split("\n"):
		if line == "AT LARGE" or \
		   line == "" or \
		   line[:7] == "VerDate" or \
		   (len(line) > 2 and line[2] == ":") or \
		   line[:3] == "Jkt" or \
		   line[:2] == "PO" or \
		   line[:3] == "Frm" or \
		   line[:3] == "Fmt" or \
		   line[:4] == "Sfmt" or \
		   line[:3] == "C:\\" or \
		   line == "PUB1" or \
		   line == "PsN: PUB1" or \
		   line[0] == "\u000c" or \
		   line[-10:] == "—Continued":
			continue
		if "......." in line:
			candidates.append(line.split(" .")[0])
			continue
		try:
			votes.append(int(line.replace(",", "").replace("1 ", "")))
			continue
		except ValueError:
			pass
		if line == "(1 )" or line == "(2 )":
			votes.append(1)
			continue

	for candidate in candidates:
		candidate = candidate.rsplit(", ", 1)
		if len(candidate) is 1:
			candidate.append(candidate[0])
			candidate[0] = ""
		if ". " in candidate[0]:
			try:
				int(candidate[0].split(". ")[0])
				districts.append(district)
				district = []
				candidate[0] = candidate[0].split(". ", 1)[1]
			except ValueError:
				pass
		district.append((candidate[0], candidate[1], votes.pop(0)))
	districts.append(district)
	if districts[0] == []:
		districts.pop(0)
	all_districts.append(districts)

state_names = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"]

for state in all_districts:
	print(state_names.pop(0) + ":")
	for district in state:
		for candidate in district:
			print("%30s\t%25s\t%d" % (candidate[0], candidate[1], candidate[2]))
		print("")
	print("")
