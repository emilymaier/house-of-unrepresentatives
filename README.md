# house-of-unrepresentatives

This is a project to publish and analyze US House of Representatives election
results.

Detailed election results are surprisingly difficult to come by. Although they
are available on many websites, they aren't published in a form that's easily
processed in code. This project starts with the PDFs of official election
results published by the House Clerk. The text is then extracted and parsed into
a single JSON file that contains all of the results.

Although more analysis is planned, currently only a few graphs and statistics
from the results are generated. Each party in each state gets an expected seat
count based on the overall state popular vote, and those state-level numbers are
aggregated into a national expected seat total. The project also generates
cumulative distribution charts showing the party win margins by district.

The project also generates maps at the national, state, and district levels to
help illustrate election results as well as the shapes of districts that are
created by politicians.

## Usage

To generate election results, fetchpdfs.sh pulls them all from the House clerk
site. Then, parsepdfs.sh generates the results.json file that stores the parsed
and processed results.

The election charts are generated by render.py, while all of the maps are
generated by maps.py.

The website is served by server.go.

## Configuration

The only configuration needed is config.json. It's a JSON object with a single
string field, "root", that specifies the root path of the website. This allows
the server to generate correct URLs regardless of where the site is placed
inside your website.

## results.json

### root

{"1998": year, "2000": year, ...}

### year

{"totalVotes": int, "totalSeats": int, "parties": party, "states": state}

### party

{"name": string, "votes": int, "seatCount": int, "expectedSeats": [float],
seats: [seat]}

### state

{"totalVotes": int, "totalSeats": int, "parties": party, "districts": district}

### seat

int or [string, [int]]

### district

{"totalVotes": int, "candidates": candidate, "winner": string, "margin": float}

### candidate

{"name": string, "party": string, "votes": string}
