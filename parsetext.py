#!/usr/bin/python3

import json
import operator
import re
import sys
import time

def parse_candidates(lines):
	candidates = []
	votes = []
	orphaned_district_numbers = 0
	for line in lines:
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
	return candidates, votes, orphaned_district_numbers

def parse_state(state_raw):
	state = state_raw.split("\nRecapitulation of Votes Cast in")[0].split("Total ..........")[0].split("\n..........")[0].split("\nPresidential electors ..........")[0].split("\n\u000c..........")[0].split("\n\u000cRepublican")[0]
	candidates, votes, orphaned_district_numbers = parse_candidates(state.split("\n"))
	state_result = {"totalVotes": 0, "totalSeats": 0, "parties": [], "districts": []}
	unsorted_parties = {}
	district = {"totalVotes": 0, "candidates": []}
	district_winner_party = ""
	district_winner_votes = 0
	for candidate in candidates:
		candidate = candidate.rsplit(", ", 1)
		if len(candidate) is 1:
			candidate.append(candidate[0])
			candidate[0] = ""
		if (candidate[1] == "Republican" or len(district["candidates"]) > 0 and district["candidates"][-1]["party"] != "Republican" and candidate[1] == "Democrat") and orphaned_district_numbers > 0:
			orphaned_district_numbers -= 1
			candidate[0] = "0. " + candidate[0]
		if ". " in candidate[0]:
			try:
				int(candidate[0].split(". ")[0])
				state_result["districts"].append(district)
				if district_winner_party != "":
					unsorted_parties[district_winner_party]["seats"] += 1
				district_winner_party = ""
				district_winner_votes = 0
				district = {"totalVotes": 0, "candidates": []}
				candidate[0] = candidate[0].split(". ", 1)[1]
			except ValueError:
				pass
		current_candidate_votes = votes.pop(0)
		if candidate[1] not in unsorted_parties:
			unsorted_parties[candidate[1]] = {"name": candidate[1], "votes": 0, "seats": 0}
		unsorted_parties[candidate[1]]["votes"] += current_candidate_votes
		if current_candidate_votes > district_winner_votes:
			district_winner_party = candidate[1]
			district_winner_votes = current_candidate_votes
		state_result["totalVotes"] += current_candidate_votes
		district["totalVotes"] += current_candidate_votes
		district["candidates"].append({"name": candidate[0], "party": candidate[1], "votes": current_candidate_votes})
	state_result["districts"].append(district)
	if state_result["districts"][0] == {"totalVotes": 0, "candidates": []}:
		state_result["districts"].pop(0)
	state_result["totalSeats"] = len(state_result["districts"])
	unsorted_parties[district_winner_party]["seats"] += 1
	state_result["parties"] = sorted(unsorted_parties.values(), key=operator.itemgetter("votes"), reverse=True)
	return state_result

json_input = open("stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()
state_names = config_data["states"]

apportionment_1992 = [7, 1, 6, 4, 52, 6, 6, 1, 23, 11, 2, 2, 20, 10, 5, 4, 6, 7, 2, 8, 10, 16, 8, 5, 9, 1, 3, 2, 2, 13, 3, 31, 12, 1, 19, 6, 5, 21, 2, 6, 1, 9, 30, 3, 1, 11, 9, 3, 9, 1]
apportionment_1992 = dict(zip(state_names, apportionment_1992))

apportionment_2002 = [7, 1, 8, 4, 53, 7, 5, 1, 25, 13, 2, 2, 19, 9, 5, 4, 6, 7, 2, 8, 10, 15, 8, 4, 9, 1, 3, 3, 2, 13, 3, 29, 13, 1, 18, 5, 5, 19, 2, 6, 1, 9, 32, 3, 1, 11, 9, 3, 8, 1]
apportionment_2002 = dict(zip(state_names, apportionment_2002))

apportionment_2012 = [7, 1, 9, 4, 53, 7, 5, 1, 27, 14, 2, 2, 18, 9, 4, 4, 6, 6, 2, 8, 9, 14, 8, 4, 8, 1, 3, 4, 2, 12, 3, 27, 13, 1, 16, 5, 5, 18, 2, 7, 1, 9, 36, 4, 1, 11, 10, 3, 8, 1]
apportionment_2012 = dict(zip(state_names, apportionment_2012))

complete_results = {}
for year in range(2000, 2014, 2):
	election_file = open("temp/" + str(year) + "election", "r")
	election_string = election_file.read()
	election_file.close()

	state_regex = re.compile("STATES REPRESENTATIVE1?\n")
	states = re.split(state_regex, election_string)

	complete_year = {}
	for state_number in range(50):
		complete_year[state_names[state_number]] = parse_state(states[state_number + 1])

	for state_name, state_result in complete_year.items():
		print(state_name + ":")
		if year >= 1992 and year < 2002:
			current_apportionment = apportionment_1992
		elif year >= 2002 and year < 2012:
			current_apportionment = apportionment_2002
		elif year >= 2012 and year < 2022:
			current_apportionment = apportionment_2012
		for district_index in range(0, current_apportionment[state_name]):
			print(district_index + 1, ":")
			for candidate in state_result["districts"][district_index]["candidates"]:
				print("%30s\t%25s\t%d" % (candidate["name"], candidate["party"], candidate["votes"]))
			print("")
		print("")
	complete_results[year] = complete_year

json_output = open("results.json", "w")
json_output.write(json.dumps(complete_results))
json_output.close()
