## Development Setup

This repo requires Python 3.6 or higher. We recommend you use a Python virtual environment to install
the required dependencies.

Set up venv (one time):

- `python3 -m venv venv`

Active venv:

- `. venv/bin/activate` (if your shell is bash/zsh)
- `. venv/bin/activate.fish` (if your shell is fish)

Install dependencies:

- `pip install -r requirements.txt`

Run tests:

- First, start an instance of [sandbox](https://github.com/algorand/sandbox) (requires Docker): `./sandbox up nightly`
- `pytest`
- When finished, the sandbox can be stopped with `./sandbox down`

Format code:

- `black .`

Chạy để compile:

```
MAIN:
python3 mainCompile.py

MARKETPLACE:
python3 marketplaceCompile.py
```

Test:
```
MAIN:
TODO

MARKETPLACE:
python3 marketplace_test.py
```