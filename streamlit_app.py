from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Load .env from project root so OPENAI_API_KEY is available regardless of cwd
_env_file = ROOT / ".env"
# #region agent log
import json, os
_debug_log = ROOT.parent / "debug-0cdc00.log"
with open(_debug_log, "a", encoding="utf-8") as _f:
    _f.write(json.dumps({"hypothesisId": "A", "location": "streamlit_app.py:env_load", "message": "env_check", "data": {"root": str(ROOT), "env_path": str(_env_file), "env_exists": _env_file.exists(), "OPENAI_API_KEY_in_env_before": "OPENAI_API_KEY" in os.environ}, "timestamp": __import__("time").time() * 1000}) + "\n")
# #endregion
if _env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_file)
# #region agent log
with open(_debug_log, "a", encoding="utf-8") as _f:
    _f.write(json.dumps({"hypothesisId": "A", "location": "streamlit_app.py:after_load_dotenv", "message": "env_after_load", "data": {"OPENAI_API_KEY_in_env_after": "OPENAI_API_KEY" in os.environ}, "timestamp": __import__("time").time() * 1000}) + "\n")
# #endregion

from interview_app.app.main import run


if __name__ == "__main__":
    run()

