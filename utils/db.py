from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
import streamlit as st
import os

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(
    BASE_DIR / ".env",
    override=True
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL missing")

if not SUPABASE_KEY:
    raise Exception("SUPABASE_KEY missing")

@st.cache_resource
def get_supabase():
    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY
    )

supabase = get_supabase()