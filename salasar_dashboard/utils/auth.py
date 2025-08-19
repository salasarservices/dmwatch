import streamlit as st
from google.oauth2 import service_account
from google.auth.transport.requests import Request as GAuthRequest
import json
from pymongo import MongoClient

def get_credentials(scopes):
    sa = st.secrets['gcp']['service_account']
    info = json.loads(sa)
    pk = info.get('private_key', '').replace('\\n', '\n')
    if not pk.endswith('\n'):
        pk += '\n'
    info['private_key'] = pk
    creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    creds.refresh(GAuthRequest())
    return creds

def flush_mongo_database():
    try:
        mongo_uri = st.secrets["mongo_uri"]
        db_name = "sal-leads"
        client = MongoClient(mongo_uri)
        db = client[db_name]
        for collection_name in db.list_collection_names():
            db[collection_name].delete_many({})
        client.close()
        return True
    except Exception as e:
        st.error(f"Could not flush database: {e}")
        return False
