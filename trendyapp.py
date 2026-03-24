import streamlit as st
import requests
import pandas as pd
from pytrends.request import TrendReq
import json
from datetime import datetime

# Page config
st.set_page_config(page_title="Viral Clips Generator", layout="wide")

st.title("🎥 Viral Clips Generator")
st.subheader("Trending Topics → Video Clips → X Posts")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    pexels_api_key = st.text_input("Pexels API Key", type="password")
    grok_api_key = st.text_input("Grok API Key", type="password")
    x_credentials = st.checkbox("Add X/Twitter Credentials")

# Main content
col1, col2 = st.columns(2)

with col1:
    st.header("📊 Trending Topics")
    if st.button("🔥 Fetch Trending Topics"):
        try:
            pytrends = TrendReq(hl='en-US', tz=360)
            trending = pytrends.trending_searches(pn=0)
            st.dataframe(trending.head(10))
            st.success("✅ Trending topics loaded!")
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    st.header("🎬 Video Clips")
    selected_topic = st.text_input("Enter trending topic")
    
    if st.button("🔥 Generate & Post 1-Min Clip Now"):
        if not pexels_api_key:
            st.error("⚠️ Add Pexels API Key in settings")
        elif not selected_topic:
            st.error("⚠️ Enter a trending topic")
        else:
            st.info("🔄 Fetching video clips...")
            try:
                headers = {'Authorization': pexels_api_key}
                response = requests.get(
                    f'https://api.pexels.com/videos/search?query={selected_topic}&per_page=1',
                    headers=headers
                )
                data = response.json()
                
                if data['videos']:
                    video = data['videos'][0]
                    st.video(video['video_files'][0]['link'])
                    st.success("✅ Video clip fetched!")
                    st.write(f"**Source:** Pexels - {video['user']['name']}")
                else:
                    st.warning("No videos found for this topic")
            except Exception as e:
                st.error(f"Error: {e}")

# Footer
st.divider()
st.caption("Made with ❤️ for viral content creators")
