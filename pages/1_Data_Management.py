import streamlit as st
import pandas as pd
import io
import time
from pymongo import MongoClient
import certifi

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="TrendTracker | Data Engine", layout="wide")

# 2. DESIGNED CSS WITH DARK THEME
st.markdown("""
    <style>
    /* Dark Theme Background */
    .stApp { 
        background-color: #121212 !important; 
        color: #E0E0E0 !important;
    }
    
    /* Header Container Box */
    .header-box {
        background-color: #1E1E1E !important;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .header-box h1 { 
        color: #FF6B6B !important; /* Brighter accent for dark theme */
        font-weight: 800; 
        font-size: 42px; 
    }
    .header-box p { 
        color: #B0BEC5 !important; 
        font-size: 16px; 
    }
    
    /* Modern Section Headers */
    .section-title {
        color: #FF6B6B !important;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        border-left: 5px solid #FF6B6B;
        padding-left: 15px;
    }

    /* Schema Cards */
    .schema-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 30px;
    }
    .schema-card {
        background: #1E1E1E !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        flex: 1;
        text-align: center;
        border: none !important;
    }
    .schema-card h4 { color: #FF6B6B !important; margin-bottom: 10px; font-size: 18px; }
    .schema-card p { color: #CFD8DC !important; font-size: 14px; }

    /* Button Styling */
    div[data-testid="stDownloadButton"] button, 
    button:has(span:contains("Analytics")) {
        background-color: #264653 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
    }
    button:has(span:contains("Purge")) {
        background-color: #800020 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        border: none !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 25px;
        background-color: #262626 !important;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [data-baseweb="tab"] * { color: #B0BEC5 !important; font-weight: bold !important; }
    .stTabs [aria-selected="true"] { background-color: #264653 !important; }
    .stTabs [aria-selected="true"] * { color: white !important; }

    /* Metrics & Input Fields */
    div[data-testid="stMetricValue"] { color: #FF6B6B !important; }
    div[data-testid="stMetricLabel"] { color: #B0BEC5 !important; }
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stFileUploader"] label { color: #E0E0E0 !important; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1E1E1E !important; }
    </style>
""", unsafe_allow_html=True)


# 3. SECURITY & ACCESS MANAGEMENT CONTROL
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("Access Denied. Please authenticate via the Partner Gateway home page.")
    st.stop()

# 4. INITIALIZE SECURE CLOUD MONGODB ENGINE PERSISTENCE
@st.cache_resource
def get_db_connection():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())

history_collection = None
db = None
try:
    client = get_db_connection()
    db = client["trendtracker_db"]
    history_collection = db["analytics_history"]
except Exception as e:
    st.error(f"Database Archiving Engine Offline: {e}")

# --- HEADER ---
st.markdown('<div class="header-box"><h1>Data Processing Engine</h1><p>Clean and transform your social media exports effortlessly.</p></div>', unsafe_allow_html=True)

# --- NAVIGATION ---
tab1, tab2 = st.tabs(["Setup & Resources", "Data Processing Lab"])

