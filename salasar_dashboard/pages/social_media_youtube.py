"""
Social Media Analytics — YouTube Sub-section
--------------------------------------------
Displays YouTube channel analytics (subscribers, views, watch time), top videos,
traffic sources, and trends, using OAuth and the YouTube Data & Analytics APIs.

Complies with Salasar dashboard design brief: sections, cards, tooltips, colors, and responsiveness.
"""

import streamlit as st
import pandas as pd
import requests
from datetime import date, timedelta
import plotly.express as px

# =========================
# YOUTUBE API CONFIGURATION
# =========================

def get_access_token(client_id, client_secret, refresh_token):
    """Fetches a new access token using the refresh token."""
    if not refresh_token or refresh_token == "YOUR_REFRESH_TOKEN":
        st.error(
            "Missing refresh token! Please generate a new refresh token using the OAuth flow "
            "and add it to your .streamlit/secrets.toml under [youtube]."
        )
        st.stop()
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        st.error(f"OAuth error: {response.text}")
        st.stop()
    return response.json()["access_token"]

def get_auth_headers(access_token):
    """Headers for OAuth requests."""
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

def get_date_ranges():
    """Returns start/end dates for current and previous 28-day periods."""
    today = date.today()
    end_cur = today
    start_cur = today - timedelta(days=27)
    end_prev = start_cur - timedelta(days=1)
    start_prev = end_prev - timedelta(days=27)
    return start_cur, end_cur, start_prev, end_prev

# --- Read credentials from Streamlit secrets
client_id = st.secrets["youtube"].get("client_id", "YOUR_CLIENT_ID")
client_secret = st.secrets["youtube"].get("client_secret", "YOUR_CLIENT_SECRET")
refresh_token = st.secrets["youtube"].get("refresh_token", "YOUR_REFRESH_TOKEN")
YOUTUBE_API_KEY = st.secrets["youtube"].get("api_key", "YOUR_API_KEY")
CHANNEL_ID = st.secrets["youtube"].get("channel_id", "YOUR_CHANNEL_ID")

# --- Get OAuth access token for Analytics API
ACCESS_TOKEN = get_access_token(client_id, client_secret, refresh_token)

# =========================
# 1. CHANNEL OVERVIEW METRICS
# =========================

def get_yt_analytics_summary(start_date, end_date):
    """Fetches core YouTube channel metrics for a date range."""
    endpoint = "https://youtubeanalytics.googleapis.com/v2/reports"
    params = {
        "ids": f"channel=={CHANNEL_ID}",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost",
        "dimensions": "",
    }
    resp = requests.get(endpoint, headers=get_auth_headers(ACCESS_TOKEN), params=params).json()
    if "rows" not in resp:
        return {"views": 0, "watch_time": 0, "subs_gained": 0, "subs_lost": 0}
    row = resp["rows"][0]
    col_map = {c["name"]: i for i, c in enumerate(resp["columnHeaders"])}
    return {
        "views": int(row[col_map["views"]]),
        "watch_time": int(row[col_map["estimatedMinutesWatched"]]),
        "subs_gained": int(row[col_map["subscribersGained"]]),
        "subs_lost": int(row[col_map["subscribersLost"]]),
    }

def get_total_subscribers():
    """Fetches total subscriber count (lifetime)."""
    url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={CHANNEL_ID}&key={YOUTUBE_API_KEY}"
    resp = requests.get(url).json()
    if "items" in resp and len(resp["items"]) > 0:
        return int(resp["items"][0]["statistics"].get("subscriberCount", 0))
    return 0

def get_new_subs_text(subs_gained, subs_lost):
    """Returns color-coded HTML for net new subscribers."""
    net = subs_gained - subs_lost
    if net > 0:
        color = "#2ecc40"
        sign = "+"
        text = f"<span style='color:{color}; font-weight:bold;'>{sign}{net} new</span>"
    elif net < 0:
        color = "#ff4136"
        sign = "-"
        text = f"<span style='color:{color}; font-weight:bold;'>{sign}{abs(net)} unsubscribed</span>"
    else:
        color = "#888"
        text = f"<span style='color:{color}; font-weight:bold;'>0 (no change)</span>"
    return text

