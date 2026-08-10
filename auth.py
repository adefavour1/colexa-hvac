import streamlit as st

def check_auth():
    # If already authenticated in this session, return True immediately
    if st.session_state.get("authenticated", False):
        return True

    # Otherwise, show your login form
    st.subheader("🔐 Colexa Biosensor - Secure Login")
    
    # Simple form or input fields for password/credentials
    password = st.text_input("Enter Access Password", type="password")
    
    if st.button("Login"):
        # Replace 'your_secure_password' with your actual password check logic
        if password == "your_secure_password":  
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect Password")
            
    return False
