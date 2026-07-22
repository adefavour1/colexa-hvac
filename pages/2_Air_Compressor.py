"""
Air Compressor Monitoring - Single-parameter (Bar) telemetry entry, pressure trends, and log history.
"""
import streamlit as st
from auth import check_auth, render_logout_sidebar

st.set_page_config(page_title="Executive Dashboard", layout="wide")

# Block access if user manually clears session or logs out
if not check_auth():
    st.stop()

render_logout_sidebar()

if st.button("⬅️ Back to Home page"):
    st.switch_page("app.py")

import os
import base64
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

from database.operations import insert_compressor_log, fetch_compressor_logs
from utils.ui_components import (
    inject_global_css, render_facility_header, render_deviation_alert,
    evaluate_parameter_bounds,
)
from utils.rca_engine import get_rca_capa

st.set_page_config(page_title="Air Compressor | COLEXA", page_icon="🌀", layout="wide")
inject_global_css()

# ---------------------------------------------------------------------------
# Sidebar Navigation & Branding
# ---------------------------------------------------------------------------
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
        sidebar_logo_html = '<span style="font-size: 26px;">🧪</span>'

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
    st.caption("Navigate using the pages listed above.")

# Render Branded Header Banner
render_facility_header("Air Compressor Monitoring", "Governing SOP: CBL-MNT-03 — Air Compressor Operating Procedure")

# Direct User Instruction
st.info("please fill in the input data below.")

# Compressor Panel Selection
unit_id = st.selectbox("Select Compressor Unit", options=["Air Compressor Panel"])

st.subheader("Detailed Compressor Telemetry Entry")

# Form: Pressure (Bar)
with st.form("compressor_detail_form"):
    pressure_val = st.number_input("Pressure (Bar)", value=6.0, step=0.1)

    submitted = st.form_submit_button("🌀 Log Compressor Details")

if submitted:
    entry = {
        "unit_id": unit_id,
        "delivery_pressure": pressure_val,
        "operator_id": st.session_state.get("operator_id", "SYS_OPERATOR"),
    }
    new_id = insert_compressor_log(entry)
    if new_id is None:
        st.error("Failed to save compressor detail. Check logs/db_errors.log.")
    else:
        st.success(f"Compressor detail logged (Record #{new_id}) for {unit_id}.")

    # Bounds evaluation against controlled SOP limits
    evaluation = evaluate_parameter_bounds("compressor_pressure", pressure_val)
    if not evaluation["in_bounds"]:
        render_deviation_alert(
            evaluation["label"],
            evaluation["status"],
            pressure_val,
            evaluation["low"],
            evaluation["high"],
            evaluation["unit"]
        )
        rca_result = get_rca_capa("compressor_pressure", evaluation["status"], evaluation["referenced_sop"])
        with st.expander(f"RCA / CAPA — {evaluation['label']}"):
            for cause in rca_result.get("causes", []):
                st.markdown(f"- {cause}")
            st.markdown(f"**CAPA:** {rca_result.get('recommended_capa', 'N/A')}")

st.write("")

# ---------------------------------------------------------------------------
# Pressure Trend Section (Formated strictly to HH:MM)
# ---------------------------------------------------------------------------
st.subheader("Pressure Trend")

history_df = fetch_compressor_logs(limit=200)

if not history_df.empty:
    df_chart = history_df.copy()
    
    if "timestamp" in df_chart.columns:
        df_chart["timestamp_dt"] = pd.to_datetime(df_chart["timestamp"])
    elif "created_at" in df_chart.columns:
        df_chart["timestamp_dt"] = pd.to_datetime(df_chart["created_at"])
    else:
        df_chart["timestamp_dt"] = datetime.now()

    # Create strict HH:MM time column for the trend axis
    df_chart["Time"] = df_chart["timestamp_dt"].dt.strftime("%H:%M")

    pressure_col = "delivery_pressure" if "delivery_pressure" in df_chart.columns else ("pressure" if "pressure" in df_chart.columns else None)

    if pressure_col:
        fig_p = px.line(
            df_chart,
            x="Time",
            y=pressure_col,
            labels={"Time": "Time", pressure_col: "Pressure (Bar)"},
            title="Pressure (Bar) vs Time"
        )
        fig_p.update_traces(
            line_color="#06B6D4", 
            line_width=2,
            hovertemplate="Time: %{x}<br>Pressure: %{y} Bar<extra></extra>"
        )
        fig_p.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
        st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.info("No pressure trend data available.")
else:
    st.info("No telemetry logged yet for Pressure Trend.")

st.write("")

# ---------------------------------------------------------------------------
# Compressor Detailed Log History Table (Strict HH:MM time format)
# ---------------------------------------------------------------------------
st.subheader("Compressor Detailed Log History")

if not history_df.empty:
    df_table = history_df.copy()

    if "timestamp" in df_table.columns:
        dt_series = pd.to_datetime(df_table["timestamp"])
    elif "created_at" in df_table.columns:
        dt_series = pd.to_datetime(df_table["created_at"])
    else:
        dt_series = pd.Series([datetime.now()] * len(df_table))

    df_table["Date"] = dt_series.dt.strftime("%Y-%m-%d")
    df_table["Time"] = dt_series.dt.strftime("%H:%M")  # Formatted as HH:MM

    pressure_col = "delivery_pressure" if "delivery_pressure" in df_table.columns else ("pressure" if "pressure" in df_table.columns else None)
    df_table["Pressure (Bar)"] = df_table[pressure_col] if pressure_col else 0.0

    df_table["S/N"] = range(1, len(df_table) + 1)
    display_table = df_table[["S/N", "Date", "Time", "Pressure (Bar)"]]

    st.dataframe(display_table, use_container_width=True, hide_index=True)
else:
    st.info("No compressor telemetry logged yet.")