with tab1:
    st.markdown('<p class="section-title">Data Configuration Guide</p>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="schema-container">
            <div class="schema-container" style="width: 100%;">
                <div class="schema-card">
                    <h4>Date Format</h4>
                    <p>Required: <b>YYYY-MM-DD</b><br>(e.g., 2026-05-14)</p>
                </div>
                <div class="schema-card">
                    <h4>Content Type</h4>
                    <p>Video, Reel, Carousel,<br>or Static Image</p>
                </div>
                <div class="schema-card">
                    <h4>Core Metrics</h4>
                    <p>Numerical values for<br>Likes, Shares & Saves</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.info("Instructions: Download the template to ensure your column headers match the engine requirements. This prevents processing errors.")
    with col_t2:
        template_df = pd.DataFrame({
            'date': ['2026-05-01'], 'content_type': ['Reel'],
            'likes': [120], 'comments': [15], 'shares': [45], 'saves': [30], 'time': ['18:00']
        })
        st.download_button(
            "Download CSV Template",
            template_df.to_csv(index=False),
            "trendtracker_template.csv",
            "text/csv",
            use_container_width=True
        )

with tab2:
    st.markdown('<p class="section-title">Upload & Sanitize</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your messy Instagram CSV file", type="csv")

    if uploaded_file:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        raw_data = pd.read_csv(uploaded_file)
        
        raw_data.columns = [c.lower().strip() for c in raw_data.columns]
        expected_fields = {'likes', 'shares', 'saves'}
        present_fields = set(raw_data.columns)
        
        if not expected_fields.issubset(present_fields):
            missing_items = expected_fields - present_fields
            st.error(f"Structural Validation Error: Your file is missing vital structural targets: {list(missing_items)}. Please apply our layout template.")
        else:
            if "last_processed_file" not in st.session_state or st.session_state["last_processed_file"] != file_id:
                with st.status("Processing Optimization Sequence...", expanded=True) as status:
                    time.sleep(1.0)
                    
                    current_client = st.session_state.get("username", "Unknown_Partner")
                    incoming_records = raw_data.to_dict(orient="records")
                    
                    for record in incoming_records:
                        record["username"] = current_client
                        if 'date' in record:
                            record['date'] = str(record['date'])

                    if db is not None:
                        try:
                            raw_data_collection = db["raw_user_datasets"]
                            raw_data_collection.insert_many(incoming_records)
                            
                            cloud_cursor = raw_data_collection.find({"username": current_client})
                            combined_cloud_df = pd.DataFrame(list(cloud_cursor))
                            
                            if '_id' in combined_cloud_df.columns:
                                combined_cloud_df = combined_cloud_df.drop(columns=['_id'])
                            
                            st.session_state['cleaned_data'] = combined_cloud_df.drop_duplicates()
                            
                        except Exception as cloud_err:
                            st.error(f"Cloud Storage Synchronizer Failure: {cloud_err}")
                            st.session_state['cleaned_data'] = raw_data
                    else:
                        st.session_state['cleaned_data'] = raw_data
                        
                    st.session_state["last_processed_file"] = file_id
                    status.update(label="File Cleaned & Integrated Successfully with Cloud History!", state="complete", expanded=False)

            active_df = st.session_state.get('cleaned_data', raw_data)

            st.success(f"System completely normalized and verified {len(active_df)} total lifetime records from your cloud registry.")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Lifetime Rows Found", len(active_df))
            c2.metric("Data Status", "Cloud Synced")
            
            total_likes = int(pd.to_numeric(active_df['likes'], errors='coerce').fillna(0).sum())
            total_shares = int(pd.to_numeric(active_df['shares'], errors='coerce').fillna(0).sum())
            total_saves = int(pd.to_numeric(active_df['saves'], errors='coerce').fillna(0).sum())
            
            c3.metric("Aggregated Likes", f"{total_likes:,}")

            if history_collection is not None:
                current_client = st.session_state.get("username", "Unknown_Partner")
                history_sent_key = f"sent_{file_id}"
                
                if history_sent_key not in st.session_state:
                    session_snapshot = {
                        "username": current_client,
                        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "metrics": {
                            "record_count": len(active_df),
                            "total_likes": total_likes,
                            "total_shares": total_shares,
                            "total_saves": total_saves
                        }
                    }
                    
                    try:
                        history_collection.insert_one(session_snapshot)
                        st.session_state[history_sent_key] = True
                        st.toast(f"Progress checkpoint compiled and pinned to profile: {current_client}")
                    except Exception as e:
                        st.warning(f"Unable to write automated tracking snapshot block: {e}")

    st.markdown("---")
    st.markdown("### Engine Operations Controls:")
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("Go to Analytics Dashboard", use_container_width=True):
            st.switch_page("pages/2_Dashboard.py")
            
    with col_nav2:
        if st.button("Purge & Wipe Cloud Dataset History", use_container_width=True):
            current_client = st.session_state.get("username", "Unknown_Partner")
            if db is not None:
                try:
                    db["raw_user_datasets"].delete_many({"username": current_client})
                    
                    keys_to_clear = ['cleaned_data', 'last_processed_file']
                    for k in keys_to_clear:
                        if k in st.session_state:
                            del st.session_state[k]
                            
                    sent_keys = [key for key in st.session_state.keys() if key.startswith("sent_")]
                    for sk in sent_keys:
                        del st.session_state[sk]
                        
                    st.success("Your lifetime dataset history was permanently cleared from the cloud database!")
                    time.sleep(1.0)
                    st.rerun()
                except Exception as purge_err:
                    st.error(f"Failed to clear cloud collections: {purge_err}")    
    /* Modern Section Headers */
    .section-title {
        color: #800020 !important;
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 20px;
        border-left: 5px solid #800020;
        padding-left: 15px;
    }

    /* Horizontal Schema Cards without borders */
    .schema-container {
        display: flex;
        justify-content: space-between;
        gap: 15px;
        margin-bottom: 30px;
    }
    .schema-card {
        background: white !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        flex: 1;
        text-align: center;
        border: none !important;
    }
    .schema-card h4 { 
        color: #800020 !important; 
        margin-bottom: 10px; 
        font-size: 18px; 
    }
    .schema-card p { 
        color: #2F4F4F !important; 
        font-size: 14px; 
    }

    /* BULLETPROOF CONTAINER-LEVEL SYSTEM BUTTON OVERRIDES */
    div[data-testid="stMainBlockContainer"] button {
        background-color: #2F4F4F !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        border: none !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* Clean CSS rules targeting text explicitly within action components */
    div[data-testid="stMainBlockContainer"] button * {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Hover state shifts cleanly to Deep Wine red */
    div[data-testid="stMainBlockContainer"] button:hover {
        background-color: #800020 !important;
        box-shadow: 0 4px 12px rgba(128,0,32,0.15) !important;
    }
    div[data-testid="stMainBlockContainer"] button:hover * {
        color: #FFFFFF !important;
    }
    
    /* Clean Tab Bar Headers layout fixes */
    .stTabs [data-baseweb="tab-list"] { 
        gap: 10px; 
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 25px;
        background-color: #EAEAEA !important;
        border-radius: 8px 8px 0 0;
    }
    .stTabs [data-baseweb="tab"] * {
        color: #2F4F4F !important;
        font-weight: bold !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2F4F4F !important;
    }
    .stTabs [aria-selected="true"] * {
        color: white !important;
    }

    /* Force visibility for standard text blocks, file uploads, and status labels */
    div[data-testid="stMarkdownContainer"] p, 
    div[data-testid="stMarkdownContainer"] span,
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stFileUploader"] label, 
    div[data-testid="stFileUploader"] p,
    .stStatusValue {
        color: #2F4F4F !important;
        font-weight: 500;
    }

    /* Metrics text alignment and contrast adjustments */
    div[data-testid="stMetricValue"] {
        color: #800020 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #455A64 !important;
    }
    
    /* Sidebar matching design */
    [data-testid="stSidebarNav"] ul li a span { color: #FFFFFF !important; }
    [data-testid="stSidebar"] { background-color: #2F4F4F !important; }
    </style>
""", unsafe_allow_html=True)

# 3. SECURITY & ACCESS MANAGEMENT CONTROL
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.error("Access Denied. Please authenticate via the Partner Gateway home page.")
    st.stop()

# 4. INITIALIZE SECURE CLOUD MONGODB ENGINE PERSISTENCE
@st.cache_resource
def get_db_connection():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())

history_collection = None
db = None
try:
    client = get_db_connection()
    db = client["trendtracker_db"]
    history_collection = db["analytics_history"]
except Exception as e:
    st.error(f"Database Archiving Engine Offline: {e}")

# --- HEADER ---
st.markdown('<div class="header-box"><h1>Data Processing Engine</h1><p>Clean and transform your social media exports effortlessly.</p></div>', unsafe_allow_html=True)

# --- NAVIGATION ---
tab1, tab2 = st.tabs(["Setup & Resources", "Data Processing Lab"])

with tab1:
    st.markdown('<p class="section-title">Data Configuration Guide</p>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="schema-container">
            <div class="schema-container" style="width: 100%;">
                <div class="schema-card">
                    <h4>Date Format</h4>
                    <p>Required: <b>YYYY-MM-DD</b><br>(e.g., 2026-05-14)</p>
                </div>
                <div class="schema-card">
                    <h4>Content Type</h4>
                    <p>Video, Reel, Carousel,<br>or Static Image</p>
                </div>
                <div class="schema-card">
                    <h4>Core Metrics</h4>
                    <p>Numerical values for<br>Likes, Shares & Saves</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2 = st.columns([2, 1])
    with col_t1:
        st.info("Instructions: Download the template to ensure your column headers match the engine requirements. This prevents processing errors.")
    with col_t2:
        template_df = pd.DataFrame({
            'date': ['2026-05-01'], 'content_type': ['Reel'],
            'likes': [120], 'comments': [15], 'shares': [45], 'saves': [30], 'time': ['18:00']
        })
        st.download_button(
            "Download CSV Template",
            template_df.to_csv(index=False),
            "trendtracker_template.csv",
            "text/csv",
            use_container_width=True
        )

with tab2:
    st.markdown('<p class="section-title">Upload & Sanitize</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload your messy Instagram CSV file", type="csv")

    if uploaded_file:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        raw_data = pd.read_csv(uploaded_file)
        
        raw_data.columns = [c.lower().strip() for c in raw_data.columns]
        expected_fields = {'likes', 'shares', 'saves'}
        present_fields = set(raw_data.columns)
        
        if not expected_fields.issubset(present_fields):
            missing_items = expected_fields - present_fields
            st.error(f"Structural Validation Error: Your file is missing vital structural targets: {list(missing_items)}. Please apply our layout template.")
        else:
            if "last_processed_file" not in st.session_state or st.session_state["last_processed_file"] != file_id:
                with st.status("Processing Optimization Sequence...", expanded=True) as status:
                    time.sleep(1.0)
                    
                    current_client = st.session_state.get("username", "Unknown_Partner")
                    incoming_records = raw_data.to_dict(orient="records")
                    
                    for record in incoming_records:
                        record["username"] = current_client
                        if 'date' in record:
                            record['date'] = str(record['date'])

                    if db is not None:
                        try:
                            raw_data_collection = db["raw_user_datasets"]
                            raw_data_collection.insert_many(incoming_records)
                            
                            cloud_cursor = raw_data_collection.find({"username": current_client})
                            combined_cloud_df = pd.DataFrame(list(cloud_cursor))
                            
                            if '_id' in combined_cloud_df.columns:
                                combined_cloud_df = combined_cloud_df.drop(columns=['_id'])
                            
                            st.session_state['cleaned_data'] = combined_cloud_df.drop_duplicates()
                            
                        except Exception as cloud_err:
                            st.error(f"Cloud Storage Synchronizer Failure: {cloud_err}")
                            st.session_state['cleaned_data'] = raw_data
                    else:
                        st.session_state['cleaned_data'] = raw_data
                        
                    st.session_state["last_processed_file"] = file_id
                    status.update(label="File Cleaned & Integrated Successfully with Cloud History!", state="complete", expanded=False)

            active_df = st.session_state.get('cleaned_data', raw_data)

            st.success(f"System completely normalized and verified {len(active_df)} total lifetime records from your cloud registry.")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Lifetime Rows Found", len(active_df))
            c2.metric("Data Status", "Cloud Synced")
            
            total_likes = int(pd.to_numeric(active_df['likes'], errors='coerce').fillna(0).sum())
            total_shares = int(pd.to_numeric(active_df['shares'], errors='coerce').fillna(0).sum())
            total_saves = int(pd.to_numeric(active_df['saves'], errors='coerce').fillna(0).sum())
            
            c3.metric("Aggregated Likes", f"{total_likes:,}")

            if history_collection is not None:
                current_client = st.session_state.get("username", "Unknown_Partner")
                history_sent_key = f"sent_{file_id}"
                
                if history_sent_key not in st.session_state:
                    session_snapshot = {
                        "username": current_client,
                        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "metrics": {
                            "record_count": len(active_df),
                            "total_likes": total_likes,
                            "total_shares": total_shares,
                            "total_saves": total_saves
                        }
                    }
                    
                    try:
                        history_collection.insert_one(session_snapshot)
                        st.session_state[history_sent_key] = True
                        st.toast(f"Progress checkpoint compiled and pinned to profile: {current_client}")
                    except Exception as e:
                        st.warning(f"Unable to write automated tracking snapshot block: {e}")

    st.markdown("---")
    st.markdown("### Engine Operations Controls:")
    
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("Go to Analytics Dashboard", use_container_width=True):
            st.switch_page("pages/2_Dashboard.py")
            
    with col_nav2:
        if st.button("Purge & Wipe Cloud Dataset History", use_container_width=True):
            current_client = st.session_state.get("username", "Unknown_Partner")
            if db is not None:
                try:
                    db["raw_user_datasets"].delete_many({"username": current_client})
                    
                    keys_to_clear = ['cleaned_data', 'last_processed_file']
                    for k in keys_to_clear:
                        if k in st.session_state:
                            del st.session_state[k]
                            
                    sent_keys = [key for key in st.session_state.keys() if key.startswith("sent_")]
                    for sk in sent_keys:
                        del st.session_state[sk]
                        
                    st.success("Your lifetime dataset history was permanently cleared from the cloud database!")
                    time.sleep(1.0)
                    st.rerun()
                except Exception as purge_err:
                    st.error(f"Failed to clear cloud collections: {purge_err}")
