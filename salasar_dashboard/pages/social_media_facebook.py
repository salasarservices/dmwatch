"""
Social Media Analytics — Facebook Sub-section
---------------------------------------------
Displays Facebook Page analytics (impressions, likes, followers, posts) with metric cards, deltas, tooltips, and a posts table.
Follows finalized design brief for styles, tooltips, and modularity.
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# =========================
# FACEBOOK ANALYTICS SETUP
# =========================

# Secure credentials from Streamlit secrets
PAGE_ID = st.secrets["facebook"]["page_id"]
ACCESS_TOKEN = st.secrets["facebook"]["access_token"]

def get_fb_month_range_from_dates(start_date):
    """Get first and last day of the selected month."""
    start = start_date
    end = start_date + relativedelta(months=1)
    return start, end

def get_insight(metric, since, until):
    """Fetch a specific Facebook page insight metric between two dates."""
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/insights/{metric}"
    params = {
        "since": since,
        "until": until,
        "access_token": ACCESS_TOKEN
    }
    try:
        resp = requests.get(url, params=params).json()
        if "data" in resp and len(resp["data"]) > 0 and "values" in resp["data"][0]:
            return resp['data'][0]['values'][-1]['value']
        else:
            print(f"[DEBUG] No data for metric {metric}. Response: {resp}")
        return 0
    except Exception as e:
        print(f"[ERROR] Exception in get_insight: {e}")
        return 0

def get_posts(since, until):
    """Fetch all Facebook posts for the page within a date range."""
    url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/posts"
    params = {
        "since": since,
        "until": until,
        "limit": 100,
        "access_token": ACCESS_TOKEN
    }
    posts = []
    try:
        while url:
            resp = requests.get(url, params=params).json()
            posts.extend(resp.get('data', []))
            paging = resp.get('paging', {})
            url = paging.get('next') if 'next' in paging else None
            params = {}
        return posts
    except Exception as e:
        print(f"[ERROR] Exception in get_posts: {e}")
        return []

def safe_percent(prev, cur):
    """Returns safe percentage change. Handles zero division."""
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

def get_post_likes(post_id, access_token):
    """Fetches total likes for a given post."""
    url = f"https://graph.facebook.com/v19.0/{post_id}?fields=likes.summary(true)&access_token={access_token}"
    try:
        resp = requests.get(url).json()
        return resp.get('likes', {}).get('summary', {}).get('total_count', 0)
    except Exception as e:
        print(f"[ERROR] Exception in get_post_likes: {e}")
        return 0

# =========================
# DATE RANGES FOR FACEBOOK METRICS
# =========================

# These should be set in the main orchestrator (dashboard.py) and imported or passed in.
# For this section, assume sd, ed, psd, ped are available (current and previous month start/end dates).
# If not, you may want to import or compute them here as needed.

fb_cur_start, fb_cur_end = sd, ed + timedelta(days=1)
fb_prev_start, fb_prev_end = psd, ped + timedelta(days=1)

fb_cur_since, fb_cur_until = fb_cur_start.strftime('%Y-%m-%d'), fb_cur_end.strftime('%Y-%m-%d')
fb_prev_since, fb_prev_until = fb_prev_start.strftime('%Y-%m-%d'), fb_prev_end.strftime('%Y-%m-%d')

# =========================
# FETCH FACEBOOK ANALYTICS DATA
# =========================

cur_impressions = get_insight("page_impressions", fb_cur_since, fb_cur_until)
prev_impressions = get_insight("page_impressions", fb_prev_since, fb_prev_until)
impressions_percent = safe_percent(prev_impressions, cur_impressions)

cur_likes = get_insight("page_fans", fb_cur_since, fb_cur_until)
prev_likes = get_insight("page_fans", fb_prev_since, fb_prev_until)
likes_percent = safe_percent(prev_likes, cur_likes)

cur_followers = get_insight("page_follows", fb_cur_since, fb_cur_until)
prev_followers = get_insight("page_follows", fb_prev_since, fb_prev_until)
followers_percent = safe_percent(prev_followers, cur_followers)

cur_posts_list = get_posts(fb_cur_since, fb_cur_until)
prev_posts_list = get_posts(fb_prev_since, fb_prev_until)
cur_posts = len(cur_posts_list)
prev_posts = len(prev_posts_list)
posts_percent = safe_percent(prev_posts, cur_posts)

# --- Structure metrics for rendering ---
fb_circles = [
    {
        "title": "Page Impressions",
        "value": cur_impressions,
        "delta": impressions_percent,
        "color": "#2d448d",
    },
    {
        "title": "Page Likes",
        "value": cur_likes,
        "delta": likes_percent,
        "color": "#a6ce39",
    },
    {
        "title": "Page Followers",
        "value": cur_followers,
        "delta": followers_percent,
        "color": "#459fda",
    },
    {
        "title": "Posts (This Month)",
        "value": cur_posts,
        "delta": posts_percent,
        "color": "#d178a9",
    }
]

fb_tooltips = [
    "The total number of times any content from your Facebook page was displayed to users (impressions) during the selected period.",
    "The total number of likes your Facebook page has received during the selected period.",
    "The number of followers of your Facebook page during the selected period.",
    "Total posts published on your Facebook page this month."
]

# =========================
# RENDER FACEBOOK METRICS CARDS
# =========================

st.markdown('<div class="fb-section-header">Facebook Page Analytics</div>', unsafe_allow_html=True)

fb_cols = st.columns(4)
for i, col in enumerate(fb_cols):
    entry = fb_circles[i]
    icon, colr = get_delta_icon_and_color(entry["delta"])
    delta_val = abs(round(entry["delta"], 2))
    delta_str = f"{icon} {delta_val:.2f}%" if icon else f"{delta_val:.2f}%"
    delta_class = "fb-delta-up" if entry["delta"] > 0 else ("fb-delta-down" if entry["delta"] < 0 else "fb-delta-same")
    with col:
        st.markdown(
            f"""
            <div class="fb-metric-card">
                <div class="fb-metric-label">{entry["title"]}
                    <span class='tooltip'>
                        <span class='questionmark'>?</span>
                        <span class='tooltiptext'>{fb_tooltips[i]}</span>
                    </span>
                </div>
                <div class="fb-animated-circle" style="background:{entry['color']};">
                    <span>{entry["value"]}</span>
                </div>
                <div class="fb-delta-row">
                    <span class="{delta_class}">{delta_str}</span>
                    <span class="fb-delta-note">(vs. Previous Month)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

