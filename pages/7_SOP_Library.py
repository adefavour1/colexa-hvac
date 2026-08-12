"""SOP Library - reference library of the facility's governing operating procedures."""
import os
import base64
import streamlit as st

# 1. Page Configuration (Called only once)
st.set_page_config(page_title="SOP Library | COLEXA", page_icon="📖", layout="wide")

# 2. Authentication Gatekeeper
from auth import check_auth, render_logout_sidebar
if not check_auth():
    st.stop()

render_logout_sidebar()
from utils.ui_components import inject_global_css, render_facility_header

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
        sidebar_logo_html = '<span style="font-size: 26px;">📖</span>'

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
    st.markdown("### Navigation Controls")
    
    # Navigation updated to use st.page_link to maintain session state cleanly
    st.page_link("Home.py", label="Home Overview", icon="🏠")
    st.page_link("pages/Executive_Dashboard.py", label="Executive Dashboard", icon="📈")
    st.page_link("pages/AHU_Monitoring.py", label="AHU Monitoring", icon="❄️")
    st.page_link("pages/Air_Compressor.py", label="Air Compressor", icon="🌀")
    st.page_link("pages/DHU_Monitoring.py", label="DHU Monitoring", icon="💧")
    st.page_link("pages/RCA_and_CAPA.py", label="RCA & CAPA Engine", icon="🔍")
    st.page_link("pages/Compliance_Reports.py", label="Compliance Reports", icon="📋")
    st.page_link("pages/SOP_Library.py", label="SOP Library", icon="📚")
    st.page_link("pages/System_Settings.py", label="System Settings", icon="⚙️")
    
# Render Branded Header Banner
render_facility_header("SOP Library", "Governing Operating Procedures — Colexa Biosensor Ltd")

st.caption(
    "This library reflects the three operating procedures currently on file for the utilities monitored by this "
    "platform. Source documents: CBL-MNT-02, CBL-MNT-03, CBL-MNT-05 (Rev. A0, effective 02/01/2024, prepared by "
    "Mr. Samson John, Engineering)."
)

sop_tab_ahu, sop_tab_compressor, sop_tab_dhu = st.tabs([
    "CBL-MNT-02 — AHU", "CBL-MNT-03 — Air Compressor", "CBL-MNT-05 — Dehumidifier",
])

with sop_tab_ahu:
    st.markdown("### CBL-MNT-02 — Standard Operating Procedure of AHU")
    st.markdown("**Purpose:** Specifies how the Air Handling Unit should be operated.")
    st.markdown("**Scope:** Applicable to the operation of all AHUs in the Colexa Biosensor Ltd factory.")
    st.markdown("**Responsibility:** Engineering executes and implements this SOP; QA is responsible for compliance oversight.")
    st.markdown("**Procedure:**")
    ahu_steps = [
        "Check for availability of power supply in the general AHU main panel and individual AHU panel.",
        "Check that the doors are completely closed to avoid air leakage.",
        "Check that the fresh air dampers are all open for air flow.",
        "Check condensate drainpipe, clarity of the drain line and floor drain for easy draining of the condensate.",
        "Switch ON the AHU main panel — green indicator lamps come up.",
        "Press the start push button on the main panel — green lamps turn OFF, red lamps turn ON the control panel.",
        "Turn ON the timer panel main breaker and the monitoring hygrometer on each unit comes ON.",
        "Check for any abnormal noise or vibrations.",
        "Stop the AHU from the starter panel by pressing the stop push button — green lamps come up.",
        "Turn OFF the panel main switch.",
        "Put OFF the timer panel main breaker and the monitoring hygrometer on each unit.",
    ]
    for idx, step in enumerate(ahu_steps, start=1):
        st.markdown(f"{idx}. {step}")

with sop_tab_compressor:
    st.markdown("### CBL-MNT-03 — Air Compressor SOP")
    st.markdown("**Purpose:** Specifies how to properly operate the two Fabtech Air Compressor systems.")
    st.markdown("**Scope:** Applicable to the operation of the Air Compressor at Colexa Biosensor Ltd factory.")
    st.markdown("**Responsibility:** Engineering executes and implements this SOP; QA is responsible for compliance oversight.")

    st.markdown("**Start-Up Procedure:**")
    startup_steps = [
        "Check the oil level and ensure it is gauged.",
        "Clean the entire body.",
        "Check for possible oil leakage.",
        "Open the small door to switch ON the system breaker.",
        "Wait for the system to boot for a few seconds.",
        "After booting completes, press the start button on the screen.",
        "Ensure the cylinder storage valve is open to flush out condensate left in the cylinder.",
        "Close the valve and check the pressure gauge to know the volume building up in the cylinder.",
    ]
    for idx, step in enumerate(startup_steps, start=1):
        st.markdown(f"{idx}. {step}")

    st.markdown("**Shutdown Procedure:**")
    shutdown_steps = [
        "Press the Stop button on the screen and allow the system a few seconds to power down.",
        "Open the small door and turn off the circuit breaker.",
        "Open the discharge valve to discharge stored air and condensate from the storage cylinder.",
        "Ensure all safety regulations are strictly followed.",
    ]
    for idx, step in enumerate(shutdown_steps, start=1):
        st.markdown(f"{idx}. {step}")

with sop_tab_dhu:
    st.markdown("### CBL-MNT-05 — Dehumidifier SOP")
    st.markdown("**Purpose:** Specifies how the Dehumidifier (DHU) should be operated.")
    st.markdown("**Scope:** Applicable to the operation of the DHU at Colexa Biosensor Ltd factory.")
    st.markdown("**Responsibility:** Engineering executes and implements this SOP; QA is responsible for compliance oversight.")

    st.markdown("**Start-Up Procedure:**")
    dhu_start_steps = [
        "Remove the fresh air and heat reactant filters and clean properly.",
        "Couple back the filters firmly.",
        "Turn ON the DHU and AHU control panel switch — green indicator lights come up.",
        "Wait a few seconds for the DHU display control panel to boot.",
        "After booting completes, press the green start button — red indicator lights come ON.",
        "Go to the dehumidifier and press the DHU K1 button to set it in operation.",
        "Return to the DHU display control panel to set temperature and humidity parameters.",
        "Enter the security password on the control panel for access to set parameters.",
        "Click the control icon on the screen.",
        "Click the temp icon.",
        "Click the return icon to return to the home page.",
    ]
    for idx, step in enumerate(dhu_start_steps, start=1):
        st.markdown(f"{idx}. {step}")

    st.markdown("**Shutdown Procedure:**")
    dhu_shutdown_steps = [
        "Press the DHU K1 button on the dehumidifier to shut down.",
        "Allow the system temperature on the dehumidifier screen to fall between 45–50°C.",
        "Return to the main control panel and press the stop (red) button — green indicator lights come up.",
        "Turn off the panel control switch.",
        "Ensure all safety regulations are strictly followed.",
    ]
    for idx, step in enumerate(dhu_shutdown_steps, start=1):
        st.markdown(f"{idx}. {step}")

st.write("")
st.info(
    "These SOPs govern equipment start-up/shutdown only. The RCA/CAPA engine on the **RCA & CAPA** page uses "
    "standard GMP/HVAC engineering logic tagged back to these SOP numbers for corrective actions, since the SOPs "
    "themselves do not contain numbered failure-mode tables. Review and formal QA approval is recommended before "
    "treating generated CAPA text as validated procedure."
)
