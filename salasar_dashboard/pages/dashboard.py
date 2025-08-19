import streamlit as st
import pandas as pd
import time

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build

from components.loader import show_loader
from components.login import check_login
from components.sidebar import render_sidebar
from components.pdf_report import generate_pdf_report

from utils.auth import get_credentials
from utils.analytics import (
    get_total_users, get_traffic, get_search_console,
    get_active_users_by_country, get_new_returning_users
)
from utils.formatters import (
    pct_change, get_month_options, get_month_range, format_month_year
)

SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly'
]
PROPERTY_ID = '356205245'
SC_SITE_URL = 'https://www.salasarservices.com/'

# ---- LOGIN ----
check_login()

# ---- PAGE CONFIG ----
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

# ---- MONTH FILTER ----
month_options = get_month_options()
if "selected_month" not in st.session_state:
    st.session_state["selected_month"] = month_options[-1]
sel = st.session_state["selected_month"]
sd, ed, psd, ped = get_month_range(sel)
st.session_state["date_range"] = (sd, ed, psd, ped)

# ---- SIDEBAR ----
pdf_report_btn = render_sidebar(month_options, sel)

if st.session_state.get("refresh", False):
    st.session_state["refresh"] = False
    st.rerun()

# ---- AUTHENTICATION ----
credentials_placeholder = st.empty()
show_loader(credentials_placeholder, "Authenticating and initializing analytics APIs...")
creds = get_credentials(SCOPES)
ga4 = BetaAnalyticsDataClient(credentials=creds)
sc = build('searchconsole', 'v1', credentials=creds)
credentials_placeholder.empty()

# ---- DATA ----
metrics_placeholder = st.empty()
show_loader(metrics_placeholder, "Fetching dashboard data...")

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

cur = get_total_users(ga4, PROPERTY_ID, sd, ed)
prev = get_total_users(ga4, PROPERTY_ID, psd, ped)
delta = pct_change(cur, prev)
traf = get_traffic(ga4, PROPERTY_ID, sd, ed)
total = sum(item['sessions'] for item in traf)
prev_total = sum(item['sessions'] for item in get_traffic(ga4, PROPERTY_ID, psd, ped))
delta2 = pct_change(total, prev_total)
sc_data = get_search_console(sc, SC_SITE_URL, sd, ed)
clicks = sum(r.get('clicks',0) for r in sc_data)
prev_clicks = sum(r.get('clicks',0) for r in get_search_console(sc, SC_SITE_URL, psd, ped))
delta3 = pct_change(clicks, prev_clicks)
country_data = get_active_users_by_country(ga4, PROPERTY_ID, sd, ed)
traf_df = pd.DataFrame(traf).head(5)
sc_df = pd.DataFrame([{'page': r['keys'][0], 'query': r['keys'][1], 'clicks': r.get('clicks', 0)} for r in sc_data]).head(10)

# New vs Returning Users
total_users, new_users, returning_users = get_new_returning_users(ga4, PROPERTY_ID, sd, ed)
total_users_prev, new_users_prev, returning_users_prev = get_new_returning_users(ga4, PROPERTY_ID, psd, ped)
delta_new = pct_change(new_users, new_users_prev)
delta_returning = pct_change(returning_users, returning_users_prev)

metrics_placeholder.empty()

# ---- RENDER DASHBOARD (put your sections here) ----

st.header("Website Performance")
for metric in perf_circles:
    st.metric(label=metric["title"], value=metric["value"], delta=f"{metric['delta']:+.2f}%")

st.header("Top Content")
if top_content_data:
    st.dataframe(pd.DataFrame(top_content_data))
else:
    st.warning("No data available for this period.")

st.header("Website Analytics")
st.write(f"Total Users: {cur} ({delta:+.2f}%)")
st.write(f"Sessions: {total} ({delta2:+.2f}%)")
st.write(f"Organic Clicks: {clicks} ({delta3:+.2f}%)")

st.header("New vs Returning Users")
st.write(f"New Users: {new_users} ({delta_new:+.2f}%)")
st.write(f"Returning Users: {returning_users} ({delta_returning:+.2f}%)")

st.header("Active Users by Country (Top 5)")
st.write(country_data)

st.header("Traffic Acquisition by Channel")
st.dataframe(traf_df)

st.header("Top 10 Organic Queries")
st.dataframe(sc_df)

# ---- PDF GENERATION ----
if pdf_report_btn:
    pdf_bytes = generate_pdf_report(
        sd, psd, perf_circles, top_content_data, cur, delta, total, delta2,
        clicks, delta3, new_users, delta_new, returning_users, delta_returning,
        country_data, traf_df, sc_df, format_month_year
    )
    st.sidebar.download_button(
        label="Download PDF",
        data=pdf_bytes,
        file_name=f"Salasar-Services-Report-{st.session_state['selected_month']}.pdf",
        mime="application/pdf"
    )
