from __future__ import annotations

import os

from dotenv import dotenv_values

from interview_app.llm.openai_client import LLMClient


def main() -> None:
    vals = dotenv_values(".env")
    key = vals.get("OPENAI_API_KEY")
    if key:
        os.environ["OPENAI_API_KEY"] = key.strip().strip('"')

    # Avoid printing secrets; just ensure the call works.
    client = LLMClient()
    resp = client.generate_response(
        system_prompt="You are a helpful assistant.",
        user_prompt="Reply with exactly: ok",
        max_tokens=10,
        temperature=0.0,
        llm_route="openai_smoke_demo",
    )
    print("LLM_SMOKE_RESPONSE_TEXT", (resp.text or "").strip())
    print("LLM_SMOKE_MODEL", resp.model)


if __name__ == "__main__":
    main()

