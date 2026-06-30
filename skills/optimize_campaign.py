import asyncio
from orchestrator import run_optimization_workflow

def optimize_campaign(campaign_id: str) -> dict:
    """Runs a complete display ad optimization workflow for a campaign.
    
    This skill coordinates:
    1. Creative Analyzer to evaluate ad assets.
    2. Performance Stats agent to identify top device/time-of-day segments.
    3. Creative Generator to pause weak ads, create a new ad variant, and generate a creative display ad image.
    
    Args:
        campaign_id: The ID of the campaign to optimize (e.g., 'camp_1').
        
    Returns:
        dict: A summary of the optimization run, containing creative analysis, performance analysis, and generator actions.
    """
    try:
        # Check if there is an active loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_running():
        # If already running (e.g. inside Streamlit or an async app), apply nest_asyncio to run synchronously
        try:
            import nest_asyncio
            nest_asyncio.apply()
        except ImportError:
            pass
        return loop.run_until_complete(run_optimization_workflow(campaign_id))
    else:
        return loop.run_until_complete(run_optimization_workflow(campaign_id))
