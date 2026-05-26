import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from datetime import datetime

# 1. PAGE CONFIG
st.set_page_config(page_title="TrendTracker | Business Audit", layout="centered")

# 2. SECURITY GATEKEEPER
if "authenticated" not in st.session_state or not st.session_state["authenticated"]:
    st.warning("Access Denied. Please login on the Home page.")
    st.stop()

# 3. DATA SYNC & PREPARATION
if 'cleaned_data' in st.session_state:
    df = st.session_state['cleaned_data'].copy()
    
    # Standardize columns
    if 'media_type' in df.columns and 'content_type' not in df.columns:
        df = df.rename(columns={'media_type': 'content_type'})
    
    # Calculate Metrics
    metric_cols = ['likes', 'comments', 'shares', 'saves']
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    df['engagement'] = df['likes'] + df['comments'] + df['shares'] + df['saves']
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['day_of_week'] = df['date'].dt.day_name()
    
    # Extract Insights for the Report
    analysis_start = df['date'].min().strftime('%d %B %Y')
    analysis_end = df['date'].max().strftime('%d %B %Y')
    avg_eng = int(df['engagement'].mean())
    best_fmt = df.groupby('content_type')['engagement'].mean().idxmax()
    best_day = df.groupby('day_of_week')['engagement'].mean().idxmax()
else:
    st.info("Please process data in Data Management first.")
    st.stop()

# --- UI HEADER ---
st.markdown("""
    <div style="text-align: center; padding: 10px;">
        <h1 style="color: #800020;">Business Strategy Audit</h1>
    </div>
""", unsafe_allow_html=True)

# 4. REPORT CONFIGURATION
with st.expander("Report Details", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        business_name = st.text_input("Business Name", "Joey Clothing")
        prepared_by = st.text_input("Analyst Name", "Supipi Wanasinghe")
    with col2:
        report_date = st.date_input("Audit Issue Date", datetime.now())

# 5. PDF GENERATION LOGIC
if st.button("Generate Professional Audit Report"):
    with st.spinner("Compiling Analytics..."):
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # --- HEADER (Maroon Bar) ---
            pdf.set_fill_color(128, 0, 32) 
            pdf.rect(0, 0, 210, 40, 'F')
            pdf.set_font("Arial", 'B', 24)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(190, 15, txt="TrendTracker Performance Audit", ln=True, align='C')
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(190, 10, txt=f"Business Intelligence Report: {business_name}", ln=True, align='C')
            pdf.ln(25)
            
            # --- SECTION 1: METADATA ---
            pdf.set_text_color(128, 0, 32)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="1. REPORT METADATA", ln=True)
            pdf.set_text_color(40, 40, 40)
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 7, txt=f"Analysis Period: {analysis_start} to {analysis_end}", ln=True)
            pdf.cell(0, 7, txt=f"Report Issued: {report_date.strftime('%d %B %Y')}", ln=True)
            pdf.cell(0, 7, txt=f"Total Posts Audited: {len(df)}", ln=True)
            pdf.ln(5)

            # --- SECTION 2: KPI TABLE ---
            pdf.set_text_color(128, 0, 32)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="2. CORE KPI PERFORMANCE", ln=True)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font("Arial", 'B', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(95, 10, txt="Performance Metric", border=1, fill=True)
            pdf.cell(95, 10, txt="Result", border=1, fill=True, ln=True)
            pdf.set_font("Arial", '', 10)
            pdf.cell(95, 10, txt="Average Audience Engagement", border=1)
            pdf.cell(95, 10, txt=f"{avg_eng} interactions", border=1, ln=True)
            pdf.cell(95, 10, txt="Optimal Content Format", border=1)
            pdf.cell(95, 10, txt=f"{best_fmt}", border=1, ln=True)
            pdf.cell(95, 10, txt="Peak Posting Day", border=1)
            pdf.cell(95, 10, txt=f"{best_day}", border=1, ln=True)
            pdf.ln(10)

            # --- SECTION 3: STRATEGIC RECOMMENDATIONS ---
            pdf.set_text_color(128, 0, 32)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt="3. STRATEGIC RECOMMENDATIONS", ln=True)
            pdf.set_text_color(40, 40, 40)
            pdf.set_font("Arial", '', 11)
            
            recs = [
                f"- Increase frequency of {best_fmt} content production.",
                f"- Schedule high-priority product drops on {best_day}s.",
                "- Maintain brand consistency for recognition.",
                "- Optimize caption strategy to boost engagement."
            ]
            for rec in recs:
                pdf.multi_cell(0, 8, txt=rec)
            pdf.ln(10)

            # --- SECTION 4: SUCCESS MESSAGE ---
            pdf.set_fill_color(255, 245, 245)
            pdf.rect(10, pdf.get_y(), 190, 35, 'F')
            pdf.set_y(pdf.get_y() + 5)
            pdf.set_font("Arial", 'B', 12)
            pdf.set_text_color(128, 0, 32)
            pdf.cell(0, 10, txt=f"Best of Luck, {business_name}!", ln=True, align='C')
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(40, 40, 40)
            msg = ("Consistency is key to digital growth. Use these insights to optimize "
                    "your social media presence. We look forward to your future growth!")
            pdf.multi_cell(0, 7, txt=msg, align='C')

            # --- OUTPUT FIX ---
            pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
            b64 = base64.b64encode(pdf_bytes).decode()
            
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{business_name}_Report.pdf" style="text-decoration:none;"><button style="background-color:#800020; color:white; padding:15px 30px; border:none; border-radius:30px; cursor:pointer; width:100%; font-size:18px; font-weight:bold;">Download Full Audit Report</button></a>'
            
            st.markdown(href, unsafe_allow_html=True)
            st.success("Analysis Complete! Your corporate audit is ready.")

        except Exception as e:
            st.error(f"Generation Error: {e}")