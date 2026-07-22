"""
System Settings - Database Health, Parameter Boundary Configuration & Immutable Audit Trail.
Governing SOP: CBL-QA-01 / 21 CFR Part 11 Compliance Engine.
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
import streamlit as st

from database.schema import DB_PATH, initialize_database
from database.operations import (
    fetch_audit_trail,
    reset_all_telemetry_data,
    delete_telemetry_by_date_range,
    delete_record_by_id,
)
from utils.ui_components import (
    inject_global_css,
    render_facility_header,
    render_kpi_card,
    PARAMETER_BOUNDS,
    EXTENDED_PARAMETER_BOUNDS,
)

st.set_page_config(page_title="System Settings | COLEXA", page_icon="⚙️", layout="wide")
inject_global_css()


# ---------------------------------------------------------------------------
# Caching Helper
# ---------------------------------------------------------------------------
@st.cache_data(ttl=60)
def get_cached_audit_trail(limit: int = 500) -> pd.DataFrame:
    """Cached wrapper around database.operations.fetch_audit_trail."""
    return fetch_audit_trail(limit=limit)


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
        sidebar_logo_html = '<span style="font-size: 26px;">⚙️</span>'

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
    "System Settings & Configuration",
    "Database Diagnostics • Immutable Audit Trail • Validated Operating Boundaries"
)

# ---------------------------------------------------------------------------
# 1. Database Health & Status Section
# ---------------------------------------------------------------------------
st.subheader("Database Health & Integrity")

db_exists = os.path.exists(DB_PATH)
size_kb = 0.0

if db_exists:
    try:
        size_kb = os.path.getsize(DB_PATH) / 1024
    except OSError:
        size_kb = 0.0

db_cols = st.columns(2)
with db_cols[0]:
    render_kpi_card("Database File", "Active" if db_exists else "Not Found")
with db_cols[1]:
    render_kpi_card("Database Size", f"{size_kb:.1f} KB" if db_exists else "0 KB")

st.write("")
col_btn, _ = st.columns([1, 2])
with col_btn:
    if st.button("🔄 Verify & Re-run Schema Initialization", use_container_width=True):
        success = initialize_database()
        if success:
            st.success("✅ Schema verified and database tables initialized successfully.")
        else:
            st.error("❌ Schema initialization failed. Please check system logs for details.")

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# 2. Validated Parameter Boundaries Reference
# ---------------------------------------------------------------------------
st.subheader("Validated Parameter Boundaries")

tab_floor, tab_extended = st.tabs([
    "📋 Floor Log Boundaries (Doc. CBL/ENG/02/R01)",
    "⚙️ Extended Engineering Reference"
])

with tab_floor:
    st.caption("Paper form validated ranges actively monitored on the facility production floor.")
    bounds_rows = [
        {
            "Parameter": v.get("label", k),
            "Unit": v.get("unit", "-"),
            "Lower Limit": v.get("low", "-"),
            "Upper Limit": v.get("high", "-"),
            "Governing SOP": v.get("sop", "CBL-ENG-02")
        }
        for k, v in PARAMETER_BOUNDS.items()
    ]
    df_bounds = pd.DataFrame(bounds_rows)
    st.dataframe(df_bounds, use_container_width=True, hide_index=True)

with tab_extended:
    st.caption("Extended engineering parameters utilized for diagnostic triggers and advanced equipment specs.")
    extended_rows = [
        {
            "Parameter": v.get("label", k),
            "Unit": v.get("unit", "-"),
            "Lower Limit": v.get("low", "-"),
            "Upper Limit": v.get("high", "-"),
            "Governing SOP": v.get("sop", "CBL-ENG-02")
        }
        for k, v in EXTENDED_PARAMETER_BOUNDS.items()
    ]
    df_extended = pd.DataFrame(extended_rows)
    st.dataframe(df_extended, use_container_width=True, hide_index=True)

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# 3. Immutable System Audit Trail
# ---------------------------------------------------------------------------
col_audit_title, col_audit_btn = st.columns([3, 1])

with col_audit_title:
    st.subheader("Immutable System Audit Trail")
    st.caption("FDA 21 CFR Part 11 compliant event log — records all data inserts, system overrides, and user activities.")

with col_audit_btn:
    st.write("")  # Alignment spacing
    if st.button("🔄 Refresh Audit Log", use_container_width=True):
        get_cached_audit_trail.clear()
        st.rerun()

audit_df = get_cached_audit_trail(limit=500)

if audit_df.empty:
    st.info("No audit trail entries currently recorded.")
else:
    df_display = audit_df.copy()
    
    # Format Timestamps cleanly if available
    time_col = None
    if "timestamp" in df_display.columns: 
        time_col = "timestamp"
    elif "created_at" in df_display.columns: 
        time_col = "created_at"

    if time_col:
        dt_series = pd.to_datetime(df_display[time_col])
        df_display["Date"] = dt_series.dt.strftime("%Y-%m-%d")
        df_display["Time"] = dt_series.dt.strftime("%H:%M:%S")
        df_display.drop(columns=[time_col], inplace=True, errors="ignore")

    # Rename common columns for UI presentation
    rename_dict = {
        "action": "Action / Event",
        "user": "Operator / System ID",
        "user_id": "Operator / System ID",
        "operator_id": "Operator / System ID",
        "details": "Log Details",
        "description": "Log Details"
    }
    df_display.rename(columns=rename_dict, inplace=True)

    # Reorder columns with Serial Number
    if "id" in df_display.columns:
        df_display.drop(columns=["id"], inplace=True)
        
    df_display.insert(0, "S/N", range(1, len(df_display) + 1))

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.write("")
    csv_audit = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download System Audit Log (CSV)",
        data=csv_audit,
        file_name=f"COLEXA_System_Audit_Trail_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        type="primary"
    )

st.write("")
st.divider()

# ---------------------------------------------------------------------------
# 4. Data Management & Targeted Purge Controls
# ---------------------------------------------------------------------------
st.subheader("🛠️ Data Management & Deletion Controls")
st.caption("Perform targeted record purges by date range, single ID, or full system reset.")

tab_range, tab_single, tab_full = st.tabs([
    "📅 Delete by Date Range",
    "🎯 Delete Specific Record by ID",
    "⚠️ Full System Data Reset"
])

table_options = {
    "Facility Shift Logs": "facility_logs",
    "AHU Detailed Logs": "ahu_detailed_logs",
    "DHU Detailed Logs": "dhu_detailed_logs",
    "Compressor Logs": "compressor_logs",
    "Deviation / CAPA Logs": "deviation_logs"
}

# --- TAB 1: Date Range Deletion ---
with tab_range:
    st.write("##### Purge Telemetry for a Specific Date Period")
    st.caption("Select the date range and target tables you wish to remove from the database.")
    
    col_dates = st.columns(2)
    with col_dates[0]:
        start_date_val = st.date_input("Start Date", value=datetime.now().date())
    with col_dates[1]:
        end_date_val = st.date_input("End Date", value=datetime.now().date())

    selected_labels = st.multiselect(
        "Select target tables to clean",
        options=list(table_options.keys()),
        default=list(table_options.keys())
    )
    
    target_tables = [table_options[lbl] for lbl in selected_labels]
    
    col_range_act, _ = st.columns([1, 1])
    with col_range_act:
        confirm_range = st.checkbox("Confirm date-range purge", key="chk_range")
        if st.button("🗓️ Purge Data in Range", disabled=not (confirm_range and target_tables), type="primary", use_container_width=True):
            s_str = start_date_val.strftime("%Y-%m-%d")
            e_str = end_date_val.strftime("%Y-%m-%d")
            
            success, rows_deleted = delete_telemetry_by_date_range(s_str, e_str, target_tables, username="Admin")
            if success:
                st.success(f"✅ Purged {rows_deleted} record(s) recorded between {s_str} and {e_str}.")
                st.rerun()
            else:
                st.error("❌ Failed to purge records. Please check log files.")

# --- TAB 2: Single Record Deletion ---
with tab_single:
    st.write("##### Delete an Individual Record")
    st.caption("Remove a single entry by selecting its table and entering its Record S/N (ID).")
    
    col_single_inputs = st.columns(2)
    with col_single_inputs[0]:
        target_label = st.selectbox("Target Table", options=list(table_options.keys()))
        selected_table = table_options[target_label]
    with col_single_inputs[1]:
        record_id_to_delete = st.number_input("Record ID", min_value=1, step=1)
        
    confirm_single = st.checkbox(f"Confirm deletion of Record #{record_id_to_delete} from {target_label}", key="chk_single")
    
    col_single_act, _ = st.columns([1, 1])
    with col_single_act:
        if st.button("🗑️ Delete Selected Record", disabled=not confirm_single, type="primary", use_container_width=True):
            success = delete_record_by_id(selected_table, int(record_id_to_delete), username="Admin")
            if success:
                st.success(f"✅ Record #{record_id_to_delete} removed successfully from {target_label}.")
                st.rerun()
            else:
                st.error(f"❌ Record ID #{record_id_to_delete} not found or could not be deleted.")

# --- TAB 3: Full Reset ---
with tab_full:
    st.error("WARNING: This action is completely irreversible. All recorded telemetry and audit trail data will be permanently wiped.")
    confirm_wipe = st.checkbox("I confirm that I want to delete ALL database records.", key="chk_full")
    
    col_wipe_act, _ = st.columns([1, 1])
    with col_wipe_act:
        if st.button("💥 Wipe Entire Database", disabled=not confirm_wipe, type="primary", use_container_width=True):
            success = reset_all_telemetry_data()
            if success:
                st.success("✅ All database records have been wiped successfully.")
                st.rerun()
            else:
                st.error("❌ Failed to wipe database. Check logs for details.")