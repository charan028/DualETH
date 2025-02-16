import streamlit as st
from auth import login, logout, is_authenticated

st.title("Login Page")

if not is_authenticated():
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if login(email, password):
            st.success("Logged in successfully")
            st.rerun()

else:
    st.success(f"Logged in as {st.session_state['email']}")
    st.button("Go to Dashboard", on_click=lambda: st.switch_page("main1.py"))
    if st.button("Logout"):
        logout()
        st.rerun()