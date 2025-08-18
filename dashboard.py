import streamlit as st
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GAuthRequest
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import time
import io
from fpdf import FPDF
import requests
from PIL import Image
import pycountry
import plotly.express as px
import json
from pymongo import MongoClient
from streamlit_js_eval import streamlit_js_eval


# =========================
# YOUTUBE API CONFIGURATION
# =========================

def get_access_token(client_id, client_secret, refresh_token):
    """Dynamically fetches an access token using your refresh_token."""
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
    """Sets headers for OAuth requests."""
    return {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}

def get_date_ranges():
    """Gets start and end dates for current and previous period (last 28 days granularity)."""
    today = date.today()
    end_cur = today
    start_cur = today - timedelta(days=27)
    end_prev = start_cur - timedelta(days=1)
    start_prev = end_prev - timedelta(days=27)
    return start_cur, end_cur, start_prev, end_prev

# Read credentials from Streamlit secrets
client_id = st.secrets["youtube"].get("client_id", "YOUR_CLIENT_ID")
client_secret = st.secrets["youtube"].get("client_secret", "YOUR_CLIENT_SECRET")
refresh_token = st.secrets["youtube"].get("refresh_token", "YOUR_REFRESH_TOKEN")

# Obtain access token dynamically
ACCESS_TOKEN = get_access_token(client_id, client_secret, refresh_token)

YOUTUBE_API_KEY = st.secrets["youtube"].get("api_key", "YOUR_API_KEY")
CHANNEL_ID = st.secrets["youtube"].get("channel_id", "YOUR_CHANNEL_ID")

# =========================
# 1. CHANNEL OVERVIEW METRICS
# =========================
# Debug 1
st.write("DEBUG: Entered get_yt_analytics_summary")
def get_yt_analytics_summary(start_date, end_date):
    st.write("DEBUG: Entered get_yt_analytics_summary")
    try:
        endpoint = "https://youtubeanalytics.googleapis.com/v2/reports"
        params = {
            "ids": f"channel=={CHANNEL_ID}",   # Try "MINE" if this fails
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
            "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost",
            "dimensions": "",
        }
        st.write("DEBUG: Params for API call:", params)
        st.write("DEBUG: ACCESS_TOKEN starts with:", ACCESS_TOKEN[:10], "...")

        resp = requests.get(endpoint, headers=get_auth_headers(ACCESS_TOKEN), params=params)
        st.write("YouTube Analytics API Request URL:", resp.url)
        st.write("Status Code:", resp.status_code)
        st.write("Headers sent:", resp.request.headers)
        try:
            api_response = resp.json()
        except Exception as e:
            st.write("API response is not JSON:", resp.text)
            return {"views": 0, "watch_time": 0, "subs_gained": 0, "subs_lost": 0}
        st.write("YouTube Analytics API Raw Response:", api_response)
        if "rows" not in api_response:
            return {"views": 0, "watch_time": 0, "subs_gained": 0, "subs_lost": 0}
        row = api_response["rows"][0]
        col_map = {c["name"]: i for i, c in enumerate(api_response["columnHeaders"])}
        return {
            "views": int(row[col_map["views"]]),
            "watch_time": int(row[col_map["estimatedMinutesWatched"]]),
            "subs_gained": int(row[col_map["subscribersGained"]]),
            "subs_lost": int(row[col_map["subscribersLost"]]),
        }
    except Exception as e:
        st.error(f"Exception in get_yt_analytics_summary: {e}")
        import traceback
        st.text(traceback.format_exc())
        return {"views": 0, "watch_time": 0, "subs_gained": 0, "subs_lost": 0}
     
    # API returns a single row with totals if dimensions is blank
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

def get_delta(current, previous):
    return (current - previous) / previous * 100 if previous else 0

# Fetch date ranges for analytics (last 28 days vs previous 28 days)
start_cur, end_cur, start_prev, end_prev = get_date_ranges()

# Fetch current and previous period analytics
overview_cur = get_yt_analytics_summary(start_cur, end_cur)
overview_prev = get_yt_analytics_summary(start_prev, end_prev)

# Compute deltas
subs_current_net = overview_cur["subs_gained"] - overview_cur["subs_lost"]
subs_prev_net = overview_prev["subs_gained"] - overview_prev["subs_lost"]
subs_delta = get_delta(subs_current_net, subs_prev_net)
views_delta = get_delta(overview_cur["views"], overview_prev["views"])
watch_delta = get_delta(overview_cur["watch_time"], overview_prev["watch_time"])

