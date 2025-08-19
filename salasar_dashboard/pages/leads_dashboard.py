"""
Leads Dashboard Section
-----------------------
Displays leads statistics and a styled, responsive table for the Salasar Services Digital Marketing Reporting Dashboard.
Follows finalized design brief for UI, colors, fonts, and modularity.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# --- HELPER FUNCTIONS ---

def get_leads_from_mongodb():
    """Fetch all leads from the MongoDB collection."""
    try:
        mongo_uri = st.secrets["mongo_uri"]
        from pymongo import MongoClient
        client = MongoClient(mongo_uri)
        db = client["sal-leads"]
        leads_collection = db["leads"]
        leads = list(leads_collection.find({}, {"_id": 0}))
        client.close()
        return leads
    except Exception as e:
        st.error(f"Could not fetch leads: {e}")
        return []

def lead_status_colored(status):
    """Returns HTML colored label for lead status."""
    status_clean = str(status).strip()
    colors = {
        "Interested": "#FFD700",
        "Not Interested": "#FB4141",
        "Closed": "#B4E50D"
    }
    color = colors.get(status_clean, "#666")
    return f"<b style='color: {color};'>{status_clean}</b>"

def get_month_color(month_index):
    """Assigns a unique pastel color for each month."""
    palette = [
        "#f7f1d5", "#fbe4eb", "#d3fbe4", "#e4eaff", "#ffe4f1",
        "#e4fff6", "#f5e4ff", "#f1ffe4", "#ffe4e4", "#e4f1ff"
    ]
    return palette[month_index % len(palette)]

def yyyymmdd_to_month_year(yyyymmdd):
    """Converts integer date YYYYMMDD to 'Month YYYY'."""
    try:
        date_str = str(yyyymmdd)[:8]
        dt = datetime.strptime(date_str, "%Y%m%d")
        return dt.strftime("%B %Y")
    except Exception:
        return ""

def format_brokerage_circle_value(val):
    """Formats brokerage amount with Indian units (K/L/Cr)."""
    if val >= 10000000:
        return f"₹ {val/10000000:.1f}Cr"
    elif val >= 100000:
        return f"₹ {val/100000:.1f}L"
    elif val >= 10000:
        return f"₹ {val/1000:.0f}K"
    elif val >= 1000:
        return f"₹ {val/1000:.1f}K"
    else:
        return f"₹ {val:.2f}"

# --- SECTION HEADER ---
st.markdown('<div class="section-header">Leads Dashboard</div>', unsafe_allow_html=True)

# --- DATA PROCESSING ---
leads = get_leads_from_mongodb()
if leads:
    df = pd.DataFrame(leads)

    # Convert "Date" to "Month YYYY"
    if "Date" in df.columns:
        df["Date"] = df["Date"].apply(yyyymmdd_to_month_year)

    # Brokerage calculation
    if "Brokerage Received" in df.columns:
        df["Brokerage Received"] = pd.to_numeric(df["Brokerage Received"], errors="coerce")
        total_brokerage = df["Brokerage Received"].dropna().sum()
    else:
        df["Brokerage Received"] = np.nan
        total_brokerage = 0.0

    # Lead status tallies
    if "Lead Status" in df.columns:
        df["Lead Status Clean"] = df["Lead Status"].astype(str).str.strip()
        interested_count = (df["Lead Status Clean"] == "Interested").sum()
        not_interested_count = (df["Lead Status Clean"] == "Not Interested").sum()
        closed_count = (df["Lead Status Clean"] == "Closed").sum()
    else:
        interested_count = not_interested_count = closed_count = 0

    total_leads = len(df)
else:
    df = pd.DataFrame()
    total_leads = interested_count = not_interested_count = closed_count = 0
    total_brokerage = 0.0

display_brokerage = format_brokerage_circle_value(total_brokerage)

# --- SECTION CSS (BRANDING, CIRCLES, TABLES) ---
st.markdown("""
<style>
/* Leads Table Styles */
.leads-table-wrapper {
    margin: 0 auto 16px auto;
    width: 98vw;
    min-width: 360px;
    max-width: 1100px;
    overflow-x: auto;
    font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(44, 62, 80, 0.09);
    padding: 8px 0 18px 0;
}
.leads-table {
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    min-width: 360px;
    background: #fff;
    font-size: 0.90rem;
    border-radius: 12px;
    overflow: hidden;
}
.leads-table th {
    background: linear-gradient(90deg, #31406e 0%, #37509b 100%);
    color: #fff;
    font-weight: 600;
    padding: 9px 18px 8px 13px;
    border-bottom: 2.5px solid #e3e6eb;
    text-align: left;
    white-space: nowrap;
    font-size: 1.02rem;
    letter-spacing: 0.02em;
    position: sticky;
    top: 0;
    z-index: 2;
    box-shadow: 0 2px 6px rgba(44,62,80,0.04);
}
.leads-table td {
    padding: 7px 13px 6px 13px;
    border-bottom: 1px solid #f1f2f6;
    background: #fff;
    vertical-align: middle;
    white-space: nowrap;
    font-size: 0.93rem;
    color: #21272b;
    line-height: 1.35;
    letter-spacing: 0.01em;
    transition: background 0.17s;
}
.leads-table tr:hover td {
    background: #f5f7fa;
}
.leads-table tr:last-child td {
    border-bottom: none;
}
.leads-table th:first-child, .leads-table td:first-child {
    border-top-left-radius: 10px;
}
.leads-table th:last-child, .leads-table td:last-child {
    border-top-right-radius: 10px;
}
.leads-table-wrapper::-webkit-scrollbar {
    height: 8px;
    background: #e6eaf2;
    border-radius: 5px;
}
.leads-table-wrapper::-webkit-scrollbar-thumb {
    background: #b5b9c5;
    border-radius: 5px;
}
/* Circles Row */
.circles-row {
    display: flex;
    justify-content: center;
    gap: 42px;
    margin-bottom: 30px;
    flex-wrap: wrap;
}
.circle-animate {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.1rem;
    color: #fff;
    font-weight: bold;
    box-shadow: 0 4px 16px rgba(250, 190, 88, 0.3);
    animation: pop 1s ease;
    margin-bottom: 6px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    text-shadow: 0 1px 3px #2227;
    letter-spacing: 1px;
}
.circle-animate:hover {
    transform: scale(1.10);
    box-shadow: 0 8px 32px rgba(250, 190, 88, 0.4);
}
.circle-leads    { background: linear-gradient(135deg, #f6d365 0%, #fda085 100%);}
.circle-int      { background: linear-gradient(135deg, #FFD700 0%, #FFB200 100%);}
.circle-notint   { background: linear-gradient(135deg, #FB4141 0%, #C91F1F 100%);}
.circle-closed   { background: linear-gradient(135deg, #B4E50D 0%, #7BA304 100%);}
.circle-brokerage { background: linear-gradient(135deg, #0dbe62 0%, #1ff1a7 100%);}
.lead-label {
    text-align:center; 
    font-weight:600;
    font-size: 1.1rem;
    color: #888;
    letter-spacing: 1px;
    margin-bottom: 0.7rem;
}
@keyframes pop {
    0% { transform: scale(0.5);}
    80% { transform: scale(1.1);}
    100% { transform: scale(1);}
}
@media (max-width: 900px) {
    .leads-table th, .leads-table td {
        font-size: 0.87rem;
        padding: 6px 8px 5px 8px;
    }
    .leads-table-wrapper {
        max-width: 99vw;
        padding: 0 0 8px 0;
    }
}
</style>
""", unsafe_allow_html=True)

# --- DASHBOARD CIRCLES (ANIMATED) ---
st.markdown(f"""
<div class="circles-row">
    <div>
        <div class="circle-animate circle-leads">{total_leads}</div>
        <div class="lead-label">Total Leads</div>
    </div>
    <div>
        <div class="circle-animate circle-int">{interested_count}</div>
        <div class="lead-label">Interested</div>
    </div>
    <div>
        <div class="circle-animate circle-notint">{not_interested_count}</div>
        <div class="lead-label">Not Interested</div>
    </div>
    <div>
        <div class="circle-animate circle-closed">{closed_count}</div>
        <div class="lead-label">Closed</div>
    </div>
    <div>
        <div class="circle-animate circle-brokerage">{display_brokerage}</div>
        <div class="lead-label">Total Brokerage received</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- LEADS DATA TABLE ---
st.markdown("### Leads Data")

if not df.empty:
    # Assign unique color to each month
    if "Date" in df.columns:
        months = df["Date"].fillna("").astype(str).unique()
        months = [m for m in months if m.strip() != ""]
        months.sort()
        month_to_color = {m: get_month_color(i) for i, m in enumerate(months)}
    else:
        month_to_color = {}

    # Color Lead Status column with badges
    if "Lead Status" in df.columns:
        df["Lead Status"] = df["Lead Status"].astype(str).str.strip()
        df["Lead Status"] = df["Lead Status"].apply(lead_status_colored)
    if "Lead Status Clean" in df.columns:
        df = df.drop(columns=["Lead Status Clean"])

    # Drop phone number column if it exists
    if "Number" in df.columns:
        df = df.drop(columns=["Number"])

    # Format Brokerage column for display
    if "Brokerage Received" in df.columns:
        df["Brokerage Received"] = df["Brokerage Received"].apply(
            lambda x: f"₹ {x:.2f}" if pd.notnull(x) else ""
        )
        # Place just after Lead Status for readability
        lead_status_idx = df.columns.get_loc("Lead Status") if "Lead Status" in df.columns else -1
        if lead_status_idx != -1:
            cols = list(df.columns)
            cols.insert(lead_status_idx + 1, cols.pop(cols.index("Brokerage Received")))
            df = df[cols]

    def df_to_colored_html(df):
        """
        Returns HTML for the leads table using pastel backgrounds for months,
        status color badges, and brokerage formatting.
        """
        headers = df.columns.tolist()
        html = '<div class="leads-table-wrapper"><table class="leads-table">\n<thead><tr>'
        for h in headers:
            html += f'<th>{h}</th>'
        html += '</tr></thead>\n<tbody>'
        for idx, row in df.iterrows():
            html += '<tr>'
            for i, cell in enumerate(row):
                if headers[i] == "Date":
                    month = str(cell).strip()
                    bgcolor = f'background-color: {month_to_color.get(month, "#fff")}; font-weight: bold;'
                    html += f'<td style="{bgcolor}">{cell}</td>'
                else:
                    html += f'<td>{cell}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'
        return html

    st.write(
        df_to_colored_html(df),
        unsafe_allow_html=True,
    )
else:
    st.info("No leads data found in MongoDB.")
