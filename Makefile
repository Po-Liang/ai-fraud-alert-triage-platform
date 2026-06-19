.PHONY: build-CreateAlertFunction build-ListAlertsFunction build-GetAlertFunction build-AnalyzeAlertFunction build-AnalysisWorkerFunction build-RagQueryFunction

PYTHON_FOR_SAM_BUILD ?= $(if $(wildcard /opt/homebrew/bin/python3.12),/opt/homebrew/bin/python3.12,python3.12)

build-CreateAlertFunction:
	PIP_CACHE_DIR="$(PWD)/.pip-cache" "$(PYTHON_FOR_SAM_BUILD)" -m pip install -r requirements.txt -t "$(ARTIFACTS_DIR)"
	cp -R src "$(ARTIFACTS_DIR)/src"

build-ListAlertsFunction:
	PIP_CACHE_DIR="$(PWD)/.pip-cache" "$(PYTHON_FOR_SAM_BUILD)" -m pip install -r requirements.txt -t "$(ARTIFACTS_DIR)"
	cp -R src "$(ARTIFACTS_DIR)/src"

build-GetAlertFunction:
	PIP_CACHE_DIR="$(PWD)/.pip-cache" "$(PYTHON_FOR_SAM_BUILD)" -m pip install -r requirements.txt -t "$(ARTIFACTS_DIR)"
	cp -R src "$(ARTIFACTS_DIR)/src"

build-AnalyzeAlertFunction:
	PIP_CACHE_DIR="$(PWD)/.pip-cache" "$(PYTHON_FOR_SAM_BUILD)" -m pip install -r requirements.txt -t "$(ARTIFACTS_DIR)"
	cp -R src "$(ARTIFACTS_DIR)/src"

build-AnalysisWorkerFunction:
	PIP_CACHE_DIR="$(PWD)/.pip-cache" "$(PYTHON_FOR_SAM_BUILD)" -m pip install -r requirements.txt -t "$(ARTIFACTS_DIR)"
	cp -R src "$(ARTIFACTS_DIR)/src"

build-RagQueryFunction:
	PIP_CACHE_DIR="$(PWD)/.pip-cache" "$(PYTHON_FOR_SAM_BUILD)" -m pip install -r requirements.txt -t "$(ARTIFACTS_DIR)"
	cp -R src "$(ARTIFACTS_DIR)/src"
