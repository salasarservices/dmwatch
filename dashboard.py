import streamlit as st
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GAuthRequest
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import time
import io
from fpdf import FPDF
import requests
from PIL import Image
import pycountry
import json

# =========================
# PAGE CONFIG & STYLES
# =========================
st.set_page_config(
    page_title='Salasar Services Digital Marketing Reporting Dashboard',
    layout='wide'
)

st.markdown("""
<div style="display:flex; align-items:center; margin-bottom: 1.5em;">
    <img src="https://www.salasarservices.com/assets/Frontend/images/logo-black.png" style="height:48px; margin-right:28px;">
    <span style="font-family:'Lato',Arial,sans-serif; font-size:2.2em; font-weight:700; color:#2d448d;">
        Salasar Services Digital Marketing Reporting Dashboard
    </span>
</div>
""", unsafe_allow_html=True)

# =========================
# CSS for bounce/zoom animation
# =========================
st.markdown("""
<style>
... (CSS code unchanged, omitted here for brevity) ...
</style>
""", unsafe_allow_html=True)

# =========================
# HELPER AND DATA FUNCTIONS
# =========================
def pct_change(current, previous):
    return 0 if previous == 0 else (current - previous) / previous * 100

def get_month_options():
    months, today, d = [], date.today(), date(2025,1,1)
    while d <= today:
        months.append(d)
        d += relativedelta(months=1)
    return [m.strftime('%B %Y') for m in months]

def get_month_range(sel):
    start = datetime.strptime(sel, '%B %Y').date().replace(day=1)
    end = start + relativedelta(months=1) - timedelta(days=1)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end.replace(day=1)
    return start, end, prev_start, prev_end

def format_month_year(d):
    return d.strftime('%B %Y')

@st.cache_resource
def get_credentials():
    sa = st.secrets['gcp']['service_account']
    info = json.loads(sa)
    pk = info.get('private_key', '').replace('\\n', '\n')
    if not pk.endswith('\n'):
        pk += '\n'
    info['private_key'] = pk
    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    creds.refresh(GAuthRequest())
    return creds

@st.cache_data(ttl=3600)
def get_total_users(pid, sd, ed):
    try:
        req = {
            'property': f'properties/{pid}',
            'date_ranges': [{'start_date': sd.strftime('%Y-%m-%d'), 'end_date': ed.strftime('%Y-%m-%d')}],
            'metrics': [{'name': 'totalUsers'}]
        }
        resp = ga4.run_report(request=req)
        return int(resp.rows[0].metric_values[0].value)
    except Exception as e:
        st.error(f"Error fetching total users: {e}")
        return 0

@st.cache_data(ttl=3600)
def get_traffic(pid, sd, ed):
    try:
        req = {
            'property': f'properties/{pid}',
            'date_ranges': [{'start_date': sd.strftime('%Y-%m-%d'), 'end_date': ed.strftime('%Y-%m-%d')}],
            'dimensions': [{'name': 'sessionDefaultChannelGroup'}],
            'metrics': [{'name': 'sessions'}]
        }
        resp = ga4.run_report(request=req)
        return [{'channel': r.dimension_values[0].value, 'sessions': int(r.metric_values[0].value)} for r in resp.rows]
    except Exception as e:
        st.error(f"Error fetching traffic data: {e}")
        return []

@st.cache_data(ttl=3600)
def get_search_console(site, sd, ed):
    try:
        body = {
            'startDate': sd.strftime('%Y-%m-%d'),
            'endDate': ed.strftime('%Y-%m-%d'),
            'dimensions': ['page','query'],
            'rowLimit': 500
        }
        resp = sc.searchanalytics().query(siteUrl=site, body=body).execute()
        return resp.get('rows', [])
    except Exception as e:
        st.error(f"Error fetching Search Console data: {e}")
        return []

