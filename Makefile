PYTHON_INTERPRETER = python3
PYTEST_COMMAND = $(PYTHON_INTERPRETER) -m pytest
PYTEST_ARGS = -v -p no:cacheprovider --cov-report=xml --cov=./

.PHONY: test setup clean validate
setup: requirements.txt ## Install required packages
	pip install -r requirements.txt
test: setup ## Run unit test
	$(PYTEST_COMMAND) $(PYTEST_ARGS) test/unit
validate: setup ## Run integration test
	docker run --name blaze --rm -d -e JAVA_TOOL_OPTIONS=-Xmx2g -p 8080:8080 samply/blaze:latest
	.github/scripts/wait-for-url.sh  http://localhost:8080/health
	$(PYTEST_COMMAND) $(PYTEST_ARGS) test/integration
	docker stop blaze
clean:
	rm -rf __pycache__