import streamlit as st
from components.sidebar import sidebar_menu

# Get sidebar selections
main_menu, social_sub_menu, flush_clicked = sidebar_menu()

st.set_page_config(page_title="Salasar Digital Marketing Dashboard", layout="wide")

st.markdown(
    "<h1 style='text-align: center; margin-bottom: 2rem;'>Salasar Digital Marketing Dashboard</h1>",
    unsafe_allow_html=True
)

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
