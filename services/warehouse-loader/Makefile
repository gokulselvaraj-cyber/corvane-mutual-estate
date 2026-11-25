# warehouse-loader developer tasks
.PHONY: test lint load-sample

test:
	python -m pytest -q tests

lint:
	python -m ruff check corvane_loader

load-sample:
	python -m corvane_loader.billing --file tests/data/billing_sample.txt --dry-run
