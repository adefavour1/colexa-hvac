import streamlit as str_lit  # or just use st if imported

def check_auth():
    """Checks if the user is authenticated in session state. If not, displays login form."""
    if st.session_state.get("authenticated", False):
        return True

    st.subheader("🔐 Colexa Biosensor - Secure Login")
    password = st.text_input("Enter Access Password", type="password")
    
    if st.button("Login"):
        # Set your desired password here
        if password == "colexa2026":  
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect Password")
            
    return False

def render_logout_sidebar():
    """Renders a logout button in the sidebar to clear session authentication."""
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.divider()
            if st.button("🔒 Logout", use_container_width=True):
                st.session_state["authenticated"] = False
                st.rerun()
