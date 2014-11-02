package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
)

type partyResult struct {
	name  string
	votes int
	seats int
}

type candidateResult struct {
	name  string
	party string
	votes int
}

type districtResult struct {
	totalVotes int
	candidates []candidateResult
}

type stateResult struct {
	totalVotes int
	totalSeats int
	parties    []partyResult
	districts  []districtResult
}

var years []string
var states []string

var results map[string]map[string]stateResult

func parseYear(url string) string {
	for _, year := range years {
		if strings.HasPrefix(url, "/"+year) {
			return year
		}
	}
	return ""
}

func parseState(url string) string {
	for _, state := range states {
		if strings.HasPrefix(url[5:], "/"+state) {
			return state
		}
	}
	return ""
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprint(w, "<h1>House of Representatives Election Results</h1>")
	for _, year := range years {
		fmt.Fprintf(w, "<a href=/%s>%s</a> ", year, year)
	}
}

func yearHandler(w http.ResponseWriter, r *http.Request) {
	year := parseYear(r.URL.Path)
	fmt.Fprintf(w, "<h1>%s</h1>", year)
	fmt.Fprint(w, "<a href=/>Home</a><br /><br />")
	for _, state := range states {
		fmt.Fprintf(w, "<a href=/%s/%s>%s</a> ", year, state, state)
	}
}

func stateHandler(w http.ResponseWriter, r *http.Request) {
	year := parseYear(r.URL.Path)
	state := parseState(r.URL.Path)
	fmt.Fprintf(w, "<h1>%s — %s</h1>", year, state)
	fmt.Fprintf(w, "<a href=/>Home</a> <a href=/%s>%s</a>", year, year)
	fmt.Fprint(w, "<h2>Overall Results</h2>")
	fmt.Fprint(w, "<table><thead><th>Party</th><th>Votes</th><th></th><th>Seats</th><th></th></thead><tbody>")
	for _, currentParty := range results[year][state].parties {
		fmt.Fprintf(w, "<tr><td>%s</td><td>%d</td><td>%.1f%%</td><td>%d</td><td>%.1f%%</td></tr>", currentParty.name, currentParty.votes, float64(currentParty.votes*100)/float64(results[year][state].totalVotes), currentParty.seats, float64(currentParty.seats*100)/float64(results[year][state].totalSeats))
	}
	fmt.Fprintf(w, "<tr><td>Total</td><td>%d</td><td></td><td>%d</td><td></td></tr>", results[year][state].totalVotes, results[year][state].totalSeats)
	fmt.Fprint(w, "</tbody></table>")
	for districtNumber, currentDistrict := range results[year][state].districts {
		fmt.Fprintf(w, "<h2>District %d</h2>", districtNumber+1)
		fmt.Fprint(w, "<table><thead><th>Candidate</th><th>Party</th><th>Votes</th><th>Percentage</th></thead><tbody>")
		for _, currentCandidate := range currentDistrict.candidates {
			fmt.Fprintf(w, "<tr><td>%s</td><td>%s</td><td>%d</td><td>%.1f%%</td></tr>", currentCandidate.name, currentCandidate.party, currentCandidate.votes, float64(currentCandidate.votes*100)/float64(currentDistrict.totalVotes))
		}
		fmt.Fprintf(w, "<tr><td>Total</td><td></td><td>%d</td></tr>", currentDistrict.totalVotes)
		fmt.Fprint(w, "</tbody></table>")
	}
}

func parseRawState(resultsRawState map[string]interface{}) stateResult {
	var newState stateResult
	newState.totalVotes = int(resultsRawState["totalVotes"].(float64))
	newState.totalSeats = int(resultsRawState["totalSeats"].(float64))
	newState.parties = make([]partyResult, 0)
	for _, resultsRawParty := range resultsRawState["parties"].([]interface{}) {
		var newParty partyResult
		newParty.name = resultsRawParty.(map[string]interface{})["name"].(string)
		newParty.votes = int(resultsRawParty.(map[string]interface{})["votes"].(float64))
		newParty.seats = int(resultsRawParty.(map[string]interface{})["seats"].(float64))
		newState.parties = append(newState.parties, newParty)
	}
	newState.districts = make([]districtResult, 0)
	for _, resultsRawDistrict := range resultsRawState["districts"].([]interface{}) {
		var newDistrict districtResult
		newDistrict.totalVotes = int(resultsRawDistrict.(map[string]interface{})["totalVotes"].(float64))
		newDistrict.candidates = make([]candidateResult, 0)
		for _, resultsRawCandidate := range resultsRawDistrict.(map[string]interface{})["candidates"].([]interface{}) {
			var newCandidate candidateResult
			newCandidate.name = resultsRawCandidate.(map[string]interface{})["name"].(string)
			newCandidate.party = resultsRawCandidate.(map[string]interface{})["party"].(string)
			newCandidate.votes = int(resultsRawCandidate.(map[string]interface{})["votes"].(float64))
			newDistrict.candidates = append(newDistrict.candidates, newCandidate)
		}
		newState.districts = append(newState.districts, newDistrict)
	}
	return newState
}

func main() {
	file, _ := os.Open("stateInfo.json")
	jsonDecoder := json.NewDecoder(file)
	configData := make(map[string][]string)
	jsonDecoder.Decode(&configData)
	file.Close()
	years = configData["years"]
	states = configData["states"]

	resultsRaw := make(map[string]map[string]interface{})
	file, _ = os.Open("results.json")
	jsonDecoder = json.NewDecoder(file)
	jsonDecoder.Decode(&resultsRaw)
	file.Close()

	results = make(map[string]map[string]stateResult)
	for year, resultsRawYear := range resultsRaw {
		results[year] = make(map[string]stateResult)
		for state, resultsRawState := range resultsRawYear {
			results[year][state] = parseRawState(resultsRawState.(map[string]interface{}))
		}
	}

	http.HandleFunc("/", rootHandler)
	for _, year := range years {
		http.HandleFunc("/"+year, yearHandler)
		for _, state := range states {
			http.HandleFunc("/"+year+"/"+state, stateHandler)
		}
	}
	http.ListenAndServe(":8080", nil)
}
