import streamlit as st

def check_auth():
    """Checks if user is authenticated. If not, renders a login screen requiring username & password."""
    if st.session_state.get("authenticated", False):
        return True

    # Center or structure the login screen cleanly
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Colexa Biosensor - Secure Login")
        st.markdown("Please enter your credentials to access the facility monitoring platform.")
        
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Login", use_container_width=True)
            
            if submit_btn:
                # Retrieve expected credentials from st.secrets
                expected_user = st.secrets.get("username", "admin")
                expected_pass = st.secrets.get("password", "colexa2026")
                
                if username_input == expected_user and password_input == expected_pass:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username_input
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
    return False

def render_logout_sidebar():
    """Renders a logout button and user info in the sidebar after successful login."""
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.write(f"👤 Logged in as: **{st.session_state.get('username', 'User')}**")
            st.divider()
            if st.button("🔒 Logout", use_container_width=True):
                st.session_state["authenticated"] = False
                st.session_state.pop("username", None)
                st.rerun()
