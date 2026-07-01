import os
import sys
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("AdTech Data Service")

# Resolve path to data directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

CAMPAIGNS_FILE = os.path.join(DATA_DIR, "campaigns.csv")
ADS_FILE = os.path.join(DATA_DIR, "ads.csv")
PERFORMANCE_FILE = os.path.join(DATA_DIR, "ad_performance.csv")
CHANGELOG_FILE = os.path.join(DATA_DIR, "change_log.csv")

# Standard schemas matching user's pre-existing files
CAMPAIGN_COLS = ["campaign_id", "name", "objective", "channel", "total_budget", "status", "start_date", "end_date", "time_of_day", "device"]
ADS_COLS = ["ad_id", "campaign_id", "headline", "body_text", "cta", "image_size", "image_url", "ad_type", "status", "copy_tone", "img_category"]
PERF_COLS = ["perf_id", "ad_id", "campaign_id", "date", "day_of_week", "device", "time_of_day", "impressions", "clicks", "ctr", "spend", "conversions", "roas", "cost_per_click"]
CHANGELOG_COLS = ["log_id", "timestamp", "campaign_id", "change_type", "target_id", "details"]

def _load_csv(file_path: str, default_cols: list) -> pd.DataFrame:
    """Helper to load a CSV or return an empty DataFrame with expected columns if it doesn't exist."""
    if not os.path.exists(file_path):
        df = pd.DataFrame(columns=default_cols)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        df.to_csv(file_path, index=False)
        return df
    try:
        df = pd.read_csv(file_path)
        # Ensure all default columns exist
        for col in default_cols:
            if col not in df.columns:
                df[col] = None
        return df
    except Exception as e:
        return pd.DataFrame(columns=default_cols)

