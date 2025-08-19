import streamlit as st

sidebar_menu = {
    "Website Performance": ["Overview", "Traffic Sources", "Speed", "SEO"],
    "Social Media Analytics": ["YouTube", "Instagram", "LinkedIn"],
    "Leads & Conversion": ["Overview", "CRM", "Campaigns"],
}

# Set default states on first load
if "expanded_section" not in st.session_state:
    st.session_state.expanded_section = "Website Performance"
if "selected_subsection" not in st.session_state:
    st.session_state.selected_subsection = "Overview"

st.sidebar.title("Salasar Dashboard")

# Sidebar menu rendering
for major_section, subsections in sidebar_menu.items():
    # Expander shows subsections only if this major section is expanded
    expanded = (major_section == st.session_state.expanded_section)
    with st.sidebar.expander(major_section, expanded=expanded):
        if expanded:
            for subsection in subsections:
                selected = st.sidebar.button(
                    subsection,
                    key=f"{major_section}_{subsection}"
                )
                if selected:
                    st.session_state.selected_subsection = subsection
                    st.session_state.expanded_section = major_section
        else:
            # Clicking the major section name expands it
            if st.sidebar.button(f"Show {major_section}", key=f"expand_{major_section}"):
                st.session_state.expanded_section = major_section

# Main area: show report for selected subsection
st.write(f"### {st.session_state.expanded_section} > {st.session_state.selected_subsection} Report")

# You would route to the appropriate report/component here
if st.session_state.expanded_section == "Website Performance":
    if st.session_state.selected_subsection == "Overview":
        st.info("Website Performance Overview Data goes here.")
    elif st.session_state.selected_subsection == "Traffic Sources":
        st.info("Traffic Sources Data goes here.")
    # ...and so on for other subsections
elif st.session_state.expanded_section == "Social Media Analytics":
    # ...handle social analytics subsections
    pass# Entry point for the Salasar Services Digital Marketing Reporting Dashboard
# TODO: Implement app layout, theming, and routing
