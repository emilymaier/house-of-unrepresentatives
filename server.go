package main

import (
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"os"
	"strings"
)

type partyResult struct {
	Name          string
	Votes         int
	SeatCount     int
	ExpectedSeats float64
	Seats         []interface{}
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

type yearResult struct {
	TotalVotes int
	TotalSeats int // needed for template duck typing
	Parties    []partyResult
	States     map[string]stateResult
}

var years []string
var states []string

var results map[string]yearResult

var rootTemplate *template.Template
var yearTemplate *template.Template
var stateTemplate *template.Template

func templateRenderPercentage(numerator, denominator int) string {
	return fmt.Sprintf("%.1f%%", float64(numerator*100)/float64(denominator))
}

func templateRenderDistrict(number int) int {
	return number + 1
}

func templateLargestPartyDiff(parties []partyResult) string {
	largestParty := parties[0]
	return string(largestParty.Name[0]) + "+" + fmt.Sprintf("%.1f", float64(largestParty.SeatCount)-largestParty.ExpectedSeats)
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
	err := rootTemplate.Execute(w, map[string]interface{}{
		"years":  years,
		"states": states,
	})
	if err != nil {
		panic(err.Error())
	}
}

func yearHandler(w http.ResponseWriter, r *http.Request) {
	year := parseYear(r.URL.Path)
	err := yearTemplate.Execute(w, map[string]interface{}{
		"years":      years,
		"year":       year,
		"states":     states,
		"yearResult": results[year],
	})
	if err != nil {
		panic(err.Error())
	}
}

func stateHandler(w http.ResponseWriter, r *http.Request) {
	year := parseYear(r.URL.Path)
	state := parseState(r.URL.Path)
	err := stateTemplate.Execute(w, map[string]interface{}{
		"years":       years,
		"year":        year,
		"states":      states,
		"state":       state,
		"stateResult": results[year].States[state],
	})
	if err != nil {
		panic(err.Error())
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
	for year, yearResult := range results {
		yearResult.TotalSeats = 435
		results[year] = yearResult
	}

	funcMap := template.FuncMap{
		"renderPercentage": templateRenderPercentage,
		"renderDistrict":   templateRenderDistrict,
		"largestPartyDiff": templateLargestPartyDiff,
	}

	var err error
	rootTemplate = template.New("root.html")
	rootTemplate = rootTemplate.Funcs(funcMap)
	rootTemplate, err = rootTemplate.ParseFiles("html/root.html", "html/header.html", "html/footer.html", "html/sidebar.html")
	if err != nil {
		fmt.Println(err.Error())
		return
	}
	yearTemplate = template.New("year.html")
	yearTemplate = yearTemplate.Funcs(funcMap)
	yearTemplate, err = yearTemplate.ParseFiles("html/year.html", "html/header.html", "html/footer.html", "html/sidebar.html")
	if err != nil {
		fmt.Println(err.Error())
		return
	}
	stateTemplate = template.New("state.html")
	stateTemplate = stateTemplate.Funcs(funcMap)
	stateTemplate, err = stateTemplate.ParseFiles("html/state.html", "html/header.html", "html/footer.html", "html/sidebar.html")
	if err != nil {
		fmt.Println(err.Error())
		return
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
