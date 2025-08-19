import streamlit as st

# Set up the sidebar heading
st.sidebar.title("Salasar Digital Marketing Dashboard")

# Main navigation radio for the three sections
menu = st.sidebar.radio(
    "Navigation",
    [
        "WEBSITE ANALYTICS",
        "LEADS DASHBOARD",
        "SOCIAL MEDIA ANALYTICS"
    ]
)

# Social media analytics dropdown, only visible when that section is selected
social_media_option = None
if menu == "SOCIAL MEDIA ANALYTICS":
    social_media_option = st.sidebar.selectbox(
        "Select Social Media Report",
        [
            "Linkedin Analytics",
            "Facebook Page Analytics",
            "Instagram Analytics",
            "YouTube Channel Overview"
        ]
    )

# Place the Flush Mongo button at the bottom of the sidebar
st.sidebar.markdown("---")
flush_clicked = st.sidebar.button("Flush Mongo")

# Expose navigation states for use in your main app
def get_sidebar_selection():
    return menu, social_media_option, flush_clicked
