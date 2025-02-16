import streamlit as st
from auth import login

st.title("Login Page")

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if login(email, password):
        st.success("Login successful!")
        st.rerun()  # Ensure page refresh after login

# Redirect to main1.py if already logged in
if "authenticated" in st.session_state and st.session_state["authenticated"]:
    st.switch_page("pages/main1.py")
