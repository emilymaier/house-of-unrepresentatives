package main

import (
	"encoding/json"
	"fmt"
	"html/template"
	"io/ioutil"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"
)

type seatCalculation struct {
	National         float64
	NationalWithout1 float64
	State            float64
}

type partyResult struct {
	Name          string
	Votes         int
	SeatCount     int
	ExpectedSeats seatCalculation
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
	Winner     string
	Margin     float64
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

func templateFractionToPercentage(fraction float64) string {
	return fmt.Sprintf("%.1f%%", fraction*100)
}

func templateRenderDistrict(number int) int {
	return number + 1
}

func templatePartyBias(parties []partyResult) string {
	largestParty := parties[0]
	return fmt.Sprintf("%c+%.1f", largestParty.Name[0], float64(largestParty.SeatCount)-largestParty.ExpectedSeats.National)
}

func templatePartyBiasClass(parties []partyResult) string {
	largestParty := parties[0]
	if largestParty.Name == "Republican" {
		return "biasRepublican"
	}
	if largestParty.Name == "Democrat" {
		return "biasDemocrat"
	}
	return "biasIndependent"
}

func templateDistrictMargin(district districtResult) string {
	return fmt.Sprintf("%c+%.1f%%", district.Winner[0], district.Margin*100)
}

func templateDistrictMarginClass(district districtResult) string {
	if district.Winner == "Republican" {
		return "biasRepublican"
	}
	if district.Winner == "Democrat" {
		return "biasDemocrat"
	}
	return "biasIndependent"
}

func templateDistrictImage(year, state string, district int) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("%d%s%d.png", (yearNum-1786)/2, state, district+1)
}

func templateCommaNum(number int) string {
	if number < 1000 {
		return fmt.Sprintf("%d", number)
	}
	return templateCommaNum(number/1000) + fmt.Sprintf(",%03d", number%1000)
}

func templateChart(name string) template.HTML {
	chartFile, _ := os.Open("charts/" + name + ".svg")
	chartData, _ := ioutil.ReadAll(chartFile)
	svgRegex, _ := regexp.Compile("(?s)<svg.*")
	return template.HTML(svgRegex.Find(chartData))
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
	w.Write([]byte("<?xml version=\"1.0\" encoding=\"utf-8\"?>"))
	err := rootTemplate.Execute(w, map[string]interface{}{
		"years":   years,
		"states":  states,
		"results": results,
	})
	if err != nil {
		panic(err.Error())
	}
}

func yearHandler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte("<?xml version=\"1.0\" encoding=\"utf-8\"?>"))
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
	w.Write([]byte("<?xml version=\"1.0\" encoding=\"utf-8\"?>"))
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
		"renderPercentage":     templateRenderPercentage,
		"fractionToPercentage": templateFractionToPercentage,
		"renderDistrict":       templateRenderDistrict,
		"partyBias":            templatePartyBias,
		"partyBiasClass":       templatePartyBiasClass,
		"districtMargin":       templateDistrictMargin,
		"districtMarginClass":  templateDistrictMarginClass,
		"districtImage":        templateDistrictImage,
		"commaNum":             templateCommaNum,
		"chart":                templateChart,
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
	http.Handle("/districts/", http.StripPrefix("/districts/", http.FileServer(http.Dir("./districts/"))))
	for _, year := range years {
		http.HandleFunc("/"+year, yearHandler)
		for _, state := range states {
			http.HandleFunc("/"+year+"/"+state, stateHandler)
		}
	}
	http.ListenAndServe(":8080", nil)
}
