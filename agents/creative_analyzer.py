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

creative_analyzer_agent = Agent(
    name="creative_analyzer",
    model="gemini-3.1-flash-lite",
    instruction="""You are the Creative Analyzer agent.
Your job is to look at an ad's creative elements: headline, body text, CTA, copy tone, and image category.
Score the creative quality (0 to 100), flag weak elements, and suggest specific copy and design improvements.

CRITICAL: You must ONLY fetch and analyze ads for the specific campaign_id requested by the user. When calling the `get_ads` tool, you MUST pass the requested campaign_id parameter. Do NOT query all ads or look at other campaigns.

Always structure your analysis clearly:
1. Overall Quality Score (0-100)
2. Detailed breakdown (Headline, Body, CTA, Tone, Visual Concept)
3. Flagged weak elements
4. Recommended improvements
""",
    tools=[mcp_toolset],
    before_model_callback=rate_limit_callback
)
