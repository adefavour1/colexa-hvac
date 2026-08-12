"""
AHU Monitoring - Air Handling Unit Control Panel telemetry, trends, and log history.
"""
import os
import base64
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Page Config (Must be the first Streamlit command)
st.set_page_config(page_title="AHU Monitoring | COLEXA", page_icon="❄️", layout="wide")

# 2. Authentication Gatekeeper (Must come immediately after config)
from auth import check_auth, render_logout_sidebar
if not check_auth():
    st.stop()

from database.operations import insert_ahu_detail, fetch_ahu_details
from utils.ui_components import (
    inject_global_css, render_facility_header, render_deviation_alert,
    evaluate_parameter_bounds,
)
from utils.rca_engine import get_rca_capa

inject_global_css()

# ---------------------------------------------------------------------------
# Sidebar Navigation & Branding
# ---------------------------------------------------------------------------
render_logout_sidebar()

with st.sidebar:
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    possible_logos = ["logo.jpg", "logo.png", "colexa_logo.png", "logo.svg"]
    
    logo_path = None
    for f in possible_logos:
        p = os.path.join(assets_dir, f)
        if os.path.exists(p):
            logo_path = p
            break

    if logo_path and logo_path.endswith(('.jpg', '.jpeg', '.png')):
        with open(logo_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        sidebar_logo_html = f'<img src="data:image/png;base64,{encoded_string}" style="height: 38px; width: auto; object-fit: contain;" alt="Colexa Logo"/>'
    elif logo_path and logo_path.endswith('.svg'):
        with open(logo_path, "r", encoding="utf-8") as f:
            sidebar_logo_html = f'<div style="height:38px; width:38px;">{f.read()}</div>'
    else:
        sidebar_logo_html = '<span style="font-size: 26px;">❄️</span>'

    st.markdown(
        f"""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
            {sidebar_logo_html}
            <span style="font-weight: 800; font-size: 1.15rem; letter-spacing: 1px; color: inherit;">COLEXA BIOSENSOR</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.caption("HVAC & Facility Infrastructure Matrix")
    st.divider()
    st.markdown("### Navigation Controls")
    
    # Using st.page_link to prevent session-resetting browser refreshes
    st.page_link("app.py", label="Home Overview", icon="🏠")
    st.page_link("pages/4_Executive_Dashboard.py", label="Executive Dashboard", icon="📈")
    st.page_link("pages/1_AHU_Monitoring.py", label="AHU Monitoring", icon="❄️")
    st.page_link("pages/2_Air_Compressor.py", label="Air Compressor", icon="🌀")
    st.page_link("pages/3_DHU_Monitoring.py", label="DHU Monitoring", icon="💧")
    st.page_link("pages/5_RCA_and_CAPA.py", label="RCA & CAPA Engine", icon="🔍")
    st.page_link("pages/6_Compliance_Reports.py", label="Compliance Reports", icon="📋")
    st.page_link("pages/7_SOP_Library.py", label="SOP Library", icon="📚")
    st.page_link("pages/8_System_Settings.py", label="System Settings", icon="⚙️")

# Render Branded Header Banner
render_facility_header("AHU Monitoring", "Governing SOP: CBL-MNT-02 — AHU Operating Procedure")

# ... [rest of your page logic follows here]
