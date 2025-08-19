"""
Social Media Analytics — LinkedIn Sub-section
---------------------------------------------
Displays LinkedIn Organization Page analytics: Followers, Impressions,
Engagement Rate, Clicks (with deltas), trend charts, top posts, and
demographics (if available), using the linkedin-api-python-client.

Assumptions:
- You have a registered LinkedIn app with correct permissions.
- You have an access token for the LinkedIn Organization APIs.
- Place organization URN and access token in Streamlit secrets.
- The @linkedin-developers/linkedin-api-python-client is installed and configured.

Required in .streamlit/secrets.toml:
[linkedin]
org_urn = "urn:li:organization:XXXXXXX"
access_token = "YOUR_ACCESS_TOKEN"

"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from linkedin_api_client import LinkedinAPIClient

# ================ CONFIGURATION ================

ORG_URN = st.secrets["linkedin"]["org_urn"]
ACCESS_TOKEN = st.secrets["linkedin"]["access_token"]

# Initialize LinkedIn API client
client = LinkedinAPIClient(access_token=ACCESS_TOKEN)

# ================ DATE HELPERS ================

def get_periods(days=28):
    today = datetime.utcnow().date()
    cur_end = today
    cur_start = today - timedelta(days=days-1)
    prev_end = cur_start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=days-1)
    return cur_start, cur_end, prev_start, prev_end

cur_start, cur_end, prev_start, prev_end = get_periods(28)

def date_fmt(dateobj):
    return dateobj.strftime("%Y-%m-%d")

# ================ DATA FETCHING ================

def get_followers(urn, start, end):
    """Fetch new followers in the period and current total."""
    stats = client.get_organization_follower_statistics(urn)
    # The API returns stats by time bucket
    df = pd.DataFrame(stats.get("elements", []))
    df["followerCount"] = df["followerCounts"].apply(lambda x: x.get("organicFollowerCount", 0))
    df["time"] = pd.to_datetime(df["timeRange"].apply(lambda x: x["start"]))
    df = df.sort_values("time")
    # Get total followers (last bucket)
    total = df["followerCount"].iloc[-1] if not df.empty else 0
    # Followers gained in period
    cur = df[(df["time"] >= pd.Timestamp(start)) & (df["time"] <= pd.Timestamp(end))]
    prev = df[(df["time"] >= pd.Timestamp(prev_start)) & (df["time"] <= pd.Timestamp(prev_end))]
    cur_gain = cur["followerCount"].diff().sum() if not cur.empty else 0
    prev_gain = prev["followerCount"].diff().sum() if not prev.empty else 0
    return total, cur_gain, prev_gain, df

def get_page_stats(urn, start, end):
    """Fetch impressions, clicks, engagement for page in period."""
    stats = client.get_organization_page_statistics(
        organization=urn,
        time_interval_start=date_fmt(start),
        time_interval_end=date_fmt(end)
    )
    # API returns a list of dictionaries by date
    df = pd.DataFrame(stats.get("elements", []))
    # Flatten nested values
    df["impressions"] = df["impressions"].apply(lambda x: x.get("organic", 0))
    df["clicks"] = df["clicks"].apply(lambda x: x.get("organic", 0))
    df["engagement"] = df["engagement"].apply(lambda x: x.get("organic", 0))
    df["date"] = pd.to_datetime(df["timeRange"].apply(lambda x: x["start"]))
    return df

def get_top_posts(urn, start, end, limit=5):
    """Fetch top posts by impressions for period."""
    # Get UGC posts for the org (most recent 50)
    posts = client.get_organization_ugc_posts(urn, count=50)
    post_data = []
    for post in posts.get("elements", []):
        post_urn = post["id"]
        created = datetime.utcfromtimestamp(int(post["created"]["time"])/1000)
        if not (start <= created.date() <= end): continue
        title = post.get("specificContent", {}).get("com.linkedin.ugc.ShareContent", {}).get("shareCommentary", {}).get("text", "")
        stats = client.get_ugc_post_statistics(post_urn)
        impressions = stats.get("impressionCount", 0)
        clicks = stats.get("clickCount", 0)
        engagement = stats.get("engagement", 0)
        post_data.append({
            "title": title[:60] + ("..." if len(title) > 60 else ""),
            "date": created.strftime("%d %b %Y"),
            "impressions": impressions,
            "engagement": engagement,
            "clicks": clicks
        })
    df = pd.DataFrame(post_data).sort_values("impressions", ascending=False).head(limit)
    return df

def safe_percent(prev, cur):
    if prev == 0 and cur == 0:
        return 0
    elif prev == 0:
        return 100 if cur > 0 else 0
    try:
        return ((cur - prev) / prev) * 100
    except Exception:
        return 0

def get_delta_icon_and_color(val):
    if val > 0:
        return "↑", "#2ecc40"
    elif val < 0:
        return "↓", "#ff4136"
    else:
        return "", "#aaa"

# ================ METRICS DATA ================

followers_total, followers_cur, followers_prev, followers_df = get_followers(ORG_URN, cur_start, cur_end)
page_cur = get_page_stats(ORG_URN, cur_start, cur_end)
page_prev = get_page_stats(ORG_URN, prev_start, prev_end)
# Sums for current/previous period
cur_impressions = page_cur["impressions"].sum()
prev_impressions = page_prev["impressions"].sum()
cur_clicks = page_cur["clicks"].sum()
prev_clicks = page_prev["clicks"].sum()
cur_engagement = page_cur["engagement"].sum()
prev_engagement = page_prev["engagement"].sum()
cur_engagement_rate = round((cur_engagement / cur_impressions) * 100, 2) if cur_impressions > 0 else 0
prev_engagement_rate = round((prev_engagement / prev_impressions) * 100, 2) if prev_impressions > 0 else 0

# Deltas
followers_delta = safe_percent(followers_prev, followers_cur)
impressions_delta = safe_percent(prev_impressions, cur_impressions)
clicks_delta = safe_percent(prev_clicks, cur_clicks)
engagement_rate_delta = safe_percent(prev_engagement_rate, cur_engagement_rate)

# ================ OVERVIEW CARDS ================
st.markdown("""
<style>
.lk-section-header {font-size:2.1em !important; font-weight:bold !important; color:#0a66c2 !important; margin-bottom:0.5em;}
.lk-metric-card {background:#f4f8fc; border-radius:16px; box-shadow:0 2px 10px #0a66c214; padding:1.2em 0.4em 0.9em 0.4em; margin-bottom:16px; text-align:center;}
.lk-metric-label {font-weight:500; font-size:22px; margin-bottom:0.2em; color:#0a66c2;}
.lk-animated-circle {width:100px; height:100px; font-size:2em; font-family:Fira Code, monospace; font-weight:bold; margin:0.5em auto 0.3em auto; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; box-shadow:0 4px 16px #0a66c211;}
.lk-delta-row {margin-top:0.1em; font-size:1.07em; min-height:1.7em;}
.lk-delta-up {color:#2ecc40; font-weight:600;}
.lk-delta-down {color:#ff4136; font-weight:600;}
.lk-delta-same {color:#aaa;}
.lk-delta-note {font-size:0.93em; color:#888; margin-left:5px;}
.tooltip {position: relative; display:inline-block;}
.questionmark {background:#eee; color:#888; border-radius:50%; padding:0 7px; font-size:0.88em; cursor:pointer;}
.tooltiptext {visibility:hidden; width:240px; background:#222; color:#fff; text-align:left; border-radius:4px; padding:8px 12px; position:absolute; z-index:99; bottom:135%; left:50%; margin-left:-120px; opacity:0; transition:opacity 0.19s; font-size:0.99em;}
.tooltip:hover .tooltiptext {visibility:visible; opacity:1;}
</style>
""", unsafe_allow_html=True)

lk_circles = [
    {
        "title": "Followers",
        "value": followers_total,
        "delta": followers_delta,
        "color": "#0a66c2",
        "tooltip": "Total followers of your LinkedIn page. Delta = growth vs previous period."
    },
    {
        "title": "Impressions",
        "value": cur_impressions,
        "delta": impressions_delta,
        "color": "#41b6e6",
        "tooltip": "Number of times your posts were displayed to users in this period."
    },
    {
        "title": "Engagement Rate (%)",
        "value": cur_engagement_rate,
        "delta": engagement_rate_delta,
        "color": "#b3c100",
        "tooltip": "Engagements divided by impressions, as a percentage."
    },
    {
        "title": "Clicks",
        "value": cur_clicks,
        "delta": clicks_delta,
        "color": "#f0832b",
        "tooltip": "Number of clicks on your posts in this period."
    }
]

st.markdown('<div class="lk-section-header">LinkedIn Page Analytics</div>', unsafe_allow_html=True)
lk_cols = st.columns(len(lk_circles))
for i, col in enumerate(lk_cols):
    entry = lk_circles[i]
    icon, colr = get_delta_icon_and_color(entry["delta"])
    delta_val = abs(round(entry["delta"], 2))
    delta_str = f"{icon} {delta_val:.2f}%" if icon else f"{delta_val:.2f}%"
    delta_class = "lk-delta-up" if entry["delta"] > 0 else ("lk-delta-down" if entry["delta"] < 0 else "lk-delta-same")
    with col:
        st.markdown(
            f"""
            <div class="lk-metric-card">
                <div class="lk-metric-label">{entry["title"]}
                    <span class='tooltip'>
                        <span class='questionmark'>?</span>
                        <span class='tooltiptext'>{entry['tooltip']}</span>
                    </span>
                </div>
                <div class="lk-animated-circle" style="background:{entry['color']};">
                    <span>{entry["value"]}</span>
                </div>
                <div class="lk-delta-row">
                    <span class="{delta_class}">{delta_str}</span>
                    <span class="lk-delta-note">(vs. Previous Period)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ================ TRENDS OVER TIME ================
st.markdown('<div class="lk-section-header">Trends Over Time</div>', unsafe_allow_html=True)
trend_metrics = [
    ("Followers", followers_df, "time", "followerCount", "#0a66c2"),
    ("Impressions", page_cur, "date", "impressions", "#41b6e6"),
    ("Engagement", page_cur, "date", "engagement", "#b3c100"),
]
trend_cols = st.columns(3)
for i, (label, df, xfield, yfield, color) in enumerate(trend_metrics):
    with trend_cols[i]:
        if not df.empty:
            fig = px.line(df, x=xfield, y=yfield, title=f"{label} (Last 28 days)", markers=True, color_discrete_sequence=[color])
            fig.update_layout(height=290, margin=dict(l=10, r=10, b=25, t=40))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"No {label.lower()} data.")

# ================ TOP POSTS TABLE ================
top_posts_df = get_top_posts(ORG_URN, cur_start, cur_end, limit=5)
st.markdown('<div class="lk-section-header">Top 5 Posts (Current Period)</div>', unsafe_allow_html=True)
if not top_posts_df.empty:
    st.markdown("""
    <style>
    .lk-table th, .lk-table td {padding:7px 13px; font-size:1.01em;}
    .lk-table th {background:#0a66c2; color:#fff;}
    .lk-table tr:nth-child(even) {background:#f3f3f3;}
    .lk-table tr:nth-child(odd) {background:#fff;}
    </style>
    """, unsafe_allow_html=True)
    display_df = top_posts_df[["title", "date", "impressions", "engagement", "clicks"]].copy()
    display_df.columns = ["Title", "Date", "Impressions", "Engagement", "Clicks"]
    st.markdown(display_df.to_html(index=False, classes="lk-table"), unsafe_allow_html=True)
else:
    st.info("No post data found for this period.")

# ================ DEMOGRAPHICS (if available) ================
def get_follower_demographics(urn):
    """Fetches demographics by country, industry, job function."""
    demo = client.get_organization_follower_statistics(urn)
    # These may be in 'followerCountry', 'followerIndustry', 'followerJobFunction'
    df_country = pd.DataFrame(demo.get("followerCountry", []))
    df_industry = pd.DataFrame(demo.get("followerIndustry", []))
    df_job = pd.DataFrame(demo.get("followerJobFunction", []))
    return df_country, df_industry, df_job

st.markdown('<div class="lk-section-header">Audience Demographics</div>', unsafe_allow_html=True)
df_country, df_industry, df_job = get_follower_demographics(ORG_URN)
demo_cols = st.columns(3)
if not df_country.empty:
    with demo_cols[0]:
        fig = px.pie(df_country, values="followerCount", names="country", title="By Country")
        st.plotly_chart(fig, use_container_width=True)
if not df_industry.empty:
    with demo_cols[1]:
        fig = px.bar(df_industry, x="industry", y="followerCount", title="By Industry", color="industry")
        st.plotly_chart(fig, use_container_width=True)
if not df_job.empty:
    with demo_cols[2]:
        fig = px.bar(df_job, x="jobFunction", y="followerCount", title="By Job Function", color="jobFunction")
        st.plotly_chart(fig, use_container_width=True)

st.caption("Data uses LinkedIn Organization APIs. Tokens and URNs loaded securely from Streamlit secrets. Ensure your app has required permissions and access.")
