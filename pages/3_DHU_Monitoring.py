"""
DHU Monitoring - Dehumidifier telemetry entry for DHU-1 and DHU-2, combined trend analysis, and log history.
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

from database.operations import insert_dhu_detail, fetch_dhu_details
from utils.ui_components import (
    inject_global_css, render_facility_header, render_deviation_alert,
    evaluate_parameter_bounds,
)
from utils.rca_engine import get_rca_capa

st.set_page_config(page_title="DHU Monitoring | COLEXA", page_icon="💧", layout="wide")
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

    # Side-by-side Logo and Title Layout
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
render_facility_header("DHU Monitoring", "Governing SOP: CBL-MNT-05 — Dehumidifier Operating Procedure")

# Direct User Instruction
st.info("please fill in the input data below.")

# ---------------------------------------------------------------------------
# Distinct Telemetry Entry Sections (DHU-1 and DHU-2 Side-by-Side)
# ---------------------------------------------------------------------------
col1, col2 = st.columns(2)

# Function to process telemetry submission
def process_dhu_submission(unit_id, rh_val, dpg_val, bound_prefix):
    entry = {
        "unit_id": unit_id,
        "relative_humidity": rh_val,
        "dpg_mmwc": dpg_val,
        "operator_id": st.session_state.get("operator_id", "SYS_OPERATOR"),
    }
    new_id = insert_dhu_detail(entry)
    if new_id is None:
        st.error(f"Failed to save {unit_id} detail. Check logs/db_errors.log.")
    else:
        st.success(f"{unit_id} detail logged (Record #{new_id}).")

    rh_eval = evaluate_parameter_bounds(f"{bound_prefix}_rh", rh_val)
    dpg_eval = evaluate_parameter_bounds(f"{bound_prefix}_dpg", dpg_val)

    for key, evaluation, value in [
        (f"{bound_prefix}_rh", rh_eval, rh_val),
        (f"{bound_prefix}_dpg", dpg_eval, dpg_val),
    ]:
        if not evaluation["in_bounds"]:
            render_deviation_alert(
                f"{unit_id} - {evaluation['label']}",
                evaluation["status"],
                value,
                evaluation["low"],
                evaluation["high"],
                evaluation["unit"]
            )
            if evaluation["status"] == "High Excursion" and "rh" in key:
                st.error(f"🚨 Moisture Ingress Risk: {unit_id} dry room humidity excursion detected — review desiccant wheel and filters immediately.")
            rca_result = get_rca_capa(key, evaluation["status"], evaluation["referenced_sop"])
            with st.expander(f"RCA / CAPA — {unit_id} {evaluation['label']}"):
                for cause in rca_result.get("causes", []):
                    st.markdown(f"- {cause}")
                st.markdown(f"**CAPA:** {rca_result.get('recommended_capa', 'N/A')}")

# DHU-1 Section
with col1:
    st.subheader("💧 DHU-1 Telemetry Entry")
    with st.form("dhu1_form"):
        rh1 = st.number_input("RH (%)", value=35.0, step=0.1, key="dhu1_rh_input")
        dpg1 = st.number_input("DPG (mmWC)", value=10.0, step=0.1, key="dhu1_dpg_input")
        sub1 = st.form_submit_button("Log DHU-1 Details")
    if sub1:
        process_dhu_submission("DHU-1", rh1, dpg1, "dhu1")

# DHU-2 Section
with col2:
    st.subheader("💧 DHU-2 Telemetry Entry")
    with st.form("dhu2_form"):
        rh2 = st.number_input("RH (%)", value=35.0, step=0.1, key="dhu2_rh_input")
        dpg2 = st.number_input("DPG (mmWC)", value=10.0, step=0.1, key="dhu2_dpg_input")
        sub2 = st.form_submit_button("Log DHU-2 Details")
    if sub2:
        process_dhu_submission("DHU-2", rh2, dpg2, "dhu2")

st.write("")

# ---------------------------------------------------------------------------
# Combined RH Trend and DPG Trend Charts (DHU-1 & DHU-2 Overlaid)
# ---------------------------------------------------------------------------
st.subheader("Combined DHU Telemetry Trends")

history_df = fetch_dhu_details(limit=400)

if not history_df.empty:
    df_chart = history_df.copy()

    # Standardize DHU unit IDs if logged with legacy names (e.g., DHU-01 -> DHU-1)
    if "unit_id" in df_chart.columns:
        df_chart["unit_id"] = df_chart["unit_id"].replace({"DHU-01": "DHU-1", "DHU-02": "DHU-2"})

    # Parse timestamps and create HH:MM time column
    if "timestamp" in df_chart.columns:
        df_chart["timestamp_dt"] = pd.to_datetime(df_chart["timestamp"])
    elif "created_at" in df_chart.columns:
        df_chart["timestamp_dt"] = pd.to_datetime(df_chart["created_at"])
    else:
        df_chart["timestamp_dt"] = datetime.now()

    df_chart["Time"] = df_chart["timestamp_dt"].dt.strftime("%H:%M")

    rh_col = "relative_humidity" if "relative_humidity" in df_chart.columns else ("rh" if "rh" in df_chart.columns else None)
    dpg_col = "dpg_mmwc" if "dpg_mmwc" in df_chart.columns else ("dpg" if "dpg" in df_chart.columns else None)

    # Palette for distinguishing units
    unit_color_map = {"DHU-1": "#06B6D4", "DHU-2": "#F59E0B"}

    # 1. Combined RH Trend Chart
    st.markdown("### Combined RH Trend (DHU-1 vs DHU-2)")
    if rh_col:
        fig_rh = px.line(
            df_chart,
            x="Time",
            y=rh_col,
            color="unit_id",
            color_discrete_map=unit_color_map,
            labels={"Time": "Time (HH:MM)", rh_col: "RH (%)", "unit_id": "Unit"},
            title="RH (%) vs Time"
        )
        fig_rh.update_traces(line_width=2.5, hovertemplate="Time: %{x}<br>RH: %{y}%<extra></extra>")
        fig_rh.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
        st.plotly_chart(fig_rh, use_container_width=True)
    else:
        st.info("No RH trend data available.")

    # 2. Combined DPG Trend Chart
    st.markdown("### Combined DPG Trend (DHU-1 vs DHU-2)")
    if dpg_col:
        fig_dpg = px.line(
            df_chart,
            x="Time",
            y=dpg_col,
            color="unit_id",
            color_discrete_map=unit_color_map,
            labels={"Time": "Time (HH:MM)", dpg_col: "DPG (mmWC)", "unit_id": "Unit"},
            title="DPG (mmWC) vs Time"
        )
        fig_dpg.update_traces(line_width=2.5, hovertemplate="Time: %{x}<br>DPG: %{y} mmWC<extra></extra>")
        fig_dpg.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
        st.plotly_chart(fig_dpg, use_container_width=True)
    else:
        st.info("No DPG trend data available.")
else:
    st.markdown("### Combined RH Trend (DHU-1 vs DHU-2)")
    st.info("No telemetry logged yet for RH Trend.")
    st.markdown("### Combined DPG Trend (DHU-1 vs DHU-2)")
    st.info("No telemetry logged yet for DPG Trend.")

st.write("")

# ---------------------------------------------------------------------------
# DHU Detailed Log History Table
# ---------------------------------------------------------------------------
st.subheader("DHU Detailed Log History")

if not history_df.empty:
    df_table = history_df.copy()

    if "timestamp" in df_table.columns:
        dt_series = pd.to_datetime(df_table["timestamp"])
    elif "created_at" in df_table.columns:
        dt_series = pd.to_datetime(df_table["created_at"])
    else:
        dt_series = pd.Series([datetime.now()] * len(df_table))

    df_table["Date"] = dt_series.dt.strftime("%Y-%m-%d")
    df_table["Time"] = dt_series.dt.strftime("%H:%M")  # Format as HH:MM

    if "unit_id" in df_table.columns:
        df_table["Unit"] = df_table["unit_id"].replace({"DHU-01": "DHU-1", "DHU-02": "DHU-2"})
    else:
        df_table["Unit"] = "DHU-1"

    rh_col = "relative_humidity" if "relative_humidity" in df_table.columns else ("rh" if "rh" in df_table.columns else None)
    dpg_col = "dpg_mmwc" if "dpg_mmwc" in df_table.columns else ("dpg" if "dpg" in df_table.columns else None)

    df_table["RH (%)"] = df_table[rh_col] if rh_col else 0.0
    df_table["DPG (mmWC)"] = df_table[dpg_col] if dpg_col else 0.0

    df_table["S/N"] = range(1, len(df_table) + 1)
    display_table = df_table[["S/N", "Unit", "Date", "Time", "RH (%)", "DPG (mmWC)"]]

    st.dataframe(display_table, use_container_width=True, hide_index=True)
else:
    st.info("No detailed DHU telemetry logged yet.")