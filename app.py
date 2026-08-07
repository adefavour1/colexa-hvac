import os
import base64
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from auth import check_auth, render_logout_sidebar
from database.schema import initialize_database
from database.operations import compute_kpis, fetch_facility_logs
from utils.ui_components import inject_global_css, render_kpi_card

# 1. Page Configuration (Must be the very first Streamlit call)
st.set_page_config(
    page_title="COLEXA BIOSENSOR | HVAC Monitoring",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Hide unnecessary toolbar icons and viewer items while ensuring the sidebar collapse control is clean and fully operational
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden !important;}
[data-testid="stToolbar"] {visibility: hidden !important;}
[data-testid="stDecoration"] {visibility: hidden !important;}
[data-testid="stStatusWidget"] {visibility: hidden !important;}
footer {visibility: hidden !important;}
.viewerBadge_link__1S13V {display: none !important;}
div[class*="viewerBadge"] {display: none !important;}

/* Target header elements specifically to leave only the sidebar control visible */
header[data-testid="stHeader"] {
    background: transparent !important;
    visibility: visible !important;
}
header[data-testid="stHeader"] > div:first-child {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 2. Authentication Gatekeeper (Shows login screen and halts if unauthenticated)
if not check_auth():
    st.stop()

# Startup: ensure database schema exists
if "db_ready" not in st.session_state:
    st.session_state["db_ready"] = initialize_database()

inject_global_css()

# Define explicit multi-page router including app.py so st.switch_page("app.py") targets it properly
pg = st.navigation([
    st.Page("app.py", title="Executive Dashboard", icon="📊"),
    st.Page("pages/1_AHU_Monitoring.py", title="AHU Monitoring", icon="❄️"),
    st.Page("pages/2_Air_Compressor.py", title="Air Compressor", icon="🌀"),
    st.Page("pages/3_DHU_Monitoring.py", title="DHU Monitoring", icon="💧"),
    st.Page("pages/4_Executive_Dashboard.py", title="Executive Overview", icon="📈"),
    st.Page("pages/5_RCA_and_CAPA.py", title="RCA & CAPA Engine", icon="🔍"),
    st.Page("pages/6_Compliance_Reports.py", title="Compliance Reports", icon="📋"),
    st.Page("pages/7_SOP_Library.py", title="SOP Library", icon="📚"),
])

# ---------------------------------------------------------------------------
# Top Header: Dynamic Real-Time Ticking Clock (JS-driven)
# ---------------------------------------------------------------------------
def render_top_header():
    assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
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
        logo_html = f'<img src="data:image/png;base64,{encoded_string}" style="height: 52px; width: auto; object-fit: contain;" alt="Colexa Logo"/>'
    elif logo_path and logo_path.endswith('.svg'):
        with open(logo_path, "r", encoding="utf-8") as f:
            logo_html = f'<div style="height:52px; width:52px;">{f.read()}</div>'
    else:
        # High-tech Fallback Biosensor SVG Logo
        logo_html = '<svg width="50" height="50" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="50" cy="50" r="45" stroke="#00d2ff" stroke-width="6" fill="#0b192c"/><path d="M30 50 Q 40 30, 50 50 T 70 50" stroke="#00d2ff" stroke-width="5" fill="none"/><circle cx="50" cy="50" r="8" fill="#3abf07"/><circle cx="30" cy="50" r="5" fill="#00d2ff"/><circle cx="70" cy="50" r="5" fill="#00d2ff"/></svg>'

    header_component_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: transparent;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                overflow: hidden;
            }}
            .colexa-top-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: linear-gradient(135deg, #0b192c 0%, #1e3e62 100%);
                padding: 0.9rem 1.75rem;
                border-radius: 12px;
                color: #ffffff;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
                border-bottom: 3px solid #00d2ff;
                box-sizing: border-box;
            }}
            .brand-group {{
                display: flex;
                align-items: center;
                gap: 1.25rem;
            }}
            .brand-title {{
                font-size: 1.65rem;
                font-weight: 800;
                letter-spacing: 2px;
                color: #ffffff;
                margin: 0;
                line-height: 1.1;
                text-transform: uppercase;
            }}
            .brand-subtitle {{
                font-size: 0.95rem;
                font-weight: 600;
                color: #00d2ff;
                letter-spacing: 1.5px;
                margin-top: 3px;
                text-transform: uppercase;
            }}
            .clock-card {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 210, 255, 0.35);
                padding: 0.5rem 1.1rem;
                border-radius: 8px;
                text-align: right;
                backdrop-filter: blur(4px);
            }}
            .clock-label {{
                font-size: 0.65rem;
                color: #94a3b8;
                text-transform: uppercase;
                letter-spacing: 1.2px;
                font-weight: 700;
                margin-bottom: 2px;
            }}
            .clock-value {{
                font-size: 1.1rem;
                font-weight: 700;
                color: #00d2ff;
                font-family: 'Courier New', Courier, monospace;
            }}
        </style>
    </head>
    <body>
        <div class="colexa-top-header">
            <div class="brand-group">
                {logo_html}
                <div>
                    <div class="brand-title">COLEXA BIOSENSOR</div>
                    <div class="brand-subtitle">HVAC monitoring</div>
                </div>
            </div>
            <div class="clock-card">
                <div class="clock-label">Real-Time Date & Time</div>
                <div class="clock-value" id="live-clock">Syncing clock...</div>
            </div>
        </div>

        <script>
            function updateClock() {{
                const now = new Date();
                const optionsDate = {{ month: 'long', day: 'numeric', year: 'numeric' }};
                const dateStr = now.toLocaleDateString('en-US', optionsDate);
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const seconds = String(now.getSeconds()).padStart(2, '0');
                
                document.getElementById('live-clock').textContent = dateStr + ' | ' + hours + ':' + minutes + ':' + seconds;
            }}
            
            updateClock();
            setInterval(updateClock, 1000);
        </script>
    </body>
    </html>
    """

    st.iframe(header_component_html, height=95)

render_top_header()

if not st.session_state.get("db_ready", False):
    st.error("Database initialization failed. Check logs/db_errors.log before continuing.")

# ---------------------------------------------------------------------------
# KPI Row
# ---------------------------------------------------------------------------
kpis = compute_kpis()
kpi_cols = st.columns(5)
with kpi_cols[0]:
    render_kpi_card("Total Log Entries", f"{kpis['total_logs']}", "All-time shift records")
with kpi_cols[1]:
    render_kpi_card("Open Deviations", f"{kpis['open_deviations']}", "Awaiting CAPA closure")
with kpi_cols[2]:
    render_kpi_card("Environmental Compliance", f"{kpis['compliance_pct']}%", "vs. logged deviations")
with kpi_cols[3]:
    render_kpi_card("Today's Log Entries", f"{kpis['today_log_count']}", datetime.now().strftime("%Y-%m-%d"))
with kpi_cols[4]:
    render_kpi_card("Equipment Health Score", f"{kpis['equipment_health_score']}", "100 = no open deviations")

st.write("")

# ---------------------------------------------------------------------------
# Facility Infrastructure Scopes Matrix
# ---------------------------------------------------------------------------
st.subheader("Facility Infrastructure Scopes Matrix")
scope_cols = st.columns(4)
scope_labels = [
    ("AHU Control Panel", "CBL-MNT-02", "❄️"),
    ("DHU-1 / DHU-2", "CBL-MNT-05", "💧"),
    ("Air Compressor", "CBL-MNT-03", "🌀"),
    ("Air Conditioning (3-Zone)", "CBL-MNT-02", "🌡️"),
]
for col, (name, sop, icon) in zip(scope_cols, scope_labels):
    with col:
        st.markdown(
            f"""<div class="colexa-kpi-card"><div style="font-size:1.6rem;">{icon}</div>
            <div style="font-weight:700;margin-top:0.3rem;">{name}</div>
            <div style="color:#94A3B8;font-size:0.78rem;">Governing SOP: {sop}</div></div>""",
            unsafe_allow_html=True,
        )

st.write("")

# ---------------------------------------------------------------------------
# Shift Telemetry Logs Table
# ---------------------------------------------------------------------------
st.subheader("Recent Shift Telemetry")
recent_logs = fetch_facility_logs(limit=15)
if recent_logs.empty:
    st.info("No telemetry logs available.")
else:
    st.dataframe(recent_logs, width='stretch', hide_index=True)

# ---------------------------------------------------------------------------
# Navigation & Sidebar Routing (Only render logout sidebar when pg.run() is executing the router context to avoid root duplication)
# ---------------------------------------------------------------------------
if "_streamlit_navigation_running" not in st.session_state:
    st.session_state["_streamlit_navigation_running"] = True
    render_logout_sidebar()

pg.run()
