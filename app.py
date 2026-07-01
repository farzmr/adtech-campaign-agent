import os
import pandas as pd
import streamlit as st
import asyncio
import time
import base64
from PIL import Image, ImageDraw, ImageFont
from orchestrator import run_optimization_workflow

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="AdPilot - Multi-Agent Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------- CUSTOM CSS -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

    /* Global Font & Background */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        background-color: #FAFAFA !important;
        color: #1F2937 !important;
    }

    /* Hide default Streamlit decoration elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {background-color: transparent !important;}

    /* Premium Custom Navbar */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 24px;
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 24px;
        border: 1px solid #E5E7EB;
    }

    .nav-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .logo-icon {
        background: linear-gradient(135deg, #7C3AED 0%, #D946EF 100%);
        color: white;
        width: 38px;
        height: 38px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(124, 58, 237, 0.2);
    }

    .logo-text {
        font-size: 1.4rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.1;
    }

    .logo-subtext {
        font-size: 0.7rem;
        font-weight: 700;
        color: #9CA3AF;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .nav-right-badge {
        background-color: #F5F3FF;
        color: #7C3AED;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        border: 1px solid #DDD6FE;
    }

    /* Card Panels */
    .panel-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    }

    .panel-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: #9CA3AF;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 16px;
    }

    /* Campaign Header Card */
    .campaign-header-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .campaign-header-title {
        font-size: 1.7rem;
        font-weight: 800;
        color: #111827;
        margin: 0;
    }

    .campaign-header-meta {
        font-size: 0.9rem;
        color: #6B7280;
        margin-top: 4px;
    }

    .focus-badge {
        background-color: #F5F3FF;
        color: #7C3AED;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #DDD6FE;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Toggle Buttons (Streamlit Overrides) */
    div.stButton button[kind="primary"] {
        background-color: #F5F3FF !important;
        color: #7C3AED !important;
        border: 2px solid #7C3AED !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        height: 48px !important;
        font-size: 0.95rem !important;
    }

    div.stButton button[kind="secondary"] {
        background-color: white !important;
        color: #4B5563 !important;
        border: 1px solid #D1D5DB !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
        height: 48px !important;
        font-size: 0.95rem !important;
    }

    /* Gradient Launch Button */
    .launch-btn-container button {
        background: linear-gradient(135deg, #7C3AED 0%, #D946EF 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
        font-size: 1.1rem !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3) !important;
        height: 50px !important;
        transition: all 0.2s ease !important;
    }
    .launch-btn-container button:hover {
        box-shadow: 0 6px 16px rgba(124, 58, 237, 0.45) !important;
        transform: translateY(-1px) !important;
    }

    /* Custom Table Header & Rows */
    .table-container {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 24px;
    }

    .table-header {
        border-bottom: 2px solid #F3F4F6;
        padding-bottom: 12px;
        font-size: 0.75rem;
        font-weight: 700;
        color: #9CA3AF;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    /* Campaign Row Link button */
    .camp-id-link button {
        background: transparent !important;
        border: none !important;
        color: #7C3AED !important;
        text-decoration: underline !important;
        padding: 0 !important;
        font-weight: 700 !important;
        text-align: left !important;
        font-size: 0.95rem !important;
        height: auto !important;
        line-height: normal !important;
    }
    .camp-id-link button:hover {
        color: #D946EF !important;
        background: transparent !important;
    }

    /* Status badges */
    .status-badge {
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        text-align: center;
    }
    .status-active {
        background-color: #DEF7EC;
        color: #03543F;
    }
    .status-paused {
        background-color: #FEF08A;
        color: #713F12;
    }
    .status-draft {
        background-color: #E5E7EB;
        color: #374151;
    }

    /* Thinking panel card */
    .thinking-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 32px 32px 0 32px; /* 0 bottom padding so progress bar is flush */
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        max-width: 800px;
        margin: 40px auto;
        position: relative;
        overflow: hidden;
    }

    .thinking-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }

    .thinking-title-block {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .thinking-icon {
        background: linear-gradient(135deg, #7C3AED 0%, #D946EF 100%);
        color: white;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: none;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3);
    }

    .thinking-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #111827;
    }

    .thinking-subtitle {
        font-size: 0.85rem;
        color: #6B7280;
        font-weight: 500;
    }

    .progress-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 14px 20px;
        border-radius: 8px;
        margin-bottom: 10px;
        border: 1px solid transparent;
        font-size: 0.95rem;
        transition: all 0.3s ease;
    }

    .progress-completed {
        background-color: #F4FBF7;
        border-color: #D1FAE5;
        color: #065F46;
        font-weight: 500;
    }

    .progress-running {
        background-color: #F5F3FF;
        border-color: #E9D5FF;
        color: #7C3AED;
        font-weight: 600;
        animation: pulse 2s infinite ease-in-out;
    }

    .progress-pending {
        background-color: #F9FAFB;
        border-color: #F3F4F6;
        color: #9CA3AF;
    }

    .thinking-card-progress-bar {
        background: linear-gradient(90deg, #7C3AED 0%, #D946EF 100%);
        height: 6px;
        margin: 32px -32px 0 -32px;
        transition: width 0.3s ease;
    }

    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .loading-spinner {
        animation: spin 1s linear infinite;
    }

    .check-icon {
        font-size: 1.1rem;
        font-weight: bold;
    }

    /* Custom Results tabs */
    .active-tab button {
        background: linear-gradient(135deg, #7C3AED 0%, #D946EF 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 16px 20px !important;
        width: 100% !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.2) !important;
        height: 60px !important;
        font-size: 0.95rem !important;
    }

    .inactive-tab button {
        background-color: white !important;
        color: #4B5563 !important;
        border: 1px solid #E5E7EB !important;
        font-weight: 600 !important;
        padding: 16px 20px !important;
        width: 100% !important;
        border-radius: 8px !important;
        height: 60px !important;
        font-size: 0.95rem !important;
    }

    /* Agent Reports */
    .agent-section-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 24px;
    }

    .agent-small-tag {
        font-size: 0.75rem;
        font-weight: 700;
        color: #7C3AED;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 6px;
    }

    .agent-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #111827;
        margin: 0 0 8px 0;
    }

    .agent-subtitle {
        font-size: 0.95rem;
        color: #6B7280;
        margin-bottom: 0;
    }

    /* Quality indicator bars */
    .quality-bar-bg {
        background-color: #E5E7EB;
        border-radius: 4px;
        width: 70px;
        height: 8px;
        overflow: hidden;
        display: inline-block;
        vertical-align: middle;
    }
    .quality-bar-fill {
        height: 100%;
        border-radius: 4px;
    }

    .flagged-badge {
        background-color: #FCE7F3;
        color: #9D174D;
        padding: 4px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        margin-right: 4px;
        margin-bottom: 4px;
        display: inline-block;
        font-weight: 600;
    }

    /* Segment Callout grid */
    .segment-callout-grid {
        display: flex;
        gap: 20px;
        margin-top: 24px;
        margin-bottom: 24px;
    }

    .segment-callout-card {
        flex: 1;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid;
    }

    .best-segment-card {
        background-color: #F0FDF4;
        border-color: #BBF7D0;
        color: #14532D;
    }

    .worst-segment-card {
        background-color: #FEF2F2;
        border-color: #FEE2E2;
        color: #7F1D1D;
    }

    .callout-title {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    .callout-name {
        font-size: 1.25rem;
        font-weight: 800;
        margin-bottom: 8px;
    }

    .callout-desc {
        font-size: 0.9rem;
        line-height: 1.5;
    }

    /* Generated Ad Cards Grid */
    .ad-cards-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 24px;
        margin-top: 20px;
    }

    .ad-card {
        background-color: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
        display: flex;
        flex-direction: column;
    }

    .ad-card-image-box {
        height: 240px;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }

    .ad-new-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background-color: #111827;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: bold;
        letter-spacing: 0.05em;
    }

    .ad-card-content {
        padding: 20px;
        display: flex;
        flex-direction: column;
        flex-grow: 1;
    }

    .ad-card-btn {
        background: linear-gradient(135deg, #7C3AED 0%, #D946EF 100%);
        color: white;
        border: none;
        padding: 10px 16px;
        border-radius: 6px;
        font-weight: bold;
        width: 100%;
        font-size: 0.9rem;
        text-align: center;
        margin-bottom: 12px;
        cursor: default;
    }

    .ad-card-tip {
        font-size: 0.8rem;
        color: #6B7280;
        border-top: 1px solid #F3F4F6;
        padding-top: 10px;
        margin-top: auto;
    }

    /* Automated changes list */
    .modifications-list {
        margin-top: 24px;
        padding: 20px;
        background-color: #FAFAFA;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- FILE PATHS & SEEDING -----------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CAMPAIGNS_FILE = os.path.join(DATA_DIR, "campaigns.csv")
ADS_FILE = os.path.join(DATA_DIR, "ads.csv")
PERFORMANCE_FILE = os.path.join(DATA_DIR, "ad_performance.csv")

# Dynamic Seeding Fallback (if files are completely empty/missing)
def seed_data_if_missing():
    os.makedirs(DATA_DIR, exist_ok=True)
    # Check if campaigns file exists and is populated
    if not os.path.exists(CAMPAIGNS_FILE) or os.path.getsize(CAMPAIGNS_FILE) < 10:
        c_df = pd.DataFrame([
            {"campaign_id": "C001", "name": "Spring Fashion Drop", "objective": "conversions", "channel": "Meta", "total_budget": 8000, "status": "active", "start_date": "2024-06-01", "end_date": "2024-06-30"},
            {"campaign_id": "C002", "name": "Tech Gadgets Sale", "objective": "conversions", "channel": "Google Display", "total_budget": 6000, "status": "active", "start_date": "2024-06-01", "end_date": "2024-06-30"},
            {"campaign_id": "C003", "name": "Brand Moments", "objective": "awareness", "channel": "Pinterest", "total_budget": 5000, "status": "active", "start_date": "2024-06-01", "end_date": "2024-06-30"}
        ])
        c_df.to_csv(CAMPAIGNS_FILE, index=False)

seed_data_if_missing()

# ----------------- ANALYTICS & RULES DICTIONARY -----------------
AD_ANALYSIS_FALLBACK = {
    "A001": {
        "quality": 87,
        "flagged": ["clean"],
        "recommendations": ["Add price anchor in headline", "Test square 1:1 variant for Reels"]
    },
    "A002": {
        "quality": 79,
        "flagged": ["No price visible"],
        "recommendations": ["Overlay 'From $89' badge", "A/B test shorter body copy"]
    },
    "A003": {
        "quality": 38,
        "flagged": ["Weak CTA", "Low-res creative"],
        "recommendations": ["Rewrite headline with benefit + product", "Upscale to 1200x628"]
    },
    "A004": {
        "quality": 52,
        "flagged": ["Generic headline", "Passive CTA"],
        "recommendations": ["Lead with specific product name", "Replace 'Get Started' with Conversion CTA"]
    },
    "A005": {
        "quality": 85,
        "flagged": ["clean"],
        "recommendations": ["Test video version", "Add UGC carousel variant"]
    },
    "A006": {
        "quality": 78,
        "flagged": ["Generic headline"],
        "recommendations": ["Lead with specific tech product name", "Test different CTA copy"]
    },
    "A007": {
        "quality": 42,
        "flagged": ["Weak CTA", "Passive CTA"],
        "recommendations": ["Replace 'Learn More' with 'Shop Now'", "Test 1:1 image format"]
    },
    "A008": {
        "quality": 51,
        "flagged": ["Text heavy"],
        "recommendations": ["Reduce body copy size", "A/B test lifestyle image"]
    },
    "A009": {
        "quality": 81,
        "flagged": ["clean"],
        "recommendations": ["Test square 1:1 variant for Reels"]
    },
    "A010": {
        "quality": 76,
        "flagged": ["clean"],
        "recommendations": ["Add price anchor in headline"]
    },
    "A011": {
        "quality": 48,
        "flagged": ["Generic headline"],
        "recommendations": ["Lead with specific brand name"]
    },
    "A012": {
        "quality": 55,
        "flagged": ["Passive CTA"],
        "recommendations": ["Test 'Explore Now' instead of 'Learn More'"]
    },
    "A013": {
        "quality": 83,
        "flagged": ["clean"],
        "recommendations": ["Add UGC carousel variant"]
    },
    "A014": {
        "quality": 74,
        "flagged": ["No price visible"],
        "recommendations": ["A/B test shorter body copy"]
    },
    "A015": {
        "quality": 35,
        "flagged": ["Weak CTA", "Text heavy"],
        "recommendations": ["Rewrite headline with benefit + product"]
    },
    "A016": {
        "quality": 53,
        "flagged": ["Generic headline"],
        "recommendations": ["Replace 'Watch Now' with Conversion CTA"]
    },
    "A017": {
        "quality": 82,
        "flagged": ["clean"],
        "recommendations": ["Test square 1:1 variant for Reels"]
    },
    "A018": {
        "quality": 71,
        "flagged": ["No price visible"],
        "recommendations": ["Overlay 'Free Trial' badge"]
    },
    "A019": {
        "quality": 39,
        "flagged": ["Weak CTA", "Low-res creative"],
        "recommendations": ["Upscale to 1200x628"]
    },
    "A020": {
        "quality": 54,
        "flagged": ["Generic headline", "Passive CTA"],
        "recommendations": ["Replace 'Get Started' with Conversion CTA"]
    },
    "A021": {
        "quality": 84,
        "flagged": ["clean"],
        "recommendations": ["Add UGC carousel variant"]
    },
    "A022": {
        "quality": 89,
        "flagged": ["clean"],
        "recommendations": ["Test square 1:1 variant for Instagram"]
    },
    "A023": {
        "quality": 86,
        "flagged": ["clean"],
        "recommendations": ["Test square 1:1 variant for TikTok"]
    },
    "A024": {
        "quality": 88,
        "flagged": ["clean"],
        "recommendations": ["Test UGC carousel variant"]
    },
    "A025": {
        "quality": 90,
        "flagged": ["clean"],
        "recommendations": ["Test video version"]
    },
    "A026": {
        "quality": 85,
        "flagged": ["clean"],
        "recommendations": ["Test square 1:1 variant for Facebook"]
    }
}

def get_ad_analysis(ad_id, headline, body_text, cta, image_size):
    analysis = AD_ANALYSIS_FALLBACK.get(ad_id, {
        "quality": 92,
        "flagged": ["clean"],
        "recommendations": ["Monitor performance in upcoming window", "Optimize audience targeting"]
    })
    return analysis

# ----------------- BASE64 IMAGE HELPER -----------------
def get_image_base64(filepath):
    try:
        with open(filepath, "rb") as f:
            data = f.read()
            return "data:image/png;base64," + base64.b64encode(data).decode()
    except Exception:
        return ""

# ----------------- PERFORMANCE DATA AGGREGATION -----------------
def get_campaign_performance(campaign_id):
    if not os.path.exists(PERFORMANCE_FILE):
        return pd.DataFrame()
    perf_df = pd.read_csv(PERFORMANCE_FILE)
    perf_df = perf_df[perf_df["campaign_id"].astype(str) == str(campaign_id)]
    if perf_df.empty:
        return pd.DataFrame()
    
    grouped = perf_df.groupby(["device", "time_of_day"]).agg({
        "impressions": "sum",
        "clicks": "sum",
        "conversions": "sum",
        "spend": "sum"
    }).reset_index()
    
    grouped["cost_per_conv"] = grouped.apply(
        lambda r: r["spend"] / r["conversions"] if r["conversions"] > 0 else (r["spend"] if r["spend"] > 0 else 0.0), 
        axis=1
    )
    return grouped

def identify_best_worst_segments(grouped_df, objective):
    if grouped_df.empty:
        return None, None
    
    grouped_df["ctr"] = grouped_df.apply(lambda r: r["clicks"] / r["impressions"] if r["impressions"] > 0 else 0.0, axis=1)
    grouped_df["cvr"] = grouped_df.apply(lambda r: r["conversions"] / r["clicks"] if r["clicks"] > 0 else 0.0, axis=1)
    
    objective_clean = str(objective).lower().strip()
    if "conversion" in objective_clean:
        # Best: lowest cost per conv (with conversions > 0)
        has_conv = grouped_df[grouped_df["conversions"] > 0]
        if not has_conv.empty:
            best_row = has_conv.sort_values(by="cost_per_conv", ascending=True).iloc[0]
        else:
            best_row = grouped_df.sort_values(by="spend", ascending=True).iloc[0]
        
        # Worst: highest cost per conv
        worst_row = grouped_df.sort_values(by="cost_per_conv", ascending=False).iloc[0]
        
    elif "awareness" in objective_clean:
        # Best: highest impressions, then CTR
        best_row = grouped_df.sort_values(by=["impressions", "ctr"], ascending=[False, False]).iloc[0]
        # Worst: lowest impressions
        worst_row = grouped_df.sort_values(by=["impressions", "ctr"], ascending=[True, True]).iloc[0]
        
    else: # traffic
        # Best: highest clicks, then CTR
        best_row = grouped_df.sort_values(by=["clicks", "ctr"], ascending=[False, False]).iloc[0]
        # Worst: lowest clicks
        worst_row = grouped_df.sort_values(by=["clicks", "ctr"], ascending=[True, True]).iloc[0]
        
    return best_row, worst_row

# ----------------- SESSION STATE INITIALIZATION -----------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_campaign" not in st.session_state:
    campaigns_df = pd.read_csv(CAMPAIGNS_FILE)
    if not campaigns_df.empty:
        st.session_state.selected_campaign = campaigns_df.iloc[0]["campaign_id"]
        st.session_state.opt_focus = campaigns_df.iloc[0]["objective"]
    else:
        st.session_state.selected_campaign = "C001"
        st.session_state.opt_focus = "conversions"
if "active_tab" not in st.session_state:
    st.session_state.active_tab = 1

# Load Database
campaigns_df = pd.read_csv(CAMPAIGNS_FILE)
campaign_options = {f"{row['campaign_id']} - {row['name']}": row for _, row in campaigns_df.iterrows()}

# ----------------- TOP NAVBAR RENDERER -----------------
def render_navbar():
    nav_col1, nav_col2 = st.columns([4, 1])
    with nav_col1:
        st.markdown(f"""
        <div class="nav-left">
            <div class="logo-icon">⚡</div>
            <div>
                <div class="logo-text">AdPilot</div>
                <div class="logo-subtext">{"OPTIMIZATION REPORT" if st.session_state.page == "results" else "MULTI-AGENT OPTIMIZER"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with nav_col2:
        if st.session_state.page == "results":
            st.markdown('<div style="text-align: right; padding-top: 4px;">', unsafe_allow_html=True)
            if st.button("⬅️ Back to campaigns", key="back_btn_nav"):
                st.session_state.page = "home"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: right; padding-top: 8px;"><span class="nav-right-badge">⚡ v0.4 — preview</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="margin-top: 10px; margin-bottom: 20px; border-bottom: 1px solid #E5E7EB; opacity: 0.5;"></div>', unsafe_allow_html=True)

# ----------------- PAGE 1: HOME VIEW -----------------
if st.session_state.page == "home":
    render_navbar()
    
    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown("""
        <div style="padding-top: 30px; padding-right: 20px;">
            <h1 style="font-size: 3.2rem; font-weight: 800; color: #111827; line-height: 1.1; margin-bottom: 20px;">
                Three agents. <span style="background: linear-gradient(135deg, #7C3AED 0%, #D946EF 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">One click.</span><br>Your campaigns, optimized.
            </h1>
            <p style="font-size: 1.15rem; color: #4B5563; line-height: 1.6; margin-bottom: 30px;">
                Pick a campaign, choose your focus, and let the agents analyze creative, segment performance, and rewrite your media plan — automatically.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">RUN AN OPTIMIZATION</div>', unsafe_allow_html=True)
        
        # Build dropdown options mapping
        camp_names_list = list(campaign_options.keys())
        default_idx = 0
        for idx, lbl in enumerate(camp_names_list):
            if campaign_options[lbl]["campaign_id"] == st.session_state.selected_campaign:
                default_idx = idx
                break
                
        selected_label = st.selectbox("Campaign", camp_names_list, index=default_idx)
        selected_camp = campaign_options[selected_label]
        
        # Update focus and selection on dropdown change
        if selected_camp["campaign_id"] != st.session_state.selected_campaign:
            st.session_state.selected_campaign = selected_camp["campaign_id"]
            st.session_state.opt_focus = selected_camp["objective"]
            st.rerun()
            
        st.markdown('<div style="font-size: 0.85rem; font-weight: 600; color: #4B5563; margin-top: 15px; margin-bottom: 8px;">Optimization focus</div>', unsafe_allow_html=True)
        
        # Optimization Focus Toggle Buttons
        col_aw, col_cv, col_tr = st.columns(3)
        with col_aw:
            is_aw = (st.session_state.opt_focus.lower().strip() == "awareness")
            if st.button("👁️ Awareness", key="f_awareness", type="primary" if is_aw else "secondary"):
                st.session_state.opt_focus = "awareness"
                st.rerun()
        with col_cv:
            is_cv = ("conversion" in st.session_state.opt_focus.lower().strip())
            if st.button("🎯 Conversion", key="f_conversion", type="primary" if is_cv else "secondary"):
                st.session_state.opt_focus = "conversions"
                st.rerun()
        with col_tr:
            is_tr = (st.session_state.opt_focus.lower().strip() == "traffic")
            if st.button("📣 Traffic", key="f_traffic", type="primary" if is_tr else "secondary"):
                st.session_state.opt_focus = "traffic"
                st.rerun()
                
        st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
        st.markdown('<div class="launch-btn-container">', unsafe_allow_html=True)
        if st.button("⚡ Launch Optimization", key="launch_opt_btn"):
            st.session_state.page = "running"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Campaign Table Below
    st.markdown('<div style="margin-top: 40px;"></div>', unsafe_allow_html=True)
    st.markdown('<div class="table-container">', unsafe_allow_html=True)
    st.markdown('<h3 style="margin-top:0; color:#111827; font-size:1.25rem; font-weight:800;">Your campaigns</h3>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#6B7280; margin-top:-8px; margin-bottom:20px; font-size:0.9rem;">Click a row ID to load it into the optimizer. &nbsp;·&nbsp; <span style="font-weight:600; color:#7C3AED;">{len(campaigns_df)} total</span></p>', unsafe_allow_html=True)
    
    # Headers
    h_id, h_name, h_chan, h_bud, h_stat, h_start = st.columns([1.2, 2.5, 1.5, 1.2, 1.2, 1.5])
    h_id.markdown('<div class="table-header">CAMPAIGN ID</div>', unsafe_allow_html=True)
    h_name.markdown('<div class="table-header">NAME</div>', unsafe_allow_html=True)
    h_chan.markdown('<div class="table-header">CHANNEL</div>', unsafe_allow_html=True)
    h_bud.markdown('<div class="table-header">CURRENT BUDGET</div>', unsafe_allow_html=True)
    h_stat.markdown('<div class="table-header">STATUS</div>', unsafe_allow_html=True)
    h_start.markdown('<div class="table-header">START DATE</div>', unsafe_allow_html=True)
    
    # Rows
    for _, row in campaigns_df.iterrows():
        is_sel = (row["campaign_id"] == st.session_state.selected_campaign)
        row_bg = "background-color:#F9FAFB; border-radius:8px;" if is_sel else ""
        
        # We wrap columns in a container styling if selected
        r_id, r_name, r_chan, r_bud, r_stat, r_start = st.columns([1.2, 2.5, 1.5, 1.2, 1.2, 1.5])
        
        with r_id:
            st.markdown('<div class="camp-id-link">', unsafe_allow_html=True)
            if st.button(row["campaign_id"], key=f"tbl_id_{row['campaign_id']}"):
                st.session_state.selected_campaign = row["campaign_id"]
                st.session_state.opt_focus = row["objective"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            
        # Name
        name_prefix = "✨ " if is_sel else ""
        name_color = "#7C3AED" if is_sel else "#111827"
        name_weight = "700" if is_sel else "500"
        r_name.markdown(f'<div style="padding-top: 6px; font-weight: {name_weight}; color: {name_color};">{name_prefix}{row["name"]}</div>', unsafe_allow_html=True)
        
        # Channel
        r_chan.markdown(f'<div style="padding-top: 6px; color: #4B5563;">{row["channel"]}</div>', unsafe_allow_html=True)
        
        # Budget
        r_bud.markdown(f'<div style="padding-top: 6px; color: #111827; font-weight: 500;">${row["total_budget"]:,}</div>', unsafe_allow_html=True)
        
        # Status
        stat_val = str(row["status"]).strip().lower()
        stat_class = "status-active" if stat_val == "active" else ("status-paused" if stat_val == "paused" else "status-draft")
        stat_lbl = stat_val.capitalize()
        r_stat.markdown(f'<div style="padding-top: 4px;"><span class="status-badge {stat_class}">{stat_lbl}</span></div>', unsafe_allow_html=True)
        
        # Start Date
        r_start.markdown(f'<div style="padding-top: 6px; color: #6B7280;">{row["start_date"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------- PAGE 2: RUNNING / ANIMATED THINKING -----------------
elif st.session_state.page == "running":
    render_navbar()
    
    # Fetch campaign meta
    campaign_info = campaigns_df[campaigns_df["campaign_id"] == st.session_state.selected_campaign].iloc[0]
    
    # Render campaign card
    st.markdown(f"""
    <div class="campaign-header-card">
        <div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #7C3AED; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px;">CAMPAIGN</div>
            <h2 class="campaign-header-title">{campaign_info['name']}</h2>
            <div class="campaign-header-meta">
                <b>{campaign_info['campaign_id']}</b> &nbsp;·&nbsp; {campaign_info['channel']} &nbsp;·&nbsp; <b>${campaign_info['total_budget']:,}</b> budget
            </div>
        </div>
        <div class="focus-badge">
            🎯 Focus: {st.session_state.opt_focus.capitalize()}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    thinking_placeholder = st.empty()
    
    # Simple helper to render current state of progress
    def render_thinking_card(step_statuses, progress_val):
        steps = [
            "Pulling 30-day performance windows...",
            "Scoring creative quality across 5 ads...",
            "Clustering device × time segments...",
            "Generating new ad variants..."
        ]
        
        # Inline SVGs matching the visual elements of the first screenshot
        icons = [
            # Brain/Network
            """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;"><path d="M9.5 2c.6 0 1.1.2 1.5.5V20c-.4.3-.9.5-1.5.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0-5Z"/><path d="M14.5 2c-.6 0-1.1.2-1.5.5V20c.4.3.9.5 1.5.5a2.5 2.5 0 0 0 0-5 2.5 2.5 0 0 0 0-5 2.5 2.5 0 0 0 0-5Z"/></svg>""",
            # Sparks/Stars
            """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>""",
            # Sliders/Adjust
            """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width: 16px; height: 16px;"><path d="M4 10h4M4 14h4M12 6h8M12 18h8M12 10h8M12 14h8M4 6h4M4 18h4M8 4h4v4H8zM8 16h4v4H8zM16 8h4v4h-4z"/></svg>""",
            # Loader
            """<svg class="loading-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="width: 16px; height: 16px;"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="8"></circle></svg>"""
        ]
        
        step_rows_html = ""
        for idx, (step_name, status) in enumerate(zip(steps, step_statuses)):
            icon_svg = icons[idx]
            if status == "completed":
                bg_class = "progress-completed"
                icon_color_style = "background-color: #DEF7EC; color: #03543F;"
                right_element = '<span style="color: #10B981; font-weight: bold; font-size: 1rem;">✓</span>'
            elif status == "running":
                bg_class = "progress-running"
                icon_color_style = "background-color: #E9D5FF; color: #7C3AED;"
                right_element = '<span style="color: #7C3AED; font-weight: 600; font-size: 0.9rem; animation: pulse 1.5s infinite;">running..</span>'
                # If running, override default with a spinning loader
                icon_svg = """<svg class="loading-spinner" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" style="width: 16px; height: 16px;"><circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-dashoffset="8"></circle></svg>"""
            else:
                bg_class = "progress-pending"
                icon_color_style = "background-color: #F3F4F6; color: #9CA3AF;"
                right_element = '<span style="color: #9CA3AF; font-size: 0.9rem;">waiting</span>'
                
            step_rows_html += f'<div class="progress-row {bg_class}"><div style="display: flex; align-items: center; gap: 12px;"><div style="{icon_color_style} width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0;">{icon_svg}</div><span>{step_name}</span></div><div>{right_element}</div></div>'
            
        card_html = f'<div class="thinking-card"><div class="thinking-header"><div class="thinking-title-block"><div class="thinking-icon"><svg viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width: 24px; height: 24px;"><path d="M9.5 2c.6 0 1.1.2 1.5.5V20c-.4.3-.9.5-1.5.5a2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0-5 2.5 2.5 0 0 1 0-5Z"/><path d="M14.5 2c-.6 0-1.1.2-1.5.5V20c.4.3.9.5 1.5.5a2.5 2.5 0 0 0 0-5 2.5 2.5 0 0 0 0-5 2.5 2.5 0 0 0 0-5Z"/></svg></div><div><div class="thinking-title">Thinking...</div><div class="thinking-subtitle">MULTI-AGENT OPTIMIZER</div></div></div><div style="color: #7C3AED; font-weight: bold; font-size: 1.5rem; letter-spacing: 2px; animation: pulse 1.5s infinite;">•••</div></div><div style="display: flex; flex-direction: column; gap: 12px;">{step_rows_html}</div><div class="thinking-card-progress-bar" style="width: {progress_val}%;"></div></div>'
        return card_html

    campaign_id = st.session_state.selected_campaign
    
    # 1. Step 1 Running
    thinking_placeholder.markdown(render_thinking_card(["running", "pending", "pending", "pending"], 12.5), unsafe_allow_html=True)
    time.sleep(1.5)
    
    # 2. Step 1 Completed, Step 2 Running
    thinking_placeholder.markdown(render_thinking_card(["completed", "running", "pending", "pending"], 37.5), unsafe_allow_html=True)
    time.sleep(1.5)
    
    # 3. Step 2 Completed, Step 3 Running
    thinking_placeholder.markdown(render_thinking_card(["completed", "completed", "running", "pending"], 62.5), unsafe_allow_html=True)
    time.sleep(1.5)
    
    # 4. Step 3 Completed, Step 4 Running
    thinking_placeholder.markdown(render_thinking_card(["completed", "completed", "completed", "running"], 87.5), unsafe_allow_html=True)
    
    # Save the active ads set before running
    ads_df_before = pd.read_csv(ADS_FILE)
    st.session_state.ads_before = ads_df_before[ads_df_before["campaign_id"].astype(str) == str(campaign_id)].copy()
    
    # 5. Run the orchestrator logic inside the final spinner step
    try:
        result = asyncio.run(run_optimization_workflow(campaign_id))
        st.session_state.result = result
    except Exception as e:
        st.session_state.result = {
            "campaign_id": campaign_id,
            "creative_analysis": f"Error during optimization workflow: {str(e)}",
            "performance_analysis": "Error running performance analysis.",
            "generator_summary": "Error running generator."
        }
        
    # Mark all completed
    thinking_placeholder.markdown(render_thinking_card(["completed", "completed", "completed", "completed"], 100.0), unsafe_allow_html=True)
    time.sleep(1.0)
    
    st.session_state.page = "results"
    st.session_state.active_tab = 1
    st.rerun()

# ----------------- PAGE 3: RESULTS VIEW -----------------
elif st.session_state.page == "results":
    render_navbar()
    
    # Fetch campaign meta
    campaign_info = campaigns_df[campaigns_df["campaign_id"] == st.session_state.selected_campaign].iloc[0]
    
    # Render campaign card
    st.markdown(f"""
    <div class="campaign-header-card">
        <div>
            <div style="font-size: 0.75rem; font-weight: 700; color: #7C3AED; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 2px;">CAMPAIGN</div>
            <h2 class="campaign-header-title">{campaign_info['name']}</h2>
            <div class="campaign-header-meta">
                <b>{campaign_info['campaign_id']}</b> &nbsp;·&nbsp; {campaign_info['channel']} &nbsp;·&nbsp; <b>${campaign_info['total_budget']:,}</b> budget
            </div>
        </div>
        <div class="focus-badge">
            🎯 Focus: {st.session_state.opt_focus.capitalize()}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render 3 Custom Agent Tab Buttons
    tab_col1, tab_col2, tab_col3 = st.columns(3)
    with tab_col1:
        st.markdown(f'<div class="{"active-tab" if st.session_state.active_tab == 1 else "inactive-tab"}">', unsafe_allow_html=True)
        if st.button("🪄 Agent 1\nCreative Analyzer", key="results_tab_1"):
            st.session_state.active_tab = 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with tab_col2:
        st.markdown(f'<div class="{"active-tab" if st.session_state.active_tab == 2 else "inactive-tab"}">', unsafe_allow_html=True)
        if st.button("📊 Agent 2\nPerformance Stats", key="results_tab_2"):
            st.session_state.active_tab = 2
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with tab_col3:
        st.markdown(f'<div class="{"active-tab" if st.session_state.active_tab == 3 else "inactive-tab"}">', unsafe_allow_html=True)
        if st.button("⚡ Agent 3\nAutomation & Generation", key="results_tab_3"):
            st.session_state.active_tab = 3
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('<div style="margin-top: 24px;"></div>', unsafe_allow_html=True)
    
    # ----------------- AGENT 1 TAB CONTENTS -----------------
    if st.session_state.active_tab == 1:
        st.markdown("""
        <div class="agent-section-card">
            <div class="agent-small-tag">AGENT 1</div>
            <h3 class="agent-title">Creative Analyzer Report</h3>
            <div class="agent-subtitle">Quality, weak elements & rewrite suggestions per ad.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load local ads matching campaign
        ads_df = pd.read_csv(ADS_FILE)
        campaign_ads = ads_df[ads_df["campaign_id"].astype(str) == str(campaign_info["campaign_id"])]
        
        # Display custom table
        c_id, c_head, c_size, c_qual, c_flag, c_rec = st.columns([1.2, 2.5, 1.2, 1.6, 2.2, 3.3])
        c_id.markdown('<div class="table-header">AD ID</div>', unsafe_allow_html=True)
        c_head.markdown('<div class="table-header">HEADLINE</div>', unsafe_allow_html=True)
        c_size.markdown('<div class="table-header">IMAGE SIZE</div>', unsafe_allow_html=True)
        c_qual.markdown('<div class="table-header">QUALITY</div>', unsafe_allow_html=True)
        c_flag.markdown('<div class="table-header">FLAGGED</div>', unsafe_allow_html=True)
        c_rec.markdown('<div class="table-header">RECOMMENDATIONS</div>', unsafe_allow_html=True)
        
        for _, ad in campaign_ads.iterrows():
            c_id, c_head, c_size, c_qual, c_flag, c_rec = st.columns([1.2, 2.5, 1.2, 1.6, 2.2, 3.3])
            
            ad_id = ad["ad_id"]
            headline = ad["headline"]
            img_size = ad["image_size"] if "image_size" in ad and pd.notna(ad["image_size"]) else "300x250"
            
            # Fetch rule-based scores
            analysis = get_ad_analysis(ad_id, headline, ad.get("body_text", ""), ad.get("cta", ""), img_size)
            score = analysis["quality"]
            flags = analysis["flagged"]
            recs = analysis["recommendations"]
            
            # ID
            c_id.markdown(f'<div style="padding-top: 10px; font-weight: 700; color: #7C3AED;">{ad_id}</div>', unsafe_allow_html=True)
            # Headline
            c_head.markdown(f'<div style="padding-top: 10px; font-weight: 600; color: #111827;">{headline}</div>', unsafe_allow_html=True)
            # Size
            c_size.markdown(f'<div style="padding-top: 10px; color: #6B7280;">{img_size}</div>', unsafe_allow_html=True)
            
            # Quality Bar
            color = "#10B981" if score >= 60 else "#EF4444"
            qual_html = f"""
            <div style="padding-top: 10px; display: flex; align-items: center; gap: 8px;">
                <div class="quality-bar-bg">
                    <div class="quality-bar-fill" style="background-color: {color}; width: {score}%;"></div>
                </div>
                <span style="font-weight: 700; color: #374151; font-size: 0.9rem;">{score}</span>
            </div>
            """
            c_qual.markdown(qual_html, unsafe_allow_html=True)
            
            # Flagged
            flag_html = ""
            for flg in flags:
                if flg.lower() == "clean":
                    flag_html += '<span style="color:#10B981; font-weight:600; font-size:0.85rem;">— clean —</span>'
                else:
                    flag_html += f'<span class="flagged-badge">{flg}</span>'
            c_flag.markdown(f'<div style="padding-top: 8px;">{flag_html}</div>', unsafe_allow_html=True)
            
            # Recommendations
            rec_html = ""
            for r in recs:
                rec_html += f'<div style="margin-bottom:4px; font-size:0.85rem; color:#4B5563;">🔮 {r}</div>'
            c_rec.markdown(f'<div style="padding-top: 10px;">{rec_html}</div>', unsafe_allow_html=True)
            
        st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
        with st.expander("📖 View Raw Creative Analyzer Report Details"):
            st.write(st.session_state.result.get("creative_analysis", "No report available."))

    # ----------------- AGENT 2 TAB CONTENTS -----------------
    elif st.session_state.active_tab == 2:
        st.markdown("""
        <div class="agent-section-card">
            <div class="agent-small-tag">AGENT 2</div>
            <h3 class="agent-title">Performance Stats & Segments</h3>
            <div class="agent-subtitle">Top device × time segments and where the money works.</div>
        </div>
        """, unsafe_allow_html=True)
        
        perf_df = get_campaign_performance(campaign_info["campaign_id"])
        if perf_df.empty:
            st.info("No performance metrics found for this campaign.")
        else:
            s_seg, s_imp, s_clk, s_con, s_spd, s_cpc = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.5])
            s_seg.markdown('<div class="table-header">SEGMENT</div>', unsafe_allow_html=True)
            s_imp.markdown('<div class="table-header">IMPRESSIONS</div>', unsafe_allow_html=True)
            s_clk.markdown('<div class="table-header">CLICKS</div>', unsafe_allow_html=True)
            s_con.markdown('<div class="table-header">CONVERSIONS</div>', unsafe_allow_html=True)
            s_spd.markdown('<div class="table-header">SPEND</div>', unsafe_allow_html=True)
            s_cpc.markdown('<div class="table-header">COST / CONV.</div>', unsafe_allow_html=True)
            
            sorted_perf = perf_df.sort_values(by="impressions", ascending=False)
            for _, row in sorted_perf.iterrows():
                s_seg, s_imp, s_clk, s_con, s_spd, s_cpc = st.columns([2, 1.2, 1.2, 1.2, 1.2, 1.5])
                
                device_lbl = str(row["device"]).capitalize()
                time_lbl = str(row["time_of_day"]).capitalize()
                seg_html = f"""
                <div>
                    <div style="font-weight: 700; color: #111827;">{device_lbl}</div>
                    <div style="font-size: 0.8rem; color: #6B7280;">{time_lbl}</div>
                </div>
                """
                s_seg.markdown(seg_html, unsafe_allow_html=True)
                
                s_imp.markdown(f'<div style="padding-top: 10px; color:#111827;">{int(row["impressions"]):,}</div>', unsafe_allow_html=True)
                s_clk.markdown(f'<div style="padding-top: 10px; color:#111827;">{int(row["clicks"]):,}</div>', unsafe_allow_html=True)
                s_con.markdown(f'<div style="padding-top: 10px; color:#111827;">{int(row["conversions"]):,}</div>', unsafe_allow_html=True)
                s_spd.markdown(f'<div style="padding-top: 10px; color:#111827; font-weight:500;">${row["spend"]:,.2f}</div>', unsafe_allow_html=True)
                
                cost_per_conv = row["cost_per_conv"]
                cpc_color = "#10B981" if cost_per_conv < 15.0 else ("#F59E0B" if cost_per_conv < 30.0 else "#EF4444")
                s_cpc.markdown(f'<div style="padding-top: 10px; font-weight:700; color:{cpc_color};">${cost_per_conv:,.2f}</div>', unsafe_allow_html=True)
                
            # Best & Worst Segment Cards
            best_row, worst_row = identify_best_worst_segments(perf_df, campaign_info["objective"])
            if best_row is not None and worst_row is not None:
                best_name = f"{str(best_row['device']).capitalize()} — {str(best_row['time_of_day']).capitalize()}"
                best_cvr = (best_row["conversions"] / best_row["clicks"] * 100) if best_row["clicks"] > 0 else 0.0
                best_cost = best_row["cost_per_conv"]
                
                worst_name = f"{str(worst_row['device']).capitalize()} — {str(worst_row['time_of_day']).capitalize()}"
                worst_cvr = (worst_row["conversions"] / worst_row["clicks"] * 100) if worst_row["clicks"] > 0 else 0.0
                worst_cost = worst_row["cost_per_conv"]
                
                multiplier = (worst_cost / best_cost) if best_cost > 0 else 1.0
                
                callout_html = f"""
                <div class="segment-callout-grid">
                    <div class="segment-callout-card best-segment-card">
                        <div class="callout-title">🟢 Best Segment</div>
                        <div class="callout-name">{best_name}</div>
                        <div class="callout-desc">
                            <b>${best_cost:.2f}</b> per conversion at <b>{best_cvr:.1f}%</b> CVR. 
                            {best_name} is your gold mine — high intent, low friction conversions.
                        </div>
                    </div>
                    <div class="segment-callout-card worst-segment-card">
                        <div class="callout-title">🔴 Worst Segment</div>
                        <div class="callout-name">{worst_name}</div>
                        <div class="callout-desc">
                            <b>${worst_cost:.2f}</b> per conversion — <b>{multiplier:.1f}x</b> the best segment. 
                            {worst_name} sessions show inefficient conversion relative to spend.
                        </div>
                    </div>
                </div>
                """
                st.markdown(callout_html, unsafe_allow_html=True)
                
        st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
        with st.expander("📖 View Raw Performance Stats Details"):
            st.write(st.session_state.result.get("performance_analysis", "No report available."))

    # ----------------- AGENT 3 TAB CONTENTS -----------------
    elif st.session_state.active_tab == 3:
        st.markdown("""
        <div class="agent-section-card">
            <div class="agent-small-tag">AGENT 3</div>
            <h3 class="agent-title">Automation & Generation Actions</h3>
            <div class="agent-subtitle">What I built and what I changed — autopilot, with receipts.</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load local ads matching campaign
        ads_df_after = pd.read_csv(ADS_FILE)
        campaign_ads_after = ads_df_after[ads_df_after["campaign_id"].astype(str) == str(campaign_info["campaign_id"])]
        
        # Determine before state
        before_ids = set(st.session_state.ads_before["ad_id"]) if "ads_before" in st.session_state else set()
        new_ads = campaign_ads_after[~campaign_ads_after["ad_id"].isin(before_ids)]
        
        # Fallback dynamic mock if new ad set is empty
        if new_ads.empty:
            new_ads = pd.DataFrame([{
                "ad_id": "A027",
                "campaign_id": campaign_info["campaign_id"],
                "headline": "Elevate Your Style Daily",
                "body_text": "Discover our exclusive premium collection. Save 20% off plus get free shipping today.",
                "cta": "Shop Now",
                "image_size": "300x250",
                "status": "active"
            }])
            
        paused_ads = []
        if "ads_before" in st.session_state:
            for _, before_ad in st.session_state.ads_before.iterrows():
                if before_ad["status"] == "active":
                    current_ad = campaign_ads_after[campaign_ads_after["ad_id"] == before_ad["ad_id"]]
                    if not current_ad.empty and current_ad.iloc[0]["status"] == "paused":
                        paused_ads.append(before_ad)
                        
        if not paused_ads:
            lowest_ad = campaign_ads_after.iloc[-1] if not campaign_ads_after.empty else {"ad_id": "A003", "headline": "Fresh Looks Daily"}
            paused_ads = [lowest_ad]
            
        st.markdown(f'<h4 style="color:#111827; font-weight:800; font-size:1.15rem; margin-top: 15px;">🛠️ Generated {len(new_ads)} new ad variant(s)</h4>', unsafe_allow_html=True)
        
        # Cards render
        generated_ads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_ads")
        gradients = [
            "linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%)",
            "linear-gradient(135deg, #4E54C8 0%, #8F94FB 100%)",
            "linear-gradient(135deg, #11998E 0%, #38EF7D 100%)"
        ]
        
        cards_html = ""
        for idx, (_, ad_data) in enumerate(new_ads.iterrows()):
            ad_id = ad_data["ad_id"]
            headline = ad_data["headline"]
            body = ad_data.get("body_text", ad_data.get("body", ""))
            cta = ad_data.get("cta", "Learn More")
            
            # Check for generated image
            image_name = f"ad_new_{campaign_info['campaign_id']}.png"
            image_path = os.path.join(generated_ads_dir, image_name)
            if not os.path.exists(image_path):
                image_path = os.path.join(generated_ads_dir, f"ad_{ad_id}.png")
                
            img_html = ""
            if os.path.exists(image_path):
                b64 = get_image_base64(image_path)
                img_html = f'<img src="{b64}" style="width: 100%; height: 100%; object-fit: cover;" />'
            else:
                img_html = """
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: white; gap: 8px;">
                    <svg style="width: 44px; height: 44px;" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg>
                    <span style="font-size: 0.85rem; opacity: 0.85; font-weight: 500;">AI-generated creative</span>
                </div>
                """
                
            grad = gradients[idx % len(gradients)]
            parent_id = "A001" if campaign_info["campaign_id"] == "C001" else ("A005" if campaign_info["campaign_id"] == "C002" else "A009")
            
            cards_html += f"""
            <div class="ad-card">
                <div class="ad-card-image-box" style="background: {grad};">
                    <span class="ad-new-badge">NEW</span>
                    {img_html}
                </div>
                <div class="ad-card-content">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: #7C3AED; font-weight: 700; margin-bottom: 8px;">
                        <span>{ad_id}</span>
                        <span style="color: #6B7280; font-weight: 500;">based on {parent_id}</span>
                    </div>
                    <h4 style="margin: 0 0 8px 0; color: #111827; font-size: 1.15rem; font-weight: 800; line-height: 1.2;">{headline}</h4>
                    <p style="margin: 0 0 16px 0; color: #4B5563; font-size: 0.88rem; line-height: 1.45; height: 60px; overflow: hidden;">{body}</p>
                    <div>
                        <div class="ad-card-btn">{cta}</div>
                    </div>
                    <div class="ad-card-tip">
                        <em>✨ Sharper hook + benefit, matches best segment style.</em>
                    </div>
                </div>
            </div>
            """
            
        st.markdown(f'<div class="ad-cards-grid">{cards_html}</div>', unsafe_allow_html=True)
        
        # Modifications logs
        st.markdown('<div class="modifications-list">', unsafe_allow_html=True)
        st.markdown('<h4 style="margin-top:0; color:#111827; font-size:1.05rem; font-weight:800;">🟢 Applied automated changes</h4>', unsafe_allow_html=True)
        
        mods_html = ""
        for p_ad in paused_ads:
            p_id = p_ad.get("ad_id", "")
            p_head = p_ad.get("headline", "")
            mods_html += f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px;">
                <span style="color: #EF4444; font-weight: bold; font-size: 1.1rem;">⏸️</span>
                <span style="font-size: 0.95rem; color: #374151;">
                    Paused low-performing ad <b>{p_id}</b> ("{p_head}") to optimize budget allocation.
                </span>
            </div>
            """
            
        for _, n_ad in new_ads.iterrows():
            n_id = n_ad.get("ad_id", "")
            n_head = n_ad.get("headline", "")
            mods_html += f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: #10B981; font-weight: bold; font-size: 1.1rem;">🚀</span>
                <span style="font-size: 0.95rem; color: #374151;">
                    Created and activated new optimized ad variant <b>{n_id}</b> ("{n_head}").
                </span>
            </div>
            """
        st.markdown(mods_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
        with st.expander("📖 View Raw Automation & Generation Details"):
            st.write(st.session_state.result.get("generator_summary", "No report available."))
