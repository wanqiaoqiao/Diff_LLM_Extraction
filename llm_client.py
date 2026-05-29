from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

API_URL = "https://api.openai.com/v1/responses"


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str = "gpt-4.1-mini") -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is required.")

    def json_response(self, system_prompt: str, user_text: str, schema: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "input": [
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_text}]},
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "structured_output",
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        request = urllib.request.Request(
            API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
        output_text = (data.get("output_text") or "").strip()
        if not output_text:
            raise RuntimeError("No structured output returned from OpenAI Responses API.")
        return json.loads(output_text)
