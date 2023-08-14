PYTHON_INTERPRETER = python3
PYTEST_COMMAND = $(PYTHON_INTERPRETER) -m pytest
PYTEST_ARGS = -v --cov-report=xml

.PHONY: test setup clean validate
setup: requirements.txt
	pip install -r requirements.txt
test: setup
	$(PYTEST_COMMAND) $(PYTEST_ARGS) --cov test/unit test/unit
validate: setup
	docker run --name blaze --rm -d -e JAVA_TOOL_OPTIONS=-Xmx2g -p 8080:8080 samply/blaze:latest
	.github/scripts/wait-for-url.sh  http://localhost:8080/health
	$(PYTEST_COMMAND) $(PYTEST_ARGS) --cov test/integration test/integration
	docker stop blaze
clean:
	rm -rf __pycache__