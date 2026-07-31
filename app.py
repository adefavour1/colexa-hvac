import streamlit as st
import datetime
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="COLEXA BIOSENSOR | HVAC Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- GLOBAL STYLING & CORPORATE SLATE THEME ---
st.markdown("""
    <style>
    /* Main Background & Font */
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Top Header Bar */
    .colexa-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-bottom: 2px solid #3b82f6;
        padding: 1.2rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .colexa-title {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
        letter-spacing: 0.05em;
        margin: 0;
    }
    .colexa-subtitle {
        font-size: 0.85rem;
        color: #94a3b8;
        margin: 0;
        text-transform: uppercase;
    }
    
    /* Metrics & Cards */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f8fafc !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }
    </style>
""", unsafe_allow_html=True)

# --- AUTHENTICATION GATEKEEPER ---
def check_authentication():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style='background-color: #1e293b; padding: 2rem; border-radius: 10px; border: 1px solid #3b82f6; text-align: center;'>
                    <h2 style='color: #38bdf8;'>COLEXA BIOSENSOR</h2>
                    <p style='color: #94a3b8;'>HVAC Monitoring & Optimization Platform</p>
                </div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Secure Login", use_container_width=True)
                
                if submit:
                    # Default local secure offline credentials check
                    if username == "admin" and password == "Colexa2026!":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("Authentication successful. Loading workspace...")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error("Invalid credentials. Please verify system access level.")
        return False
    return True

# --- MAIN APPLICATION EXECUTION ---
def main():
    if not check_authentication():
        return

    # Top Branded Header with Live JS Clock
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"""
        <div class="colexa-header">
            <div>
                <p class="colexa-subtitle">Medical Device Facility | GMP Environment</p>
                <h1 class="colexa-title">COLEXA BIOSENSOR — HVAC MONITORING</h1>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 0.9rem; color: #38bdf8; font-weight: 600;">SYSTEM ONLINE</span><br>
                <span style="font-size: 0.8rem; color: #94a3b8;">{current_time_str}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- SIDEBAR NAVIGATION ---
    st.sidebar.markdown("### Navigation Hub")
    module = st.sidebar.radio(
        "Select Module",
        ["Executive Dashboard", "AHU Telemetry", "DHU & Air Compressors", "Audit Trails & Compliance", "System Settings"]
    )

    st.sidebar.markdown("---")
    st.sidebar.info(f"Logged in as: **{st.session_state.get('username', 'Operator')}**")
    if st.sidebar.button("Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

    # --- MODULE ROUTING ---
    if module == "Executive Dashboard":
        st.subheader("Facility Infrastructure Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Cleanroom Delta P", "15.4 Pa", "+0.2 Pa")
        with col2:
            st.metric("Ambient Temp", "21.5 °C", "-0.1 °C")
        with col3:
            st.metric("Relative Humidity", "45.2 %", "+1.1 %")
        with col4:
            st.metric("Particle Count (0.5µm)", "1,240 /m³", "Optimal")

        st.markdown("---")
        st.markdown("### Recent Shift Telemetry & System Health")
        
        # Placeholder data frame for system telemetry logs
        import pandas as pd
        import numpy as np
        
        chart_data = pd.DataFrame(
            np.random.randn(20, 3) * 0.5 + [15, 21.5, 45],
            columns=["Pressure (Pa)", "Temperature (°C)", "Humidity (%)"]
        )
        st.line_chart(chart_data)

    elif module == "AHU Telemetry":
        st.subheader("Air Handling Unit (AHU) Real-Time Diagnostics")
        st.write("Detailed filter differential pressures, fan frequencies, and damper positions are monitored here.")

    elif module == "DHU & Air Compressors":
        st.subheader("Dehumidification Unit & Compressor Performance")
        st.write("Dew point tracking, compressor load factors, and dryer status parameters.")

    elif module == "Audit Trails & Compliance":
        st.subheader("21 CFR Part 11 Audit Trail")
        st.write("Immutable event logs, user modifications, and alarm acknowledgments.")

    elif module == "System Settings":
        st.subheader("Platform Configuration & Parameters")
        st.write("Manage sensor threshold limits, calibration reminders, and database backups.")

if __name__ == "__main__":
    main()
