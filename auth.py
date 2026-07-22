import hmac
import streamlit as st

def check_auth() -> bool:
    """Returns True if authenticated. Hides sidebar and shows login form if not."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # 🛑 HIDE SIDEBAR VIA CSS WHILE LOGGED OUT
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                display: none;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Render login screen
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.title("🔒 COLEXA Portal")
        st.caption("HVAC Monitoring & Biosensor Platform")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Log In", use_container_width=True)

            if submit:
                if (
                    hmac.compare_digest(username, st.secrets["credentials"]["username"])
                    and hmac.compare_digest(password, st.secrets["credentials"]["password"])
                ):
                    st.session_state["password_correct"] = True
                    st.session_state["username"] = username
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
    return False

def render_logout_sidebar() -> None:
    """Renders user info and log out button on all page sidebars once logged in."""
    with st.sidebar:
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets") if "os" in globals() else "assets"
        # Optional: You can place your sidebar branding/logo here
        st.markdown("---")
        current_user = st.session_state.get("username", "Operator")
        st.write(f"👤 **{current_user}**")
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state["password_correct"] = False
            st.session_state.pop("username", None)
            st.rerun()