@st.cache_data(ttl=3600)
def get_active_users_by_country(pid, sd, ed, top_n=5):
    try:
        req = {
            'property': f'properties/{pid}',
            'date_ranges': [{'start_date': sd.strftime('%Y-%m-%d'), 'end_date': ed.strftime('%Y-%m-%d')}],
            'dimensions': [{'name': 'country'}],
            'metrics': [{'name': 'activeUsers'}],
            'order_bys': [{'metric': {'metric_name': 'activeUsers'}, 'desc': True}],
            'limit': top_n
        }
        resp = ga4.run_report(request=req)
        return [{'country': r.dimension_values[0].value, 'activeUsers': int(r.metric_values[0].value)} for r in resp.rows]
    except Exception as e:
        st.error(f"Error fetching country data: {e}")
        return []

@st.cache_data(ttl=3600)
def get_gsc_site_stats(site, sd, ed):
    try:
        body = {
            'startDate': sd.strftime('%Y-%m-%d'),
            'endDate': ed.strftime('%Y-%m-%d'),
            'rowLimit': 1
        }
        resp = sc.searchanalytics().query(siteUrl=site, body=body).execute()
        if not resp.get('rows'):
            return 0, 0, 0.0
        row = resp['rows'][0]
        return row.get('clicks', 0), row.get('impressions', 0), row.get('ctr', 0.0)
    except Exception as e:
        st.error(f"Error fetching GSC site stats: {e}")
        return 0, 0, 0.0

@st.cache_data(ttl=3600)
def get_new_returning_users(pid, sd, ed):
    try:
        req = {
            'property': f'properties/{pid}',
            'date_ranges': [{'start_date': sd.strftime('%Y-%m-%d'), 'end_date': ed.strftime('%Y-%m-%d')}],
            'metrics': [{'name': 'totalUsers'}, {'name': 'newUsers'}]
        }
        resp = ga4.run_report(request=req)
        total_users = int(resp.rows[0].metric_values[0].value)
        new_users = int(resp.rows[0].metric_values[1].value)
        returning_users = total_users - new_users
        return total_users, new_users, returning_users
    except Exception as e:
        st.error(f"Error fetching new/returning users: {e}")
        return 0, 0, 0

def render_table(df):
    if df.empty:
        st.warning("No data available for this period.")
    else:
        html = df.to_html(index=False, classes='styled-table')
        st.markdown(html, unsafe_allow_html=True)

def country_name_to_code(name):
    try:
        country = pycountry.countries.lookup(name)
        return country.alpha_2.lower()
    except LookupError:
        for country in pycountry.countries:
            if name.lower() in country.name.lower():
                return country.alpha_2.lower()
        return None

# =========================
# AUTHENTICATION & CONFIG
# =========================
PROPERTY_ID = '356205245'
SC_SITE_URL = 'https://www.salasarservices.com/'
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly'
]

creds = get_credentials()
ga4 = BetaAnalyticsDataClient(credentials=creds)
sc = build('searchconsole', 'v1', credentials=creds)

