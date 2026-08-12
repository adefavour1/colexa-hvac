import streamlit as st

def check_auth():
    """Checks if user is authenticated. Returns True if yes, renders login if no."""
    # Ensure session state is initialized
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    # Render login UI only if NOT authenticated
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔐 Colexa Biosensor - Secure Login")
        st.markdown("Please enter your credentials to access the facility monitoring platform.")
        
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_btn = st.form_submit_button("Login", use_container_width=True)
            
            if submit_btn:
                # Use standard dict access to avoid potential issues with .get() on secrets
                expected_user = "colexa"
                expected_pass = "cbl@cbl123"
                
                # Check credentials
                if password_input == expected_pass and username_input == expected_user:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username_input
                    st.rerun() # Rerun to remove login form and show the page
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
