package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sort"
	"strings"
)

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
	partyNames []string
	partyVotes []int
	totalVotes int
	districts  []districtResult
}

type sortedPartyVotes struct {
	parties []string
	votes   []int
}

var years []string
var states []string

var results map[string]map[string]stateResult

func (this sortedPartyVotes) Len() int {
	return len(this.parties)
}

func (this sortedPartyVotes) Swap(i, j int) {
	this.parties[i], this.parties[j] = this.parties[j], this.parties[i]
	this.votes[i], this.votes[j] = this.votes[j], this.votes[i]
}

func (this sortedPartyVotes) Less(i, j int) bool {
	return this.votes[i] > this.votes[j]
}

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
	fmt.Fprint(w, "<table><tbody>")
	for i, currentPartyName := range results[year][state].partyNames {
		fmt.Fprintf(w, "<tr><td>%s</td><td>%d</td></tr>", currentPartyName, results[year][state].partyVotes[i])
	}
	fmt.Fprintf(w, "<tr><td>Total</td><td>%d</td></tr>", results[year][state].totalVotes)
	fmt.Fprint(w, "</tbody></table>")
	for districtNumber, currentDistrict := range results[year][state].districts {
		fmt.Fprintf(w, "<h2>District %d</h2>", districtNumber+1)
		fmt.Fprint(w, "<table><tbody>")
		for _, currentCandidate := range currentDistrict.candidates {
			fmt.Fprintf(w, "<tr><td>%s</td><td>%s</td><td>%d</td></tr>", currentCandidate.name, currentCandidate.party, currentCandidate.votes)
		}
		fmt.Fprintf(w, "<tr><td>Total</td><td></td><td>%d</td></tr>", currentDistrict.totalVotes)
		fmt.Fprint(w, "</tbody></table>")
	}
}

func main() {
	file, _ := os.Open("data.json")
	jsonDecoder := json.NewDecoder(file)
	configData := make(map[string][]string)
	jsonDecoder.Decode(&configData)
	file.Close()
	years = configData["years"]
	states = configData["states"]

	resultsRaw := make(map[string]map[string][][][]interface{})
	for _, year := range years {
		file, _ := os.Open("json/" + year + ".json")
		jsonDecoder := json.NewDecoder(file)
		currentResults := make(map[string][][][]interface{})
		jsonDecoder.Decode(&currentResults)
		file.Close()
		resultsRaw[year] = currentResults
	}

	results = make(map[string]map[string]stateResult)
	for year, resultsRawYear := range resultsRaw {
		results[year] = make(map[string]stateResult)
		for state, resultsRawState := range resultsRawYear {
			var newState stateResult
			newState.districts = make([]districtResult, 0)
			tempPartyVotes := make(map[string]int)
			for _, resultsRawDistrict := range resultsRawState {
				var newDistrict districtResult
				newDistrict.candidates = make([]candidateResult, 0)
				for _, resultsRawCandidate := range resultsRawDistrict {
					var newCandidate candidateResult
					newCandidate.name = resultsRawCandidate[0].(string)
					newCandidate.party = resultsRawCandidate[1].(string)
					newCandidate.votes = int(resultsRawCandidate[2].(float64))
					newDistrict.candidates = append(newDistrict.candidates, newCandidate)
					newDistrict.totalVotes += newCandidate.votes
					newState.totalVotes += newCandidate.votes
					tempPartyVotes[newCandidate.party] += newCandidate.votes
				}
				newState.districts = append(newState.districts, newDistrict)
			}
			sorter := sortedPartyVotes{make([]string, 0), make([]int, 0)}
			for currentParty, currentVotes := range tempPartyVotes {
				sorter.parties = append(sorter.parties, currentParty)
				sorter.votes = append(sorter.votes, currentVotes)
			}
			sort.Sort(sorter)
			newState.partyNames = sorter.parties
			newState.partyVotes = sorter.votes
			results[year][state] = newState
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
