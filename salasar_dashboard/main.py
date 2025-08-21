import streamlit as st
# Inject custom CSS
st.markdown("""
    <style>
    /* Style the default sidebar navigation links */
    /* These selectors target the navigation links in the sidebar */
    section[data-testid="stSidebar"] nav ul li a {
        text-transform: uppercase;
        font-weight: bold;
        color: #2d448d !important;
        border: 2px solid #a6ce39;
        border-radius: 6px;
        padding: 8px 12px !important;
        margin-bottom: 10px;
        display: block;
        background: #f8fafd;
        transition: background 0.2s, color 0.2s;
        font-size: 1.05em;
    }
    /* Optional: highlight the active (selected) nav link */
    section[data-testid="stSidebar"] nav ul li[data-testid="stSidebarNavLinkActive"] a {
        background: #a6ce39 !important;
        color: #fff !important;
    }
    </style>
""", unsafe_allow_html=True)
from components.sidebar import sidebar_menu

# Remove Streamlit's default navigation/sidebar, if any, by not using multipage or page_link features.
# Use only the custom sidebar.
st.set_page_config(page_title="Salasar Digital Marketing Dashboard", layout="wide")

# Get sidebar selections
main_menu, social_sub_menu, flush_clicked = sidebar_menu()

# Do NOT repeat the title in the main area, since it's now only in the sidebar.
# If you want it in both places, uncomment the next two lines:
# st.markdown(
#     "<h1 style='text-align: center; margin-bottom: 2rem;'>Salasar Digital Marketing Dashboard</h1>",
#     unsafe_allow_html=True
# )

if flush_clicked:
    # Add your cache clearing logic here if needed
    st.success("MongoDB cache cleared!")

# --- MAIN DASHBOARD LOGIC ---
if main_menu == "WEBSITE ANALYTICS":
    # Import and run website analytics dashboard (single page for all sections)
    import pages.dashboard

elif main_menu == "LEADS DASHBOARD":
    # Import and run leads dashboard (shows both dashboard and data)
    import pages.leads_dashboard

elif main_menu == "SOCIAL MEDIA ANALYTICS":
    # Show the selected social media analytics page
    if social_sub_menu == "Linkedin Analytics":
        import pages.social_media_linkedin
    elif social_sub_menu == "Facebook Page Analytics":
        import pages.social_media_facebook
    elif social_sub_menu == "Instagram Analytics":
        import pages.social_media_instagram
    elif social_sub_menu == "YouTube Channel Overview":
        import pages.social_media_youtube

else:
    st.info("Select a report from the sidebar to get started.")
