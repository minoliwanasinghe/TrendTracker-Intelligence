import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
import certifi

st.set_page_config(page_title="TrendTracker Intelligence", layout="wide")

def apply_custom_style():
    st.markdown("""
        <style>
        /* Base Page Styling */
        .stApp { 
            background-color: #FDFDFD !important; 
            font-family: 'Segoe UI', Helvetica, sans-serif; 
            color: #334155 !important;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] { background-color: #F1F5F9 !important; }
        [data-testid="stSidebar"] * { color: #475569 !important; }
        
        /* Headers */
        .main-header {
            font-size: 32px; font-weight: 800; color: #312e81 !important; 
            text-align: center; margin-bottom: 25px;
        }
        .sub-header {
            font-size: 22px; font-weight: 700; color: #312e81 !important;
            text-transform: uppercase; margin-top: 20px;
            border-bottom: 2px solid #312e81; padding-bottom: 5px;
        }
        
        /* Strategy Cards */
        .strategy-card {
            background-color: #F8FAFC !important; 
            color: #1e293b !important; 
            padding: 25px; 
            border: 1px solid #E2E8F0 !important; 
            border-left: 10px solid #312e81 !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        /* Metrics */
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important; 
            border: 1px solid #E2E8F0 !important; 
            padding: 15px;
            border-radius: 8px;
        }
        div[data-testid="stMetricValue"] { color: #1e293b !important; font-weight: bold; }
        div[data-testid="stMetricLabel"] { color: #64748b !important; }
        
        /* Text elements */
        p, b, u, label { color: #334155 !important; }
        
        /* Expanders */
        div[data-testid="stExpander"] {
            background-color: #F8FAFC !important;
            border: 1px solid #E2E8F0 !important;
        }
        div[data-testid="stExpander"] details summary p {
            color: #312e81 !important;
            font-weight: bold;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

# --- Authentication & DB Logic ---
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("AUTHENTICATION REQUIRED: ACCESS DENIED.")
    st.stop()

current_user = st.session_state.get("username", "Unknown_Partner")

@st.cache_resource
def get_db_connection():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())

history_collection = None
db = None
try:
    client = get_db_connection()
    db = client["trendtracker_db"]
    history_collection = db["analytics_history"]
except Exception as mongo_err:
    st.warning(f"Database Standby: {mongo_err}")

if 'cleaned_data' not in st.session_state and db is not None:
    try:
        raw_data_collection = db["raw_user_datasets"]
        cloud_cursor = raw_data_collection.find({"username": current_user})
        cloud_docs = list(cloud_cursor)
        if cloud_docs:
            loaded_df = pd.DataFrame(cloud_docs)
            if '_id' in loaded_df.columns: loaded_df = loaded_df.drop(columns=['_id'])
            st.session_state['cleaned_data'] = loaded_df.drop_duplicates()
    except Exception as fetch_err:
        st.warning(f"Database sync standby: {fetch_err}")

# --- Data Processing ---
if 'cleaned_data' in st.session_state and not st.session_state['cleaned_data'].empty:
    df = st.session_state['cleaned_data'].copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['day_of_week'] = df['date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)
    
    if 'media_type' in df.columns and 'content_type' not in df.columns: df = df.rename(columns={'media_type': 'content_type'})
    df['content_type'] = df['content_type'].astype(str).str.strip().str.upper().replace(['', 'NAN', 'NONE'], 'UNKNOWN')
    
    for col in ['likes', 'shares', 'saves', 'comments']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    df['engagement'] = df['likes'] + df['comments'] + df['shares'] + df['saves']
else:
    st.markdown('<p class="main-header">**PERFORMANCE DASHBOARD**</p>', unsafe_allow_html=True)
    st.info("👋 Welcome! Please upload data via the Data Management engine.")
    if st.button("Go to Data Management Engine"): st.switch_page("pages/1_Data_Management.py")
    st.stop()

# --- Main Dashboard ---
st.markdown('<p class="main-header">**BUSINESS PERFORMANCE AUDIT & ANALYTICS**</p>', unsafe_allow_html=True)
c_f1, c_f2 = st.columns(2)
with c_f1: start_date = st.date_input("START DATE", df['date'].min())
with c_f2: end_date = st.date_input("END DATE", df['date'].max())

mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
f_df = df.loc[mask]
st.divider()

if not f_df.empty:
    best_t = str(f_df.groupby('content_type')['engagement'].mean().idxmax()).upper()
    best_d = str(f_df.groupby('day_of_week')['engagement'].mean().idxmax()).upper()
    avg_e = int(f_df['engagement'].mean())
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("POST COUNT", len(f_df))
    k2.metric("BENCHMARK SCORE", f"{avg_e:,} pts")
    k3.metric("OPTIMAL FORMAT", best_t)
    k4.metric("PEAK WINDOW", best_d)

    st.divider()
    st.markdown('<p class="sub-header">LONG-TERM BRAND GROWTH AUDIT</p>', unsafe_allow_html=True)
    
    if history_collection is not None:
        user_history = list(history_collection.find({"username": current_user}).sort("timestamp", 1))
        if len(user_history) >= 2:
            curr, prev = user_history[-1], user_history[-2]
            m1, m2, m3 = st.columns(3)
            m1.metric("Catalog Volume", f"{curr['metrics']['record_count']:,}", delta=f"{curr['metrics']['record_count'] - prev['metrics']['record_count']:,}")
            m2.metric("Total Likes", f"{curr['metrics']['total_likes']:,}", delta=f"{curr['metrics']['total_likes'] - prev['metrics']['total_likes']:,}")
            m3.metric("Total Saves", f"{curr['metrics'].get('total_saves', 0):,}", delta=f"{curr['metrics'].get('total_saves', 0) - prev['metrics'].get('total_saves', 0):,}")
            
            df_hist = pd.DataFrame([{"Date": s["timestamp"], "Likes": s["metrics"]["total_likes"]} for s in user_history])
            st.line_chart(data=df_hist, x="Date", y="Likes", color="#312e81")

    st.divider()
    vl, vr = st.columns(2)
    with vl:
        st.markdown('**<u>POST STYLE PERFORMANCE</u>**', unsafe_allow_html=True)
        avg_chart = f_df.groupby('content_type')['engagement'].mean().sort_values(ascending=False)
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        sns.barplot(x=avg_chart.index, y=avg_chart.values, color="#312e81", ax=ax1)
        st.pyplot(fig1)

    with vr:
        st.markdown('**<u>BEST TIME TO POST</u>**', unsafe_allow_html=True)
        pivot = f_df.pivot_table(values='engagement', index='content_type', columns='day_of_week', aggfunc='mean').fillna(0)
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax2)
        st.pyplot(fig2)

    st.markdown('<p class="sub-header">STRATEGIC INTELLIGENCE</p>', unsafe_allow_html=True)
    st.markdown(f'''<div class="strategy-card"><b>EXECUTIVE SUMMARY:</b><br>Posting <b>{best_t}</b> on <b>{best_d}</b> brings highest engagement. We recommend planning major launches around this timing.</div>''', unsafe_allow_html=True)

    c_sim, c_plan = st.columns([1, 1.4])
    with c_sim:
        st.markdown('**<u>IMPACT FORECASTER</u>**', unsafe_allow_html=True)
        p_t = st.selectbox("FORMAT", f_df['content_type'].unique())
        p_d = st.selectbox("DAY", day_order)
        proj = int(avg_e * (1.5 if str(p_t).upper() == best_t else 1.0) * (1.3 if str(p_d).upper() == best_d else 1.0))
        st.metric("PROJECTED IMPACT", f"{proj} PTS", delta=f"{proj - avg_e}")
        st.progress(min(proj / (avg_e * 3 if avg_e > 0 else 100), 1.0))

    with c_plan:
        st.markdown('**<u>7-DAY DEPLOYMENT ROADMAP</u>**', unsafe_allow_html=True)
        road_data = []
        for d in day_order:
            if d.upper() == best_d:
                task, goal, priority = f"Post Your Best Combination: {best_t}", "Boost Sales and Clicks", "High Priority"
            elif d in ["Saturday", "Sunday"]:
                task, goal, priority = "Share a Behind-the-Scenes or Brand Story", "Build Customer Trust", "Weekend Special"
            elif d in ["Tuesday", "Thursday"]:
                task, goal, priority = "Post Interactive Stories like Polls or Q&A", "Increase Follower Replies", "Mid-Week Engagement"
            else:
                task, goal, priority = "Post a Regular Product Showcase or Style Tips", "Keep Brand Active", "Routine"
            road_data.append({"Weekday": d, "Recommended Action": task, "Main Goal": goal, "Schedule Type": priority})
        
        st.dataframe(pd.DataFrame(road_data), use_container_width=True, hide_index=True, column_config={
            "Weekday": st.column_config.TextColumn("Weekday", width="small"),
            "Schedule Type": st.column_config.TextColumn("Schedule Type", width="small"),
            "Recommended Action": st.column_config.TextColumn("Recommended Action", width="large"),
            "Main Goal": st.column_config.TextColumn("Main Goal", width="medium"),
        })
else:
    st.warning("⚠️ No results found for the selected parameters.")
