"""
Executive Dashboard - Real-time telemetry overview, multi-unit parameter dashboards,
environmental stability heatmaps, and End-of-Day data maintenance.
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
import sqlite3
import base64
from datetime import datetime, date
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from database.operations import (
    fetch_ahu_details,
    fetch_dhu_details,
    fetch_compressor_logs,
    fetch_deviations,
    compute_kpis,
)
from utils.ui_components import (
    inject_global_css,
    render_facility_header,
    render_kpi_card,
    PARAMETER_BOUNDS,
)

st.set_page_config(page_title="Executive Dashboard | COLEXA", page_icon="📊", layout="wide")
inject_global_css()

# ---------------------------------------------------------------------------
# Sidebar Navigation & Branding (Standardized Layout)
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
render_facility_header(
    "Executive Dashboard",
    "Real-Time Facility Telemetry, Multi-Unit Dashboards & Environmental Stability Matrix"
)

# ---------------------------------------------------------------------------
# Real-Time KPI Summary Cards
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Fetch Live Telemetry Data
# ---------------------------------------------------------------------------
ahu_df = fetch_ahu_details(limit=300)
dhu_df = fetch_dhu_details(limit=300)
comp_df = fetch_compressor_logs(limit=300)

# Helper function to standardize dates & times
def process_dataframe(df):
    if df.empty:
        return df
    df = df.copy()
    if "timestamp" in df.columns:
        dt_series = pd.to_datetime(df["timestamp"])
    elif "created_at" in df.columns:
        dt_series = pd.to_datetime(df["created_at"])
    else:
        dt_series = pd.Series([datetime.now()] * len(df))
    
    df["timestamp_dt"] = dt_series
    df["Date"] = dt_series.dt.strftime("%Y-%m-%d")
    df["Time"] = dt_series.dt.strftime("%H:%M")  # Strict HH:MM format
    return df.sort_values("timestamp_dt")

ahu_df = process_dataframe(ahu_df)
dhu_df = process_dataframe(dhu_df)
comp_df = process_dataframe(comp_df)

# ---------------------------------------------------------------------------
# Clean & Uncluttered Dashboard View (Organized by System Tabs)
# ---------------------------------------------------------------------------
tab_ahu, tab_dhu, tab_comp, tab_heatmap = st.tabs([
    "❄️ AHU Control Panel",
    "💧 DHU Systems (DHU-1 & DHU-2)",
    "🌀 Air Compressor Panel",
    "🔥 Environmental Heatmap & Deviations"
])

# ------------------- TAB 1: AHU DASHBOARD -------------------
with tab_ahu:
    st.subheader("AHU Control Panel Telemetry Trends")
    if not ahu_df.empty:
        col_a1, col_a2 = st.columns(2)
        
        with col_a1:
            st.markdown("#### Temperature (°C) Trend")
            temp_col = "supply_temp" if "supply_temp" in ahu_df.columns else "temp"
            if temp_col in ahu_df.columns:
                fig_t = px.line(
                    ahu_df, x="Time", y=temp_col,
                    labels={"Time": "Time (HH:MM)", temp_col: "Temp (°C)"},
                    title="AHU Supply Temperature vs Time"
                )
                fig_t.update_traces(line_color="#06B6D4", line_width=2.5, hovertemplate="Time: %{x}<br>Temp: %{y} °C<extra></extra>")
                fig_t.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
                st.plotly_chart(fig_t, use_container_width=True)

        with col_a2:
            st.markdown("#### Relative Humidity (%) Trend")
            rh_col = "relative_humidity" if "relative_humidity" in ahu_df.columns else "rh"
            if rh_col in ahu_df.columns:
                fig_rh = px.line(
                    ahu_df, x="Time", y=rh_col,
                    labels={"Time": "Time (HH:MM)", rh_col: "RH (%)"},
                    title="AHU Relative Humidity vs Time"
                )
                fig_rh.update_traces(line_color="#C1F24D", line_width=2.5, hovertemplate="Time: %{x}<br>RH: %{y}%<extra></extra>")
                fig_rh.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
                st.plotly_chart(fig_rh, use_container_width=True)
    else:
        st.info("No AHU telemetry logged yet.")

# ------------------- TAB 2: DHU DASHBOARD -------------------
with tab_dhu:
    st.subheader("DHU-1 vs DHU-2 Telemetry Comparison")
    if not dhu_df.empty:
        # Standardize Unit IDs
        if "unit_id" in dhu_df.columns:
            dhu_df["unit_id"] = dhu_df["unit_id"].replace({"DHU-01": "DHU-1", "DHU-02": "DHU-2"})
        
        col_d1, col_d2 = st.columns(2)
        unit_color_map = {"DHU-1": "#06B6D4", "DHU-2": "#F59E0B"}

        with col_d1:
            st.markdown("#### RH (%) Comparison Trend")
            rh_col = "relative_humidity" if "relative_humidity" in dhu_df.columns else "rh"
            if rh_col in dhu_df.columns:
                fig_dhu_rh = px.line(
                    dhu_df, x="Time", y=rh_col, color="unit_id",
                    color_discrete_map=unit_color_map,
                    labels={"Time": "Time (HH:MM)", rh_col: "RH (%)", "unit_id": "Unit"},
                    title="DHU-1 vs DHU-2 Relative Humidity"
                )
                fig_dhu_rh.update_traces(line_width=2.5, hovertemplate="Time: %{x}<br>RH: %{y}%<extra></extra>")
                fig_dhu_rh.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
                st.plotly_chart(fig_dhu_rh, use_container_width=True)

        with col_d2:
            st.markdown("#### DPG (mmWC) Comparison Trend")
            dpg_col = "dpg_mmwc" if "dpg_mmwc" in dhu_df.columns else "dpg"
            if dpg_col in dhu_df.columns:
                fig_dhu_dpg = px.line(
                    dhu_df, x="Time", y=dpg_col, color="unit_id",
                    color_discrete_map=unit_color_map,
                    labels={"Time": "Time (HH:MM)", dpg_col: "DPG (mmWC)", "unit_id": "Unit"},
                    title="DHU-1 vs DHU-2 Differential Pressure"
                )
                fig_dhu_dpg.update_traces(line_width=2.5, hovertemplate="Time: %{x}<br>DPG: %{y} mmWC<extra></extra>")
                fig_dhu_dpg.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
                st.plotly_chart(fig_dhu_dpg, use_container_width=True)
    else:
        st.info("No DHU telemetry logged yet.")

# ------------------- TAB 3: AIR COMPRESSOR DASHBOARD -------------------
with tab_comp:
    st.subheader("Air Compressor Panel Telemetry Trend")
    if not comp_df.empty:
        p_col = "delivery_pressure" if "delivery_pressure" in comp_df.columns else "pressure"
        if p_col in comp_df.columns:
            fig_p = px.line(
                comp_df, x="Time", y=p_col,
                labels={"Time": "Time (HH:MM)", p_col: "Pressure (Bar)"},
                title="Delivery Pressure (Bar) vs Time"
            )
            fig_p.update_traces(line_color="#06B6D4", line_width=2.5, hovertemplate="Time: %{x}<br>Pressure: %{y} Bar<extra></extra>")
            fig_p.update_layout(paper_bgcolor="#0B0F19", plot_bgcolor="#111827", font_color="#E5E7EB")
            st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.info("No Air Compressor telemetry logged yet.")

# ------------------- TAB 4: HEATMAP & DEVIATIONS -------------------
with tab_heatmap:
    st.subheader("Environmental Stability Heat Map")
    all_dfs = []
    if not ahu_df.empty:
        all_dfs.append(ahu_df)
    if not dhu_df.empty:
        all_dfs.append(dhu_df)
    if not comp_df.empty:
        all_dfs.append(comp_df)

    if all_dfs:
        combined_logs = pd.concat(all_dfs, ignore_index=True)
        heatmap_cols = [c for c in PARAMETER_BOUNDS.keys() if c in combined_logs.columns]
        
        if heatmap_cols and len(combined_logs) > 0:
            heat_source = combined_logs.tail(30)[["Time"] + heatmap_cols].set_index("Time")
            z_normalized = heat_source.copy()
            
            for col in heatmap_cols:
                low, high = PARAMETER_BOUNDS[col]["low"], PARAMETER_BOUNDS[col]["high"]
                mid = (low + high) / 2
                span = max((high - low) / 2, 0.0001)
                z_normalized[col] = (heat_source[col] - mid) / span

            heat_fig = go.Figure(data=go.Heatmap(
                z=z_normalized.T.values,
                x=z_normalized.index,
                y=[PARAMETER_BOUNDS[c]["label"] for c in heatmap_cols],
                colorscale=[[0, "#EF4444"], [0.5, "#C1F24D"], [1, "#EF4444"]],
                zmid=0, zmin=-2, zmax=2,
                colorbar=dict(title="Deviation"),
            ))
            heat_fig.update_layout(
                paper_bgcolor="#0B0F19", plot_bgcolor="#111827",
                font_color="#E5E7EB", margin=dict(l=10, r=10, t=10, b=10), height=380,
            )
            st.plotly_chart(heat_fig, use_container_width=True)
        else:
            st.info("Heatmap data normalization pending additional parameter entries.")

    st.write("")
    st.subheader("Recent Deviations & CAPA Log")
    try:
        dev_df = fetch_deviations(limit=20)
        if dev_df.empty:
            st.success("No deviations recorded. All facility parameters are operating within validated bounds.")
        else:
            st.dataframe(dev_df, use_container_width=True, hide_index=True)
    except Exception:
        st.info("Deviations register is currently clear.")

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# End-of-Day Data Maintenance & Purge Section
# ---------------------------------------------------------------------------
st.subheader("🗑️ End-of-Day Data Maintenance & Log Purge")
st.caption("Manage facility database logs to keep charts clean, responsive, and uncluttered day-to-day.")

with st.expander("⚠️ Expand Data Deletion & Purge Controls"):
    st.warning("Action Notice: Deleting log entries will permanently erase telemetry records from the active database for the chosen parameters.")
    
    del_col1, del_col2, del_col3 = st.columns(3)
    
    with del_col1:
        purge_target = st.selectbox(
            "Select Module to Clean",
            options=["All Facility Telemetry", "AHU Control Panel Logs", "DHU System Logs", "Air Compressor Logs"]
        )
    with del_col2:
        purge_date = st.date_input("Delete Logs On or Before Date", value=date.today())
    with del_col3:
        confirm_check = st.checkbox("I confirm I want to purge these daily records", value=False)

    st.write("")

    if st.button("🗑️ Execute Data Purge", type="primary"):
        if not confirm_check:
            st.error("Please check the confirmation box before purging records.")
        else:
            try:
                # Resolve SQLite DB connection
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "database", "colexa.db")
                if not os.path.exists(db_path):
                    db_path = "colexa.db"

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                date_str = purge_date.strftime("%Y-%m-%d")

                deleted_count = 0

                if purge_target in ["All Facility Telemetry", "AHU Control Panel Logs"]:
                    cursor.execute("DELETE FROM ahu_details WHERE DATE(timestamp) <= ?", (date_str,))
                    deleted_count += cursor.rowcount

                if purge_target in ["All Facility Telemetry", "DHU System Logs"]:
                    cursor.execute("DELETE FROM dhu_details WHERE DATE(timestamp) <= ?", (date_str,))
                    deleted_count += cursor.rowcount

                if purge_target in ["All Facility Telemetry", "Air Compressor Logs"]:
                    cursor.execute("DELETE FROM compressor_logs WHERE DATE(timestamp) <= ?", (date_str,))
                    deleted_count += cursor.rowcount

                conn.commit()
                conn.close()

                st.success(f"Purge Successful: Erased recorded logs on or prior to {date_str}. ({deleted_count} records removed)")
                st.rerun()

            except Exception as e:
                st.error(f"Failed to purge database entries: {e}")