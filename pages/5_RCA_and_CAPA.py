"""
RCA & CAPA - Deviation register, root cause browsing, CAPA sign-off with
Real Cause, Corrective & Preventive Actions entry, and downloadable report export.
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
import pandas as pd
import streamlit as st

from database.operations import fetch_deviations, update_capa_status
from utils.ui_components import (
    inject_global_css,
    render_facility_header,
    render_kpi_card,
)
from utils.rca_engine import (
    RCA_KNOWLEDGE_BASE,
    get_rca_capa,
    severity_rank,
)

st.set_page_config(page_title="RCA & CAPA | COLEXA", page_icon="🔍", layout="wide")
inject_global_css()

# ---------------------------------------------------------------------------
# Sidebar Navigation & Branding (E-Signature Auth Removed)
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
        sidebar_logo_html = '<span style="font-size: 26px;">🔍</span>'

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
    "Root Cause Analysis & CAPA Register",
    "Deviation Management, Failure Mode Diagnostics & Corrective Actions — 21 CFR Part 11 Baseline"
)

# ---------------------------------------------------------------------------
# High-Level Deviation KPI Overview
# ---------------------------------------------------------------------------
all_deviations = fetch_deviations(limit=1000, status_filter=None)

total_devs = len(all_deviations) if not all_deviations.empty else 0
open_devs = len(all_deviations[all_deviations["capa_status"] == "Open"]) if not all_deviations.empty and "capa_status" in all_deviations.columns else 0
prog_devs = len(all_deviations[all_deviations["capa_status"] == "In Progress"]) if not all_deviations.empty and "capa_status" in all_deviations.columns else 0
closed_devs = len(all_deviations[all_deviations["capa_status"] == "Closed"]) if not all_deviations.empty and "capa_status" in all_deviations.columns else 0

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("Total Deviations", f"{total_devs}")
with kpi_cols[1]:
    render_kpi_card("Open CAPAs", f"{open_devs}")
with kpi_cols[2]:
    render_kpi_card("In Progress", f"{prog_devs}")
with kpi_cols[3]:
    render_kpi_card("Closed CAPAs", f"{closed_devs}")

st.write("")

# ---------------------------------------------------------------------------
# Tabbed Workflow: Register, Sign-Off, & Knowledge Engine
# ---------------------------------------------------------------------------
tab_register, tab_update, tab_rca_engine = st.tabs([
    "📋 Deviation Register",
    "✍️ CAPA Electronic Sign-Off & Actions",
    "🔬 RCA Knowledge Base & Diagnostics"
])

# ------------------- TAB 1: DEVIATION REGISTER -------------------
with tab_register:
    st.subheader("Facility Deviation & CAPA Master Register")
    
    col_filter1, col_filter2 = st.columns([1, 2])
    with col_filter1:
        status_filter = st.selectbox(
            "Filter by CAPA Status", 
            options=["All", "Open", "In Progress", "Closed"],
            index=0
        )
    
    filtered_df = fetch_deviations(limit=500, status_filter=None if status_filter == "All" else status_filter)

    if filtered_df.empty:
        st.success("No deviations match this filter. Facility parameters have remained within validated bounds.")
    else:
        filtered_df = filtered_df.copy()
        if "severity" in filtered_df.columns:
            filtered_df["severity_rank"] = filtered_df["severity"].apply(severity_rank)
            filtered_df = filtered_df.sort_values(["severity_rank", "id"], ascending=[False, False])
            display_df = filtered_df.drop(columns=["severity_rank"])
        else:
            display_df = filtered_df

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": st.column_config.NumberColumn("Record ID", format="%d"),
                "capa_status": st.column_config.SelectboxColumn("Status", options=["Open", "In Progress", "Closed"]),
                "severity": st.column_config.TextColumn("Severity Rank"),
                "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm"),
            }
        )

# ------------------- TAB 2: CAPA SIGN-OFF, ACTIONS & DOWNLOAD -------------------
with tab_update:
    st.subheader("CAPA Investigation, Action Entry & Sign-Off")
    st.caption("Document the root cause, immediate corrective actions, and preventive measures.")

    with st.form("capa_full_entry_form", clear_on_submit=False):
        col_id, col_status, col_operator = st.columns(3)
        with col_id:
            deviation_id = st.number_input("Deviation Record ID", min_value=1, step=1, help="Select the ID number from the Deviation Register.")
        with col_status:
            new_status = st.selectbox("CAPA Status", options=["In Progress", "Closed", "Open"])
        with col_operator:
            operator_name = st.text_input("Investigator / Operator ID", value="OP-SYSTEM", placeholder="e.g., OP-4029")

        st.write("")
        real_cause = st.text_area(
            "Real Cause (Root Cause)", 
            placeholder="Describe the identified root cause (e.g., Desiccant wheel reactivation heater relay failure resulting in RH spike)...",
            height=100
        )
        
        col_ca, col_pa = st.columns(2)
        with col_ca:
            corrective_action = st.text_area(
                "Corrective Action (Immediate Fix)", 
                placeholder="Immediate steps taken to contain/resolve deviation (e.g., Replaced solid-state relay and re-calibrated sensors)...",
                height=120
            )
        with col_pa:
            preventive_action = st.text_area(
                "Preventive Action (Long-Term Prevention)", 
                placeholder="Actions implemented to prevent recurrence (e.g., Added bi-monthly thermal inspection of heater relays to PM schedule)...",
                height=120
            )

        update_submitted = st.form_submit_button("💾 Save & Log CAPA Record", type="primary")

    if update_submitted:
        op_id = operator_name if operator_name.strip() else "SYS_OPERATOR"
        success = update_capa_status(int(deviation_id), new_status, op_id)
        
        # Save extended CAPA text details to session state for instant downloadable export
        st.session_state[f"capa_doc_{int(deviation_id)}"] = {
            "record_id": int(deviation_id),
            "status": new_status,
            "investigator": op_id,
            "real_cause": real_cause if real_cause.strip() else "N/A",
            "corrective_action": corrective_action if corrective_action.strip() else "N/A",
            "preventive_action": preventive_action if preventive_action.strip() else "N/A"
        }

        if success:
            st.success(f"✅ CAPA Record #{int(deviation_id)} updated successfully to '{new_status}'.")
        else:
            st.info(f"CAPA details for Record #{int(deviation_id)} staged successfully.")

    st.write("")
    st.divider()

    # --- DOWNLOADABLE CAPA REPORT SECTION ---
    st.subheader("📥 Export & Download CAPA File")
    st.caption("Generate official CAPA documentation for audit compliance.")

    capa_keys = [k for k in st.session_state.keys() if k.startswith("capa_doc_")]

    if capa_keys:
        selected_doc_key = st.selectbox(
            "Select Staged CAPA Record to Download",
            options=capa_keys,
            format_func=lambda k: f"Record #{st.session_state[k]['record_id']} - Status: {st.session_state[k]['status']}"
        )
        
        doc_data = st.session_state[selected_doc_key]

        # Format Text File Content
        report_text = f"""===================================================================
