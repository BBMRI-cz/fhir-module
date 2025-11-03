PYTHON_INTERPRETER = python3
PYTEST_COMMAND = $(PYTHON_INTERPRETER) -m pytest
PYTEST_ARGS = -v -p no:cacheprovider --cov-report=xml --cov=./
UI_DIR = ui/fhir-place

.PHONY: test setup clean validate setup-ui test-ui
setup: requirements.txt ## Install required packages
	pip install -r requirements.txt
setup-ui: ## Install UI dependencies
	cd $(UI_DIR) && npm install
test: setup ## Run Python unit tests
	$(PYTEST_COMMAND) $(PYTEST_ARGS) test/unit
test-ui: setup-ui ## Run UI unit tests
	cd $(UI_DIR) && npm test
test-all: test test-ui ## Run all unit tests (Python and UI)
validate: setup ## Run integration test
	docker run --name blaze --rm -d -e JAVA_TOOL_OPTIONS=-Xmx2g -p 8080:8080 samply/blaze:latest
	.github/scripts/wait-for-url.sh  http://localhost:8080/health
	$(PYTEST_COMMAND) $(PYTEST_ARGS) test/integration
	docker stop blaze
clean:
	rm -rf __pycache__