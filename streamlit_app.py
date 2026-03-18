from __future__ import annotations

"""
Streamlit entrypoint for the Interview Practice App.

Why this file exists:
- Streamlit expects a single script to run (e.g. `streamlit run streamlit_app.py`).
- The application code itself lives under `src/interview_app/` (a proper Python package).
- This wrapper makes sure `src/` is importable and loads the optional `.env` file so
  environment-based configuration works regardless of the current working directory.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    # Put `src/` first so `import interview_app...` resolves to this project package.
    sys.path.insert(0, str(SRC))

_env_file = ROOT / ".env"
if _env_file.exists():
    from dotenv import load_dotenv

    # Load `.env` from the project folder (not from wherever Streamlit was launched).
    # This makes local setup easier for beginners: copy `.env.example` → `.env`.
    load_dotenv(_env_file)

from interview_app.app.main import run


if __name__ == "__main__":
    # Delegate to the package "run" function to keep the entrypoint thin.
    run()

