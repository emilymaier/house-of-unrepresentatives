package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strings"
)

type partyResult struct {
	Name  string
	Votes int
	Seats int
}

type candidateResult struct {
	Name  string
	Party string
	Votes int
}

type districtResult struct {
	TotalVotes int
	Candidates []candidateResult
}

type stateResult struct {
	TotalVotes int
	TotalSeats int
	Parties    []partyResult
	Districts  []districtResult
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
	for _, currentParty := range results[year][state].Parties {
		fmt.Fprintf(w, "<tr><td>%s</td><td>%d</td><td>%.1f%%</td><td>%d</td><td>%.1f%%</td></tr>", currentParty.Name, currentParty.Votes, float64(currentParty.Votes*100)/float64(results[year][state].TotalVotes), currentParty.Seats, float64(currentParty.Seats*100)/float64(results[year][state].TotalSeats))
	}
	fmt.Fprintf(w, "<tr><td>Total</td><td>%d</td><td></td><td>%d</td><td></td></tr>", results[year][state].TotalVotes, results[year][state].TotalSeats)
	fmt.Fprint(w, "</tbody></table>")
	for districtNumber, currentDistrict := range results[year][state].Districts {
		fmt.Fprintf(w, "<h2>District %d</h2>", districtNumber+1)
		fmt.Fprint(w, "<table><thead><th>Candidate</th><th>Party</th><th>Votes</th><th>Percentage</th></thead><tbody>")
		for _, currentCandidate := range currentDistrict.Candidates {
			fmt.Fprintf(w, "<tr><td>%s</td><td>%s</td><td>%d</td><td>%.1f%%</td></tr>", currentCandidate.Name, currentCandidate.Party, currentCandidate.Votes, float64(currentCandidate.Votes*100)/float64(currentDistrict.TotalVotes))
		}
		fmt.Fprintf(w, "<tr><td>Total</td><td></td><td>%d</td></tr>", currentDistrict.TotalVotes)
		fmt.Fprint(w, "</tbody></table>")
	}
}

func main() {
	file, _ := os.Open("stateInfo.json")
	jsonDecoder := json.NewDecoder(file)
	configData := make(map[string][]string)
	jsonDecoder.Decode(&configData)
	file.Close()
	years = configData["years"]
	states = configData["states"]

	file, _ = os.Open("results.json")
	jsonDecoder = json.NewDecoder(file)
	jsonDecoder.Decode(&results)
	file.Close()

	http.HandleFunc("/", rootHandler)
	for _, year := range years {
		http.HandleFunc("/"+year, yearHandler)
		for _, state := range states {
			http.HandleFunc("/"+year+"/"+state, stateHandler)
		}
	}
	http.ListenAndServe(":8080", nil)
}
