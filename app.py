import streamlit as st
from auth import check_auth
from database.schema import initialize_database
from utils.ui_components import inject_global_css

# 1. Page Configuration
st.set_page_config(
    page_title="COLEXA BIOSENSOR | HVAC Monitoring",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide unnecessary toolbar elements
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stDecoration"] {visibility: hidden !important;}
[data-testid="stStatusWidget"] {visibility: hidden !important;}
footer {visibility: hidden !important;}
header[data-testid="stHeader"] { background: transparent !important; visibility: visible !important; }
header[data-testid="stHeader"] > div:first-child { display: none !important; }
[data-testid="collapsedControl"] { display: block !important; visibility: visible !important; }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 2. Authentication Gatekeeper
if not check_auth():
    st.stop()

# Startup: ensure database schema exists
if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = initialize_database()

inject_global_css()

# Define explicit multi-page router
pg = st.navigation([
    st.Page("pages/4_Executive_Dashboard.py", title="Executive Overview", icon="📈"),
    st.Page("pages/1_AHU_Monitoring.py", title="AHU Monitoring", icon="❄️"),
    st.Page("pages/2_Air_Compressor.py", title="Air Compressor", icon="🌀"),
    st.Page("pages/3_DHU_Monitoring.py", title="DHU Monitoring", icon="💧"),
    st.Page("pages/5_RCA_and_CAPA.py", title="RCA & CAPA Engine", icon="🔍"),
    st.Page("pages/6_Compliance_Reports.py", title="Compliance Reports", icon="📋"),
    st.Page("pages/7_SOP_Library.py", title="SOP Library", icon="📚"),
])

# Execute navigation router as the sole controller
pg.run()
