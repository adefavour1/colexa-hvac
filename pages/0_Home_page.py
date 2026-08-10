# Define explicit multi-page router including the Home overview page
pg = st.navigation([
    st.Page("pages/0_Home.py", title="Home / Overview", icon="🏠"),
    st.Page("pages/4_Executive_Dashboard.py", title="Executive Overview", icon="📈"),
    st.Page("pages/1_AHU_Monitoring.py", title="AHU Monitoring", icon="❄️"),
    st.Page("pages/2_Air_Compressor.py", title="Air Compressor", icon="🌀"),
    st.Page("pages/3_DHU_Monitoring.py", title="DHU Monitoring", icon="💧"),
    st.Page("pages/5_RCA_and_CAPA.py", title="RCA & CAPA Engine", icon="🔍"),
    st.Page("pages/6_Compliance_Reports.py", title="Compliance Reports", icon="📋"),
    st.Page("pages/7_SOP_Library.py", title="SOP Library", icon="📚"),
])
