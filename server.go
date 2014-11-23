// Copyright © 2014 Emily Maier

/*
The HTTP server that serves the results website.
*/
package main

import (
	"encoding/json"
	"encoding/xml"
	"fmt"
	"html/template"
	"io/ioutil"
	"net/http"
	"os"
	"regexp"
	"strconv"
	"strings"
)

type partyResult struct {
	Name          string  `xml:"name,attr"`
	Votes         int     `xml:"votes,attr"`
	SeatCount     int     `xml:"seatCount,attr"`
	ExpectedSeats float64 `xml:"expectedSeats,attr"`
}

type statePartyResult struct {
	partyResult
}

type seatCalculation struct {
	National         float64 `xml:"national,attr"`
	NationalWithout1 float64 `xml:"nationalWithout1,attr"`
	State            float64 `xml:"state,attr"`
}

type yearPartyResult struct {
	partyResult
	ExpectedSeatsFull seatCalculation `xml:"expectedSeats"`
	Seats             map[string][]int
}

type candidateResult struct {
	Name  string `xml:"name,attr"`
	Party string `xml:"party,attr"`
	Votes int    `xml:"votes,attr"`
}

type districtResult struct {
	TotalVotes int               `xml:"totalVotes,attr"`
	Winner     string            `xml:"winner,attr"`
	Margin     float64           `xml:"margin,attr"`
	Candidates []candidateResult `xml:"candidate"`
}

type stateResult struct {
	Name       string             `xml:"name,attr"`
	TotalVotes int                `xml:"totalVotes,attr"`
	TotalSeats int                `xml:"totalSeats,attr"`
	Parties    []statePartyResult `xml:"stateParty"`
	Districts  []districtResult   `xml:"district"`
}

type yearResult struct {
	Year       string            `xml:"year,attr"`
	TotalVotes int               `xml:"totalVotes,attr"`
	PartiesRaw []yearPartyResult `xml:"yearParty"`
	Parties    []yearPartyResult
	StatesRaw  []stateResult `xml:"state"`
	States     map[string]stateResult
}

type fullResult struct {
	YearsRaw []yearResult `xml:"year"`
	Years    map[string]yearResult
}

var years []string
var states []string

var results fullResult

var rootTemplate *template.Template
var yearTemplate *template.Template
var stateTemplate *template.Template

var configData map[string]string

func templateRenderPercentage(numerator, denominator int) string {
	return fmt.Sprintf("%.1f%%", float64(numerator*100)/float64(denominator))
}

func templateFractionToPercentage(fraction float64) string {
	return fmt.Sprintf("%.1f%%", fraction*100)
}

func templateRenderDistrict(number int) int {
	return number + 1
}

// Returns the string representing the dominant party and its excess seat bias
// (e.g. D+0.5).
func templatePartyBias(partiesRaw interface{}) string {
	var largestParty partyResult
	switch parties := partiesRaw.(type) {
	case []statePartyResult:
		largestParty = parties[0].partyResult
	case []yearPartyResult:
		largestParty = parties[0].partyResult
	default:
		panic("templatePartyBias: parameter of invalid type")
	}
	return fmt.Sprintf("%c+%.1f", largestParty.Name[0], float64(largestParty.SeatCount)-largestParty.ExpectedSeats)
}

// Returns the CSS class used to render the string in templatePartyBias.
func templatePartyBiasClass(partiesRaw interface{}) string {
	var largestParty partyResult
	switch parties := partiesRaw.(type) {
	case []statePartyResult:
		largestParty = parties[0].partyResult
	case []yearPartyResult:
		largestParty = parties[0].partyResult
	default:
		panic("templatePartyBiasClass: parameter of invalid type")
	}
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

func templateYearImage(year string) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("maps/%d.jpeg", (yearNum-1786)/2)
}

func templateYearImageSmall(year string) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("maps/%d-small.jpeg", (yearNum-1786)/2)
}

func templateStateImage(year, state string) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("maps/%d%s.jpeg", (yearNum-1786)/2, state)
}

func templateStateImageSmall(year, state string) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("maps/%d%s-small.jpeg", (yearNum-1786)/2, state)
}

func templateDistrictImage(year, state string, district int) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("maps/%d%s%d.jpeg", (yearNum-1786)/2, state, district+1)
}

