###############################################################################
# Version
##############################################################################
PYTHON_VERSION = python3

all: release

release:
	@$(PYTHON_VERSION) code/dcf_initialiser.py

test_%:
	@echo "Searching for test files matching '$*' (case-insensitive)..."
	@$(eval TEST_FILE := $(shell find tests -iname "*$*.py" | head -n 1))
	@if [ -n "$(TEST_FILE)" ]; then \
		echo "Running test: $(TEST_FILE)"; \
		PYTHONPATH=/Users/matswalker/DCF/code/$(basename $(TEST_FILE) .py) pytest $(TEST_FILE); \
	else \
		echo "No matching test file found for '$*'"; \
		exit 1; \
	fi

yfinance_query:
	@echo "Running yfinance library"
	@$(PYTHON_VERSION) code/yfinance_query/yfinance_query.py
