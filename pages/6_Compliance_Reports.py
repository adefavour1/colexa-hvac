"""
Compliance & Audit Reports - FDA 21 CFR Part 11 & ISO 13485 audit trail generation.
Governing SOP: CBL-QA-01 — Data Integrity, Audit Trail & Regulatory Reporting.
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
from datetime import datetime, date
import pandas as pd
import streamlit as st

from database.operations import (
    fetch_ahu_details,
    fetch_compressor_logs,
    fetch_deviations,
)
from utils.ui_components import (
    inject_global_css,
    render_facility_header,
    render_kpi_card,
)

# Safe dynamic import for DHU details
try:
    from database.operations import fetch_dhu_details
except ImportError:
    try:
        from database.operations import fetch_dhu_logs as fetch_dhu_details
    except ImportError:
        def fetch_dhu_details(limit=1000):
            return pd.DataFrame()

st.set_page_config(page_title="Compliance Reports | COLEXA", page_icon="📋", layout="wide")
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
        sidebar_logo_html = '<span style="font-size: 26px;">📋</span>'

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
render_facility_header(
    "Compliance & Audit Reports",
    "Governing SOP: CBL-QA-01 — Data Integrity, Audit Trail & Regulatory Reporting (FDA 21 CFR Part 11)"
)

# ---------------------------------------------------------------------------
# Filter Controls Section
# ---------------------------------------------------------------------------
st.subheader("Filter Criteria")

col1, col2, col3 = st.columns(3)
with col1:
    report_type = st.selectbox(
        "Select Report Module",
        options=[
            "All Facility Telemetry", 
            "AHU Control Panel Logs", 
            "DHU Logs", 
            "Air Compressor Logs", 
            "Deviations & CAPA Register"
        ]
    )
with col2:
    start_date = st.date_input("Start Date", value=date(2026, 1, 1))
with col3:
    end_date = st.date_input("End Date", value=date.today())

st.write("")

# ---------------------------------------------------------------------------
# Load & Standardize Datasets (Keeping Only Telemetry Parameters)
# ---------------------------------------------------------------------------
raw_ahu = fetch_ahu_details(limit=1000)
raw_dhu = fetch_dhu_details(limit=1000)
raw_comp = fetch_compressor_logs(limit=1000)

try:
    raw_dev = fetch_deviations(limit=1000)
except Exception:
    raw_dev = pd.DataFrame()

# 1. Process AHU Control Panel Logs
processed_ahu = pd.DataFrame()
if not raw_ahu.empty:
    df = raw_ahu.copy()
    dt_series = pd.to_datetime(df["timestamp"] if "timestamp" in df.columns else df.get("created_at", datetime.now()))
    
    df["Date"] = dt_series.dt.date
    df["Time"] = dt_series.dt.strftime("%H:%M")
    df["Location / Panel"] = "AHU Control Panel"
    
    rename_dict = {}
    if "supply_temp" in df.columns: rename_dict["supply_temp"] = "Temp (°C)"
    elif "temperature" in df.columns: rename_dict["temperature"] = "Temp (°C)"
    
    if "relative_humidity" in df.columns: rename_dict["relative_humidity"] = "RH (%)"
    elif "humidity" in df.columns: rename_dict["humidity"] = "RH (%)"
    
    if "operator_id" in df.columns: rename_dict["operator_id"] = "Operator ID"
    if "remarks" in df.columns: rename_dict["remarks"] = "Remarks"
    
    df.rename(columns=rename_dict, inplace=True)
    
    desired_ahu_cols = ["Date", "Time", "Location / Panel", "Temp (°C)", "RH (%)", "Operator ID", "Remarks"]
    existing_ahu_cols = [c for c in desired_ahu_cols if c in df.columns]
    processed_ahu = df[existing_ahu_cols]

# 2. Process DHU Control Panel Logs
processed_dhu = pd.DataFrame()
if not raw_dhu.empty:
    df = raw_dhu.copy()
    dt_series = pd.to_datetime(df["timestamp"] if "timestamp" in df.columns else df.get("created_at", datetime.now()))
    
    df["Date"] = dt_series.dt.date
    df["Time"] = dt_series.dt.strftime("%H:%M")
    df["Location / Panel"] = "DHU Control Panel"
    
    rename_dict = {}
    if "relative_humidity" in df.columns: rename_dict["relative_humidity"] = "RH (%)"
    elif "humidity" in df.columns: rename_dict["humidity"] = "RH (%)"
    
    if "dpg" in df.columns: rename_dict["dpg"] = "DPG (Pa)"
    elif "differential_pressure" in df.columns: rename_dict["differential_pressure"] = "DPG (Pa)"
    
    if "temperature" in df.columns: rename_dict["temperature"] = "Temp (°C)"
    if "operator_id" in df.columns: rename_dict["operator_id"] = "Operator ID"
    if "remarks" in df.columns: rename_dict["remarks"] = "Remarks"
    
    df.rename(columns=rename_dict, inplace=True)
    
    desired_dhu_cols = ["Date", "Time", "Location / Panel", "RH (%)", "DPG (Pa)", "Temp (°C)", "Operator ID", "Remarks"]
    existing_dhu_cols = [c for c in desired_dhu_cols if c in df.columns]
    processed_dhu = df[existing_dhu_cols]

# 3. Process Air Compressor Panel Logs
processed_comp = pd.DataFrame()
if not raw_comp.empty:
    df = raw_comp.copy()
    dt_series = pd.to_datetime(df["timestamp"] if "timestamp" in df.columns else df.get("created_at", datetime.now()))
    
    df["Date"] = dt_series.dt.date
    df["Time"] = dt_series.dt.strftime("%H:%M")
    df["Location / Panel"] = "Air Compressor Panel"
    
    rename_dict = {}
    if "delivery_pressure" in df.columns: rename_dict["delivery_pressure"] = "Pressure (Bar)"
    elif "pressure" in df.columns: rename_dict["pressure"] = "Pressure (Bar)"
    
    if "dew_point" in df.columns: rename_dict["dew_point"] = "Dew Point (°C)"
    if "operator_id" in df.columns: rename_dict["operator_id"] = "Operator ID"
    if "status" in df.columns: rename_dict["status"] = "Status"
    if "remarks" in df.columns: rename_dict["remarks"] = "Remarks"
    
    df.rename(columns=rename_dict, inplace=True)
    
    desired_comp_cols = ["Date", "Time", "Location / Panel", "Pressure (Bar)", "Dew Point (°C)", "Operator ID", "Status", "Remarks"]
    existing_comp_cols = [c for c in desired_comp_cols if c in df.columns]
    processed_comp = df[existing_comp_cols]

# 4. Process Deviations & CAPA Register
processed_dev = pd.DataFrame()
if not raw_dev.empty:
    df = raw_dev.copy()
    dt_series = pd.to_datetime(df["timestamp"] if "timestamp" in df.columns else df.get("created_at", datetime.now()))
    
    df["Date"] = dt_series.dt.date
    df["Time"] = dt_series.dt.strftime("%H:%M")
    
    rename_dict = {
        "parameter": "Parameter",
        "value": "Excursion Value",
        "severity": "Severity",
        "capa_status": "CAPA Status",
        "operator_id": "Operator ID"
    }
    df.rename(columns=rename_dict, inplace=True)
    
    desired_dev_cols = ["Date", "Time", "Parameter", "Excursion Value", "Severity", "CAPA Status", "Operator ID"]
    existing_dev_cols = [c for c in desired_dev_cols if c in df.columns]
    processed_dev = df[existing_dev_cols]

# ---------------------------------------------------------------------------
# Filter Data by Selected Date Range
# ---------------------------------------------------------------------------
def filter_by_date(df):
    if df.empty or "Date" not in df.columns:
        return df
    return df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

p_ahu_filtered = filter_by_date(processed_ahu)
p_dhu_filtered = filter_by_date(processed_dhu)
p_comp_filtered = filter_by_date(processed_comp)
p_dev_filtered = filter_by_date(processed_dev)

# High-Level Metric Summary
kpi_cols = st.columns(5)
with kpi_cols[0]:
    render_kpi_card("AHU Panel Records", f"{len(p_ahu_filtered)}")
with kpi_cols[1]:
    render_kpi_card("DHU Records", f"{len(p_dhu_filtered)}")
with kpi_cols[2]:
    render_kpi_card("Compressor Records", f"{len(p_comp_filtered)}")
with kpi_cols[3]:
    render_kpi_card("Logged Excursions", f"{len(p_dev_filtered)}")
with kpi_cols[4]:
    render_kpi_card("Compliance", "21 CFR Part 11")

st.write("")
st.subheader("Audit Trail Parameter Table")

# Select Dataset Based on Module Filter
if report_type == "AHU Control Panel Logs":
    display_df = p_ahu_filtered.copy()
elif report_type == "DHU Logs":
    display_df = p_dhu_filtered.copy()
elif report_type == "Air Compressor Logs":
    display_df = p_comp_filtered.copy()
elif report_type == "Deviations & CAPA Register":
    display_df = p_dev_filtered.copy()
else:
    # All Facility Telemetry
    dfs = []
    if not p_ahu_filtered.empty: dfs.append(p_ahu_filtered)
    if not p_dhu_filtered.empty: dfs.append(p_dhu_filtered)
    if not p_comp_filtered.empty: dfs.append(p_comp_filtered)
    if dfs:
        display_df = pd.concat(dfs, ignore_index=True)
    else:
        display_df = pd.DataFrame()

# ---------------------------------------------------------------------------
# Final Table Render & CSV Export
# ---------------------------------------------------------------------------
if not display_df.empty:
    display_df["Date"] = display_df["Date"].astype(str)
    
    if "Date" in display_df.columns and "Time" in display_df.columns:
        display_df = display_df.sort_values(by=["Date", "Time"], ascending=[False, False])
        
    display_df.insert(0, "S/N", range(1, len(display_df) + 1))

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.write("")
    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Audit Trail Report (CSV)",
        data=csv_data,
        file_name=f"COLEXA_Audit_Report_{report_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("No compliance telemetry records match the selected date range and report module criteria.")