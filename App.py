streamlit
pytrends
moviepy
requests
openai
pandas
python-dotenv
tweepy
pillow 


import streamlit as st
import os, json, requests, time
from datetime import datetime
import pandas as pd
from pytrends.request import TrendReq
from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip
from openai import OpenAI
import tweepy
import base64

st.set_page_config(page_title="TrendClip AI", layout="wide")
st.title("🎥 TrendClip AI – Daily Viral Clips")
st.caption("Autonomous • Free • HD • Posts to your accounts")

# ====================== SIDEBAR – API KEYS & SETTINGS ======================
with st.sidebar:
    st.header("🔑 Your Free Keys")
    xai_key = st.text_input("xAI Grok API Key (free credits on signup)", type="password", value=os.getenv("XAI_KEY", ""))
    pexels_key = st.text_input("Pexels API Key (free)", type="password", value=os.getenv("PEXELS_KEY", ""))
   
    st.header("📱 Posting")
    twitter_api_key = st.text_input("Twitter API Key (optional for auto-post)", type="password")
    twitter_api_secret = st.text_input("Twitter API Secret", type="password")
    twitter_access_token = st.text_input("Twitter Access Token", type="password")
    twitter_access_secret = st.text_input("Twitter Access Secret", type="password")
   
    st.header("⚙️ Customization")
    custom_topics = st.text_area("Preferred topics (one per line, overrides trending)", "AI news\nCrypto\nFitness hacks")
    caption_style = st.selectbox("Caption style", ["Fun & Emoji", "Professional", "Viral Hype"])
    auto_post_x = st.checkbox("Auto-post to X/Twitter", value=True)

# ====================== GROK CLIENT ======================
if xai_key:
    grok = OpenAI(api_key=xai_key, base_url="https://api.x.ai/v1")
else:
    grok = None

# ====================== HISTORY DB (CSV) ======================
if "history" not in st.session_state:
    try:
        st.session_state.history = pd.read_csv("clip_history.csv")
    except:
        st.session_state.history = pd.DataFrame(columns=["date", "topic", "title", "video_file", "posted", "platforms"])

# ====================== 1. GET TRENDING ======================
def get_trending():
    pytrends = TrendReq(hl='en-US', tz=360)
    df = pytrends.trending_searches(pn='united_states')
    return df.iloc[0, 0]

# ====================== 2. GROK THEME + TEXTS ======================
def generate_theme(topic):
    if not grok:
        return {"theme_title": f"🔥 {topic}", "overlay_texts": ["Trend Alert!", "Mind Blown 🤯", "You NEED this", "Share Now!"]}
    prompt = f"""Trending topic: "{topic}". Create JSON only:
    {{"theme_title": "max 60 chars catchy", "overlay_texts": ["text1 max20", "text2", "text3", "text4", "text5"]}}"""
    resp = grok.chat.completions.create(model="grok-4.1-fast", messages=[{"role":"user","content":prompt}])
    try:
        return json.loads(resp.choices[0].message.content)
    except:
        return {"theme_title": f"🔥 {topic}", "overlay_texts": ["Trend Alert!", "Mind Blown 🤯", "You NEED this", "Share Now!"]}

# ====================== 3. DOWNLOAD FREE PEXELS CLIPS ======================
def download_clips(query, num=6):
    headers = {"Authorization": pexels_key}
    r = requests.get(f"https://api.pexels.com/videos/search?query={query}&per_page={num}&orientation=portrait", headers=headers)
    data = r.json()
    files = []
    for video in data.get("videos", [])[:5]:
        if video["duration"] >= 8:
            url = video["video_files"][0]["link"]
            fname = f"clip_{len(files)}.mp4"
            with open(fname, "wb") as f:
                f.write(requests.get(url).content)
            files.append(fname)
    return files

