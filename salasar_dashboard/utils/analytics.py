import streamlit as st

@st.cache_data(ttl=3600)
def get_total_users(ga4, pid, sd, ed):
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
def get_traffic(ga4, pid, sd, ed):
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
def get_search_console(sc, site, sd, ed):
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
def get_active_users_by_country(ga4, pid, sd, ed, top_n=5):
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
def get_new_returning_users(ga4, pid, sd, ed):
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