# --- Fetch date ranges and current/previous overview
start_cur, end_cur, start_prev, end_prev = get_date_ranges()
overview_cur = get_yt_analytics_summary(start_cur, end_cur)
overview_prev = get_yt_analytics_summary(start_prev, end_prev)
total_subscribers = get_total_subscribers()

# =========================
# DESIGN: CHANNEL OVERVIEW ROW
# =========================

st.markdown("""
<style>
.section-header {
    font-size: 2.1em !important;
    font-weight: bold !important;
    color: #2d448d !important;
    margin-bottom: 0.5em;
}
.yt-metric-circle {
    transition: transform 0.18s cubic-bezier(.4,2,.55,.44);
    cursor: pointer;
}
.yt-metric-circle:hover {
    transform: scale(1.13);
    box-shadow: 0 6px 20px rgba(44,68,141,0.18);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header">YouTube Channel Overview</div>', unsafe_allow_html=True)
overview_cols = st.columns(3)

# --- Subscribers/Views/Watch time metric cards
subs_gained = overview_cur["subs_gained"]
subs_lost = overview_cur["subs_lost"]
subs_text = get_new_subs_text(subs_gained, subs_lost)

overview_metrics = [
    {
        "label": "Subscribers (Net)",
        "value": total_subscribers,
        "subs_text": subs_text,
        "color": "#ffe1c8",
        "circle_color": "#e67e22",
    },
    {
        "label": "Total Views",
        "value": overview_cur["views"],
        "subs_text": None,
        "color": "#c8e6fa",
        "circle_color": "#3498db",
    },
    {
        "label": "Watch Time (min)",
        "value": overview_cur["watch_time"],
        "subs_text": None,
        "color": "#a7f1df",
        "circle_color": "#16a085",
    },
]

for i, col in enumerate(overview_cols):
    metric = overview_metrics[i]
    with col:
        st.markdown(
            f"""
            <div style='text-align:center; font-weight:500; font-size:23px; margin-bottom:0.2em; color:#2d448d'>
                {metric["label"]}
            </div>
            <div style='margin:0 auto; display:flex; align-items:center; justify-content:center; height:110px;'>
                <div class="yt-metric-circle" style='background:{metric["color"]}; border-radius:50%; width:100px; height:100px; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 12px rgba(0,0,0,0.12);'>
                    <span style='color:{metric["circle_color"]}; font-size:2em; font-family: Fira Code, monospace; font-weight:bold;'>{metric["value"]}</span>
                </div>
            </div>
            <div style='text-align:center; font-size:16px; margin-top:0.3em; min-height:1.5em;'>
                {metric["subs_text"] if metric["subs_text"] else ""}
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# 2. TOP 5 VIDEOS SECTION
# =========================

def get_top_videos(start_date, end_date, max_results=5):
    """Fetches stats for the top 5 videos in the period."""
    video_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=id&order=date&type=video&maxResults=50"
    resp = requests.get(video_url).json()
    video_ids = [item["id"]["videoId"] for item in resp.get("items", [])]
    if not video_ids:
        return pd.DataFrame()
    stats_url = f"https://www.googleapis.com/youtube/v3/videos?key={YOUTUBE_API_KEY}&id={','.join(video_ids)}&part=snippet,statistics"
    stats_resp = requests.get(stats_url).json()
    data = []
    for item in stats_resp.get("items", []):
        published = item["snippet"]["publishedAt"][:10]
        vid_id = item["id"]
        title = item["snippet"]["title"][:60]
        views = int(item["statistics"].get("viewCount", 0))
        likes = int(item["statistics"].get("likeCount", 0))
        comments = int(item["statistics"].get("commentCount", 0))
        data.append({"id": vid_id, "title": title, "published": published, "views": views, "likes": likes, "comments": comments})
    df = pd.DataFrame(data).sort_values("views", ascending=False).head(max_results)
    ids = list(df["id"])
    if not ids:
        return df
    endpoint = "https://youtubeanalytics.googleapis.com/v2/reports"
    params = {
        "ids": "channel==MINE",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "estimatedMinutesWatched,views,likes,comments",
        "dimensions": "video",
        "filters": f"video=={','.join(ids)}"
    }
    resp = requests.get(endpoint, headers=get_auth_headers(ACCESS_TOKEN), params=params).json()
    if "rows" not in resp:
        df["watch_time"] = 0
    else:
        wt_dict = {row[0]: row[1] for row in resp["rows"]}
        df["watch_time"] = df["id"].map(wt_dict).fillna(0)
    return df

top_videos_df = get_top_videos(start_cur, end_cur, max_results=5)

st.markdown('<div class="section-header">Top 5 Videos (Current Period)</div>', unsafe_allow_html=True)
if not top_videos_df.empty:
    st.markdown("""
    <style>
    .yt-table th, .yt-table td {padding: 7px 13px; font-size: 1.01em;}
    .yt-table th {background: #2d448d; color:#fff;}
    .yt-table tr:nth-child(even) {background: #f3f3f3;}
    .yt-table tr:nth-child(odd) {background: #fff;}
    </style>
    """, unsafe_allow_html=True)
    display_df = top_videos_df[["title", "views", "watch_time", "likes", "comments"]].copy()
    display_df.columns = ["Title", "Views", "Watch Time (min)", "Likes", "Comments"]
    st.markdown(display_df.to_html(index=False, classes="yt-table"), unsafe_allow_html=True)
else:
    st.info("No video data found for this period.")

# =========================
# 3. TRAFFIC SOURCES PIE CHART
# =========================

def get_traffic_sources(start_date, end_date):
    """Fetches a breakdown of traffic sources by views."""
    endpoint = "https://youtubeanalytics.googleapis.com/v2/reports"
    params = {
        "ids": "channel==MINE",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "views",
        "dimensions": "insightTrafficSourceType",
    }
    resp = requests.get(endpoint, headers=get_auth_headers(ACCESS_TOKEN), params=params).json()
    if "rows" not in resp:
        return pd.DataFrame()
    df = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
    df["views"] = df["views"].astype(int)
    return df

traf_src_df = get_traffic_sources(start_cur, end_cur)

st.markdown('<div class="section-header">Traffic Sources</div>', unsafe_allow_html=True)
if not traf_src_df.empty:
    pie_fig = px.pie(traf_src_df, values="views", names="insightTrafficSourceType",
                     color_discrete_sequence=px.colors.sequential.Plasma,
                     title="Views by Traffic Source", hole=0.45)
    pie_fig.update_traces(textinfo='percent+label', pull=[0.05]*len(traf_src_df))
    st.plotly_chart(pie_fig, use_container_width=True)
else:
    st.info("No traffic source data available.")

# =========================
# 4. TRENDS OVER TIME (LINE CHARTS)
# =========================

def get_trends_over_time(start_date, end_date):
    """Returns views, watch time, and net subs for each day in the period."""
    endpoint = "https://youtubeanalytics.googleapis.com/v2/reports"
    params = {
        "ids": "channel==MINE",
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost",
        "dimensions": "day",
    }
    resp = requests.get(endpoint, headers=get_auth_headers(ACCESS_TOKEN), params=params).json()
    if "rows" not in resp:
        return pd.DataFrame()
    df = pd.DataFrame(resp["rows"], columns=[c["name"] for c in resp["columnHeaders"]])
    df["date"] = pd.to_datetime(df["day"])
    df["views"] = df["views"].astype(int)
    df["watch_time"] = df["estimatedMinutesWatched"].astype(int)
    df["subs"] = df["subscribersGained"].astype(int) - df["subscribersLost"].astype(int)
    return df

trend_df = get_trends_over_time(start_cur - timedelta(days=59), end_cur)

st.markdown('<div class="section-header">Trends Over Time</div>', unsafe_allow_html=True)
if not trend_df.empty:
    tr_cols = st.columns(3)
    with tr_cols[0]:
        fig1 = px.line(trend_df, x="date", y="views", title="Views (Last 60 days)", markers=True)
        fig1.update_layout(height=290, margin=dict(l=10, r=10, b=25, t=40))
        st.plotly_chart(fig1, use_container_width=True)
    with tr_cols[1]:
        fig2 = px.line(trend_df, x="date", y="watch_time", title="Watch Time (min)", markers=True)
        fig2.update_layout(height=290, margin=dict(l=10, r=10, b=25, t=40))
        st.plotly_chart(fig2, use_container_width=True)
    with tr_cols[2]:
        fig3 = px.line(trend_df, x="date", y="subs", title="Net Subscribers", markers=True)
        fig3.update_layout(height=290, margin=dict(l=10, r=10, b=25, t=40))
        st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No trend data available.")
