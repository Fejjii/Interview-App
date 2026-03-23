"""Streamlit entrypoint for the AI Interview Preparation Assistant.

Ensures ``src/`` is on ``sys.path`` so ``import interview_app`` resolves when
running ``streamlit run streamlit_app.py`` from the project root. Loads a
project-local ``.env`` if present, then delegates rendering to
``interview_app.app.main.run``.

Inputs: none (process env and optional ``.env`` file). Outputs: runs the Streamlit
event loop until stopped.
"""

from __future__ import annotations

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