def _save_csv(df: pd.DataFrame, file_path: str):
    """Helper to save a DataFrame to CSV."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    df.to_csv(file_path, index=False)

def _write_change_log(campaign_id: str, change_type: str, target_id: str, details: str):
    """Helper to log a change in the change_log dataset."""
    import datetime
    df = _load_csv(CHANGELOG_FILE, CHANGELOG_COLS)
    
    if not df.empty:
        try:
            numeric_ids = df["log_id"].astype(str).str.extract(r'(\d+)').dropna().astype(int)
            next_id = int(numeric_ids.max().iloc[0]) + 1
        except Exception:
            next_id = len(df) + 1
    else:
        next_id = 1
        
    log_id = f"L{str(next_id).zfill(3)}"
    new_log = {
        "log_id": log_id,
        "timestamp": datetime.datetime.now().isoformat(),
        "campaign_id": str(campaign_id),
        "change_type": change_type,
        "target_id": str(target_id),
        "details": details
    }
    df = pd.concat([df, pd.DataFrame([new_log])], ignore_index=True)
    _save_csv(df, CHANGELOG_FILE)


@mcp.tool()
def get_campaigns() -> str:
    """Get list and details of all advertising campaigns."""
    df = _load_csv(CAMPAIGNS_FILE, CAMPAIGN_COLS)
    return df.to_json(orient="records")

@mcp.tool()
def get_ads(campaign_id: str = None) -> str:
    """Get ads. Optionally filter by campaign_id."""
    df = _load_csv(ADS_FILE, ADS_COLS)
    if campaign_id:
        df = df[df["campaign_id"].astype(str) == str(campaign_id)]
    return df.to_json(orient="records")

@mcp.tool()
def get_performance_summary(campaign_id: str = None, ad_id: str = None) -> str:
    """Get aggregated performance stats grouped by device and time of day.
    
    Filters by campaign_id or ad_id if provided.
    Returns aggregated metrics: impressions, clicks, conversions, spend.
    """
    perf_df = _load_csv(PERFORMANCE_FILE, PERF_COLS)
    ads_df = _load_csv(ADS_FILE, ADS_COLS)
    
    if perf_df.empty:
        return "[]"
        
    # Merge with ads to resolve campaign_id if filtering by campaign
    merged = pd.merge(perf_df, ads_df, on="ad_id", how="left")
    
    if campaign_id:
        # Use campaign_id from either performance record or ad mapping
        merged = merged[
            (merged["campaign_id_x"].astype(str) == str(campaign_id)) | 
            (merged["campaign_id_y"].astype(str) == str(campaign_id))
        ]
    if ad_id:
        merged = merged[merged["ad_id"].astype(str) == str(ad_id)]
        
    if merged.empty:
        return "[]"
        
    # Group by device and time of day, and aggregate metrics
    group_cols = ["device", "time_of_day"]
    agg_dict = {
        "impressions": "sum",
        "clicks": "sum",
        "conversions": "sum",
        "spend": "sum"
    }
    
    summary = merged.groupby(group_cols).agg(agg_dict).reset_index()
    return summary.to_json(orient="records")

@mcp.tool()
def update_ad_status(ad_id: str, status: str) -> str:
    """Update the status of an ad (e.g. 'active', 'paused')."""
    status = status.lower().strip()
    if status not in ["active", "paused"]:
        return f"Error: Status must be 'active' or 'paused'. Received '{status}'"
        
    df = _load_csv(ADS_FILE, ADS_COLS)
    
    if df.empty or ad_id not in df["ad_id"].astype(str).values:
        return f"Error: Ad ID '{ad_id}' not found."
        
    # Look up campaign_id before saving status
    ad_row = df[df["ad_id"].astype(str) == str(ad_id)]
    campaign_id = ad_row["campaign_id"].values[0] if not ad_row.empty else "Unknown"

    df.loc[df["ad_id"].astype(str) == str(ad_id), "status"] = status
    _save_csv(df, ADS_FILE)
    _write_change_log(campaign_id, "update_ad_status", ad_id, f"Updated status to '{status}'")
    return f"Successfully updated ad '{ad_id}' status to '{status}'"


@mcp.tool()
def create_ad(campaign_id: str, headline: str, body: str, status: str = "active") -> str:
    """Create a new ad under a specified campaign."""
    # Input validation
    if not campaign_id or not campaign_id.strip():
        return "Error: campaign_id is required and cannot be empty."
    if not headline or not headline.strip():
        return "Error: headline is required and cannot be empty."
    if not body or not body.strip():
        return "Error: body is required and cannot be empty."
        
    status = status.lower().strip()
    if status not in ["active", "paused"]:
        return f"Error: Status must be 'active' or 'paused'. Received '{status}'"

    campaigns_df = _load_csv(CAMPAIGNS_FILE, CAMPAIGN_COLS)
    if campaigns_df.empty or campaign_id not in campaigns_df["campaign_id"].astype(str).values:
         print(f"Warning: Campaign ID '{campaign_id}' not found in campaign list.", file=sys.stderr)

    ads_df = _load_csv(ADS_FILE, ADS_COLS)
    
    # Generate simple next sequential ad_id
    if not ads_df.empty:
        try:
            numeric_ids = ads_df["ad_id"].astype(str).str.extract(r'(\d+)').dropna().astype(int)
            next_id = int(numeric_ids.max().iloc[0]) + 1
        except Exception:
            next_id = len(ads_df) + 1
    else:
        next_id = 1
        
    new_ad_id = f"A{str(next_id).zfill(3)}"
    new_ad = {
        "ad_id": new_ad_id,
        "campaign_id": str(campaign_id),
        "headline": headline,
        "body_text": body,
        "status": status,
        "cta": "Learn More",
        "image_size": "300x250",
        "image_url": f"images/{new_ad_id}.png",
        "ad_type": "display",
        "copy_tone": "conversational",
        "img_category": "lifestyle"
    }
    
    ads_df = pd.concat([ads_df, pd.DataFrame([new_ad])], ignore_index=True)
    _save_csv(ads_df, ADS_FILE)
    _write_change_log(campaign_id, "create_ad", new_ad_id, f"Created new ad with headline: '{headline}'")
    return f"Successfully created ad '{new_ad_id}' under campaign '{campaign_id}'"


@mcp.tool()
def update_campaign_targeting(campaign_id: str, device: str, time_of_day: str) -> str:
    """Update targeting settings (device and time of day) for a campaign."""
    if not campaign_id or not campaign_id.strip():
        return "Error: campaign_id is required."
    if not device or not device.strip():
        return "Error: device is required."
    if not time_of_day or not time_of_day.strip():
        return "Error: time_of_day is required."
        
    df = _load_csv(CAMPAIGNS_FILE, CAMPAIGN_COLS)
    if df.empty or campaign_id not in df["campaign_id"].astype(str).values:
        return f"Error: Campaign ID '{campaign_id}' not found."
        
    # Standardize case to match expected casing
    df.loc[df["campaign_id"].astype(str) == str(campaign_id), "device"] = device.lower().strip()
    df.loc[df["campaign_id"].astype(str) == str(campaign_id), "time_of_day"] = time_of_day.lower().strip()
    _save_csv(df, CAMPAIGNS_FILE)
    _write_change_log(campaign_id, "update_campaign_targeting", campaign_id, f"Updated targeting to device: '{device}', time_of_day: '{time_of_day}'")
    return f"Successfully updated campaign '{campaign_id}' targeting: device='{device}', time_of_day='{time_of_day}'"


if __name__ == "__main__":
    mcp.run(transport="stdio")

