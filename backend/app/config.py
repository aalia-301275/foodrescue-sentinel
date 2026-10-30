import os
from pathlib import Path

from dotenv import load_dotenv

# Reads backend/.env if it exists. Never commit that file.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

NEBIUS_API_KEY = os.getenv("NEBIUS_API_KEY", "")
NEBIUS_BASE_URL = os.getenv("NEBIUS_BASE_URL", "")  # AI lead: copy from Nebius docs
MODEL_NAME = os.getenv("MODEL_NAME", "nvidia/Nemotron-3_5-Lightning")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")