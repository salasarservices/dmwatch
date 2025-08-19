"""
Social Media Analytics — Instagram Sub-section
----------------------------------------------
Displays Instagram Business Account analytics (followers, impressions, reach, posts),
top 5 posts, traffic sources (if available), and trends, using Instagram Graph API.

Complies with Salasar dashboard design brief: sections, cards, tooltips, colors, and responsiveness.
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px

# =========================
# INSTAGRAM API CONFIGURATION
# =========================

# You must have an Instagram Business or Creator account linked to a Facebook Page.
# The following secrets must be set in Streamlit secrets:
# [instagram]
# ig_user_id = "YOUR_INSTAGRAM_USER_ID"
# access_token = "YOUR_LONG_LIVED_USER_ACCESS_TOKEN"

IG_USER_ID = st.secrets["instagram"].get("ig_user_id", "")
ACCESS_TOKEN = st.secrets["instagram"].get("access_token", "")

def ig_api(endpoint, params=None):
    """Generic IG Graph API GET request."""
    base_url = f"https://graph.facebook.com/v19.0/{endpoint}"
    params = params or {}
    params["access_token"] = ACCESS_TOKEN
    resp = requests.get(base_url, params=params).json()
    if "error" in resp:
        st.error(f"Instagram API error: {resp['error'].get('message','Unknown error')}")
        return {}
    return resp

# --- Date helpers
def get_date_ranges():
    """Returns start/end for current and previous 28-day periods."""
    today = datetime.utcnow().date()
    end_cur = today
    start_cur = today - timedelta(days=27)
    end_prev = start_cur - timedelta(days=1)
    start_prev = end_prev - timedelta(days=27)
    return start_cur, end_cur, start_prev, end_prev

start_cur, end_cur, start_prev, end_prev = get_date_ranges()

# =========================
# 1. INSTAGRAM OVERVIEW METRICS
# =========================

def get_ig_metrics(user_id, since, until):
    """Fetches impressions, reach, and profile views for a period."""
    metrics = "impressions,reach,profile_views"
    params = {
        "metric": metrics,
        "period": "day",
        "since": since.strftime("%Y-%m-%d"),
        "until": until.strftime("%Y-%m-%d"),
    }
    resp = ig_api(f"{user_id}/insights", params)
    out = {"impressions": 0, "reach": 0, "profile_views": 0}
    if "data" in resp:
        for metric in resp["data"]:
            name = metric["name"]
            values = metric.get("values", [])
            total = sum(int(v.get("value", 0)) for v in values)
            out[name] = total
    return out

def get_ig_followers(user_id):
    """Fetches current follower count."""
    resp = ig_api(f"{user_id}?fields=followers_count")
    return resp.get("followers_count", 0)

def get_ig_posts(user_id, since, until, limit=50):
    """Fetches posts for the account between two dates."""
    url = f"{user_id}/media"
    params = {
        "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
        "limit": limit
    }
    posts = []
    resp = ig_api(url, params)
    posts.extend(resp.get("data", []))
    # Filter by time range (API does not filter by date natively)
    filtered = []
    for post in posts:
        post_time = datetime.strptime(post["timestamp"], "%Y-%m-%dT%H:%M:%S%z").date()
        if since <= post_time <= until:
            filtered.append(post)
    return filtered

def safe_percent(prev, cur):
    """Safe percent change calculation."""
    if prev == 0 and cur == 0:
        return 0
    elif prev == 0:
        return 100 if cur > 0 else 0
    try:
        return ((cur - prev) / prev) * 100
    except Exception:
        return 0

def get_delta_icon_and_color(val):
    """Returns arrow and color for metric delta."""
    if val > 0:
        return "↑", "#2ecc40"
    elif val < 0:
        return "↓", "#ff4136"
    else:
        return "", "#aaa"

# --- Fetch metrics for current and previous period
cur_metrics = get_ig_metrics(IG_USER_ID, start_cur, end_cur)
prev_metrics = get_ig_metrics(IG_USER_ID, start_prev, end_prev)
followers = get_ig_followers(IG_USER_ID)

cur_posts_list = get_ig_posts(IG_USER_ID, start_cur, end_cur)
prev_posts_list = get_ig_posts(IG_USER_ID, start_prev, end_prev)
cur_posts = len(cur_posts_list)
prev_posts = len(prev_posts_list)

# --- Deltas
impressions_percent = safe_percent(prev_metrics["impressions"], cur_metrics["impressions"])
reach_percent = safe_percent(prev_metrics["reach"], cur_metrics["reach"])
profile_views_percent = safe_percent(prev_metrics["profile_views"], cur_metrics["profile_views"])
posts_percent = safe_percent(prev_posts, cur_posts)

# --- Structure metrics for rendering
ig_circles = [
    {
        "title": "Followers",
        "value": followers,
        "delta": 0,  # Optionally, compute net delta if storing historical
        "color": "#e1306c",
        "tooltip": "Current total followers of your Instagram account."
    },
    {
        "title": "Impressions",
        "value": cur_metrics["impressions"],
        "delta": impressions_percent,
        "color": "#2d448d",
        "tooltip": "Number of times your content was displayed to users during this period."
    },
    {
        "title": "Reach",
        "value": cur_metrics["reach"],
        "delta": reach_percent,
        "color": "#a6ce39",
        "tooltip": "Number of unique users who saw any of your content during this period."
    },
    {
        "title": "Profile Views",
        "value": cur_metrics["profile_views"],
        "delta": profile_views_percent,
        "color": "#459fda",
        "tooltip": "Number of times your profile was viewed during this period."
    },
    {
        "title": "Posts (This Period)",
        "value": cur_posts,
        "delta": posts_percent,
        "color": "#d178a9",
        "tooltip": "Total posts published during this period."
    }
]

# =========================
# RENDER INSTAGRAM OVERVIEW CARDS
# =========================

st.markdown("""
<style>
.ig-section-header {
    font-size: 2.1em !important;
    font-weight: bold !important;
    color: #e1306c !important;
    margin-bottom: 0.5em;
}
.ig-metric-card {
    background: #f8f6fa;
    border-radius: 16px;
    box-shadow: 0 2px 10px rgba(44,68,141,0.08);
    padding: 1.2em 0.4em 0.9em 0.4em;
    margin-bottom: 16px;
    text-align: center;
    transition: box-shadow 0.18s cubic-bezier(.4,2,.55,.44), transform 0.18s cubic-bezier(.4,2,.55,.44);
}
.ig-metric-card:hover {
    transform: scale(1.045);
    box-shadow: 0 8px 26px #e1306c36;
}
.ig-metric-label {
    font-weight: 500;
    font-size: 22px;
    margin-bottom: 0.2em;
    color: #2d448d;
}
.ig-animated-circle {
    width: 100px;
    height: 100px;
    font-size: 2em;
    font-family: Fira Code, monospace;
    font-weight: bold;
    margin: 0.5em auto 0.3em auto;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    box-shadow: 0 4px 16px rgba(44,68,141,0.13);
    transition: background 0.2s;
}
.ig-delta-row {
    margin-top: 0.1em;
    font-size: 1.07em;
    min-height:1.7em;
}
.ig-delta-up { color: #2ecc40; font-weight: 600;}
.ig-delta-down { color: #ff4136; font-weight: 600;}
.ig-delta-same { color: #aaa; }
.ig-delta-note { font-size: 0.93em; color: #888; margin-left: 5px;}
.tooltip { position: relative; display: inline-block;}
.questionmark { background:#eee; color:#888; border-radius:50%; padding:0 7px; font-size:0.88em; cursor:pointer;}
.tooltiptext {
    visibility: hidden;
    width: 240px;
    background-color: #222;
    color: #fff;
    text-align: left;
    border-radius: 4px;
    padding: 8px 12px;
    position: absolute;
    z-index: 99;
    bottom: 135%; /* Above */
    left: 50%;
    margin-left: -120px;
    opacity: 0;
    transition: opacity 0.19s;
    font-size: 0.99em;
}
.tooltip:hover .tooltiptext {
    visibility: visible;
    opacity: 1;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="ig-section-header">Instagram Analytics</div>', unsafe_allow_html=True)

ig_cols = st.columns(len(ig_circles))
for i, col in enumerate(ig_cols):
    entry = ig_circles[i]
    icon, colr = get_delta_icon_and_color(entry["delta"])
    delta_val = abs(round(entry["delta"], 2))
    delta_str = f"{icon} {delta_val:.2f}%" if i > 0 and icon else (f"{delta_val:.2f}%" if i > 0 else "")
    delta_class = "ig-delta-up" if entry["delta"] > 0 else ("ig-delta-down" if entry["delta"] < 0 else "ig-delta-same")
    with col:
        st.markdown(
            f"""
            <div class="ig-metric-card">
                <div class="ig-metric-label">{entry["title"]}
                    <span class='tooltip'>
                        <span class='questionmark'>?</span>
                        <span class='tooltiptext'>{entry["tooltip"]}</span>
                    </span>
                </div>
                <div class="ig-animated-circle" style="background:{entry['color']};">
                    <span>{entry["value"]}</span>
                </div>
                <div class="ig-delta-row">
                    <span class="{delta_class}">{delta_str}</span>
                    <span class="ig-delta-note">{'(vs. Previous Period)' if i > 0 else ''}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

if all((entry["value"] == 0 or entry["value"] is None) for entry in ig_circles):
    st.warning("No data detected for any metric. If your Instagram account is new, or if your API token is missing permissions, you may see zeros. Double-check your Instagram access token, permissions, and that your account has analytics data.")

# =========================
# 2. TOP 5 POSTS (CURRENT PERIOD)
# =========================

def get_top_posts(posts, max_results=5):
    """Sorts posts by total engagement (likes+comments) and returns top N."""
    for post in posts:
        post["engagement"] = post.get("like_count", 0) + post.get("comments_count", 0)
    top = sorted(posts, key=lambda x: x.get("engagement", 0), reverse=True)[:max_results]
    return top

top_posts = get_top_posts(cur_posts_list, max_results=5)

st.markdown('<div class="ig-section-header">Top 5 Posts (Current Period)</div>', unsafe_allow_html=True)
if top_posts:
    post_table = []
    for idx, post in enumerate(top_posts, 1):
        caption = post.get("caption", "")
        title_text = (caption[:60] + "...") if len(caption) > 60 else caption
        title_html = f"<b>{title_text}</b>"
        created_time = datetime.strptime(
            post["timestamp"], "%Y-%m-%dT%H:%M:%S%z"
        ).strftime("%-d %b %Y")
        post_type = post.get("media_type", "")
        likes = post.get("like_count", 0)
        comments = post.get("comments_count", 0)
        permalink = post.get("permalink", "#")
        post_table.append({
            "Rank": idx,
            "Post Type": post_type,
            "Title": f'<a href="{permalink}" target="_blank">{title_html}</a>',
            "Date": created_time,
            "Likes": likes,
            "Comments": comments,
            "Engagement": likes + comments
        })
    df = pd.DataFrame(post_table)
    st.markdown("""
    <style>
    .ig-table th, .ig-table td {padding: 7px 13px; font-size: 1.01em;}
    .ig-table th {background: #e1306c; color:#fff;}
    .ig-table tr:nth-child(even) {background: #f3f3f3;}
    .ig-table tr:nth-child(odd) {background: #fff;}
    </style>
    """, unsafe_allow_html=True)
    st.markdown(df.to_html(index=False, escape=False, classes="ig-table"), unsafe_allow_html=True)
else:
    st.info("No post data found for this period.")

# =========================
# 3. TRENDS OVER TIME (LINE CHART)
# =========================

def get_ig_trend_metric(user_id, metric, since, until):
    """Fetches daily metric for the period (for trendline)."""
    params = {
        "metric": metric,
        "period": "day",
        "since": since.strftime("%Y-%m-%d"),
        "until": until.strftime("%Y-%m-%d"),
    }
    resp = ig_api(f"{user_id}/insights", params)
    if "data" not in resp or not resp["data"]:
        return pd.DataFrame()
    data = []
    for m in resp["data"]:
        if m["name"] != metric:
            continue
        for value in m["values"]:
            data.append({"date": value["end_time"][:10], "value": value["value"]})
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.groupby("date")["value"].sum().reset_index()
    return df

st.markdown('<div class="ig-section-header">Trends Over Time</div>', unsafe_allow_html=True)
trend_cols = st.columns(3)
metrics_for_trend = [("impressions", "Impressions"), ("reach", "Reach"), ("profile_views", "Profile Views")]
for i, (met, met_label) in enumerate(metrics_for_trend):
    with trend_cols[i]:
        trend_df = get_ig_trend_metric(IG_USER_ID, met, start_cur - timedelta(days=59), end_cur)
        if not trend_df.empty:
            fig = px.line(trend_df, x="date", y="value", title=f"{met_label} (Last 60 days)", markers=True,
                          color_discrete_sequence=["#e1306c"])
            fig.update_layout(height=290, margin=dict(l=10, r=10, b=25, t=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No {met_label.lower()} data for trend.")

st.caption("All data is pulled live from Instagram Graph API. Tokens and IDs are loaded securely from Streamlit secrets.")
