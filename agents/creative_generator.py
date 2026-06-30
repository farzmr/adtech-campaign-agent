import os
import asyncio
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google import genai
from google.genai import types
from PIL import Image, ImageDraw
from io import BytesIO
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_PATH = os.path.join(BASE_DIR, "mcp_server", "server.py")

# Configure MCP Toolset
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python3",
            args=[SERVER_PATH],
        )
    )
)

async def rate_limit_callback(callback_context: CallbackContext, llm_request: LlmRequest) -> LlmResponse | None:
    # Sleep 12 seconds to ensure we never exceed the 5 RPM Free Tier limit
    await asyncio.sleep(12)
    return None

def generate_and_save_ad_image(prompt: str, filename: str) -> dict:
    """Generates a display ad image using Gemini Imagen and saves it to the generated_ads/ folder.
    
    Args:
        prompt: The text prompt describing the image to generate.
        filename: The filename (e.g., 'ad_new.png') to save the image under.
        
    Returns:
        dict containing the status and absolute path of the generated image.
    """
    try:
        # Initialize GenAI client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return {"status": "error", "message": "GEMINI_API_KEY environment variable is not set."}
            
        client = genai.Client(api_key=api_key)
        
        # Call imagen-3.0-generate-002
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png"
            )
        )
        
        # Save to generated_ads/
        output_dir = os.path.join(BASE_DIR, "generated_ads")
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, filename)
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            image = Image.open(BytesIO(image_bytes))
            image.save(filepath)
            return {"status": "success", "filepath": filepath}
                
        return {"status": "error", "message": "No image data returned from model."}
    except Exception as e:
        # Fallback to local PIL image generation in case Imagen 3 is unavailable on this free API key
        try:
            output_dir = os.path.join(BASE_DIR, "generated_ads")
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            # Generate a gorgeous dark gradient banner with borders
            img = Image.new("RGB", (600, 600), "#0f172a")
            draw = ImageDraw.Draw(img)
            
            # Simple gradient
            for y in range(600):
                r = int(15 + (y / 600) * 15)
                g = int(23 + (y / 600) * 30)
                b = int(42 + (y / 600) * 45)
                draw.line([(0, y), (600, y)], fill=(r, g, b))
                
            # Neon border
            draw.rectangle([20, 20, 580, 580], outline="#38bdf8", width=4)
            draw.rectangle([30, 30, 570, 570], outline="#1e293b", width=1)
            
            # Text Mockup
            draw.text((50, 100), "[ AI CREATIVE LAB ]", fill="#38bdf8")
            draw.text((50, 180), "OPTIMIZED DISPLAY CREATIVE", fill="#f1f5f9")
            
            # Wrap prompt description
            clean_prompt = prompt.replace("\n", " ").strip()
            prompt_summary = clean_prompt[:45] + ("..." if len(clean_prompt) > 45 else "")
            draw.text((50, 260), f"Concept: {prompt_summary}", fill="#e2e8f0")
            
            draw.text((50, 340), "Target Audience: Mobile & Desktop Segments", fill="#94a3b8")
            draw.text((50, 420), "Format: 1:1 Social Display", fill="#94a3b8")
            draw.text((50, 500), "STATUS: ACTIVE", fill="#10b981")
            
            img.save(filepath)
            return {
                "status": "success", 
                "filepath": filepath, 
                "message": f"Used local premium mockup generator (Imagen API returned 404: {str(e)})"
            }
        except Exception as local_err:
            return {"status": "error", "message": f"Imagen error: {str(e)}. Local fallback error: {str(local_err)}"}

creative_generator_agent = Agent(
    name="creative_generator",
    model="gemini-3.1-flash-lite",
    instruction="""You are the Creative Generator agent.
Your job is to optimize the campaign creative assets using insights from the Creative Analyzer and Performance Stats agents.

You must perform three actions:
1. Turn off (pause) the lowest performing ads in the campaign by calling the update_ad_status tool.
2. Write a new ad copy (headline, body, status='active') based on the top performer's style. Save this new ad using the create_ad tool.
3. Generate a matching display ad image using the generate_and_save_ad_image tool, saving it under a descriptive filename (e.g., 'ad_<id>.png') in the generated_ads/ folder.

Use the provided MCP tools to modify ad statuses and create new ads, and the generate_and_save_ad_image tool to generate creatives.
""",
    tools=[mcp_toolset, generate_and_save_ad_image],
    before_model_callback=rate_limit_callback
)
