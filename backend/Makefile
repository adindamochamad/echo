.PHONY: dev phase1 agent1 agent2 agent3 agent4 agent5 agent6 agent7 agent8 agents-all test test-stress test-all

export PYTHONPATH := .

BASE_URL ?= http://localhost:8000
VENV_PYTHON := .venv/bin/python
VENV_UVICORN := .venv/bin/uvicorn

# Jalankan API dengan Python dari venv proyek (wajib — jangan pakai system Python 3.9)
dev:
	$(VENV_UVICORN) app.main:app --reload --port 8000

# Phase 1 — Database Foundation (verifikasi + stress test, tidak butuh HTTP server)
phase1:
	$(VENV_PYTHON) agents/phase1_database.py

# Phase 2 — Auth Layer (butuh backend running: make dev)
phase2:
	$(VENV_PYTHON) agents/phase2_auth.py

# Phase 3 — Embeddings & Search (butuh backend running: make dev)
phase3:
	$(VENV_PYTHON) agents/phase3_embeddings.py

# Phase 4 — Demo Data Integrity (butuh backend running: make dev)
phase4:
	$(VENV_PYTHON) agents/phase4_demo.py

# Phase 5 — Frontend (TypeScript check, no agent needed)
phase5:
	cd ../frontend && npx tsc --noEmit && echo "Phase 5: TypeScript OK"

agent1:
	$(VENV_PYTHON) agents/day1_infra.py

agent2:
	$(VENV_PYTHON) agents/day2_extraction.py

agent3:
	$(VENV_PYTHON) agents/day3_matching.py

agent4:
	$(VENV_PYTHON) agents/day4_demo_data.py

agent5:
	$(VENV_PYTHON) agents/day5_frontend.py

agent6:
	$(VENV_PYTHON) agents/day6_integration.py

agent7:
	$(VENV_PYTHON) agents/day7_chaos.py

agent8:
	ECHO_PROD_URL=$(ECHO_PROD_URL) ECHO_FRONTEND_URL=$(ECHO_FRONTEND_URL) $(VENV_PYTHON) agents/day8_presubmit.py

agents-all:
	@echo "Running all agents sequentially..."
	$(VENV_PYTHON) agents/day1_infra.py
	$(VENV_PYTHON) agents/day2_extraction.py
	$(VENV_PYTHON) agents/day3_matching.py
	$(VENV_PYTHON) agents/day4_demo_data.py
	$(VENV_PYTHON) agents/day5_frontend.py
	$(VENV_PYTHON) agents/day6_integration.py
	$(VENV_PYTHON) agents/day7_chaos.py
	@echo "All agents complete. Run 'make agent8' with PROD URLs for final check."

test:
	pytest tests/ -v --tb=short

test-stress:
	pytest tests/test_stress.py -v --tb=long

test-all:
	pytest tests/ -v --cov=app --cov-report=term-missing
