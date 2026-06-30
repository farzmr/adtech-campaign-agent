import os
import sys
import asyncio
import pandas as pd
from dotenv import load_dotenv
load_dotenv()
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents import (
    creative_analyzer_agent,
    performance_stats_agent,
    creative_generator_agent,
)

async def run_optimization_workflow(campaign_id: str) -> dict:
    """Coordinates the 3 agents in sequence to complete one full optimization run.
    
    Includes try/catch safeguards and checks for missing API keys to prevent crashes.
    """
    # 0. Check API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "your_gemini_api_key_here":
        error_msg = (
            "Error: GEMINI_API_KEY is not set or contains the default placeholder. "
            "Please configure your actual Gemini API key in the '.env' file in the project directory."
        )
        return {
            "campaign_id": campaign_id,
            "creative_analysis": error_msg,
            "performance_analysis": "Aborted due to missing API key.",
            "generator_summary": "Aborted due to missing API key."
        }

    session_service = InMemorySessionService()
    session_id = f"opt_session_{campaign_id}"
    user_id = "adtech_user"
    
    await session_service.create_session(app_name="adtech", user_id=user_id, session_id=session_id)
    
    # 1. Run Creative Analyzer
    analyzer_response = "No response from Creative Analyzer."
    try:
        analyzer_runner = Runner(agent=creative_analyzer_agent, app_name="adtech", session_service=session_service)
        analyzer_prompt = f"Analyze the creative quality of all ads in campaign '{campaign_id}'."
        
        async for event in analyzer_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=analyzer_prompt)])
        ):
            if event.is_final_response() and event.content and event.content.parts:
                analyzer_response = event.content.parts[0].text
    except Exception as e:
        analyzer_response = f"Failed to run Creative Analyzer: {str(e)}"

    # Sleep to respect Gemini API Free Tier rate limits (429 prevention)
    await asyncio.sleep(12)

    # 2. Run Performance Stats Agent
    stats_response = "No response from Performance Stats Agent."
    try:
        stats_runner = Runner(agent=performance_stats_agent, app_name="adtech", session_service=session_service)
        stats_prompt = f"Retrieve performance stats and determine the best device and time patterns for campaign '{campaign_id}'."
        
        async for event in stats_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=stats_prompt)])
        ):
            if event.is_final_response() and event.content and event.content.parts:
                stats_response = event.content.parts[0].text
    except Exception as e:
        stats_response = f"Failed to run Performance Stats: {str(e)}"

    # Guardrail: Check active ads in campaign before running Creative Generator
    ads_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ads.csv")
    if os.path.exists(ads_file_path):
        try:
            ads_df = pd.read_csv(ads_file_path)
            active_ads = ads_df[(ads_df["campaign_id"].astype(str) == str(campaign_id)) & (ads_df["status"].astype(str).str.lower() == "active")]
            if len(active_ads) <= 1:
                warning_msg = f"Guardrail Warning: Aborting optimization for campaign '{campaign_id}'. Only {len(active_ads)} active ad(s) remaining. Turning off any ads would leave zero active ads."
                return {
                    "campaign_id": campaign_id,
                    "creative_analysis": analyzer_response,
                    "performance_analysis": stats_response,
                    "generator_summary": warning_msg
                }
        except Exception as e:
            pass

    # Sleep to respect Gemini API Free Tier rate limits (429 prevention)
    await asyncio.sleep(12)

    # 3. Run Creative Generator Agent
    generator_response = "No response from Creative Generator."
    try:
        generator_runner = Runner(agent=creative_generator_agent, app_name="adtech", session_service=session_service)
        generator_prompt = f"""
Using the following insights for campaign '{campaign_id}':

Creative Analysis:
{analyzer_response}

Performance Analysis:
{stats_response}

Please perform the optimization steps:
1. Turn off (pause) the lowest performing ad in this campaign via update_ad_status.
2. Create a new optimized ad (headline, body) based on the top performer's style via create_ad.
3. Generate a matching display ad image using generate_and_save_ad_image (save it as 'ad_new_{campaign_id}.png').
"""
        async for event in generator_runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part.from_text(text=generator_prompt)])
        ):
            if event.is_final_response() and event.content and event.content.parts:
                generator_response = event.content.parts[0].text
    except Exception as e:
        generator_response = f"Failed to run Creative Generator: {str(e)}"

    return {
        "campaign_id": campaign_id,
        "creative_analysis": analyzer_response,
        "performance_analysis": stats_response,
        "generator_summary": generator_response
    }

if __name__ == "__main__":
    cid = sys.argv[1] if len(sys.argv) > 1 else "camp_1"
    print(f"Running optimization for campaign: {cid}...")
    res = asyncio.run(run_optimization_workflow(cid))
    print("\n=== OPTIMIZATION SUMMARY ===")
    print(f"Creative Analysis:\n{res['creative_analysis']}\n")
    print(f"Performance Analysis:\n{res['performance_analysis']}\n")
    print(f"Generator Actions:\n{res['generator_summary']}\n")
