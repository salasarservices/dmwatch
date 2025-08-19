import streamlit as st

def get_sidebar_selection(default="WEBSITE ANALYTICS"):
    st.sidebar.title("Salasar Digital Marketing Dashboard")
    
    # Main navigation with 3 sections
    menu = st.sidebar.radio(
        "",
        [
            "WEBSITE ANALYTICS",
            "LEADS DASHBOARD",
            "SOCIAL MEDIA ANALYTICS"
        ],
        index=["WEBSITE ANALYTICS", "LEADS DASHBOARD", "SOCIAL MEDIA ANALYTICS"].index(default)
    )
    
    # Only show the dropdown if SOCIAL MEDIA ANALYTICS is selected
    social_media_option = None
    if menu == "SOCIAL MEDIA ANALYTICS":
        st.sidebar.markdown("**Social Media Analytics Reports**")
        social_media_option = st.sidebar.selectbox(
            "Choose a report",
            [
                "Linkedin Analytics",
                "Facebook Page Analytics",
                "Instagram Analytics",
                "YouTube Channel Overview"
            ]
        )
    else:
        st.sidebar.markdown("")  # Space holder for layout consistency

    st.sidebar.markdown("---")
    flush_clicked = st.sidebar.button("Flush Mongo")

    return menu, social_media_option, flush_clicked