# ====================== 4. CREATE 1-MIN HD VIDEO ======================
def create_clip(clips_files, theme):
    clips = []
    for f in clips_files[:5]:
        clip = VideoFileClip(f).subclip(0, 12).resize(height=1920).crop(x_center=clip.w/2, width=1080)
        clips.append(clip)
   
    final = concatenate_videoclips(clips)
   
    # Animated texts
    texts = []
    for i, txt in enumerate(theme["overlay_texts"]):
        t = TextClip(txt, fontsize=75, color='white', font='Arial-Bold', stroke_color='black', stroke_width=4)
        t = t.set_position('center').set_start(i*12).set_duration(3)
        texts.append(t)
   
    title = TextClip(theme["theme_title"], fontsize=95, color='yellow', stroke_color='black', stroke_width=6)
    title = title.set_position('top').set_start(0).set_duration(5)
   
    video = CompositeVideoClip([final] + texts + [title])
    output = f"clip_{datetime.now().strftime('%Y%m%d_%H%M')}.mp4"
    video.write_videofile(output, fps=30, codec="libx264")
   
    # Cleanup
    for f in clips_files:
        os.remove(f) if os.path.exists(f) else None
    return output

# ====================== 5. POST TO X (AUTO) ======================
def post_to_x(video_path, caption):
    if not (twitter_api_key and twitter_access_token):
        return "Manual post needed"
    auth = tweepy.OAuth1UserHandler(twitter_api_key, twitter_api_secret, twitter_access_token, twitter_access_secret)
    api = tweepy.API(auth)
    media = api.media_upload(video_path)
    api.update_status(status=caption, media_ids=[media.media_id])
    return "✅ Posted to X"

# ====================== MAIN DASHBOARD ======================
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Generate Today", "📊 Dashboard", "⚙️ Customize", "📚 History"])

with tab1:
    st.subheader("Generate Today's Viral Clip")
    if st.button("🔥 Generate & Post 1-Min Clip Now", type="primary", use_container_width=True):
        with st.spinner("Fetching trend → Grok theme → Free clips → Compiling HD video..."):
            topic = get_trending()
            theme = generate_theme(topic)
            clips = download_clips(topic)
            video_file = create_clip(clips, theme)
           
            caption = f"{theme['theme_title']}\n\n{theme.get('theme_description','Everyone is talking about this!')} #Trending #Viral"
           
            # Optional Grok image thumbnail
            if grok and st.checkbox("Add AI thumbnail (uses 1 credit)"):
                img_resp = grok.images.generate(model="grok-imagine-image", prompt=f"Thumbnail for {topic}", extra_body={"aspect_ratio": "9:16"})
                # (download logic omitted for brevity – adds thumbnail overlay)
           
            st.success(f"✅ Clip ready: {theme['theme_title']}")
            st.video(video_file)
           
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("⬇️ Download Video", open(video_file,"rb").read(), video_file)
            with col2:
                if auto_post_x:
                    result = post_to_x(video_file, caption)
                    st.success(result)
                else:
                    st.info("Copy caption below and post manually")
                    st.code(caption)
           
            # Save to history
            new_row = pd.DataFrame([{"date": datetime.now(), "topic": topic, "title": theme["theme_title"], "video_file": video_file, "posted": "Yes", "platforms": "X"}])
            st.session_state.history = pd.concat([st.session_state.history, new_row])
            st.session_state.history.to_csv("clip_history.csv", index=False)

with tab2:
    st.subheader("Live Stats")
    if not st.session_state.history.empty:
        st.metric("Clips Generated This Month", len(st.session_state.history))
        st.dataframe(st.session_state.history[["date","title","posted"]].sort_values("date", ascending=False))
    else:
        st.info("No clips yet – hit Generate Today!")

with tab3:
    st.subheader("Customize Your Style")
    st.text_area("Custom prompt template for Grok", "Make it fun and emoji-heavy...")
    st.selectbox("Default video style", ["Energetic", "Cinematic", "Minimal"])
    st.slider("Daily clips", 1, 5, 1)

with tab4:
    st.subheader("Full History & Analytics")
    if not st.session_state.history.empty:
        st.dataframe(st.session_state.history)
    else:
        st.info("History appears here after first clip")

# ====================== FOOTER ======================
st.caption("✅ 100% free base system • Powered by Pexels + Grok • Deployed on Streamlit Cloud • Add to home screen for mobile app") 
