from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
from auth import check_auth
from database.schema import initialize_database
from utils.ui_components import inject_global_css

st.set_page_config(
    page_title="COLEXA BIOSENSOR | HVAC Monitoring",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

if not check_auth():
    st.stop()

if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = initialize_database()

inject_global_css()

# This is the router — it belongs ONLY in app.py
pg = st.navigation([
    st.Page("pages/0_Home.py", title="Home / Overview", icon="🏠"),
    st.Page("pages/4_Executive_Dashboard.py", title="Executive Overview", icon="📈"),
    st.Page("pages/1_AHU_Monitoring.py", title="AHU Monitoring", icon="❄️"),
    st.Page("pages/2_Air_Compressor.py", title="Air Compressor", icon="🌀"),
    st.Page("pages/3_DHU_Monitoring.py", title="DHU Monitoring", icon="💧"),
    st.Page("pages/5_RCA_and_CAPA.py", title="RCA & CAPA Engine", icon="🔍"),
    st.Page("pages/6_Compliance_Reports.py", title="Compliance Reports", icon="📋"),
    st.Page("pages/7_SOP_Library.py", title="SOP Library", icon="📚"),
])

pg.run()
