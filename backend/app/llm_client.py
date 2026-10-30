
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

# Automatically load environment variables from backend/.env
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)


def call_nemotron(messages: list[dict]) -> str:
    """Send conversation messages to NVIDIA Nemotron."""

    api_key = os.getenv("NVIDIA_API_KEY")

    if not api_key:
        raise RuntimeError(
            "NVIDIA_API_KEY is not configured. "
            "Add it to backend/.env."
        )

    url = os.getenv(
        "LLM_BASE_URL",
        "https://integrate.api.nvidia.com/v1/chat/completions"
    )

    model = os.getenv(
        "LLM_MODEL",
        "nvidia/nemotron-3.5-bolt-e4b"
    )

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": 384,
        "stream": False,
    }

    try:
        response = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=(10, 45),
        )

        response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Nemotron returned an empty response.")

        return content

    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            "Nemotron API timed out."
        ) from exc

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Nemotron API request failed: {type(exc).__name__}"
        ) from exc

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "Nemotron returned an invalid response."
        ) from exc
