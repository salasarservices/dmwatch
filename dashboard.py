import streamlit as st
from google.oauth2 import service_account
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700&family=Fira+Code:wght@400;500;700&display=swap');
body,.styled-table td,.styled-table th,.section-header,.tooltip .tooltiptext,
.styled-table,.styled-table thead tr,.tooltip .questionmark,.styled-table tbody tr,
.styled-table tbody tr:hover,.styled-table tbody tr:nth-of-type(even),
.styled-table tbody tr:nth-of-type(odd),.styled-table th,.styled-table td,
.styled-table thead tr { font-family: 'Lato', Arial, sans-serif !important; font-weight: 400; }
.section-header { font-weight: 700 !important; font-size: 1.7em !important; margin-top: 0.4em; margin-bottom: 0.4em; color: #2d448d; }
.styled-table th { font-weight: 500 !important; }
.styled-table td { font-weight: 400 !important; }
.tooltip .tooltiptext { font-size: 0.80em; font-weight: 300 !important; line-height: 1.4; }
.tooltip .questionmark { font-weight: 500 !important; font-size: 0.72em; background: #e3e8f0; color: #2d448d; border-radius: 50%; padding: 0 3px; margin-left: 4px; border: 1px solid #d1d5db; box-shadow: 0 1.5px 3px rgba(44,44,44,0.08); display: inline-block; vertical-align: super; line-height: 1em; }
.animated-circle-value { font-family: 'Fira Code', monospace !important; font-size: 2.1em; font-weight: 500; padding: 0.5em 0.6em; background: transparent; border-radius: 0.7em; width: auto; display: inline-block; letter-spacing: 0.02em; }
.animated-circle { width: 110px; height: 110px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Lato', Arial, sans-serif !important; font-weight: 500 !important; color: white; background: #2d448d; box-shadow: 0 4px 12px rgba(0,0,0,0.10); transition: transform 0.2s cubic-bezier(.4,2,.3,1); margin: 0 auto; padding: 1em; }
.animated-circle-delta-note { font-size: 14px; color: #666; font-family: Lato, sans-serif; letter-spacing: 0.01em; }
.stProgress { margin: 0 !important; padding: 0 !important; }
table.styled-table { border-collapse: collapse; width: 100%; border-radius: 5px 5px 0 0; overflow: hidden; }
table.styled-table thead tr { background-color: #2d448d; color: #ffffff; text-transform: uppercase; border-bottom: 4px solid #459fda; }
table.styled-table th { color: #ffffff; text-transform: uppercase; text-align: center; }
table.styled-table td { padding: 12px 15px; color: #2d448d !important; }
table.styled-table tbody tr:nth-of-type(even) { background-color: #f3f3f3; }
table.styled-table tbody tr:nth-of-type(odd) { background-color: #ffffff; }
table.styled-table tbody tr:hover { background-color: #a6ce39 !important; }
.tooltip { display: inline-block; position: relative; cursor: pointer; vertical-align: super; }
.tooltip .tooltiptext { visibility: hidden; width: 240px; background-color: #222; color: #fff; text-align: left; border-radius: 6px; padding: 8px 10px; position: absolute; z-index: 10; bottom: 120%; left: 50%; margin-left: -120px; opacity: 0; transition: opacity 0.2s; }
.tooltip:hover .tooltiptext { visibility: visible; opacity: 1; }
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
    # st.write("Raw service_account from TOML (repr):", repr(sa))  # <-- Removed
    try:
        info = json.loads(sa)
        # st.write("Parsed JSON keys:", list(info.keys()))          # <-- Removed
    except Exception as e:
        st.error(f"JSON decode error: {e}")
        st.stop()
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
    # Default to current month on first load or refresh
    if "selected_month" not in st.session_state:
        st.session_state["selected_month"] = month_options[-1]
    # Selectbox for month selection
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
        # After refresh, always select current month
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

# =========================
# PDF GENERATION LOGIC (CORRECTED)
# =========================
def generate_pdf_report():
    pdf = FPDF()
    pdf.add_page()
    # --- Logo at top ---
    logo_url = "https://www.salasarservices.com/assets/Frontend/images/logo-black.png"
    try:
        logo_bytes = requests.get(logo_url, timeout=5).content
        logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
        logo_path = "logo_temp.png"
        logo_img.save(logo_path)
        pdf.image(logo_path, x=10, y=8, w=50)
    except Exception:
        pass  # fallback: no logo

    # --- Title ---
    pdf.set_xy(65, 15)
    pdf.set_font("Arial", 'B', 17)
    pdf.set_text_color(45, 68, 141)
    pdf.cell(0, 12, "Salasar Services Digital Marketing Reporting Dashboard", ln=1)

    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0,0,0)
    pdf.ln(8)
    pdf.cell(0, 10, f"Reporting Period: {format_month_year(sd)} | Previous: {format_month_year(psd)}", ln=1)

    # --- Website Performance ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(45, 68, 141)
    pdf.cell(0, 12, "Website Performance", ln=1)
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0,0,0)
    for metric in perf_circles:
        val = f"{metric['value']:.2f}" if metric["title"]=="Average CTR" else str(metric['value'])
        pdf.cell(0, 10, f"{metric['title']}: {val} ({metric['delta']:+.2f} % from previous month)", ln=1)
    pdf.ln(2)

    # --- Top Content ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(45, 68, 141)
    pdf.cell(0, 10, "Top Content", ln=1)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(110, 8, "Page", border=1)
    pdf.cell(30, 8, "Clicks", border=1)
    pdf.cell(35, 8, "Change (%)", border=1, ln=1)
    pdf.set_font("Arial", '', 12)
    for row in top_content_data:
        pdf.cell(110, 8, row['Page'][:65], border=1)
        pdf.cell(30, 8, str(row['Clicks']), border=1)
        pdf.cell(35, 8, row['Change (%)'], border=1, ln=1)
    pdf.ln(4)

    # --- Website Analytics ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(45, 68, 141)
    pdf.cell(0, 10, "Website Analytics", ln=1)

    pdf.set_font("Arial", '', 12)
    pdf.cell(60, 8, f"Total Users: {cur} ({delta:+.2f}%)", ln=1)
    pdf.cell(60, 8, f"Sessions: {total} ({delta2:+.2f}%)", ln=1)
    pdf.cell(60, 8, f"Organic Clicks: {clicks} ({delta3:+.2f}%)", ln=1)
    pdf.ln(1)

    # --- Active Users by Country ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 9, "Active Users by Country (Top 5)", ln=1)
    pdf.set_font("Arial", '', 12)
    for c in country_data:
        pdf.cell(0, 7, f"{c['country']}: {c['activeUsers']}", ln=1)
    pdf.ln(1)

    # --- Traffic Acquisition by Channel ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 9, "Traffic Acquisition by Channel", ln=1)
    pdf.set_font("Arial", '', 12)
    for idx,row in traf_df.iterrows():
        pdf.cell(0, 7, f"{row['channel']}: {row['sessions']}", ln=1)
    pdf.ln(1)

    # --- Top 10 Organic Queries ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 9, "Top 10 Organic Queries", ln=1)
    pdf.set_font("Arial", '', 12)
    for idx,row in sc_df.iterrows():
        pdf.cell(0, 7, f"{row['query']} ({row['clicks']} clicks)", ln=1)
    pdf.ln(2)

    # --- Footer ---
    pdf.set_y(-25)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150,150,150)
    pdf.cell(0, 10, "Generated by Salasar Services Digital Marketing Reporting Dashboard", 0, 0, 'C')

    # Corrected PDF export for Streamlit
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return io.BytesIO(pdf_bytes)

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
st.markdown('<div class="section-header">Website Performance</div>', unsafe_allow_html=True)
cols_perf = st.columns(3)
animation_duration = 0.5  # Fast animation
perf_tooltips = [
    "The total number of times users clicked your website's listing in Google Search results during the selected period.",
    "The total number of times your website appeared in Google Search results (regardless of clicks) for any query.",
    "The percentage of impressions that resulted in a click (Click-Through Rate) for your website in Google Search results during the selected period."
]
for i, col in enumerate(cols_perf):
    entry = perf_circles[i]
    with col:
        st.markdown(
            f"""<div style='text-align:center; font-weight:500; font-size:22px; margin-bottom:0.2em'>
                {entry["title"]}
                <span class='tooltip'>
                  <span class='questionmark'>?</span>
                  <span class='tooltiptext'>{perf_tooltips[i]}</span>
                </span>
            </div>""",
            unsafe_allow_html=True
        )
        placeholder = st.empty()
        steps = 45
        for n in range(steps + 1):
            if entry["title"] == "Average CTR":
                display_val = f"{entry['value'] * n / steps:.2f}%"
            else:
                display_val = int(entry["value"] * n / steps)
            placeholder.markdown(
                f"""
                <div style='margin:0 auto; display:flex; align-items:center; justify-content:center; height:110px;'>
                  <div class='animated-circle' style='background:{entry["color"]};'>
                    <span class='animated-circle-value'>{display_val}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            time.sleep(animation_duration / steps)
        pct_color = "#2ecc40" if entry["delta"] >= 0 else "#ff4136"
        pct_icon = (
            "↑" if entry["delta"] >= 0 else "↓"
        )
        pct_icon_colored = (
            f"<span style='color:{pct_color}; font-size:1.05em; vertical-align:middle;'>{pct_icon}</span>"
        )
        pct_delta_text = (
            f"{pct_icon_colored} <span class='animated-circle-value' style='color:{pct_color}; font-size:1.1em;'>{abs(entry['delta']):.2f}%</span> <span class='animated-circle-delta-note'>(From Previous Month)</span>"
        )
        st.markdown(
            f"<div style='text-align:center; font-size:18px; margin-top:0.2em; color:{pct_color}; font-weight:500'>{pct_delta_text}</div>",
            unsafe_allow_html=True
        )

# =========================
# TOP CONTENT SECTION
# =========================
st.markdown('<div class="section-header">Top Content</div>', unsafe_allow_html=True)
def render_top_content_table(data):
    df = pd.DataFrame(data)
    if not df.empty:
        df["Clicks"] = df["Clicks"].apply(lambda x: f"<span class='animated-circle-value' style='font-size:1.2em'>{x}</span>")
        def fmt_change(val):
            pct = float(val)
            color = "#2ecc40" if pct >= 0 else "#ff4136"
            arrow = "↑" if pct >= 0 else "↓"
            return f"<span class='animated-circle-value' style='color:{color};font-size:1.15em'>{arrow} {pct:+.2f}%</span>"
        df["Change (%)"] = df["Change (%)"].apply(fmt_change)
        st.markdown(df.to_html(escape=False, index=False, classes="styled-table"), unsafe_allow_html=True)
    else:
        st.warning("No top content data available for this period.")
render_top_content_table(top_content_data)

# =========================
# WEBSITE ANALYTICS SECTION (with 3 animated circles AND 2 side-by-side tables)
# =========================
st.markdown('<div class="section-header">Website Analytics</div>', unsafe_allow_html=True)

# --- Three animated circles ---
circle_colors = ["#2d448d", "#a6ce39", "#459fda"]
titles = [
    "Total Users",
    "Sessions",
    "Organic Clicks"
]
tooltips = [
    "Number of people who visited your website.",
    "Total number of visits to your website.",
    "Times people clicked on your website in Google search."
]
values = [cur, total, clicks]
deltas = [delta, delta2, delta3]
cols = st.columns(3)
animation_duration = 0.5
for i, col in enumerate(cols):
    with col:
        st.markdown(
            f"""<div style='text-align:center; font-weight:500; font-size:22px; margin-bottom:0.2em'>
                {titles[i]}
                <span class='tooltip'>
                  <span class='questionmark'>?</span>
                  <span class='tooltiptext'>{tooltips[i]}</span>
                </span>
            </div>""",
            unsafe_allow_html=True
        )
        placeholder = st.empty()
        steps = 45
        for n in range(steps + 1):
            display_val = int(values[i] * n / steps)
            placeholder.markdown(
                f"""
                <div style='margin:0 auto; display:flex; align-items:center; justify-content:center; height:110px;'>
                  <div class='animated-circle' style='background:{circle_colors[i]};'>
                    <span class='animated-circle-value'>{display_val}</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            time.sleep(animation_duration / steps)
        pct_color = "#2ecc40" if deltas[i] >= 0 else "#ff4136"
        pct_icon = (
            "↑" if deltas[i] >= 0 else "↓"
        )
        pct_icon_colored = (
            f"<span style='color:{pct_color}; font-size:1.05em; vertical-align:middle;'>{pct_icon}</span>"
        )
        st.markdown(
            f"<div style='text-align:center; font-size:18px; margin-top:0.2em; color:{pct_color}; font-weight:500'>{pct_icon_colored} <span class='animated-circle-value' style='color:{pct_color}; font-size:1.1em;'>{abs(deltas[i]):.2f}%</span> <span class='animated-circle-delta-note'>(From Previous Month)</span></div>",
            unsafe_allow_html=True
        )

# --- Two side-by-side tables ---
col1, col2 = st.columns(2)
with col1:
    st.subheader('Active Users by Country (Top 5)')
    country_df = pd.DataFrame(country_data)
    def flag_html(row):
        code = country_name_to_code(row['country'])
        flag_url = f"https://flagcdn.com/16x12/{code}.png" if code else ""
        flag_img = f'<img src="{flag_url}" style="height:12px;margin-right:7px;vertical-align:middle;">' if code else ""
        return f"{flag_img}{row['country']}"
    country_df['Country'] = country_df.apply(flag_html, axis=1)
    country_df = country_df[['Country', 'activeUsers']]
    country_df.rename(columns={'activeUsers': 'Active Users'}, inplace=True)
    st.markdown(country_df.to_html(escape=False, index=False, classes='styled-table'), unsafe_allow_html=True)

with col2:
    st.subheader('Traffic Acquisition by Channel')
    render_table(traf_df)

st.subheader('Top 10 Organic Queries')
render_table(sc_df)

# =========================
# SOCIAL MEDIA ANALYTICS REPORTING DASHBOARD STARTS
# =========================

# =========================
# FACEBOOK ANALYTICS
# =========================

# --- Secrets ---
PAGE_ID = st.secrets["facebook"]["page_id"]
ACCESS_TOKEN = st.secrets["facebook"]["access_token"]

# --- Helpers ---
def get_fb_prev_month(year, month):
    """Robust previous month calculation for Facebook metrics."""
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

# --- Data ---
today = date.today()
cy, cm = today.year, today.month
py, pm = get_fb_prev_month(cy, cm)

cur_start, cur_end = get_fb_month_range(cy, cm)
prev_start, prev_end = get_fb_month_range(py, pm)

cur_since, cur_until = cur_start.isoformat(), cur_end.isoformat()
prev_since, prev_until = prev_start.isoformat(), prev_end.isoformat()

cur_views = get_insight("page_views_total", cur_since, cur_until)
prev_views = get_insight("page_views_total", prev_since, prev_until)
views_percent = safe_percent(prev_views, cur_views)

cur_likes = get_insight("page_fans", cur_since, cur_until)
prev_likes = get_insight("page_fans", prev_since, prev_until)
likes_percent = safe_percent(prev_likes, cur_likes)

cur_followers = get_insight("page_follows", cur_since, cur_until)
prev_followers = get_insight("page_follows", prev_since, prev_until)
followers_percent = safe_percent(prev_followers, cur_followers)

cur_posts_list = get_posts(cur_since, cur_until)
prev_posts_list = get_posts(prev_since, prev_until)
cur_posts = len(cur_posts_list)
prev_posts = len(prev_posts_list)
posts_percent = safe_percent(prev_posts, cur_posts)

# --- Circle metrics config (colors match main dashboard, labels, values, deltas) ---
fb_circles = [
    {
        "title": "Page Views",
        "value": cur_views,
        "delta": views_percent,
        "color": "#2d448d",  # dark blue
    },
    {
        "title": "Page Likes",
        "value": cur_likes,
        "delta": likes_percent,
        "color": "#a6ce39",  # green
    },
    {
        "title": "Page Followers",
        "value": cur_followers,
        "delta": followers_percent,
        "color": "#459fda",  # light blue
    },
    {
        "title": "Posts (This Month)",
        "value": cur_posts,
        "delta": posts_percent,
        "color": "#d178a9",  # pink
    }
]

fb_tooltips = [
    "The total number of times your Facebook page was viewed during the selected period.",
    "The total number of likes your Facebook page has received during the selected period.",
    "The number of followers of your Facebook page during the selected period.",
    "Total posts published on your Facebook page this month."
]

# --- CSS for circles (reuse style for consistency) ---
st.markdown("""
<style>
.fb-section-header {
    font-weight: 700 !important;
    font-size: 1.7em !important;
    margin-top: 1.3em;
    margin-bottom: 0.8em;
    color: #2d448d;
    font-family: 'Lato', Arial, sans-serif !important;
}
.fb-metric-row {
    display: flex;
    flex-wrap: nowrap;
    justify-content: center;
    gap: 2.5rem;
    margin-bottom: 2.2rem;
    margin-top: 1.0rem;
}
.fb-metric-card {
    background: transparent;
    text-align: center;
    flex: 0 0 240px;
    max-width: 270px;
    min-width: 180px;
}
.fb-metric-label {
    font-size: 1.32rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
    margin-top: 0.2rem;
    color: #2d448d;
    letter-spacing: 0.09px;
    font-family: 'Lato', Arial, sans-serif;
}
.fb-animated-circle {
    margin: 0 auto;
    width: 110px;
    height: 110px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.1em;
    font-weight: 500;
    color: #fff;
    margin-bottom: 0.6rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.10);
    font-family: 'Fira Code', monospace !important;
    transition: box-shadow .2s;
}
.fb-delta-row {
    font-size: 1.1rem;
    font-weight: 500;
    min-height: 30px;
    display: flex;
    align-items: center;
    gap: 0.45rem;
    justify-content: center;
}
.fb-delta-up {
    color: #2ecc40;
    font-weight: 700;
    margin-right: 0.2rem;
    letter-spacing: 0.5px;
}
.fb-delta-down {
    color: #ff4136;
    font-weight: 700;
    margin-right: 0.2rem;
    letter-spacing: 0.5px;
}
.fb-delta-same {
    color: #aaa;
    font-weight: 500;
    margin-right: 0.2rem;
    letter-spacing: 0.5px;
}
.fb-delta-note {
    color: #666;
    font-size: 0.98rem;
    font-weight: 400;
    margin-left: 0.3rem;
    letter-spacing: 0.15px;
}
@media (max-width: 1200px) {
    .fb-metric-row { gap: 1.1rem; }
    .fb-metric-card { flex: 1 1 150px; max-width: 180px;}
    .fb-animated-circle { width:80px; height:80px; font-size:1.2em;}
    .fb-metric-label { font-size: 1rem;}
}
@media (max-width: 850px) {
    .fb-metric-row { flex-wrap: wrap; gap: 1.1rem;}
    .fb-metric-card { flex: 1 1 130px; max-width: 150px;}
    .fb-animated-circle { width:60px; height:60px; font-size:0.97em;}
    .fb-metric-label { font-size: 0.82rem;}
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="fb-section-header">Facebook Page Analytics</div>', unsafe_allow_html=True)

# --- Place circles SIDE BY SIDE using st.columns for robust Streamlit layout ---
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

# --- Posts Table ---
st.subheader(f"Posts Published in {cur_start.strftime('%B %Y')} ({fb_circles[3]['value']} posts)")
if fb_circles[3]['value'] > 0:
    post_table = [
        {
            "ID": post["id"],
            "Created Time": datetime.strptime(post["created_time"].replace("+0000", ""), "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d %H:%M"),
            "Message": post.get("message", "")[:100] + ("..." if len(post.get("message", "")) > 100 else "")
        }
        for post in cur_posts_list
    ]
    df = pd.DataFrame(post_table)
    st.dataframe(df, use_container_width=True)
else:
    st.info("No posts published this month.")

st.caption("All data is pulled live from Facebook Graph API. Tokens and IDs are loaded securely from Streamlit secrets.")
# END OF DASHBOARD
