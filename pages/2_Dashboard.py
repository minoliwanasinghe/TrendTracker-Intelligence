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

# Load records from cluster if state validation checks show empty pipeline cache
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

# Pipeline parsing logic for incoming metrics structures
if 'cleaned_data' in st.session_state and not st.session_state['cleaned_data'].empty:
    df = st.session_state['cleaned_data'].copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['day_of_week'] = df['date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)
    
    if 'media_type' in df.columns and 'content_type' not in df.columns:
        df = df.rename(columns={'media_type': 'content_type'})
        
    # Standardize content formats to uppercase strings and filter empty variants
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
    st.info("👋 Welcome! No existing metrics history found. Please navigate to the Data Management page and upload a data file to activate your metrics dashboard pipeline.")
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

# Safety wrapper checks framework status to prevent reduction operation fmin exceptions
if not f_df.empty:
    try:
        best_t = str(f_df.groupby('content_type')['engagement'].mean().idxmax()).upper()
    except (ValueError, KeyError):
        best_t = "N/A"

    try:
        best_d = str(f_df.groupby('day_of_week')['engagement'].mean().idxmax()).upper()
    except (ValueError, KeyError):
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
            query = {"username": current_user}
            cursor = history_collection.find(query).sort("timestamp", 1)
            user_history = list(cursor)
            
            if not user_history or len(user_history) < 2:
                st.info("Additional historical data snapshots are required to compute brand performance changes. Your performance tracking will update dynamically on your next data export.")
            else:
                current_audit = user_history[-1]
                previous_audit = user_history[-2]
                
                c_count = current_audit["metrics"]["record_count"]
                p_count = previous_audit["metrics"]["record_count"]
                
                c_likes = current_audit["metrics"]["total_likes"]
                p_likes = previous_audit["metrics"]["total_likes"]
                
                c_saves = current_audit["metrics"].get("total_saves", 0)
                p_saves = previous_audit["metrics"].get("total_saves", 0)
                
                diff_count = c_count - p_count
                diff_likes = c_likes - p_likes
                diff_saves = c_saves - p_saves
                
                st.write("**Overall Account Performance Growth Status:**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Data Catalog Volume", f"{c_count:,} items", delta=f"{diff_count:,} vs last upload")
                m2.metric("Total Brand Reach (Likes)", f"{c_likes:,} total", delta=f"{diff_likes:,} vs last upload")
                m3.metric("Purchase Intent (Saves)", f"{c_saves:,} saved", delta=f"{diff_saves:,} vs last upload")
                
                flat_history = []
                for snapshot in user_history:
                    flat_history.append({
                        "Upload Date": snapshot["timestamp"],
                        "Audience Likes": snapshot["metrics"]["total_likes"]
                    })
                df_history_plot = pd.DataFrame(flat_history)
                st.line_chart(data=df_history_plot, x="Upload Date", y="Audience Likes", color="#800020")
                
        except Exception as query_err:
            st.warning(f"Unable to read business audit history: {query_err}")
    else:
        st.info("Database connection offline. Historical progress audit bypassed.")
        
    st.divider()

    vl, vr = st.columns(2)
    with vl:
        st.markdown('**<u>POST STYLE PERFORMANCE</u>**', unsafe_allow_html=True)
        avg_chart = f_df.groupby('content_type')['engagement'].mean().sort_values(ascending=False)
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        fig1.patch.set_facecolor('#FDFDFD')
        ax1.set_facecolor('#FFFFFF')
        sns.barplot(x=avg_chart.index, y=avg_chart.values, color="#800020", ax=ax1)
        st.pyplot(fig1)

    with vr:
        st.markdown('**<u>BEST TIME TO POST</u>**', unsafe_allow_html=True)
        pivot = f_df.pivot_table(values='engagement', index='content_type', columns='day_of_week', aggfunc='mean').fillna(0)
        
        # Guard clause checks dimensions before executing seaborn matrix configuration operations
        if pivot.shape[0] > 0 and pivot.shape[1] > 0:
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            fig2.patch.set_facecolor('#FDFDFD')
            sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Reds", ax=ax2)
            st.pyplot(fig2)
        else:
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            fig2.patch.set_facecolor('#FDFDFD')
            ax2.set_facecolor('#FFFFFF')
            ax2.text(0.5, 0.5, "Insufficient scheduling variance\nfor heatmap layout generation.", 
                     ha='center', va='center', color='#455A64', fontsize=11, style='italic')
            ax2.set_axis_off()
            st.pyplot(fig2)

    st.divider()
    st.markdown('<p class="sub-header">STRATEGIC INTELLIGENCE</p>', unsafe_allow_html=True)
    
    with st.expander("HOW TO USE THIS PAGE"):
        st.markdown("""
        **USER GUIDE:**
        1. **Benchmark Score:** This is your account's past average interaction. Your goal is to post content that scores higher than this number.
        2. **Impact Forecaster:** Use the drop-down menus below to pick a post type and a day. The system will guess how many points that post might get.
        3. **Weekly Roadmap:** Look at the table to see what you should post each day to get the most attention from your followers.
        """)

    st.markdown(f"""
    <div class="strategy-card">
        <b style="color:#800020;"><u>EXECUTIVE SUMMARY:</u></b><br><br>
        Our data shows that posting a <b>{best_t}</b> on <b>{best_d}</b> brings in the highest customer engagement. 
        We highly recommend planning your largest product launches around this timing.
    </div>
    """, unsafe_allow_html=True)

    c_sim, c_plan = st.columns([1, 1.4])

    with c_sim:
        st.markdown('**<u>IMPACT FORECASTER</u>**', unsafe_allow_html=True)
        unique_types = f_df['content_type'].unique()
        p_t = st.selectbox("FORMAT SELECTION", unique_types if len(unique_types) > 0 else ["N/A"])
        p_d = st.selectbox("DAY SELECTION", day_order)
        
        t_w = 1.5 if str(p_t).upper() == best_t else 1.0
        d_w = 1.3 if str(p_d).upper() == best_d else 1.0
        proj_score = int(avg_e * t_w * d_w)
        
        st.metric("PROJECTED IMPACT SCORE", f"{proj_score} PTS", delta=f"{proj_score - avg_e}")
        st.progress(min(proj_score / (avg_e * 3 if avg_e > 0 else 100), 1.0))

    with c_plan:
        st.markdown('**<u>7-DAY DEPLOYMENT ROADMAP</u>**', unsafe_allow_html=True)
        road_data = []
        
        for d in day_order:
            if d.upper() == best_d:
                task = f"Post Your Best Combination: {best_t}"
                goal = "Boost Sales and Clicks"
                priority = "High Priority"
            elif d in ["Saturday", "Sunday"]:
                task = "Share a Behind-the-Scenes or Brand Story"
                goal = "Build Customer Trust"
                priority = "Weekend Special"
            elif d in ["Tuesday", "Thursday"]:
                task = "Post Interactive Stories like Polls or Q&A"
                goal = "Increase Follower Replies"
                priority = "Mid-Week Engagement"
            else:
                task = "Post a Regular Product Showcase or Style Tips"
                goal = "Keep Brand Active"
                priority = "Routine"
                
            road_data.append({
                "Weekday": d, 
                "Recommended Action": task, 
                "Main Goal": goal,
                "Schedule Type": priority
            })
        
        df_roadmap = pd.DataFrame(road_data)
        st.dataframe(
            df_roadmap,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Weekday": st.column_config.TextColumn("Weekday", width="small"),
                "Schedule Type": st.column_config.TextColumn("Schedule Type", width="small"),
                "Recommended Action": st.column_config.TextColumn("Recommended Action", width="large"),
                "Main Goal": st.column_config.TextColumn("Main Goal", width="medium"),
            }
        )

    st.divider()
    with st.expander("VIEW DATASET ARCHIVE"):
        st.dataframe(f_df.sort_values(by='date', ascending=False), use_container_width=True)

else:
    st.warning("⚠️ NO RESULTS FOUND FOR THE SELECTED PARAMETERS. Try adjusting your date range filters.")