#!/usr/bin/python3
# Copyright © 2014 Emily Maier
# Generates results.json that holds all of the extracted election data.

import bs4
import json
import operator
import os
import psycopg2
import re
import sys
import time

json_input = open(os.path.dirname(os.path.realpath(__file__)) + "/stateInfo.json", "r")
config_data = json.loads(json_input.read())
json_input.close()
state_names = config_data["states"]

apportionment_1992 = dict(zip(state_names, config_data["apportionment_1992"]))
apportionment_2002 = dict(zip(state_names, config_data["apportionment_2002"]))
apportionment_2012 = dict(zip(state_names, config_data["apportionment_2012"]))

pg_conn = psycopg2.connect(database="gis")
pg_cursor = pg_conn.cursor()
pg_cursor.execute("create table results (year integer, state text, district integer, winner text)")

# Add a (possibly) new candidate to this district.
def finalize_candidate(district, candidate_string, votes):
	new_candidate = {"name": "", "party": "", "votes": votes}

	# a bunch of ugly code to try to figure out the candidate's party.
	# this is much harder than you would think
	if "Don Sherwood" in candidate_string:
		split_candidate = ["Don Sherwood", "Republican"]
	elif ", Democrat" in candidate_string:
		split_candidate = [candidate_string.split(", Democrat")[0], "Democrat"]
	elif ", Republican" in candidate_string:
		split_candidate = [candidate_string.split(", Republican")[0], "Republican"]
	else:
		split_candidate = candidate_string.rsplit(", ", 1)
	if len(split_candidate) == 1:
		if len(district["candidates"]) > 0 and split_candidate[0] != "Blank/Scattering" and split_candidate[0] != "Other" and split_candidate[0] != "Write-in" and split_candidate[0] != "Unenrolled" and split_candidate[0] != "Scattering" and split_candidate[0] != "No Vote Cast" and split_candidate[0] != "Unaffiliated" and split_candidate[0] != "Over Vote" and split_candidate[0] != "Other Candidates" and split_candidate[0] != "Blank/Void/Scattering":
			# electoral fusion
			district["candidates"][-1]["votes"] += votes
			return
		split_candidate = ["", split_candidate[0]]
	new_candidate["name"], new_candidate["party"] = split_candidate[0], split_candidate[1]
	district["candidates"].append(new_candidate)

# Finish processing this district and add it to the state results.
def finalize_district(state_result, district):
	for candidate in district["candidates"]:
		district["totalVotes"] += candidate["votes"]
	state_result["districts"].append(district)

# Verify that the correct number of districts have been parsed for this state,
# performs per-party calculations for the state's overall results, and add it
# all to the national results.
def finalize_state(year, state, year_result, state_result):
	if year >= 1992 and year < 2002:
		current_apportionment = apportionment_1992
	elif year >= 2002 and year < 2012:
		current_apportionment = apportionment_2002
	elif year >= 2012 and year < 2022:
		current_apportionment = apportionment_2012
	if current_apportionment[state] != len(state_result["districts"]):
		print("%d: %s: Incorrect number of districts parsed, expected %d, got %d" % (year, state, current_apportionment[state], len(state_result["districts"])))
		print(state_result)
		quit()
	state_result["totalSeats"] = current_apportionment[state]
	unsorted_parties = {}
	district_number = 1
	for district in state_result["districts"]:
		state_result["totalVotes"] += district["totalVotes"]
		winner_party = ""
		winner_votes = 0
		second_votes = 0
		for candidate in district["candidates"]:
			if candidate["votes"] > winner_votes:
				winner_party = candidate["party"]
				second_votes = winner_votes
				winner_votes = candidate["votes"]
			elif candidate["votes"] > second_votes:
				second_votes = candidate["votes"]
			if candidate["party"] not in unsorted_parties:
				unsorted_parties[candidate["party"]] = {"name": candidate["party"], "votes": 0, "seatCount": 0, "expectedSeats": {"national": 0}, "seats": []}
			unsorted_parties[candidate["party"]]["votes"] += candidate["votes"]
		district["winner"] = winner_party
		district["margin"] = float(winner_votes - second_votes) / district["totalVotes"]
		unsorted_parties[winner_party]["seatCount"] += 1
		unsorted_parties[winner_party]["seats"].append(district_number)
		pg_cursor.execute("insert into results values(%d, '%s', %d, '%s')" % (year, state, district_number, winner_party))
		district_number += 1
	for party in unsorted_parties.values():
		party["expectedSeats"]["national"] = float(party["votes"]) * state_result["totalSeats"] / state_result["totalVotes"]
	state_result["parties"] = sorted(unsorted_parties.values(), key=lambda party: party["seatCount"] * 1000000000 + party["votes"], reverse=True)

	print("")
	print("")
	print(state)
	i = 1
	for district in state_result["districts"]:
		print("")
		print("District %d" % i)
		for candidate in district["candidates"]:
			print("%30s\t%25s\t%d" % (candidate["name"], candidate["party"], candidate["votes"]))
		i += 1

	year_result["states"][state] = state_result

