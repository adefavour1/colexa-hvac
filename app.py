from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent))

import streamlit as st
from auth import check_auth, render_logout_sidebar
from database.schema import initialize_database
from database.operations import compute_kpis
from utils.ui_components import inject_global_css, render_facility_header, render_kpi_card

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

render_logout_sidebar()

# Startup: ensure database schema exists
if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = initialize_database()

inject_global_css()

# Render Branded Header Banner
render_facility_header(
    "Facility Home & Overview",
    "Colexa Biosensor HVAC & Infrastructure Monitoring Matrix"
)

# 3. Real-Time KPI Summary Cards
kpis = compute_kpis() if callable(compute_kpis) else {}
kpi_cols = st.columns(5)

with kpi_cols[0]:
    render_kpi_card("Total Log Entries", f"{kpis.get('total_logs', 0)}")
with kpi_cols[1]:
    render_kpi_card("Open Deviations", f"{kpis.get('open_deviations', 0)}")
with kpi_cols[2]:
    render_kpi_card("Compliance %", f"{kpis.get('compliance_pct', 100.0)}%")
with kpi_cols[3]:
    render_kpi_card("Today's Entries", f"{kpis.get('today_log_count', 0)}")
with kpi_cols[4]:
    render_kpi_card("Health Score", f"{kpis.get('equipment_health_score', 98.5)}")

st.write("")
st.subheader("Facility Infrastructure Scopes Matrix")
st.info("👈 Use the sidebar navigation menu on the left to switch between AHU Monitoring, Executive Dashboards, Compliance Reports, and SOP Library.")
