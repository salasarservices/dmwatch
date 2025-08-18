import streamlit as st

# Loader CSS
def inject_loader_css():
    st.markdown(\"\"\"
    <style>
    .loader { ... } /* (CSS as in your code, omitted for brevity) */
    </style>
    \"\"\", unsafe_allow_html=True)

def show_loader(placeholder, message="Loading..."):
    inject_loader_css()
    placeholder.markdown(
        f\"\"\"
        <div style="width:100%;text-align:center;margin:1.7em 0;">
            <div class="loader"></div>
            <div style="margin-top:0.8em; font-size:1.05em; color:#2d448d; font-weight:500;">{message}</div>
        </div>
        \"\"\",
        unsafe_allow_html=True
    )