# Calculates the national results for this election.
def finalize_year(year, complete_results, year_result):
	unsorted_parties = {}
	for state_name, state in sorted(year_result["states"].items()):
		year_result["totalVotes"] += state["totalVotes"]
		for party in state["parties"]:
			if party["name"] not in unsorted_parties:
				unsorted_parties[party["name"]] = {"name": party["name"], "votes": 0, "seatCount": 0, "expectedSeats": {"national": 0, "nationalWithout1": 0, "state": 0}, "seats": []}
			unsorted_parties[party["name"]]["votes"] += party["votes"]
			unsorted_parties[party["name"]]["seatCount"] += party["seatCount"]
			if len(party["seats"]) > 0:
				unsorted_parties[party["name"]]["seats"].append((state_name, party["seats"]))
	for party in unsorted_parties.values():
		party["expectedSeats"]["national"] = float(party["votes"]) * 435 / year_result["totalVotes"]
		multi_district_votes_total = 0
		multi_district_votes_party = 0
		for state in year_result["states"].values():
			if state["totalSeats"] > 1:
				for state_party in state["parties"]:
					if state_party["name"] == party["name"]:
						multi_district_votes_party += state_party["votes"]
						break
				multi_district_votes_total += state["totalVotes"]
			for state_party in state["parties"]:
				if state_party["name"] == party["name"]:
					party["expectedSeats"]["state"] += state_party["expectedSeats"]["national"]
		party["expectedSeats"]["nationalWithout1"] = float(multi_district_votes_party) * 435 / multi_district_votes_total

	year_result["parties"] = sorted(unsorted_parties.values(), key=lambda party: party["seatCount"] * 1000000000 + party["votes"], reverse=True)
	complete_results[year] = year_result

