import os
import pandas as pd
import streamlit as st
import asyncio
from PIL import Image, ImageDraw, ImageFont
from orchestrator import run_optimization_workflow

# Page config with premium title & layout
st.set_page_config(
    page_title="AdTech Multi-Agent Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern premium design aesthetics
st.markdown("""
<style>
    .reportview-container {
        background: #0f172a;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    .metric-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        margin-bottom: 1rem;
    }
    .agent-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #38bdf8;
        margin-bottom: 0.5rem;
    }
    h1, h2, h3 {
        color: #f1f5f9;
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.4);
        transform: translateY(-1px);
    }
</style>
""", unsafe_allow_html=True)

# File Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CAMPAIGNS_FILE = os.path.join(DATA_DIR, "campaigns.csv")
ADS_FILE = os.path.join(DATA_DIR, "ads.csv")
PERFORMANCE_FILE = os.path.join(DATA_DIR, "ad_performance.csv")

# ----------------- DATA SEEDING (Auto-runs if empty) -----------------
def seed_data_if_missing():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 1. Seed campaigns if missing or empty
    if not os.path.exists(CAMPAIGNS_FILE) or os.path.getsize(CAMPAIGNS_FILE) < 10:
        c_df = pd.DataFrame([
            {"campaign_id": "camp_1", "campaign_name": "Summer Running Shoes Kickoff", "budget": 5000, "status": "active", "objective": "conversions", "channel": "search"},
            {"campaign_id": "camp_2", "campaign_name": "Eco-Friendly Water Bottle Launch", "budget": 3000, "status": "active", "objective": "awareness", "channel": "social"},
            {"campaign_id": "camp_3", "campaign_name": "Smart Home Thermostat Promo", "budget": 8000, "status": "active", "objective": "traffic", "channel": "display"}
        ])
        c_df.to_csv(CAMPAIGNS_FILE, index=False)
        
    # 2. Seed ads if missing or empty
    if not os.path.exists(ADS_FILE) or os.path.getsize(ADS_FILE) < 10:
        a_df = pd.DataFrame([
            {"ad_id": "ad_1", "campaign_id": "camp_1", "headline": "Run Faster in Comfort", "body": "Get the new CloudStride shoes with 20% off today. Lightweight and durable.", "cta": "Shop Now", "copy_tone": "energetic", "image_category": "athletic shoes", "status": "active"},
            {"ad_id": "ad_2", "campaign_id": "camp_1", "headline": "Upgrade Your Daily Run", "body": "Premium cushioning for all athletes. Free shipping on all orders.", "cta": "Buy Today", "copy_tone": "informative", "image_category": "shoes close-up", "status": "active"},
            {"ad_id": "ad_3", "campaign_id": "camp_2", "headline": "Save the Planet, Hydrate Well", "body": "100% biodegradable stainless steel water bottles. Keeps drinks cold for 24h.", "cta": "Learn More", "copy_tone": "inspirational", "image_category": "bottle in nature", "status": "active"}
        ])
        a_df.to_csv(ADS_FILE, index=False)
        
    # 3. Seed performance if missing or empty
    if not os.path.exists(PERFORMANCE_FILE) or os.path.getsize(PERFORMANCE_FILE) < 10:
        p_df = pd.DataFrame([
            {"ad_id": "ad_1", "date": "2026-06-25", "time_of_day": "morning", "device": "mobile", "impressions": 1000, "clicks": 50, "conversions": 5, "spend": 100},
            {"ad_id": "ad_1", "date": "2026-06-25", "time_of_day": "afternoon", "device": "mobile", "impressions": 1200, "clicks": 60, "conversions": 6, "spend": 120},
            {"ad_id": "ad_1", "date": "2026-06-25", "time_of_day": "morning", "device": "desktop", "impressions": 300, "clicks": 10, "conversions": 1, "spend": 30},
            {"ad_id": "ad_1", "date": "2026-06-25", "time_of_day": "afternoon", "device": "desktop", "impressions": 400, "clicks": 12, "conversions": 0, "spend": 40},
            {"ad_id": "ad_2", "date": "2026-06-25", "time_of_day": "morning", "device": "mobile", "impressions": 900, "clicks": 30, "conversions": 1, "spend": 90},
            {"ad_id": "ad_2", "date": "2026-06-25", "time_of_day": "afternoon", "device": "mobile", "impressions": 1100, "clicks": 40, "conversions": 2, "spend": 110},
            {"ad_id": "ad_2", "date": "2026-06-25", "time_of_day": "morning", "device": "desktop", "impressions": 200, "clicks": 5, "conversions": 0, "spend": 20},
            {"ad_id": "ad_2", "date": "2026-06-25", "time_of_day": "afternoon", "device": "desktop", "impressions": 300, "clicks": 8, "conversions": 0, "spend": 30},
            {"ad_id": "ad_3", "date": "2026-06-25", "time_of_day": "morning", "device": "mobile", "impressions": 1500, "clicks": 120, "conversions": 10, "spend": 150}
        ])
        p_df.to_csv(PERFORMANCE_FILE, index=False)

seed_data_if_missing()

# ----------------- HELPER: GENERATE MOCK IMAGE IF GEMINI FAILS -----------------
def generate_fallback_image(headline: str, body: str, filename: str):
    """Generates a beautiful gradient banner as a fallback if Imagen is unavailable."""
    img = Image.new("RGB", (600, 600), "#0f172a")
    draw = ImageDraw.Draw(img)
    
    # Draw simple gradient / background shape
    for y in range(600):
        r = int(15 + (y / 600) * 15)
        g = int(23 + (y / 600) * 30)
        b = int(42 + (y / 600) * 45)
        draw.line([(0, y), (600, y)], fill=(r, g, b))
        
    # Draw simple design borders
    draw.rectangle([20, 20, 580, 580], outline="#38bdf8", width=3)
    draw.rectangle([30, 30, 570, 570], outline="#1e293b", width=1)
    
    # Text drawing with fallback fonts
    draw.text((50, 150), "[NEW AD DESIGN]", fill="#38bdf8")
    draw.text((50, 220), headline[:30] + ("..." if len(headline) > 30 else ""), fill="#f1f5f9")
    draw.text((50, 300), body[:70] + ("..." if len(body) > 70 else ""), fill="#94a3b8")
    draw.text((50, 480), "Tap to Learn More", fill="#38bdf8")
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_ads")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    return filepath

# ----------------- MAIN UI -----------------
st.title("⚡ AdTech Multi-Agent Ad Optimizer")
st.subheader("Automate creative analysis, performance optimization, and ad asset generation")

# Load campaigns
campaigns_df = pd.read_csv(CAMPAIGNS_FILE)
campaign_options = {row["name"]: row for _, row in campaigns_df.iterrows()}

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🛠️ Configuration")
    
    selected_name = st.selectbox("Select Campaign to Optimize", list(campaign_options.keys()))
    campaign_info = campaign_options[selected_name]
    
    # Display current metrics
    st.markdown(f"""
    <div class="metric-card">
        <p style='margin: 0; color: #94a3b8;'>Campaign Objective</p>
        <h3 style='margin: 0; color: #38bdf8;'>{campaign_info['objective'].upper()}</h3>
        <p style='margin: 10px 0 0 0; color: #94a3b8;'>Channel: <b>{campaign_info['channel'].capitalize()}</b></p>
        <p style='margin: 0; color: #94a3b8;'>Current Budget: <b>${campaign_info['total_budget']}</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    opt_focus = st.selectbox("Optimization Focus", ["conversions", "awareness", "traffic"], index=["conversions", "awareness", "traffic"].index(campaign_info["objective"]))
    budget_level = st.select_slider("Target Budget Level", ["low", "medium", "high"], value="medium")
    channel_focus = st.selectbox("Channel Focus Override", ["search", "social", "display", "all"], index=0)
    
    confirm_opt = st.checkbox(f"Confirm optimization parameters for: {selected_name}")
    
    if confirm_opt:
        run_btn = st.button("Run Optimization Loop", use_container_width=True)
    else:
        st.info("⚠️ Review parameters and check the box above to enable the Run button.")
        run_btn = False

with col2:
    st.markdown("### 📊 Live Optimization Dashboard")
    
    if run_btn:
        with st.spinner("🤖 Orchestrating agents (Creative Analyzer ➡️ Performance Stats ➡️ Creative Generator)..."):
            # Run the orchestrator workflow
            result = asyncio.run(run_optimization_workflow(campaign_info["campaign_id"]))
            
            st.success("🎉 Optimization complete!")
            
            tab1, tab2, tab3 = st.tabs([
                "🎨 Creative Analyzer Findings", 
                "📈 Performance recommendations", 
                "🚀 Generator Outputs"
            ])
            
            with tab1:
                st.markdown("<div class='agent-header'>🔍 Creative Analyzer Report</div>", unsafe_allow_html=True)
                st.write(result["creative_analysis"])
                
            with tab2:
                st.markdown("<div class='agent-header'>📉 Performance Stats & Segments</div>", unsafe_allow_html=True)
                st.write(result["performance_analysis"])
                
            with tab3:
                st.markdown("<div class='agent-header'>🔧 Automation & Generation Actions</div>", unsafe_allow_html=True)
                st.write(result["generator_summary"])
                
                # Check for generated image
                generated_ads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_ads")
                image_name = f"ad_new_{campaign_info['campaign_id']}.png"
                image_path = os.path.join(generated_ads_dir, image_name)
                
                # If image wasn't generated by Gemini (due to no API Key etc), create a fallback
                if not os.path.exists(image_path):
                    # Attempt to parse a mockup headline/body or just use defaults
                    generate_fallback_image(
                        headline="Discover Ultimate Comfort", 
                        body="Step into premium cloud-like cushioning. Made for champions.", 
                        filename=image_name
                    )
                
                if os.path.exists(image_path):
                    st.markdown("#### 🖼️ Newly Generated Display Ad Image")
                    st.image(image_path, caption=f"Generated Ad Image: {image_name}", use_container_width=True)
    else:
        st.info("👈 Select a campaign on the left and click 'Run Optimization Loop' to begin.")