if all(x["value"] == 0 for x in fb_circles):
    st.warning("No data detected for any metric. If your Facebook page is new, or if your API token is missing permissions, you may see zeros. Double-check your Facebook access token, permissions, and that your page has analytics data.")

# =========================
# RENDER POSTS TABLE FOR THIS MONTH
# =========================

month_title = fb_cur_start.strftime('%B %Y')
st.markdown(f"<h3 style='color:#2d448d;'>Number of Post in {month_title}</h3>", unsafe_allow_html=True)

if fb_circles[3]['value'] > 0:
    post_table = []
    for idx, post in enumerate(cur_posts_list, 1):
        post_id = post["id"]
        message = post.get("message", "")
        title_text = (message[:50] + "...") if len(message) > 50 else message
        title_html = f"<b>{title_text}</b>"
        created_time = datetime.strptime(
            post["created_time"].replace("+0000", ""), "%Y-%m-%dT%H:%M:%S"
        ).strftime("%-d %b %Y")
        likes = get_post_likes(post_id, ACCESS_TOKEN)
        post_table.append({
            "Post Count": idx,
            "Post Title": title_html,
            "Date & time": created_time,
            "Post Likes": likes
        })
    df = pd.DataFrame(post_table)
    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
else:
    st.info("No posts published this month.")

st.caption("All data is pulled live from Facebook Graph API. Tokens and IDs are loaded securely from Streamlit secrets.")
