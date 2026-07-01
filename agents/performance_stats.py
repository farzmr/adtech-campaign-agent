import os
import sys
import asyncio
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PATH = os.path.join(BASE_DIR, "mcp_server", "server.py")

# Configure MCP Toolset
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[SERVER_PATH],
        )
    )
)

async def rate_limit_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    # Sleep 12 seconds to ensure we never exceed the 5 RPM Free Tier limit
    await asyncio.sleep(12)
    return None

performance_stats_agent = Agent(
    name="performance_stats",
    model="gemini-3.1-flash-lite",
    instruction="""You are the Performance Stats agent.
Your job is to read and analyze aggregated performance data for a campaign from the MCP server.
Find the best-performing device and time of day based on the campaign's objective:
- For "conversions": Look at conversions and spend to calculate performance (e.g., Conversion Rate, Cost per Conversion / ROAS).
- For "awareness": Look at impressions and CTR (Click-Through Rate).
- For "traffic": Look at clicks and CTR.

Determine which segments (device, time of day) are performing best and which are performing worst.

CRITICAL: You must ONLY fetch data for the specific campaign_id requested by the user. When calling `get_ads` or `get_performance_summary`, you MUST pass the requested campaign_id parameter. Do NOT query global dataset.

Structure your output with clear insights on the best and worst performing segments.
""",
    tools=[mcp_toolset],
    before_model_callback=rate_limit_callback
)
