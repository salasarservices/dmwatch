import streamlit as st
from .components.sidebar import get_sidebar_selection

# Set page config for wide layout and custom heading
st.set_page_config(page_title="Salasar Digital Marketing Dashboard", layout="wide")

# Main heading
st.markdown(
    "<h1 style='text-align: center; margin-bottom: 2rem;'>Salasar Digital Marketing Dashboard</h1>",
    unsafe_allow_html=True
)

# On first load or refresh, default to 'WEBSITE ANALYTICS'
if "menu_default" not in st.session_state:
    st.session_state["menu_default"] = "WEBSITE ANALYTICS"

# Get sidebar selection states, passing the default
menu, social_media_option, flush_clicked = get_sidebar_selection(default=st.session_state["menu_default"])

# Handle Flush Mongo button (implement your logic here)
if flush_clicked:
    st.success("MongoDB cache cleared!")  # Replace with your cache clearing logic

# WEBSITE ANALYTICS (all analytics displayed in a single page)
if menu == "WEBSITE ANALYTICS":
    st.subheader("Website Analytics")
    st.markdown("### Website Performance")
    # ... (Insert Website Performance code)

    st.markdown("### Top Content")
    # ... (Insert Top Content code)

    st.markdown("### Website Analytics")
    # ... (Insert Website Analytics code)

    st.markdown("### New vs Returning Users")
    # ... (Insert New vs Returning Users code)

    st.markdown("### Active Users by Country (Top 5) + Traffic Acquisition by Channel")
    # ... (Insert Active Users by Country and Traffic Acquisition by Channel code)

# LEADS DASHBOARD (all leads data in a single page)
elif menu == "LEADS DASHBOARD":
    st.subheader("Leads Dashboard")
    st.markdown("### Leads Dashboard")
    # ... (Insert Leads Dashboard code)

    st.markdown("### Leads Data")
    # ... (Insert Leads Data code)

# SOCIAL MEDIA ANALYTICS (drop-down, individual reports)
elif menu == "SOCIAL MEDIA ANALYTICS" and social_media_option:
    if social_media_option == "Linkedin Analytics":
        st.subheader("Linkedin Analytics")
        # ... (Insert Linkedin Analytics code)

    elif social_media_option == "Facebook Page Analytics":
        st.subheader("Facebook Page Analytics")
        # ... (Insert Facebook Page Analytics code)

    elif social_media_option == "Instagram Analytics":
        st.subheader("Instagram Analytics")
        # ... (Insert Instagram Analytics code)

    elif social_media_option == "YouTube Channel Overview":
        st.subheader("YouTube Channel Overview")
        st.markdown("### Top 5 Videos")
        # ... (Insert Top 5 Videos code)
        st.markdown("### Traffic Sources")
        # ... (Insert Traffic Sources code)
        st.markdown("### Trends Over Time")
        # ... (Insert Trends Over Time code)

# Fallback info message (optional)
else:
    st.info("Select a report from the sidebar to get started.")

# Notes:
# - Place your actual analytics/reporting code where indicated.
# - Refresh and import buttons for each report should be placed inside the respective report sections, not in the sidebar.
