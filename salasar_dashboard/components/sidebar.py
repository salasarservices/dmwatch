import streamlit as st
from salasar_dashboard.utils.auth import flush_mongo_database

def sidebar(month_options, on_pdf_click):
    st.image("https://www.salasarservices.com/assets/Frontend/images/logo-black.png", width=170)
    st.title('Report Filters')
    # ... rest of sidebar logic
    if st.button("Flush Mongo 🗑️"):
        if flush_mongo_database():
            st.success("All data in the database has been deleted!")
        else:
            st.error("Failed to flush data.")
    if st.button("Download PDF Report"):
        on_pdf_click()