COLEXA BIOSENSOR - OFFICIAL CAPA INVESTIGATION REPORT
===================================================================
Deviation Record ID : #{doc_data['record_id']}
CAPA Status         : {doc_data['status']}
Investigator ID     : {doc_data['investigator']}
===================================================================

[1] IDENTIFIED REAL / ROOT CAUSE:
{doc_data['real_cause']}

[2] CORRECTIVE ACTION (IMMEDIATE):
{doc_data['corrective_action']}

[3] PREVENTIVE ACTION (LONG-TERM):
{doc_data['preventive_action']}

===================================================================
Governing SOP: CBL-MNT-01 / 21 CFR Part 11 Audit Trail
==================================================================="""

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.download_button(
                label="📄 Download CAPA Report (.txt)",
                data=report_text,
                file_name=f"CAPA_Report_Record_{doc_data['record_id']}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with d_col2:
            df_export = pd.DataFrame([doc_data])
            st.download_button(
                label="📊 Download CAPA Record (.csv)",
                data=df_export.to_csv(index=False),
                file_name=f"CAPA_Record_{doc_data['record_id']}.csv",
                mime="text/csv",
                use_container_width=True
            )
    else:
        st.info("Fill in and click '💾 Save & Log CAPA Record' above to generate downloadable CAPA files.")

# ------------------- TAB 3: RCA KNOWLEDGE BASE -------------------
with tab_rca_engine:
    st.subheader("RCA Knowledge Base Explorer")
    st.caption("Standard GMP/HVAC failure-mode logic tagged to governing Colexa Standard Operating Procedures (SOPs).")

    rca_col1, rca_col2 = st.columns([1, 2])
    
    with rca_col1:
        param_choice = st.selectbox("Select Parameter", options=list(RCA_KNOWLEDGE_BASE.keys()))
        direction_choice = st.radio("Deviation Direction / Excursion Type", options=["Low Warning", "High Excursion"])

    with rca_col2:
        if param_choice and direction_choice in RCA_KNOWLEDGE_BASE.get(param_choice, {}):
            result = get_rca_capa(param_choice, direction_choice)
            
            sev_color = "#EF4444" if result.get("severity") in ["Critical", "High"] else "#F59E0B"
            st.markdown(
                f"""
                <div style="padding: 12px 18px; border-radius: 8px; background-color: #111827; border-left: 5px solid {sev_color}; margin-bottom: 16px;">
                    <span style="font-weight: 700; color: {sev_color}; font-size: 1.1rem;">Severity Rank: {result.get('severity', 'N/A')}</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("#### 🛠️ Top Probable Causes")
            for cause in result.get("causes", []):
                st.markdown(f"- {cause}")

            st.markdown("---")
            st.markdown("#### 📋 Recommended Corrective & Preventive Action (CAPA)")
            st.info(result.get("recommended_capa", "No specific CAPA protocol defined."))
        else:
            st.info("No diagnostic rule defined for this specific parameter and excursion combination.")