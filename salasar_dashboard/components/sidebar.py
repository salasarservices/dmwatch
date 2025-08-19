import streamlit as st
from salasar_dashboard.utils.auth import flush_mongo_database

def render_sidebar(month_options, selected_month):
    st.image("https://www.salasarservices.com/assets/Frontend/images/logo-black.png", width=170)
    st.title('Report Filters')
    sel = st.selectbox('Select report month:', month_options, index=month_options.index(selected_month))
    if sel != st.session_state["selected_month"]:
        st.session_state["selected_month"] = sel

    sd, ed, psd, ped = st.session_state["date_range"]

    st.markdown(
        f"""
        <div style="border-left: 4px solid #459fda; background: #f0f7fa; padding: 1em 1.2em; margin-bottom: 1em; border-radius: 6px;">
            <span style="font-size: 1.1em; color: #2d448d;">
            <b>Current period:</b> {sd.strftime('%B %Y')}<br>
            <b>Previous period:</b> {psd.strftime('%B %Y')}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("Refresh Data (Clear Cache)"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state["refresh"] = True

    if st.button("Flush Mongo 🗑️"):
        if flush_mongo_database():
            st.success("All data in the database has been deleted!")
        else:
            st.error("Failed to flush data.")

    return st.button("Download PDF Report")
