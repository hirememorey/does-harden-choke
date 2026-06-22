PYTHON ?= .venv/bin/python

.PHONY: venv scrape validate-scrape scrape-pbp build-possessions validate-possessions features screen-a screen-a-adj screen-e screen-f retention screen-b screen-c visualize all clean test-client smoke-scrape event-frequency trigger-sensitivity join-causal mechanism-descriptives mechanism-models causal-chain architecture-model scrape-shot-charts validate-shot-charts shot-chart-features rq-model fta-deepdive foul-type-scrape-harden foul-type-scrape-harden-po foul-type-scrape-giannis foul-type-scrape-giannis-po foul-type-classify-harden foul-type-classify-giannis foul-type-llm-validate-harden foul-type-llm-harden foul-type-llm-harden-po foul-type-llm-giannis foul-type-llm-giannis-po foul-type-alpha foul-type-serve

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

screen-a-adj:
	$(PYTHON) src/screen_a_adj.py

screen-e:
	$(PYTHON) src/screen_e.py

screen-f:
	$(PYTHON) src/screen_f.py

retention:
	$(PYTHON) src/rs_retention_baseline.py

event-frequency:
	$(PYTHON) src/pass2/event_frequency.py

trigger-sensitivity:
	$(PYTHON) src/trigger_sensitivity.py

join-causal:
	$(PYTHON) src/join_causal_table.py

mechanism-descriptives: join-causal
	$(PYTHON) src/mechanism_descriptives.py

mechanism-models: join-causal
	$(PYTHON) src/mechanism_models.py

causal-chain: mechanism-descriptives mechanism-models

architecture-model:
	$(PYTHON) src/architecture_model.py

scrape-shot-charts:
	$(PYTHON) src/scrape_shot_charts.py --resume

validate-shot-charts:
	$(PYTHON) src/validate_shot_charts.py

shot-chart-features:
	$(PYTHON) src/shot_chart_features.py

rq-model:
	$(PYTHON) src/rq_multilevel_model.py

fta-deepdive:
	$(PYTHON) src/fta_dependency_deepdive.py

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

scrape-team-logs:
	$(PYTHON) src/scrape_team_logs.py --resume

validate-team-logs:
	$(PYTHON) src/validate_team_logs.py

smoke-team-logs:
	$(PYTHON) -c "from src.scrape_team_logs import collect_team_season_keys, scrape_team_logs; keys=collect_team_season_keys(); scrape_team_logs(keys[keys['season']=='2023-24'].head(5), force=True)"

# Foul-type video classification (Phase E — alpha test)
foul-type-scrape-harden:
	PYTHONPATH=. $(PYTHON) src/foul_type_scraper.py --player "James Harden" --season 2019-20 --games 5

foul-type-scrape-harden-po:
	PYTHONPATH=. $(PYTHON) src/foul_type_scraper.py --player "James Harden" --season 2019-20 --games 5 --season-type Playoffs

foul-type-scrape-giannis:
	PYTHONPATH=. $(PYTHON) src/foul_type_scraper.py --player "Giannis Antetokounmpo" --season 2023-24 --games 5

foul-type-scrape-giannis-po:
	PYTHONPATH=. $(PYTHON) src/foul_type_scraper.py --player "Giannis Antetokounmpo" --season 2023-24 --games 5 --season-type Playoffs

foul-type-classify-harden:
	PYTHONPATH=. $(PYTHON) src/foul_type_classifier.py --manifest data/processed/foul_type_manifest_james_harden.json

foul-type-classify-giannis:
	PYTHONPATH=. $(PYTHON) src/foul_type_classifier.py --manifest data/processed/foul_type_manifest_giannis_antetokounmpo.json

# LLM grading (Gemini recommended — native video understanding)
foul-type-llm-validate-harden:
	PYTHONPATH=. $(PYTHON) src/foul_type_llm_grader.py --player "James Harden" --provider "gemini" --model "gemini-2.5-flash" --validate-only

foul-type-llm-harden:
	PYTHONPATH=. $(PYTHON) src/foul_type_llm_grader.py --player "James Harden" --provider "gemini" --model "gemini-2.5-flash"

foul-type-llm-harden-po:
	PYTHONPATH=. $(PYTHON) src/foul_type_llm_grader.py --player "James Harden" --provider "gemini" --model "gemini-2.5-flash" --season-type Playoffs

foul-type-llm-giannis:
	PYTHONPATH=. $(PYTHON) src/foul_type_llm_grader.py --player "Giannis Antetokounmpo" --provider "gemini" --model "gemini-2.5-flash"

foul-type-llm-giannis-po:
	PYTHONPATH=. $(PYTHON) src/foul_type_llm_grader.py --player "Giannis Antetokounmpo" --provider "gemini" --model "gemini-2.5-flash" --season-type Playoffs

foul-type-alpha: foul-type-scrape-harden foul-type-scrape-giannis foul-type-classify-harden foul-type-classify-giannis
	@echo ""
	@echo "Alpha test ready. To classify, run:"
	@echo "  make foul-type-serve"
	@echo "  Then open http://localhost:8080/foul_type_classifier_james_harden.html"
	@echo "  and   http://localhost:8080/foul_type_classifier_giannis_antetokounmpo.html"

foul-type-serve:
	@echo "Serving classifier at http://localhost:8080/"
	$(PYTHON) -m http.server 8080 --directory output

all: scrape features screen-a screen-b screen-c visualize

clean:
	rm -rf data/processed/ output/figures/