func templateDistrictImageSmall(year, state string, district int) string {
	yearNum, _ := strconv.ParseInt(year, 10, 32)
	return fmt.Sprintf("maps/%d%s%d-small.jpeg", (yearNum-1786)/2, state, district+1)
}

func templateCommaNum(number int) string {
	if number < 1000 {
		return fmt.Sprintf("%d", number)
	}
	return templateCommaNum(number/1000) + fmt.Sprintf(",%03d", number%1000)
}

func templateChart(name string) template.HTML {
	chartFile, _ := os.Open("/var/lib/house/output/" + name + ".svg")
	chartData, _ := ioutil.ReadAll(chartFile)
	svgRegex, _ := regexp.Compile("(?s)<svg.*")
	return template.HTML(svgRegex.Find(chartData))
}

func templateRoot() string {
	return configData["root"]
}

func templatePartySeatList(seats map[string][]int) template.HTML {
	rendered := "<ol>"
	for _, state := range states {
		if districts, ok := seats[state]; ok {
			rendered += fmt.Sprintf("<li class=\"stateList\">%s %s</li>", state, fmt.Sprint(districts))
		}
	}
	rendered += "</ol>"
	return template.HTML(rendered)
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
		"yearResult": results.Years[year],
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
		"stateResult": results.Years[year].States[state],
	})
	if err != nil {
		panic(err.Error())
	}
}

func main() {
	file, _ := os.Open("stateInfo.json")
	jsonDecoder := json.NewDecoder(file)
	countryData := make(map[string][]string)
	jsonDecoder.Decode(&countryData)
	file.Close()
	years = countryData["years"]
	states = countryData["states"]

	file, _ = os.Open("config.json")
	jsonDecoder = json.NewDecoder(file)
	configData = make(map[string]string)
	jsonDecoder.Decode(&configData)
	file.Close()

	file, _ = os.Open("/var/lib/house/output/results.xml")
	xmlDecoder := xml.NewDecoder(file)
	xmlDecoder.Decode(&results)
	file.Close()
	results.Years = make(map[string]yearResult)
	for _, year := range results.YearsRaw {
		year.States = make(map[string]stateResult)
		for _, party := range year.PartiesRaw {
			party.ExpectedSeats = party.ExpectedSeatsFull.State
			party.Seats = make(map[string][]int)
			for _, state := range year.StatesRaw {
				var stateSeats []int
				i := 1
				for _, district := range state.Districts {
					if party.Name == district.Winner {
						stateSeats = append(stateSeats, i)
					}
					i += 1
				}
				if len(stateSeats) > 0 {
					party.Seats[state.Name] = stateSeats
				}
			}
			year.Parties = append(year.Parties, party)
		}
		for _, state := range year.StatesRaw {
			year.States[state.Name] = state
		}
		results.Years[year.Year] = year
	}

	funcMap := template.FuncMap{
		"renderPercentage":     templateRenderPercentage,
		"fractionToPercentage": templateFractionToPercentage,
		"renderDistrict":       templateRenderDistrict,
		"partyBias":            templatePartyBias,
		"partyBiasClass":       templatePartyBiasClass,
		"districtMargin":       templateDistrictMargin,
		"districtMarginClass":  templateDistrictMarginClass,
		"yearImage":            templateYearImage,
		"yearImageSmall":       templateYearImageSmall,
		"stateImage":           templateStateImage,
		"stateImageSmall":      templateStateImageSmall,
		"districtImage":        templateDistrictImage,
		"districtImageSmall":   templateDistrictImageSmall,
		"commaNum":             templateCommaNum,
		"chart":                templateChart,
		"root":                 templateRoot,
		"partySeatList":        templatePartySeatList,
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
	http.Handle("/charts/", http.StripPrefix("/charts/", http.FileServer(http.Dir("/var/lib/house/output/"))))
	http.Handle("/maps/", http.StripPrefix("/maps/", http.FileServer(http.Dir("/var/lib/house/output/"))))
	for _, year := range years {
		http.HandleFunc("/"+year, yearHandler)
		for _, state := range states {
			http.HandleFunc("/"+year+"/"+state, stateHandler)
		}
	}
	http.ListenAndServe(":8080", nil)
}
