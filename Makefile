all: fmt clean

fmt:
	ruff format

clean:
	ruff clean
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type d -name .pytest_cache -exec rm -r {} +
	find . -type d -name .ipynb_checkpoints -exec rm -r {} +