# =========================
# DESIGN: CHANNEL OVERVIEW ROW
# =========================
st.markdown('<div class="section-header">YouTube Channel Overview</div>', unsafe_allow_html=True)
overview_cols = st.columns(3)
overview_metrics = [
    {
        "label": "Subscribers (Net)",
        "value": subs_current_net,
        "delta": subs_delta,
        "color": "#e67e22"
    },
    {
        "label": "Total Views",
        "value": overview_cur["views"],
        "delta": views_delta,
        "color": "#3498db"
    },
    {
        "label": "Watch Time (min)",
        "value": overview_cur["watch_time"],
        "delta": watch_delta,
        "color": "#16a085"
    },
]
for i, col in enumerate(overview_cols):
    metric = overview_metrics[i]
    delta_sym = "↑" if metric["delta"] >= 0 else "↓"
    delta_col = "#2ecc40" if metric["delta"] >= 0 else "#ff4136"
    with col:
        st.markdown(
            f"""
            <div style='text-align:center; font-weight:500; font-size:21px; margin-bottom:0.2em'>
                {metric["label"]}
            </div>
            <div style='margin:0 auto; display:flex; align-items:center; justify-content:center; height:80px;'>
                <div style='background:{metric["color"]}; border-radius:50%; width:70px; height:70px; display:flex; align-items:center; justify-content:center; box-shadow: 0 4px 12px rgba(0,0,0,0.10);'>
                    <span style='color:white; font-size:1.2em; font-family: Fira Code, monospace; font-weight:500;'>{metric["value"]}</span>
                </div>
            </div>
            <div style='text-align:center; font-size:15px; margin-top:0.3em; color:{delta_col}; font-weight:500'>
                {delta_sym} {abs(metric["delta"]):.2f}% <span style='color:#666;'>(vs previous 28 days)</span>
            </div>
            """,
            unsafe_allow_html=True
        )

# =========================
# 2. TOP 5 VIDEOS SECTION
# =========================
def get_top_videos(start_date, end_date, max_results=5):
    # Get videos uploaded by the channel
    video_url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={CHANNEL_ID}&part=id&order=date&type=video&maxResults=50"
    resp = requests.get(video_url).json()
    video_ids = [item["id"]["videoId"] for item in resp.get("items", [])]
    if not video_ids:
        return pd.DataFrame()
    # Get video stats for each video
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
    # Sort by views in the given period
    df = pd.DataFrame(data).sort_values("views", ascending=False).head(max_results)
    # Add watch time for each video via Analytics API
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
        # rows: [video_id, estimatedMinutesWatched, views, likes, comments]
        wt_dict = {row[0]: row[1] for row in resp["rows"]}
        df["watch_time"] = df["id"].map(wt_dict).fillna(0)
    return df

# Fetch top 5 videos for current period
top_videos_df = get_top_videos(start_cur, end_cur, max_results=5)

# =========================
# DESIGN: TOP 5 VIDEOS ROW
# =========================
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

# Fetch traffic sources data
traf_src_df = get_traffic_sources(start_cur, end_cur)

# =========================
# DESIGN: TRAFFIC SOURCES PIE CHART ROW
# =========================
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

# Fetch trend data for the last 60 days for richer chart
trend_df = get_trends_over_time(start_cur - timedelta(days=59), end_cur)

# =========================
# DESIGN: TRENDS OVER TIME ROW
# =========================
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

# =========================
# FOOTNOTE / DATA UPDATE INFO
# =========================
st.caption("All YouTube metrics are updated live from YouTube Data & Analytics APIs. Credentials are loaded securely from Streamlit secrets.")

# =========================
# DEBUGGING
# =========================
def get_yt_analytics_summary(start_date, end_date):
    endpoint = "https://youtubeanalytics.googleapis.com/v2/reports"
    params = {
        "ids": "channel==MINE",  # Try replacing with f"channel=={CHANNEL_ID}" if this fails
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "metrics": "views,estimatedMinutesWatched,subscribersGained,subscribersLost",
        "dimensions": "",
    }
    resp = requests.get(endpoint, headers=get_auth_headers(ACCESS_TOKEN), params=params)
    
    # --- DEBUGGING SNIPPET START ---
    st.write("YouTube Analytics API Request URL:", resp.url)
    st.write("Status Code:", resp.status_code)
    try:
        api_response = resp.json()
    except Exception as e:
        st.write("API response is not JSON:", resp.text)
        return {"views": 0, "watch_time": 0, "subs_gained": 0, "subs_lost": 0}
    st.write("YouTube Analytics API Raw Response:", api_response)
    # --- DEBUGGING SNIPPET END ---
    
    if "rows" not in api_response:
        return {"views": 0, "watch_time": 0, "subs_gained": 0, "subs_lost": 0}
    row = api_response["rows"][0]
    col_map = {c["name"]: i for i, c in enumerate(api_response["columnHeaders"])}
    return {
        "views": int(row[col_map["views"]]),
        "watch_time": int(row[col_map["estimatedMinutesWatched"]]),
        "subs_gained": int(row[col_map["subscribersGained"]]),
        "subs_lost": int(row[col_map["subscribersLost"]]),
    }

# END OF DASHBOARD
