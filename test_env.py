# test_env.py

from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(
    Path(".env"),
    override=True
)

print(os.getenv("SUPABASE_URL"))