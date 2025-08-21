import streamlit as st

def sidebar_menu():
    # Session state for menu and social sub-menu
    if "main_menu" not in st.session_state:
        st.session_state["main_menu"] = "WEBSITE ANALYTICS"
    if "social_sub_menu" not in st.session_state:
        st.session_state["social_sub_menu"] = "Linkedin Analytics"

    # --- SIDEBAR DESIGN ---

    st.sidebar.markdown(
        "<h2 style='margin-bottom: 1.5rem;'>Salasar Digital Marketing Dashboard</h2>",
        unsafe_allow_html=True
    )

    # WEBSITE ANALYTICS button
    if st.sidebar.button("WEBSITE ANALYTICS", key="website_analytics_btn"):
        st.session_state["main_menu"] = "WEBSITE ANALYTICS"

    # LEADS DASHBOARD button
    if st.sidebar.button("LEADS DASHBOARD", key="leads_dashboard_btn"):
        st.session_state["main_menu"] = "LEADS DASHBOARD"

    # SOCIAL MEDIA ANALYTICS dropdown
    expander = st.sidebar.expander("SOCIAL MEDIA ANALYTICS", expanded=st.session_state["main_menu"] == "SOCIAL MEDIA ANALYTICS")
    with expander:
        if st.button("Linkedin Analytics", key="linkedin_btn"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "Linkedin Analytics"
        if st.button("Facebook Page Analytics", key="facebook_btn"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "Facebook Page Analytics"
        if st.button("Instagram Analytics", key="instagram_btn"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "Instagram Analytics"
        if st.button("YouTube Channel Overview", key="youtube_btn"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "YouTube Channel Overview"

    # FLUSH MONGO button
    flush_clicked = st.sidebar.button("Flush Mongo", key="flush_mongo_btn", help="Clear cached data from MongoDB")

    # Return states
    main_menu = st.session_state["main_menu"]
    social_sub_menu = st.session_state["social_sub_menu"] if main_menu == "SOCIAL MEDIA ANALYTICS" else None

    return main_menu, social_sub_menu, flush_clicked
