# Contributing

## Setup a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## Install in editable mode
```bash
python -m pip install -e .
```

## Run tests
```bash
pytest -q
```

## Pull request rules
- Keep PRs small and focused.
- Include a clear summary and testing notes.
- Avoid bundling unrelated changes.
