import streamlit as st

# Inject custom CSS for sidebar styling
st.markdown("""
    <style>
    /* Hide the default sidebar nav if any */
    [data-testid="stSidebarNav"] {display:none;}
    /* Custom sidebar styles */
    .custom-sidebar {
        padding: 1.5rem 1rem 1rem 1rem;
        background: #f6f8fa;
        height: 100vh;
        font-family: 'Segoe UI', sans-serif;
    }
    .custom-sidebar h2 {
        margin-bottom: 28px;
        font-size: 1.33rem;
        font-weight: 700;
        color: #183153;
        letter-spacing: 0.02em;
        text-align:left;
    }
    .menu-section {
        margin-bottom: 16px;
    }
    .menu-btn {
        display: block;
        width: 100%;
        background: #e5e7eb;
        border: none;
        padding: 12px;
        margin-bottom: 10px;
        border-radius: 6px;
        font-size: 1rem;
        font-weight: 600;
        color: #22223b;
        text-align: left;
        cursor: pointer;
        transition: background 0.15s;
    }
    .menu-btn.selected, .menu-btn:hover {
        background: #c7d2fe;
        color: #111;
    }
    .dropdown-content {
        margin-left: 10px;
        margin-bottom: 12px;
    }
    .dropdown-btn {
        display: block;
        width: 100%;
        background: #ede9fe;
        border: none;
        padding: 8px 10px;
        margin-bottom: 7px;
        border-radius: 5px;
        font-size: 0.98rem;
        font-weight: 500;
        color: #393939;
        text-align: left;
        cursor: pointer;
        transition: background 0.13s;
    }
    .dropdown-btn.selected, .dropdown-btn:hover {
        background: #a5b4fc;
        color: #111;
    }
    .flush-btn {
        margin-top: 40px;
        display: block;
        width: 100%;
        background: #f87171;
        border: none;
        padding: 10px 0;
        border-radius: 6px;
        font-size: 1.02rem;
        font-weight: bold;
        color: #fff;
        cursor: pointer;
        transition: background 0.15s;
    }
    .flush-btn:hover {
        background: #dc2626;
    }
    </style>
""", unsafe_allow_html=True)

# State management for menu
if "sidebar_menu" not in st.session_state:
    st.session_state["sidebar_menu"] = "WEBSITE ANALYTICS"
if "sidebar_social" not in st.session_state:
    st.session_state["sidebar_social"] = "Linkedin Analytics"

def sidebar_button(label, key, selected):
    btn = st.button(label, key=key)
    if btn:
        st.session_state["sidebar_menu"] = label
    return selected if st.session_state["sidebar_menu"] == label else ""

def dropdown_button(label, key, selected):
    btn = st.button(label, key=key)
    if btn:
        st.session_state["sidebar_social"] = label
        st.session_state["sidebar_menu"] = "SOCIAL MEDIA ANALYTICS"
    return selected if st.session_state["sidebar_social"] == label else ""

# Sidebar HTML structure
st.sidebar.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)
st.sidebar.markdown('<h2>Salasar Digital Marketing Dashboard</h2>', unsafe_allow_html=True)

# Main headings (WEBSITE ANALYTICS, LEADS DASHBOARD, SOCIAL MEDIA ANALYTICS)
col1, col2, col3 = st.columns([1,1,1])
with st.sidebar:
    # WEBSITE ANALYTICS
    st.markdown(
        f'<button class="menu-btn {"selected" if st.session_state["sidebar_menu"] == "WEBSITE ANALYTICS" else ""}" '
        f'onclick="window.location.reload()">{ "WEBSITE ANALYTICS" }</button>', unsafe_allow_html=True
    )
    if st.session_state["sidebar_menu"] == "WEBSITE ANALYTICS":
        pass

    # LEADS DASHBOARD
    st.markdown(
        f'<button class="menu-btn {"selected" if st.session_state["sidebar_menu"] == "LEADS DASHBOARD" else ""}" '
        f'onclick="window.location.reload()">{ "LEADS DASHBOARD" }</button>', unsafe_allow_html=True
    )
    if st.session_state["sidebar_menu"] == "LEADS DASHBOARD":
        pass

    # SOCIAL MEDIA ANALYTICS - Dropdown
    st.markdown(
        f'<button class="menu-btn {"selected" if st.session_state["sidebar_menu"] == "SOCIAL MEDIA ANALYTICS" else ""}">{ "SOCIAL MEDIA ANALYTICS" }</button>',
        unsafe_allow_html=True
    )
    if st.session_state["sidebar_menu"] == "SOCIAL MEDIA ANALYTICS":
        for opt in [
            "Linkedin Analytics",
            "Facebook Page Analytics",
            "Instagram Analytics",
            "YouTube Channel Overview"
        ]:
            st.markdown(
                f'<button class="dropdown-btn {"selected" if st.session_state["sidebar_social"] == opt else ""}">{opt}</button>',
                unsafe_allow_html=True
            )
            if st.button(opt, key=f"dropdown_{opt}"):
                st.session_state["sidebar_social"] = opt

# Flush Mongo button
flush_clicked = st.sidebar.button("Flush Mongo", key="flush_mongo", help="Clear cached data", type="primary")

st.sidebar.markdown('</div>', unsafe_allow_html=True)

# Output to main.py
def get_sidebar_selection(default="WEBSITE ANALYTICS"):
    menu = st.session_state["sidebar_menu"]
    social_media_opt = st.session_state["sidebar_social"] if menu == "SOCIAL MEDIA ANALYTICS" else None
    return menu, social_media_opt, flush_clicked
