import os
import pathlib
import streamlit as st

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def get_secrets():
    try:
        if st.secrets:
            return st.secrets
    except:
        pass

    path = pathlib.Path(__file__).parent.parent / ".streamlit" / "secrets.toml"
    if path.exists():
        with open(path, "rb") as f:
            return tomllib.load(f)
    
    raise FileNotFoundError("Секреты не найдены ни в st.secrets, ни в secrets.toml")

secrets = get_secrets()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]