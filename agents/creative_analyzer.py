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

# Read prompt from markdown file
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "creative_analyzer.md")
with open(PROMPT_PATH, "r") as f:
    creative_analyzer_instruction = f.read()

creative_analyzer_agent = Agent(
    name="creative_analyzer",
    model="gemini-3.1-flash-lite",
    instruction=creative_analyzer_instruction,
    tools=[mcp_toolset],
    before_model_callback=rate_limit_callback
)
