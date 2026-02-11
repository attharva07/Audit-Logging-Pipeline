.PHONY: setup test demo

setup:
	@echo "Create and activate a virtual environment, then install dependencies:"
	@echo "python -m venv .venv && source .venv/bin/activate && python -m pip install -e ."

test:
	pytest -q

demo:
	bash examples/demo.sh
