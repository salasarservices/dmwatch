import streamlit as st
from components.sidebar import get_sidebar_selection

# Get sidebar selections
menu, social_media_option, flush_clicked = get_sidebar_selection()

st.set_page_config(page_title="Salasar Digital Marketing Dashboard", layout="wide")

st.markdown(
    "<h1 style='text-align: center; margin-bottom: 2rem;'>Salasar Digital Marketing Dashboard</h1>",
    unsafe_allow_html=True
)

if flush_clicked:
    st.success("MongoDB cache cleared!")  # Add cache clear logic if needed

# --- MAIN DASHBOARD LOGIC ---
if menu == "WEBSITE ANALYTICS":
    import pages.dashboard
    # The dashboard page will render itself

elif menu == "LEADS DASHBOARD":
    import pages.leads_dashboard
    # The leads dashboard page will render itself

elif menu == "SOCIAL MEDIA ANALYTICS" and social_media_option:
    if social_media_option == "Linkedin Analytics":
        import pages.social_media_linkedin
    elif social_media_option == "Facebook Page Analytics":
        import pages.social_media_facebook
    elif social_media_option == "Instagram Analytics":
        import pages.social_media_instagram
    elif social_media_option == "YouTube Channel Overview":
        import pages.social_media_youtube

else:
    st.info("Select a report from the sidebar to get started.")
