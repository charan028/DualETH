import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth

# Load Firebase credentials
if not firebase_admin._apps:  # Ensure Firebase is initialized only once
    cred = credentials.Certificate("firebase_cred.json")  # Replace with your actual path
    firebase_admin.initialize_app(cred)

def login(email, password):
    """Authenticate user with Firebase."""
    try:
        user = auth.get_user_by_email(email)
        st.session_state["authenticated"] = True
        st.session_state["email"] = email
        return True
    except Exception as e:
        st.error("Invalid credentials. Please try again.")
        return False

def is_authenticated():
    """Check if the user is logged in."""
    return st.session_state.get("authenticated", False)

def logout():
    """Logout user."""
    st.session_state["authenticated"] = False
    st.session_state["email"] = None