# handwritten context-sensitive parser ahead, beware!
complete_results = {}
for year in range(1998, 2014, 2):
	year_result = {"totalVotes": 0, "parties": [], "states": {}}
	state_result = {"totalVotes": 0, "totalSeats": 0, "parties": [], "districts": []}
	district = {"totalVotes": 0, "candidates": [], "winner": "", "margin": 0}
	election_soup = bs4.BeautifulSoup(open("temp/" + str(year) + "elections.html", "r"))
	current_candidate = ""
	current_line = election_soup.find(text=re.compile("FOR UNITED STATES REPRESENTATIVE")).next_sibling.next_sibling
	state_index = 0
	while True:
		if current_line.string:
			current_string = current_line.string[1:] # remove newline
			match = re.compile("(.*) \.").search(current_string)
			if match:
				# ... sequence
				current_string = match.group(1)
				current_candidate += current_string
				match = re.compile("[0-9]+\.[  ](.*)").search(current_candidate)
				if match: # new district
					if len(district["candidates"]) > 0:
						finalize_district(state_result, district)
						district = {"totalVotes": 0, "candidates": [], "winner": "", "margin": 0}
					current_string = match.group(1)
					current_candidate = current_string
			else:
				if current_string == "AT LARGE" or current_string == "AT LARGE ":
					pass
				elif current_string[:7] == "VerDate":
					# go to beginning of next page
					while True:
						if current_string == "\nFOR UNITED STATES REPRESENTATIVE—Continued":
							break
						if current_line.name == "i":
							current_line = current_line.previous_sibling.previous_sibling
							break
						current_line = current_line.next_sibling
						if current_line.string:
							current_string = current_line.string
					current_line = current_line.next_sibling
				elif current_string == "FOR UNITED STATES REPRESENTATIVE—Continued":
					current_line = current_line.next_sibling
				elif current_string[:7] == "(Runoff":
					current_line = current_line.next_sibling
				elif current_string != "":
					if current_string[:2] == "1 ":
						# remove vote count footnote
						current_string = current_string[2:]
					try:
						current_votes = int(current_string.replace(",", ""))
						finalize_candidate(district, current_candidate, current_votes)
						current_candidate = ""
					except ValueError:
						# partial candidate name or footnote
						if current_string == "(1 )" or current_string == "(2 )" or current_string == "(1 ) " or current_string == "(2) ":
							finalize_candidate(district, current_candidate, 1)
							current_candidate = ""
						else:
							current_candidate += current_string
		current_line = current_line.next_sibling
		if current_line.name == "i": # go to next state
			if current_line.string[:6] == "Due to":
				current_line = current_line.next_sibling.next_sibling.next_sibling.next_sibling.next_sibling
				continue
			finalize_district(state_result, district)
			district = {"totalVotes": 0, "candidates": []}

			# special cases for when nothing else will work
			if year == 1998 and state_names[state_index] == "Texas":
				state_result["districts"][18] = {"totalVotes": 129428, "candidates": [{"name": "Larry Combest", "party": "Republican", "votes": 108266}, {"name": "Sidney Blankenship", "party": "Democrat", "votes": 21162}]}
				state_result["districts"].insert(19, {"totalVotes": 79713, "candidates": [{"name": "James Walker", "party": "Republican", "votes": 28347}, {"name": "Charlie Gonzalez", "party": "Democrat", "votes": 50356}, {"name": "Alejandro (Alex) DePena", "party": "Libertarian", "votes": 1010}]})
			elif year == 2002 and state_names[state_index] == "Louisiana":
				state_result["districts"] = state_result["districts"][:7]
				state_result["districts"][4] = {"totalVotes": 172462, "candidates": [{"name": "Lee Fletcher", "party": "Republican", "votes": 85744}, {"name": "Rodney Alexander", "party": "Democrat", "votes": 86718}]}
			elif year == 2006 and state_names[state_index] == "Texas":
				state_result["districts"][3] = state_result["districts"][-1]
				state_result["districts"] = state_result["districts"][:-1]
				state_result["districts"][25] = state_result["districts"][2]
				state_result["districts"].remove(state_result["districts"][2])
				state_result["districts"].insert(18, state_result["districts"].pop(0))
				state_result["districts"].insert(23, state_result["districts"].pop(0))
				state_result["districts"].insert(25, state_result["districts"].pop(0))
				state_result["districts"].insert(25, state_result["districts"].pop(0))
				state_result["districts"].insert(28, state_result["districts"].pop(0))
			elif year == 2008 and state_names[state_index] == "Louisiana":
				state_result["districts"][1] = {"totalVotes": 66882, "candidates": [{"name": "William J. Jefferson", "party": "Democrat", "votes": 31318}, {"name": "Anh \"Joseph\" Cao", "party": "Republican", "votes": 33132}, {"name": "Gregory W. Kahn", "party": "Libertarian", "votes": 549}, {"name": "Malik Rahim", "party": "Green", "votes": 1883}]}
				state_result["districts"][3] = {"totalVotes": 92572, "candidates": [{"name": "Paul J. Carmouche", "party": "Democrat", "votes": 44151}, {"name": "John Fleming", "party": "Republican", "votes": 44501}, {"name": "Chester T. \"Catfish\" Kelley", "party": "No Party Affiliation", "votes": 3245}, {"name": "Gerard J. Bowen, Jr.", "party": "Other", "votes": 675}]}

			finalize_state(year, state_names[state_index], year_result, state_result)
			state_result = {"totalVotes": 0, "totalSeats": 0, "parties": [], "districts": []}

			current_line = current_line.find_next_sibling(text=re.compile("FOR UNITED STATES REPRESENTATIVE($|[^—])"))
			if not current_line:
				break
			current_line = current_line.next_sibling.next_sibling
			state_index += 1
			current_candidate = ""
		elif current_line.name == "a" or (current_line.string and (current_line.string == "\n(42)" or current_line.string[:8] == "\nVerDate")):
			# go to beginning of next page
			while not current_line.string or (current_line.string != "FOR UNITED STATES REPRESENTATIVE—Continued" and current_line.string != "\nFOR UNITED STATES REPRESENTATIVE—Continued" and current_line.string != "\n(General Election)2—Continued" and current_line.string != "\nFOR UNITED STATES REPRESENTATIVE—Continued "):
				if current_line.name == "i":
					current_line = current_line.previous_sibling.previous_sibling.previous_sibling
					break
				if current_line.string and current_line.string == "—Continued":
					break
				current_line = current_line.next_sibling
			current_line = current_line.next_sibling.next_sibling
	finalize_year(year, complete_results, year_result)

json_output = open("../output/results.json", "w")
json_output.write(json.dumps(complete_results))
json_output.close()

pg_conn.commit()
