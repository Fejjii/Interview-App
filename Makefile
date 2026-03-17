.PHONY: install run test lint format typecheck

install:
	pip install -r requirements.txt

run:
	streamlit run streamlit_app.py

test:
	pytest

lint:
	ruff check src tests

format:
	black src tests

typecheck:
	mypy src

