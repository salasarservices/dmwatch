import streamlit as st

# --- Custom CSS for sidebar styling ---
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {display:none;}
    .custom-sidebar {padding: 1.5rem 1rem 1rem 1rem; background: #f6f8fa; height: 100vh;}
    .custom-sidebar h2 {margin-bottom: 28px; font-size: 1.33rem; font-weight: 700; color: #183153;}
    .menu-btn {width: 100%; background: #e5e7eb; border: none; padding: 12px; margin-bottom: 10px; border-radius: 6px; font-size: 1rem; font-weight: 600; color: #22223b; text-align: left; cursor: pointer; transition: background 0.15s;}
    .menu-btn.selected, .menu-btn:hover {background: #c7d2fe; color: #111;}
    .dropdown-content {margin-left: 10px; margin-bottom: 12px;}
    .dropdown-btn {width: 100%; background: #ede9fe; border: none; padding: 8px 10px; margin-bottom: 7px; border-radius: 5px; font-size: 0.98rem; font-weight: 500; color: #393939; text-align: left; cursor: pointer; transition: background 0.13s;}
    .dropdown-btn.selected, .dropdown-btn:hover {background: #a5b4fc; color: #111;}
    .flush-btn {margin-top: 40px; width: 100%; background: #f87171; border: none; padding: 10px 0; border-radius: 6px; font-size: 1.02rem; font-weight: bold; color: #fff; cursor: pointer; transition: background 0.15s;}
    .flush-btn:hover {background: #dc2626;}
    </style>
""", unsafe_allow_html=True)

# --- Session state initialization ---
if "sidebar_menu" not in st.session_state:
    st.session_state["sidebar_menu"] = "WEBSITE ANALYTICS"
if "sidebar_social" not in st.session_state:
    st.session_state["sidebar_social"] = "Linkedin Analytics"

# --- Sidebar UI ---
with st.sidebar:
    st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
    st.markdown('<h2>Salasar Digital Marketing Dashboard</h2>', unsafe_allow_html=True)

    # WEBSITE ANALYTICS button
    wa_selected = st.session_state["sidebar_menu"] == "WEBSITE ANALYTICS"
    if st.button("WEBSITE ANALYTICS", key="wa_btn"):
        st.session_state["sidebar_menu"] = "WEBSITE ANALYTICS"
    st.markdown(f'<div class="menu-btn{" selected" if wa_selected else ""}"></div>', unsafe_allow_html=True)

    # LEADS DASHBOARD button
    ld_selected = st.session_state["sidebar_menu"] == "LEADS DASHBOARD"
    if st.button("LEADS DASHBOARD", key="ld_btn"):
        st.session_state["sidebar_menu"] = "LEADS DASHBOARD"
    st.markdown(f'<div class="menu-btn{" selected" if ld_selected else ""}"></div>', unsafe_allow_html=True)

    # SOCIAL MEDIA ANALYTICS main button
    sma_selected = st.session_state["sidebar_menu"] == "SOCIAL MEDIA ANALYTICS"
    if st.button("SOCIAL MEDIA ANALYTICS", key="sma_btn"):
        st.session_state["sidebar_menu"] = "SOCIAL MEDIA ANALYTICS"
    st.markdown(f'<div class="menu-btn{" selected" if sma_selected else ""}"></div>', unsafe_allow_html=True)

    # Dropdown: Only show if SOCIAL MEDIA ANALYTICS is selected
    social_options = [
        "Linkedin Analytics",
        "Facebook Page Analytics",
        "Instagram Analytics",
        "YouTube Channel Overview"
    ]
    social_opt = None
    if sma_selected:
        st.markdown('<div class="dropdown-content">', unsafe_allow_html=True)
        for opt in social_options:
            drop_selected = st.session_state["sidebar_social"] == opt
            if st.button(opt, key=f"dropdown_{opt}"):
                st.session_state["sidebar_social"] = opt
            st.markdown(f'<div class="dropdown-btn{" selected" if drop_selected else ""}"></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        social_opt = st.session_state["sidebar_social"]

    # Flush Mongo button
    flush_clicked = st.button("Flush Mongo", key="flush_mongo", help="Clear cached data")

    st.markdown('</div>', unsafe_allow_html=True)

# --- Function for main.py to call ---
def get_sidebar_selection(default="WEBSITE ANALYTICS"):
    menu = st.session_state["sidebar_menu"]
    social_media_opt = st.session_state["sidebar_social"] if menu == "SOCIAL MEDIA ANALYTICS" else None
    return menu, social_media_opt, flush_clicked
