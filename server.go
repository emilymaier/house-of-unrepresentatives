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

var rootTemplate *template.Template
var yearTemplate *template.Template
var stateTemplate *template.Template

func templateRenderPercentage(numerator, denominator int) string {
	return fmt.Sprintf("%.1f%%", float64(numerator*100)/float64(denominator))
}

func templateRenderDistrict(number int) int {
	return number + 1
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
	err := rootTemplate.Execute(w, years)
	if err != nil {
		panic(err.Error())
	}
}

func yearHandler(w http.ResponseWriter, r *http.Request) {
	year := parseYear(r.URL.Path)
	err := yearTemplate.Execute(w, map[string]interface{}{"year": year, "states": states})
	if err != nil {
		panic(err.Error())
	}
}

func stateHandler(w http.ResponseWriter, r *http.Request) {
	year := parseYear(r.URL.Path)
	state := parseState(r.URL.Path)
	err := stateTemplate.Execute(w, map[string]interface{}{
		"year":       year,
		"state":      state,
		"totalVotes": results[year][state].TotalVotes,
		"totalSeats": results[year][state].TotalSeats,
		"parties":    results[year][state].Parties,
		"districts":  results[year][state].Districts,
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

	var err error
	rootTemplate, err = template.ParseFiles("html/root.html")
	if err != nil {
		fmt.Println(err.Error())
		return
	}
	yearTemplate, err = template.ParseFiles("html/year.html")
	if err != nil {
		fmt.Println(err.Error())
		return
	}
	funcMap := template.FuncMap{
		"renderPercentage": templateRenderPercentage,
		"renderDistrict":   templateRenderDistrict,
	}
	stateTemplate = template.New("state.html")
	stateTemplate = stateTemplate.Funcs(funcMap)
	stateTemplate, err = stateTemplate.ParseFiles("html/state.html")
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
