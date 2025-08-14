import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

API_URL = "http://127.0.0.1:5000/events"
CSV_URL = "http://127.0.0.1:5000/events.csv"

st.set_page_config("LPR Events Dashboard", layout="wide")
st.title("License Plate Events Dashboard")

st.sidebar.header("Controls")
auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
refresh_interval = st.sidebar.slider("Refresh interval (sec)", 2, 30, 5)

@st.cache_data(ttl=2)
def fetch_events():
    try:
        resp = requests.get(API_URL, timeout=3)
        data = resp.json()
        df = pd.DataFrame(data)
        if not df.empty and 'created_at' in df.columns:
            df['created_at'] = pd.to_datetime(df['created_at'])
            df = df.sort_values("created_at", ascending=False)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def render_table(df):
    if df.empty:
        st.warning("No events found.")
    else:
        st.dataframe(df, use_container_width=True)

if auto_refresh:
    count = st_autorefresh(interval=refresh_interval * 1000, key="refresh")

df = fetch_events()
render_table(df)

# Download CSV
st.markdown("### Export Data")
st.download_button(
    label="Download CSV",
    data=requests.get(CSV_URL).content,
    file_name="lpr_events.csv",
    mime="text/csv"
)
