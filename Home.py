import streamlit as st
import pandas as pd
from pymongo import MongoClient
import certifi

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="TrendTracker | Secure Authentication", layout="wide")

# Initialize the collection variable globally so it is always defined
users_collection = None

# 2. SECURE CACHED MONGO DB ENGINE CONNECTION
@st.cache_resource
def init_connection():
    return MongoClient(st.secrets["MONGO_URI"], tlsCAFile=certifi.where())

try:
    client = init_connection()
    db = client["trendtracker_db"]
    users_collection = db["users"]
except Exception as e:
    st.error(f"Database Connection Offline: {e}")

# 3. SESSION STATE INITIALIZATION
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 4. LOGIN & SELF-REGISTRATION INTERFACE
def login_page():
    st.markdown("""
        <style>
        /* Clean uniform background */
        .stApp { 
            background-color: #F8F9FA !important; 
        }
        
        /* Centered, balanced form container without borders */
        div[data-testid="stForm"] {
            background-color: #FFFFFF !important;
            padding: 40px !important;
            border-radius: 12px !important;
            border: none !important;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04) !important;
            max-width: 550px !important;
            margin: 0 auto !important;
        }

        /* Standard text rules for clean dark slate text */
        div[data-testid="stForm"] h3, 
        div[data-testid="stForm"] label,
        div[data-testid="stForm"] p,
        div[data-testid="stForm"] span {
            color: #2F4F4F !important;
            font-weight: 600 !important;
        }

        /* Input field fixes - ensures clean white background without dark mode cuts */
        div[data-testid="stForm"] input,
        div[data-testid="stForm"] div[data-baseweb="input"] {
            background-color: #FFFFFF !important;
            color: #000000 !important;
            border: 1px solid #D1D5DB !important;
            border-radius: 6px !important;
        }
        
        /* Fixes the specific eye icon visibility/background row on password fields */
        div[data-testid="stForm"] div[data-baseweb="input"] button {
            background-color: transparent !important;
            color: #2F4F4F !important;
        }

        /* Sleek tab buttons formatting */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px !important;
            justify-content: center !important;
            margin-bottom: 20px !important;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 8px 20px !important;
            background-color: #E5E7EB !important;
            color: #4B5563 !important;
            border-radius: 6px !important;
            font-weight: 600 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #800000 !important;
            color: #FFFFFF !important;
        }

        /* High-contrast form buttons - text is perfectly white and visible */
        div[data-testid="stForm"] button[type="submit"] {
            background-color: #800000 !important;
            color: #FFFFFF !important;
            font-weight: bold !important;
            border-radius: 6px !important;
            height: 3.2em !important;
            width: 100% !important;
            border: none !important;
            font-size: 16px !important;
            transition: background-color 0.2s ease !important;
            cursor: pointer !important;
        }
        
        div[data-testid="stForm"] button[type="submit"]:hover {
            background-color: #2F4F4F !important;
            color: #FFFFFF !important;
        }

        /* Large minimalist heading title */
        .brand-title { 
            color: #800000 !important; 
            font-size: 38px !important; 
            font-weight: 800 !important; 
            text-align: center !important; 
            margin-top: 30px !important;
            margin-bottom: 30px !important;
            letter-spacing: 1.5px !important;
            text-transform: uppercase !important;
        }
        
        /* Sidebar layout matching theme */
        [data-testid="stSidebarNav"] ul li a span { color: #FFFFFF !important; }
        [data-testid="stSidebar"] { background-color: #2F4F4F !important; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="brand-title">TrendTracker Intelligence</h1>', unsafe_allow_html=True)

    if users_collection is None:
        st.warning("System is waiting for a valid database configuration. Please ensure your connection link is inside your hidden secrets configuration file.")
        return

    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        auth_tab1, auth_tab2 = st.tabs(["Authorized Portal", "Account Registration"])
        
        # --- TAB 1: USER LOGIN GATEWAY ---
        with auth_tab1:
            with st.form("login_form"):
                st.write("### Access Account")
                user_input = st.text_input("Username", key="login_username_field")
                pass_input = st.text_input("Password", type="password", key="login_password_field")
                login_button = st.form_submit_button("Sign In")

                if login_button:
                    if not user_input or not pass_input:
                        st.warning("Please fill in all entry parameters.")
                    else:
                        user_record = users_collection.find_one({"username": user_input, "password": pass_input})
                        
                        if user_record:
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = user_input
                            st.success("Login Successful.")
                            st.rerun()
                        else:
                            st.error("Invalid Username or Password.")

        # --- TAB 2: AUTOMATED CLIENT SELF-REGISTRATION ---
        with auth_tab2:
            with st.form("registration_form"):
                st.write("### Register New Profile")
                reg_email = st.text_input("Corporate Email Address")
                reg_user = st.text_input("Desired Username")
                reg_pass = st.text_input("Secure Password", type="password")
                reg_confirm = st.text_input("Confirm Password", type="password")
                register_button = st.form_submit_button("Create Business Account")

                if register_button:
                    if not reg_email or not reg_user or not reg_pass:
                        st.warning("All input registration values must be satisfied.")
                    elif reg_pass != reg_confirm:
                        st.error("Credential validation mismatch. Passwords do not match.")
                    else:
                        duplicate_check = users_collection.find_one({"username": reg_user})
                        
                        if duplicate_check:
                            st.error("Account creation halted: This identity is already registered.")
                        else:
                            new_profile_document = {
                                "username": reg_user,
                                "password": reg_pass,
                                "email": reg_email,
                                "registration_timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            users_collection.insert_one(new_profile_document)
                            st.success("Registration Successful! Please navigate back to the Authorized Portal tab to sign in.")

# 5. IDENTITY & ACCESS MANAGEMENT AUTHENTICATION RUNNER
if not st.session_state["authenticated"]:
    login_page()
else:
    st.sidebar.markdown(f"**Active Session:** `{st.session_state['username']}`")
    
    st.sidebar.markdown("""
        <style>
        div[data-testid="stSidebar"] button {
            background-color: #800000 !important;
            color: #FFFFFF !important;
            border: none !important;
            height: auto !important;
            width: auto !important;
            padding: 5px 15px !important;
            font-size: 14px !important;
        }
        div[data-testid="stSidebar"] button:hover {
            background-color: #b30000 !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("Log out Session"):
        st.session_state["authenticated"] = False
        st.session_state["username"] = None
        st.rerun()

    st.title("Welcome to TrendTracker")
    st.write(f"Hello {st.session_state['username']}, you have successfully authenticated via your MongoDB cloud profile configuration.")
    
    st.markdown("---")
    
    st.markdown("""
        <style>
        .stApp div.stButton>button {
            background-color: #800000 !important;
            color: white !important;
            font-size: 16px !important;
            width: auto !important;
            padding: 10px 20px !important;
            border: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    if st.button("Proceed to Data Management Hub"):
        st.switch_page("pages/1_Data_Management.py")