import streamlit as st
import requests

st.title("YouTube OAuth2 Refresh Token Fetcher")

# Display info to user
st.markdown("""
This tool helps you generate an **OAuth 2.0 authorization URL** for your YouTube Analytics API integration.<br>
**Steps:**  
1. Click the link to authorize with your Google account that owns the YouTube channel.  
2. Approve the requested permissions.<br>
3. You will be redirected to an error page (since Streamlit isn't handling redirects), but **copy the `code` parameter from the URL**.<br>
4. Paste the code below and submit to get your refresh token.
""", unsafe_allow_html=True)

# Read client info from secrets.toml
client_id = st.secrets["youtube"]["client_id"]
client_secret = st.secrets["youtube"]["client_secret"]
redirect_uri = st.secrets.get("youtube", {}).get("redirect_uri", "http://localhost:8501")  # fallback to localhost

# Build the consent URL
scopes = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]
auth_url = (
    "https://accounts.google.com/o/oauth2/v2/auth"
    f"?client_id={client_id}"
    f"&redirect_uri={redirect_uri}"
    f"&response_type=code"
    f"&access_type=offline"
    f"&prompt=consent"
    f"&scope={' '.join(scopes)}"
)

st.markdown(f"**[1. Click here to authorize YouTube access]({auth_url})**", unsafe_allow_html=True)

# Input to paste the code from redirect URL
auth_code = st.text_input("2. Paste the 'code' parameter from the redirected URL here:")

if st.button("Get Refresh Token") and auth_code:
    # Exchange code for access and refresh tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code == 200:
        resp_json = resp.json()
        st.success("Refresh Token Fetched!")
        st.code(f"refresh_token: {resp_json.get('refresh_token')}", language="yaml")
        st.code(resp_json)
        st.info("Copy the refresh token above and store in your secrets.toml for future use.")
    else:
        st.error(f"Failed to fetch tokens! Response: {resp.text}")

st.caption("This page is for one-time setup. Never share the refresh token publicly.")
