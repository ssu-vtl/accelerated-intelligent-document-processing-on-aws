.PHONY: test test-cicd clean

test:
	pytest

test-cicd:
	pip install -e ".[test]"
	pytest
	mkdir -p test-reports
	cp coverage.xml test-reports/
	cp test-results.xml test-reports/

clean:
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf test-results.xml
	rm -rf test-reports
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	
# A convenience target to install the idp_common library with all, dev dependencies in edit mode
dev:
	pip install -e ".[all, dev]"
