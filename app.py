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
    initial_sidebar_state="expanded",  # Forces the sidebar to open by default
)

# Hide unnecessary toolbar elements (keeping the collapse control active)
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

# ---------------------------------------------------------------------------
# Explicit Sidebar Content (Forces the sidebar to render and stay visible)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("assets/logo.png", width=150) if Path("assets/logo.png").exists() else st.write("❄️ **COLEXA BIOSENSOR**")
    st.caption("HVAC & Facility Infrastructure")
    st.divider()
    st.markdown("### Navigation Controls")
    st.page_link("app.py", label="Home Overview", icon="🏠")
    st.page_link("pages/4_Executive_Dashboard.py", label="Executive Dashboard", icon="📈")
    st.page_link("pages/1_AHU_Monitoring.py", label="AHU Monitoring", icon="❄️")
    st.page_link("pages/2_Air_Compressor.py", label="Air Compressor", icon="🌀")
    st.page_link("pages/3_DHU_Monitoring.py", label="DHU Monitoring", icon="💧")
    st.page_link("pages/5_RCA_and_CAPA.py", label="RCA & CAPA Engine", icon="🔍")
    st.page_link("pages/6_Compliance_Reports.py", label="Compliance Reports", icon="📋")
    st.page_link("pages/7_SOP_Library.py", label="SOP Library", icon="📚")

# 3. Main Page Content
render_facility_header(
    "Facility Home & Overview",
    "Colexa Biosensor HVAC & Infrastructure Monitoring Matrix"
)

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
st.info("Use the sidebar menu on the left to navigate across monitoring panels, compliance reports, and SOP libraries.")
