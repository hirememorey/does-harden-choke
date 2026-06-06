PYTHON ?= .venv/bin/python

.PHONY: venv scrape validate-scrape scrape-pbp build-possessions validate-possessions features screen-a screen-b screen-c visualize all clean test-client smoke-scrape

venv:
	python3 -m venv .venv
	$(PYTHON) -m pip install -r requirements.txt

scrape:
	$(PYTHON) src/scrape.py

validate-scrape:
	$(PYTHON) src/validate_scrape.py

# Pass 2 Step 1 spike: 3 validation games
scrape-pbp:
	$(PYTHON) src/pass2/ingest_pbp.py --validation

build-possessions:
	$(PYTHON) src/pass2/possessions.py --validation

validate-possessions:
	$(PYTHON) src/pass2/validate_possessions.py --validation

features:
	$(PYTHON) src/features.py

screen-a:
	$(PYTHON) src/screen_a.py

screen-b:
	$(PYTHON) src/screen_b.py

screen-c:
	$(PYTHON) src/screen_c.py

visualize:
	$(PYTHON) src/visualize.py

test-client:
	$(PYTHON) src/nba_client.py

# Quick smoke test: Harden 2023-24 only
smoke-scrape:
	$(PYTHON) src/scrape.py --players "James Harden" --seasons 2023-24

all: scrape features screen-a screen-b screen-c visualize

clean:
	rm -rf data/processed/ output/figures/
