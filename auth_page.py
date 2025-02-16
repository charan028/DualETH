import streamlit as st
from auth import login, signup, is_authenticated

st.title("Firebase Authentication")

if is_authenticated():
    st.success(f"Logged in as {st.session_state['email']}")
    st.stop()  # Prevents further execution if authenticated

auth_choice = st.selectbox("Choose authentication method", ["Login", "Signup"])
email = st.text_input("Email")
password = st.text_input("Password", type="password")

if auth_choice == "Login":
    if st.button("Login"):
        if login(email, password):
            st.rerun()

elif auth_choice == "Signup":
    if st.button("Signup"):
        if signup(email, password):
            st.rerun()
