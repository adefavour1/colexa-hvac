"""
AHU Monitoring - Air Handling Unit Control Panel telemetry, trends, and log history.
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

from database.operations import insert_ahu_detail, fetch_ahu_details
from utils.ui_components import (
    inject_global_css, render_facility_header, render_deviation_alert,
    evaluate_parameter_bounds,
)
from utils.rca_engine import get_rca_capa

st.set_page_config(page_title="AHU Monitoring | COLEXA", page_icon="❄️", layout="wide")
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
render_facility_header("AHU Monitoring", "Governing SOP: CBL-MNT-02 — AHU Operating Procedure")

# Direct User Instruction
st.info("please fill in the input data below.")

# AHU Unit Selection
unit_id = st.selectbox("Select AHU Unit", options=["AHU Control Panel"])

st.subheader("Detailed AHU Telemetry Entry")

# Simplified Form: Temp (°C) and RH (%)
with st.form("ahu_detail_form"):
    col1, col2 = st.columns(2)
    temp_val = col1.number_input("Temp (°C)", value=22.0, step=0.1)
    rh_val = col2.number_input("RH (%)", value=30.0, step=0.1)

    submitted = st.form_submit_button("❄️ Log AHU Details")

if submitted:
    entry = {
        "unit_id": unit_id,
        "supply_temp": temp_val,
        "relative_humidity": rh_val,
        "operator_id": st.session_state.get("operator_id", "SYS_OPERATOR"),
    }
    new_id = insert_ahu_detail(entry)
    if new_id is None:
        st.error("Failed to save AHU detail. Check logs/db_errors.log.")
    else:
        st.success(f"AHU detail logged (Record #{new_id}) for {unit_id}.")

    # Bounds evaluation against controlled SOP limits
    for param_key, value in [("ahu_temperature", temp_val), ("ahu_rh", rh_val)]:
        evaluation = evaluate_parameter_bounds(param_key, value)
        if not evaluation["in_bounds"]:
            render_deviation_alert(
                evaluation["label"],
                evaluation["status"],
                value,
                evaluation["low"],
                evaluation["high"],
                evaluation["unit"]
            )
            rca_result = get_rca_capa(param_key, evaluation["status"], evaluation["referenced_sop"])
            with st.expander(f"RCA / CAPA — {evaluation['label']}"):
                for cause in rca_result.get("causes", []):
                    st.markdown(f"- {cause}")
                st.markdown(f"**CAPA:** {rca_result.get('recommended_capa', 'N/A')}")

st.write("")

# ---------------------------------------------------------------------------
# Temperature Trend and RH Trends Section
# ---------------------------------------------------------------------------
st.subheader("Temperature Trend and RH Trends")

history_df = fetch_ahu_details(limit=200)

if not history_df.empty:
    df_chart = history_df.copy()
    
    if "timestamp" in df_chart.columns:
        df_chart["timestamp_dt"] = pd.to_datetime(df_chart["timestamp"])
    elif "created_at" in df_chart.columns:
        df_chart["timestamp_dt"] = pd.to_datetime(df_chart["created_at"])
    else:
        df_chart["timestamp_dt"] = datetime.now()

    temp_col = "supply_temp" if "supply_temp" in df_chart.columns else ("temp" if "temp" in df_chart.columns else None)
    rh_col = "relative_humidity" if "relative_humidity" in df_chart.columns else ("rh" if "rh" in df_chart.columns else None)

    # 1. Temperature Trend Plot
    st.markdown("### Temperature Trend")
    if temp_col:
        fig_temp = px.line(
            df_chart,
            x="timestamp_dt",
            y=temp_col,
            labels={"timestamp_dt": "Time", temp_col: "Temp (°C)"},
            title="Temperature (°C) vs Time"
        )
        fig_temp.update_traces(line_color="#06B6D4", line_width=2)
        fig_temp.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
        st.plotly_chart(fig_temp, use_container_width=True)
    else:
        st.info("No temperature trend data available.")

    # 2. RH Trend Plot
    st.markdown("### RH Trend")
    if rh_col:
        fig_rh = px.line(
            df_chart,
            x="timestamp_dt",
            y=rh_col,
            labels={"timestamp_dt": "Time", rh_col: "RH (%)"},
            title="RH (%) vs Time"
        )
        fig_rh.update_traces(line_color="#C1F24D", line_width=2)
        fig_rh.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
        st.plotly_chart(fig_rh, use_container_width=True)
    else:
        st.info("No RH trend data available.")
else:
    st.markdown("### Temperature Trend")
    st.info("No telemetry logged yet for Temperature Trend.")
    st.markdown("### RH Trend")
    st.info("No telemetry logged yet for RH Trend.")

st.write("")

# ---------------------------------------------------------------------------
# AHU Detailed Log History Table (Strict HH:MM time format)
# ---------------------------------------------------------------------------
st.subheader("AHU Detailed Log History")

if not history_df.empty:
    df_table = history_df.copy()

    if "timestamp" in df_table.columns:
        dt_series = pd.to_datetime(df_table["timestamp"])
    elif "created_at" in df_table.columns:
        dt_series = pd.to_datetime(df_table["created_at"])
    else:
        dt_series = pd.Series([datetime.now()] * len(df_table))

    df_table["Date"] = dt_series.dt.strftime("%Y-%m-%d")
    df_table["Time"] = dt_series.dt.strftime("%H:%M")  # Strict HH:MM format

    temp_col = "supply_temp" if "supply_temp" in df_table.columns else ("temp" if "temp" in df_table.columns else None)
    rh_col = "relative_humidity" if "relative_humidity" in df_table.columns else ("rh" if "rh" in df_table.columns else None)

    df_table["Temp (°C)"] = df_table[temp_col] if temp_col else 0.0
    df_table["RH (%)"] = df_table[rh_col] if rh_col else 0.0

    df_table["S/N"] = range(1, len(df_table) + 1)
    display_table = df_table[["S/N", "Date", "Time", "Temp (°C)", "RH (%)"]]

    st.dataframe(display_table, use_container_width=True, hide_index=True)
else:
    st.info("No detailed AHU telemetry logged yet.")