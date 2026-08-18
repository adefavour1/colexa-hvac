"""
COLEXA BIOSENSOR - HVAC Monitoring Platform
Supabase Connection and Schema Initialization Module.

Provides a cached Supabase client connection across the application.
"""

import os
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

LOG_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def _log_exception(context: str, exc: Exception) -> None:
    """Append a timestamped exception record to logs/db_errors.log.

    Args:
        context: Short description of where the exception occurred.
        exc: The caught exception instance.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_path: str = os.path.join(LOG_DIR, "db_errors.log")
        with open(log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"[{datetime.now().isoformat()}] {context}: {exc}\n")
    except Exception:
        # Logging must never crash the application.
        pass


@st.cache_resource
def get_supabase_client() -> Client:
    """Initialize and cache the Supabase client connection using Streamlit secrets.

    Returns:
        A Supabase Client instance.
    """
    url = st.secrets["SUPABASE"]["SUPABASE_URL"]
    key = st.secrets["SUPABASE"]["SUPABASE_KEY"]
    return create_client(url, key)


def get_connection() -> Client:
    """Compatibility alias for get_supabase_client so existing calls work seamlessly."""
    return get_supabase_client()


def initialize_database() -> bool:
    """Supabase tables are created via the cloud dashboard SQL editor.
    
    Returns:
        True indicating successful configuration check.
    """
    try:
        client = get_supabase_client()
        # Simple health check query
        client.table("facility_logs").select("id", count="exact").limit(1).execute()
        return True
    except Exception as exc:
        _log_exception("initialize_database", exc)
        return False


if __name__ == "__main__":
    success: bool = initialize_database()
    print("Supabase connection initialized successfully." if success else "Supabase initialization FAILED. Check logs/db_errors.log.")