# =========================
# SIDEBAR & FILTERS
# =========================
with st.sidebar:
    st.image("https://www.salasarservices.com/assets/Frontend/images/logo-black.png", width=170)
    st.title('Report Filters')
    month_options = get_month_options()
    if "selected_month" not in st.session_state:
        st.session_state["selected_month"] = month_options[-1]
    sel = st.selectbox('Select report month:', month_options, index=month_options.index(st.session_state["selected_month"]))
    if sel != st.session_state["selected_month"]:
        st.session_state["selected_month"] = sel
    sd, ed, psd, ped = get_month_range(st.session_state["selected_month"])
    st.markdown(
        f"""
        <div style="border-left: 4px solid #459fda; background: #f0f7fa; padding: 1em 1.2em; margin-bottom: 1em; border-radius: 6px;">
            <span style="font-size: 1.1em; color: #2d448d;">
            <b>Current period:</b> {format_month_year(sd)}<br>
            <b>Previous period:</b> {format_month_year(psd)}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("Refresh Data (Clear Cache)"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.session_state["selected_month"] = month_options[-1]
        st.session_state["refresh"] = True

    pdf_report_btn = st.button("Download PDF Report")

if st.session_state.get("refresh", False):
    st.session_state["refresh"] = False
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# =========================
# DATA COLLECTION FOR PDF
# =========================
gsc_clicks, gsc_impressions, gsc_ctr = get_gsc_site_stats(SC_SITE_URL, sd, ed)
gsc_clicks_prev, gsc_impressions_prev, gsc_ctr_prev = get_gsc_site_stats(SC_SITE_URL, psd, ped)
gsc_clicks_delta = pct_change(gsc_clicks, gsc_clicks_prev)
gsc_impr_delta = pct_change(gsc_impressions, gsc_impressions_prev)
gsc_ctr_delta = pct_change(gsc_ctr, gsc_ctr_prev)

perf_circles = [
    {
        "title": "Total Website Clicks",
        "value": gsc_clicks,
        "delta": gsc_clicks_delta,
        "color": "#e67e22",
    },
    {
        "title": "Total Impressions",
        "value": gsc_impressions,
        "delta": gsc_impr_delta,
        "color": "#3498db",
    },
    {
        "title": "Average CTR",
        "value": gsc_ctr * 100,
        "delta": gsc_ctr_delta,
        "color": "#16a085",
    }
]

def get_gsc_pages_clicks(site, sd, ed, limit=5):
    try:
        body = {
            "startDate": sd.strftime('%Y-%m-%d'),
            "endDate": ed.strftime('%Y-%m-%d'),
            "dimensions": ["page"],
            "rowLimit": limit
        }
        resp = sc.searchanalytics().query(siteUrl=site, body=body).execute()
        rows = resp.get("rows", [])
        return [{"page": r["keys"][0], "clicks": r.get("clicks", 0)} for r in rows]
    except Exception as e:
        st.error(f"Error fetching top content from Search Console: {e}")
        return []

top_pages_now = get_gsc_pages_clicks(SC_SITE_URL, sd, ed, limit=5)
top_pages_prev = get_gsc_pages_clicks(SC_SITE_URL, psd, ped, limit=20)
prev_clicks_dict = {p["page"]: p["clicks"] for p in top_pages_prev}
top_content_data = []
for entry in top_pages_now:
    page = entry["page"]
    clicks = entry["clicks"]
    prev_clicks = prev_clicks_dict.get(page, 0)
    diff_pct = 0 if prev_clicks == 0 else ((clicks - prev_clicks) / prev_clicks * 100)
    top_content_data.append({
        "Page": page,
        "Clicks": clicks,
        "Change (%)": f"{diff_pct:+.2f}"
    })

cur = get_total_users(PROPERTY_ID, sd, ed)
prev = get_total_users(PROPERTY_ID, psd, ped)
delta = pct_change(cur, prev)
traf = get_traffic(PROPERTY_ID, sd, ed)
total = sum(item['sessions'] for item in traf)
prev_total = sum(item['sessions'] for item in get_traffic(PROPERTY_ID, psd, ped))
delta2 = pct_change(total, prev_total)
sc_data = get_search_console(SC_SITE_URL, sd, ed)
clicks = sum(r.get('clicks',0) for r in sc_data)
prev_clicks = sum(r.get('clicks',0) for r in get_search_console(SC_SITE_URL, psd, ped))
delta3 = pct_change(clicks, prev_clicks)
country_data = get_active_users_by_country(PROPERTY_ID, sd, ed)
traf_df = pd.DataFrame(traf).head(5)
sc_df = pd.DataFrame([{'page': r['keys'][0], 'query': r['keys'][1], 'clicks': r.get('clicks', 0)} for r in sc_data]).head(10)

# NEW: New vs Returning Users (data collection)
total_users, new_users, returning_users = get_new_returning_users(PROPERTY_ID, sd, ed)
total_users_prev, new_users_prev, returning_users_prev = get_new_returning_users(PROPERTY_ID, psd, ped)
delta_new = pct_change(new_users, new_users_prev)
delta_returning = pct_change(returning_users, returning_users_prev)

returning_new_users_circles = [
    {
        "title": "New Users",
        "value": new_users,
        "delta": delta_new,
        "color": "#e67e22",
    },
    {
        "title": "Returning Users",
        "value": returning_users,
        "delta": delta_returning,
        "color": "#3498db",
    }
]
returning_new_tooltips = [
    "Number of users who visited your website for the first time during the period.",
    "Number of users who returned to your website (not their first visit) during the period.",
]

# =========================
# PDF GENERATION LOGIC (unchanged)
# =========================
def generate_pdf_report():
    ... # (Unchanged PDF code)

if pdf_report_btn:
    pdf_bytes = generate_pdf_report()
    st.sidebar.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"Salasar-Services-Report-{date.today()}.pdf",
        mime="application/pdf"
    )

# =========================
# WEBSITE PERFORMANCE SECTION
# =========================
... # (Unchanged Website Performance section)

# =========================
# SOCIAL MEDIA ANALYTICS REPORTING DASHBOARD STARTS
# =========================

# =========================
# FACEBOOK ANALYTICS (WITH SELECT MONTH FILTER)
# =========================

PAGE_ID = st.secrets["facebook"]["page_id"]
ACCESS_TOKEN = st.secrets["facebook"]["access_token"]

def get_fb_prev_month(year, month):
    if month == 1:
        return year - 1, 12
    else:
        return year, month - 1

def get_fb_month_range(year, month):
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end

def get_insight(metric, since, until):
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
        return 0
    except Exception:
        return 0

def get_posts(since, until):
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
    except Exception:
        return []
    return posts

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

# === FACEBOOK MONTH FILTER (uses the same month selected in sidebar) ===
fb_month_str = st.session_state["selected_month"]
fb_start, fb_end, fb_prev_start, fb_prev_end = get_month_range(fb_month_str)
fb_cur_year, fb_cur_month = fb_start.year, fb_start.month
fb_prev_year, fb_prev_month = fb_prev_start.year, fb_prev_start.month

fb_cur_start, fb_cur_end = get_fb_month_range(fb_cur_year, fb_cur_month)
fb_prev_start_, fb_prev_end_ = get_fb_month_range(fb_prev_year, fb_prev_month)
fb_cur_since, fb_cur_until = fb_cur_start.isoformat(), fb_cur_end.isoformat()
fb_prev_since, fb_prev_until = fb_prev_start_.isoformat(), fb_prev_end_.isoformat()

cur_views = get_insight("page_views_total", fb_cur_since, fb_cur_until)
prev_views = get_insight("page_views_total", fb_prev_since, fb_prev_until)
views_percent = safe_percent(prev_views, cur_views)
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

fb_circles = [
    {
        "title": "Page Views",
        "value": cur_views,
        "delta": views_percent,
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
    "The total number of times your Facebook page was viewed during the selected period.",
    "The total number of likes your Facebook page has received during the selected period.",
    "The number of followers of your Facebook page during the selected period.",
    "Total posts published on your Facebook page this month."
]

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
                    <span class="fb-delta-note">(From Previous Month)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

if all(x["value"] == 0 for x in fb_circles):
    st.warning("No data detected for any metric. If your Facebook page is new, or if your API token is missing permissions, you may see zeros. Double-check your Facebook access token, permissions, and that your page has analytics data.")

# --- POSTS TABLE WITH FILTERED MONTH, NEW COLUMNS ---
def get_post_likes(post_id, access_token):
    url = f"https://graph.facebook.com/v19.0/{post_id}?fields=likes.summary(true)&access_token={access_token}"
    try:
        resp = requests.get(url).json()
        return resp.get('likes', {}).get('summary', {}).get('total_count', 0)
    except Exception:
        return 0

month_title = fb_cur_start.strftime('%B %Y')
st.markdown(f"<h3 style='color:#2d448d;'>Number of Post in {month_title}</h3>", unsafe_allow_html=True)

if fb_circles[3]['value'] > 0:
    post_table = []
    for idx, post in enumerate(cur_posts_list, 1):
        post_id = post["id"]
        # Get first 50 chars of message in bold
        message = post.get("message", "")
        title_text = (message[:50] + "...") if len(message) > 50 else message
        title_html = f"<b>{title_text}</b>"
        # Format date like "2 Aug 2025"
        created_time = datetime.strptime(
            post["created_time"].replace("+0000", ""), "%Y-%m-%dT%H:%M:%S"
        ).strftime("%-d %b %Y")
        # Get post likes
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
# END OF DASHBOARD
