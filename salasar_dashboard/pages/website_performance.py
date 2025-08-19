# WEBSITE PERFORMANCE SECTION FOR DASHBOARD
# -----------------------------------------
# This file renders the Website Performance, Top Content, Website Analytics,
# New vs Returning Users, and summary tables for the Salasar Dashboard.
# It uses modern UI, animation, and tooltip conventions per finalized design brief.

import streamlit as st
import pandas as pd
import time
from salasar_dashboard.utils.formatters import country_name_to_code

# =========================
# WEBSITE PERFORMANCE SECTION
# =========================

# Section header styled as per dashboard guidelines
st.markdown('<div class="section-header">Website Performance</div>', unsafe_allow_html=True)

# Animated metric circles for Website Performance (Clicks, Impressions, CTR)
cols_perf = st.columns(3)
animation_duration = 0.5
perf_tooltips = [
    "The total number of times users clicked your website's listing in Google Search results during the selected period.",
    "The total number of times your website appeared in Google Search results (regardless of clicks) for any query.",
    "The percentage of impressions that resulted in a click (Click-Through Rate) for your website in Google Search results during the selected period."
]
for i, col in enumerate(cols_perf):
    entry = perf_circles[i]
    with col:
        # Metric title with tooltip
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
        # Counter animation for metric value
        placeholder = st.empty()
        steps = 45  # number of animation frames
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
        # Delta (change) with arrow and color
        pct_color = "#2ecc40" if entry["delta"] >= 0 else "#ff4136"
        pct_icon = "↑" if entry["delta"] >= 0 else "↓"
        pct_icon_colored = (
            f"<span style='color:{pct_color}; font-size:1.05em; vertical-align:middle;'>{pct_icon}</span>"
        )
        pct_delta_text = (
            f"{pct_icon_colored} <span class='animated-circle-value' style='color:{pct_color}; font-size:1.1em;'>{abs(entry['delta']):.2f}%</span> <span class='animated-circle-delta-note'>(vs. Previous Month)</span>"
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
    """
    Renders a table of top content pages with animated values and colored delta arrows.
    """
    df = pd.DataFrame(data)
    if not df.empty:
        # Animate Clicks with bold font, and delta with arrows
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
# WEBSITE ANALYTICS SECTION
# =========================

st.markdown('<div class="section-header">Website Analytics</div>', unsafe_allow_html=True)

# Animated metric circles for Website Analytics (Users, Sessions, Clicks)
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
        # Metric title with tooltip
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
        # Animated counter for metric value
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
        # Delta (change) with arrow and color
        pct_color = "#2ecc40" if deltas[i] >= 0 else "#ff4136"
        pct_icon = "↑" if deltas[i] >= 0 else "↓"
        pct_icon_colored = (
            f"<span style='color:{pct_color}; font-size:1.05em; vertical-align:middle;'>{pct_icon}</span>"
        )
        st.markdown(
            f"<div style='text-align:center; font-size:18px; margin-top:0.2em; color:{pct_color}; font-weight:500'>{pct_icon_colored} <span class='animated-circle-value' style='color:{pct_color}; font-size:1.1em;'>{abs(deltas[i]):.2f}%</span> <span class='animated-circle-delta-note'>(vs. Previous Month)</span></div>",
            unsafe_allow_html=True
        )

# =========================
# NEW VS RETURNING USERS SECTION
# =========================

st.markdown('<div class="section-header">New vs Returning Users</div>', unsafe_allow_html=True)
cols_ret = st.columns(2)
animation_duration = 0.5
for i, col in enumerate(cols_ret):
    entry = returning_new_users_circles[i]
    with col:
        # Metric title with tooltip
        st.markdown(
            f"""<div style='text-align:center; font-weight:500; font-size:22px; margin-bottom:0.2em'>
                {entry["title"]}
                <span class='tooltip'>
                  <span class='questionmark'>?</span>
                  <span class='tooltiptext'>{returning_new_tooltips[i]}</span>
                </span>
            </div>""",
            unsafe_allow_html=True
        )
        # Animated counter for metric value
        placeholder = st.empty()
        steps = 45
        for n in range(steps + 1):
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
        # Delta (change) with arrow and color
        pct_color = "#2ecc40" if entry["delta"] >= 0 else "#ff4136"
        pct_icon = "↑" if entry["delta"] >= 0 else "↓"
        pct_icon_colored = (
            f"<span style='color:{pct_color}; font-size:1.05em; vertical-align:middle;'>{pct_icon}</span>"
        )
        st.markdown(
            f"<div style='text-align:center; font-size:18px; margin-top:0.2em; color:{pct_color}; font-weight:500'>{pct_icon_colored} <span class='animated-circle-value' style='color:{pct_color}; font-size:1.1em;'>{abs(entry['delta']):.2f}%</span> <span class='animated-circle-delta-note'>(vs. Previous Month)</span></div>",
            unsafe_allow_html=True
        )

# =========================
# ACTIVE USERS BY COUNTRY & TRAFFIC ACQUISITION (SIDE-BY-SIDE TABLES)
# =========================

col1, col2 = st.columns(2)

# --- Left: Active Users by Country (Top 5) ---
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

# --- Right: Traffic Acquisition by Channel ---
with col2:
    st.subheader('Traffic Acquisition by Channel')
    # Uses a custom render_table function to apply dashboard styles
    render_table(traf_df)
