#!/usr/bin/python3

import json
import re
import sys
import time

json_input = open("data.json", "r")
config_data = json.loads(json_input.read())
json_input.close()
state_names = config_data["states"]

apportionment_1992 = [7, 1, 6, 4, 52, 6, 6, 1, 23, 11, 2, 2, 20, 10, 5, 4, 6, 7, 2, 8, 10, 16, 8, 5, 9, 1, 3, 2, 2, 13, 3, 31, 12, 1, 19, 6, 5, 21, 2, 6, 1, 9, 30, 3, 1, 11, 9, 3, 9, 1]
apportionment_1992 = dict(zip(state_names, apportionment_1992))

apportionment_2002 = [7, 1, 8, 4, 53, 7, 5, 1, 25, 13, 2, 2, 19, 9, 5, 4, 6, 7, 2, 8, 10, 15, 8, 4, 9, 1, 3, 3, 2, 13, 3, 29, 13, 1, 18, 5, 5, 19, 2, 6, 1, 9, 32, 3, 1, 11, 9, 3, 8, 1]
apportionment_2002 = dict(zip(state_names, apportionment_2002))

apportionment_2012 = [7, 1, 9, 4, 53, 7, 5, 1, 27, 14, 2, 2, 18, 9, 4, 4, 6, 6, 2, 8, 9, 14, 8, 4, 8, 1, 3, 4, 2, 12, 3, 27, 13, 1, 16, 5, 5, 18, 2, 7, 1, 9, 36, 4, 1, 11, 10, 3, 8, 1]
apportionment_2012 = dict(zip(state_names, apportionment_2012))

election_file = open(sys.argv[1], "r")
election_string = election_file.read()

state_regex = re.compile("STATES REPRESENTATIVE1?\n")
states = re.split(state_regex, election_string)

all_districts = {}
for state_raw in states[1:51]:
	state = state_raw.split("\nRecapitulation of Votes Cast in")[0].split("Total ..........")[0].split("\n..........")[0].split("\nPresidential electors ..........")[0].split("\n\u000c..........")[0].split("\n\u000cRepublican")[0]
	candidates = []
	votes = []
	district = []
	districts = []
	orphaned_district_numbers = 0

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
			candidates.append(line.replace("1 ", "").split(" .")[0])
			continue
		try:
			votes.append(int(line.replace(",", "").replace("1 ", "")))
			continue
		except ValueError:
			pass
		if line == "(1 )" or line == "(2 )":
			votes.append(1)
			continue
		try:
			int(line[:-1])
			orphaned_district_numbers += 1
		except ValueError:
			pass

	for candidate in candidates:
		candidate = candidate.rsplit(", ", 1)
		if len(candidate) is 1:
			candidate.append(candidate[0])
			candidate[0] = ""
		if (candidate[1] == "Republican" or len(district) > 0 and district[-1][1] != "Republican" and candidate[1] == "Democrat") and orphaned_district_numbers > 0:
			orphaned_district_numbers -= 1
			candidate[0] = "0. " + candidate[0]
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
	all_districts[state_names.pop(0)] = districts

for state_name, state_districts in all_districts.items():
	print(state_name + ":")
	if int(sys.argv[2]) >= 1992 and int(sys.argv[2]) < 2002:
		current_apportionment = apportionment_1992
	elif int(sys.argv[2]) >= 2002 and int(sys.argv[2]) < 2012:
		current_apportionment = apportionment_2002
	elif int(sys.argv[2]) >= 2012 and int(sys.argv[2]) < 2022:
		current_apportionment = apportionment_2012
	for district_index in range(0, current_apportionment[state_name]):
		district = state_districts[district_index]
		print(district_index + 1, ":")
		for candidate in district:
			print("%30s\t%25s\t%d" % (candidate[0], candidate[1], candidate[2]))
		print("")
	print("")

json_output = open("json/" + sys.argv[2] + ".json", "w")
json_output.write(json.dumps(all_districts))
json_output.close()
