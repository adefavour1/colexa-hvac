import streamlit as st

def check_auth():
    """Checks if user is authenticated. If not, renders a clean login screen."""
    if st.session_state.get("authenticated", False):
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Colexa Biosensor - Secure Login")
        st.markdown("Please enter your credentials to access the facility monitoring platform.")
        
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Login", use_container_width=True)
            
            if submit_btn:
                # Fetch secrets safely with defaults
                expected_user = st.secrets.get("username", "colexa")
                expected_pass = st.secrets.get("password", "cbl@cbl123")
                
                # Check credentials (if username isn't strictly in secrets, validate password)
                if password_input == expected_pass and (not expected_user or username_input == expected_user):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username_input if username_input else "admin"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    return False

def render_logout_sidebar():
    """Renders logout control in the sidebar."""
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.write(f"👤 Logged in as: **{st.session_state.get('username', 'Admin')}**")
            st.divider()
            if st.button("🔒 Logout", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state.pop("username", None)
                st.rerun()
