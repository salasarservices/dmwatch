import streamlit as st

def get_sidebar_selection():
    # Session state initialization for menu and social option
    if "sidebar_menu" not in st.session_state:
        st.session_state["sidebar_menu"] = "WEBSITE ANALYTICS"
    if "sidebar_social" not in st.session_state:
        st.session_state["sidebar_social"] = "Linkedin Analytics"

    st.sidebar.title("Salasar Digital Marketing Dashboard")

    # Main menu with radio buttons
    menu = st.sidebar.radio(
        "Select Dashboard",
        ("WEBSITE ANALYTICS", "LEADS DASHBOARD", "SOCIAL MEDIA ANALYTICS"),
        index=["WEBSITE ANALYTICS", "LEADS DASHBOARD", "SOCIAL MEDIA ANALYTICS"].index(
            st.session_state["sidebar_menu"]
        ),
        key="sidebar_menu_radio"
    )
    st.session_state["sidebar_menu"] = menu

    # Social media option if relevant
    social_media_option = None
    if menu == "SOCIAL MEDIA ANALYTICS":
        social_media_option = st.sidebar.selectbox(
            "Social Media Platform",
            [
                "Linkedin Analytics",
                "Facebook Page Analytics",
                "Instagram Analytics",
                "YouTube Channel Overview"
            ],
            index=[
                "Linkedin Analytics",
                "Facebook Page Analytics",
                "Instagram Analytics",
                "YouTube Channel Overview"
            ].index(st.session_state.get("sidebar_social", "Linkedin Analytics")),
            key="sidebar_social_select"
        )
        st.session_state["sidebar_social"] = social_media_option

    # Flush cache button
    flush_clicked = st.sidebar.button("Flush Mongo Cache", help="Clear cached data from MongoDB")

    return menu, social_media_option, flush_clicked
