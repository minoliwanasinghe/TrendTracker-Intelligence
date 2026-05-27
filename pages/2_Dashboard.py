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
        .stApp { 
            background-color: #FDFDFD !important; 
            font-family: 'Segoe UI', Helvetica, sans-serif; 
        }
        [data-testid="stSidebarNav"] ul li a span { color: #FFFFFF !important; }
        [data-testid="stSidebar"] { background-color: #2F4F4F !important; }
        .main-header {
            font-size: 32px; 
            font-weight: 800; 
            color: #800020 !important; 
            text-align: center;
            margin-bottom: 25px;
        }
        .sub-header {
            font-size: 22px; font-weight: 700; color: #2F4F4F !important;
            text-transform: uppercase; margin-top: 20px;
            border-bottom: 2px solid #800020; padding-bottom: 5px;
        }
        .strategy-card {
            background-color: #FFFFFF !important; 
            color: #000000 !important; 
            padding: 25px; 
            border: 1px solid #2F4F4F !important; 
            border-left: 10px solid #800020 !important;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }
        div[data-testid="stMetric"] {
            background-color: #F8F9FA !important; 
            border: 1px solid #DEE2E6 !important; 
            padding: 15px;
            border-radius: 4px;
        }
        div[data-testid="stMetricValue"] { color: #800020 !important; }
        div[data-testid="stMetricLabel"] { color: #455A64 !important; }
        div[data-testid="stMarkdownContainer"] p, 
        div[data-testid="stMarkdownContainer"] b, 
        div[data-testid="stMarkdownContainer"] u,
        label[data-testid="stWidgetLabel"] {
            color: #2F4F4F !important;
        }
        div[data-testid="stExpander"] {
            background-color: #FFFFFF !important;
            border: 1px solid #DEE2E6 !important;
        }
        div[data-testid="stExpander"] details summary p {
            color: #800020 !important;
            font-weight: bold;
        }
        div[data-baseweb="select"] div { color: #000000 !important; }
        div[data-testid="stTable"] table {
            color: #000000 !important;
            background-color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)

apply_custom_style()

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
            if '_id' in loaded_df.columns:
                loaded_df = loaded_df.drop(columns=['_id'])
            st.session_state['cleaned_data'] = loaded_df.drop_duplicates()
    except Exception as fetch_err:
        st.warning(f"Database sync standby: {fetch_err}")

if 'cleaned_data' in st.session_state and not st.session_state['cleaned_data'].empty:
    df = st.session_state['cleaned_data'].copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['day_of_week'] = df['date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)
    
    if 'media_type' in df.columns and 'content_type' not in df.columns:
        df = df.rename(columns={'media_type': 'content_type'})
        
    if 'content_type' in df.columns:
        df['content_type'] = df['content_type'].astype(str).str.strip().str.upper()
        df['content_type'] = df['content_type'].replace(['', 'NAN', 'NONE'], 'UNKNOWN')
    else:
        df['content_type'] = 'UNKNOWN'
        
    df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0)
    df['shares'] = pd.to_numeric(df['shares'], errors='coerce').fillna(0)
    df['saves'] = pd.to_numeric(df['saves'], errors='coerce').fillna(0)
    df['comments'] = pd.to_numeric(df['comments'], errors='coerce').fillna(0) if 'comments' in df.columns else 0
        
    df['engagement'] = df['likes'] + df['comments'] + df['shares'] + df['saves']
else:
    st.markdown('<p class="main-header">**PERFORMANCE DASHBOARD**</p>', unsafe_allow_html=True)
    st.info("👋 Welcome! No existing metrics history found. Please navigate to the Data Management page.")
    if st.button("Go to Data Management Engine"):
        st.switch_page("pages/1_Data_Management.py")
    st.stop()

st.markdown('<p class="main-header">**BUSINESS PERFORMANCE AUDIT & ANALYTICS**</p>', unsafe_allow_html=True)

st.markdown('**<u>DATA FILTERS</u>**', unsafe_allow_html=True)
c_f1, c_f2 = st.columns(2)
with c_f1:
    start_date = st.date_input("START DATE", df['date'].min())
with c_f2:
    end_date = st.date_input("END DATE", df['date'].max())

start_ts = pd.to_datetime(start_date)
end_ts = pd.to_datetime(end_date)

mask = (df['date'] >= start_ts) & (df['date'] <= end_ts)
f_df = df.loc[mask]
st.divider()

if not f_df.empty:
    try:
        best_t = str(f_df.groupby('content_type')['engagement'].mean().idxmax()).upper()
    except:
        best_t = "N/A"
    try:
        best_d = str(f_df.groupby('day_of_week')['engagement'].mean().idxmax()).upper()
    except:
        best_d = "N/A"

    avg_e = int(f_df['engagement'].mean()) if not f_df['engagement'].empty else 0
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("POST COUNT", len(f_df))
    k2.metric("BENCHMARK SCORE", f"{avg_e:,} pts")
    k3.metric("OPTIMAL FORMAT", best_t)
    k4.metric("PEAK WINDOW", best_d)

    st.divider()
    st.markdown('<p class="sub-header">LONG-TERM BRAND GROWTH AUDIT</p>', unsafe_allow_html=True)
    
    if history_collection is not None:
        try:
            cursor = history_collection.find({"username": current_user}).sort("timestamp", 1)
            user_history = list(cursor)
            
            if len(user_history) < 2:
                st.info("Additional historical data snapshots are required.")
            else:
                current_audit = user_history[-1]
                previous_audit = user_history[-2]
                
                c_count = current_audit["metrics"]["record_count"]
                p_count = previous_audit["metrics"]["record_count"]
                c_likes = current_audit["metrics"]["total_likes"]
                p_likes = previous_audit["metrics"]["total_likes"]
                c_saves = current_audit["metrics"].get("total_saves", 0)
                p_saves = previous_audit["metrics"].get("total_saves", 0)
                
                st.write("**Overall Account Performance Growth Status:**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Data Catalog", f"{c_count:,}", delta=f"{c_count - p_count:,}")
                m2.metric("Total Likes", f"{c_likes:,}", delta=f"{c_likes - p_likes:,}")
                m3.metric("Total Saves", f"{c_saves:,}", delta=f"{c_saves - p_saves:,}")
                
                df_history_plot = pd.DataFrame([{"Date": s["timestamp"], "Likes": s["metrics"]["total_likes"]} for s in user_history])
                st.line_chart(data=df_history_plot, x="Date", y="Likes", color="#800020")
        except Exception as query_err:
            st.warning(f"Unable to read history: {query_err}")
        
    st.divider()
    vl, vr = st.columns(2)
    with vl:
        st.markdown('**<u>POST STYLE PERFORMANCE</u>**', unsafe_allow_html=True)
        avg_chart = f_df.groupby('content_type')['engagement'].mean().sort_values(ascending=False)
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        fig1.patch.set_facecolor('#FDFDFD')
        sns.barplot(x=avg_chart.index, y=avg_chart.values, color="#800020", ax=ax1)
        st.pyplot(fig1)

    with vr:
        st.markdown('**<u>BEST TIME TO POST</u>**', unsafe_allow_html=True)
        pivot = f_df.pivot_table(values='engagement', index='content_type', columns='day_of_week', aggfunc='mean').fillna(0)
        if not pivot.empty:
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            fig2.patch.set_facecolor('#FDFDFD')
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Reds", ax=ax2)
            st.pyplot(fig2)

    st.divider()
    st.markdown('<p class="sub-header">STRATEGIC INTELLIGENCE</p>', unsafe_allow_html=True)
    
    with st.expander("HOW TO USE THIS PAGE"):
        st.write("1. Benchmark: Aim to beat your average score.\n2. Forecaster: Predict performance.\n3. Roadmap: Follow the guide.")

    st.markdown(f"""
    <div class="strategy-card">
        <b style="color:#800020;"><u>EXECUTIVE SUMMARY:</u></b><br><br>
        Posting <b>{best_t}</b> on <b>{best_d}</b> brings highest engagement.
    </div>
    """, unsafe_allow_html=True)

    c_sim, c_plan = st.columns([1, 1.4])
    with c_sim:
        st.markdown('**<u>IMPACT FORECASTER</u>**', unsafe_allow_html=True)
        p_t = st.selectbox("FORMAT", f_df['content_type'].unique())
        p_d = st.selectbox("DAY", day_order)
        proj_score = int(avg_e * (1.5 if str(p_t) == best_t else 1.0) * (1.3 if str(p_d) == best_d else 1.0))
        st.metric("PROJECTED IMPACT", f"{proj_score} PTS")
        st.progress(min(proj_score / (avg_e * 3 if avg_e > 0 else 100), 1.0))

    with c_plan:
        st.markdown('**<u>7-DAY DEPLOYMENT ROADMAP</u>**', unsafe_allow_html=True)
        road_data = [{"Weekday": d, "Action": ("Best" if d.upper() == best_d else "Routine"), "Goal": "Engagement"} for d in day_order]
        st.dataframe(pd.DataFrame(road_data), use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ No results found.")
