import streamlit as st

def sidebar_menu():
    if "main_menu" not in st.session_state:
        st.session_state["main_menu"] = "WEBSITE ANALYTICS"
    if "social_sub_menu" not in st.session_state:
        st.session_state["social_sub_menu"] = "Linkedin Analytics"

    st.sidebar.markdown("<h2>Salasar Digital Marketing Dashboard</h2>", unsafe_allow_html=True)

    if st.sidebar.button("WEBSITE ANALYTICS"):
        st.session_state["main_menu"] = "WEBSITE ANALYTICS"

    if st.sidebar.button("LEADS DASHBOARD"):
        st.session_state["main_menu"] = "LEADS DASHBOARD"

    expander = st.sidebar.expander("SOCIAL MEDIA ANALYTICS", expanded=st.session_state["main_menu"] == "SOCIAL MEDIA ANALYTICS")
    with expander:
        if st.button("Linkedin Analytics"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "Linkedin Analytics"
        if st.button("Facebook Page Analytics"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "Facebook Page Analytics"
        if st.button("Instagram Analytics"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "Instagram Analytics"
        if st.button("YouTube Channel Overview"):
            st.session_state["main_menu"] = "SOCIAL MEDIA ANALYTICS"
            st.session_state["social_sub_menu"] = "YouTube Channel Overview"

    flush_clicked = st.sidebar.button("Flush Mongo", help="Clear cached data from MongoDB")

    main_menu = st.session_state["main_menu"]
    social_sub_menu = st.session_state["social_sub_menu"] if main_menu == "SOCIAL MEDIA ANALYTICS" else None

    return main_menu, social_sub_menu, flush_clicked
