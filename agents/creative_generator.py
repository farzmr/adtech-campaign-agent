import os
import sys
import asyncio
from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
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

def overlay_text_on_image(image: Image.Image, headline: str, body: str) -> Image.Image:
    """Overlays the headline, body text, and a call-to-action button on top of a PIL image.
    
    Ensures high legibility by drawing a translucent card or gradient behind the text.
    """
    draw = ImageDraw.Draw(image, "RGBA")
    width, height = image.size
    
    # 1. Draw a semi-transparent dark container on the lower half of the image for contrast
    card_margin = 24
    card_x1 = card_margin
    card_y1 = int(height * 0.52)
    card_x2 = width - card_margin
    card_y2 = height - card_margin
    
    # Draw dark translucent backdrop card
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=16, fill=(15, 23, 42, 215))
    
    # Also draw a subtle glowing border around the card
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=16, outline=(124, 90, 237, 120), width=1)
    
    # 2. Try loading a premium macOS TrueType font
    font_title = None
    font_body = None
    font_cta = None
    
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                font_title = ImageFont.truetype(path, 24)
                font_body = ImageFont.truetype(path, 14)
                font_cta = ImageFont.truetype(path, 13)
                break
            except Exception:
                continue
                
    if font_title is None:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_cta = ImageFont.load_default()
        
    # Helper to wrap text
    def wrap_text(text, font, max_width_px):
        if not text:
            return []
        if not hasattr(font, "getbbox"):
            words = text.split()
            lines = []
            current_line = []
            for word in words:
                if len(" ".join(current_line + [word])) * 6 < max_width_px:
                    current_line.append(word)
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(" ".join(current_line))
            return lines
            
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w <= max_width_px:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        return lines

    # Wrap title & body
    max_text_width = card_x2 - card_x1 - 40
    title_lines = wrap_text(headline, font_title, max_text_width)
    body_lines = wrap_text(body, font_body, max_text_width)
    
    # 3. Draw Headline Text
    curr_y = card_y1 + 24
    for line in title_lines[:2]:
        draw.text((card_x1 + 20, curr_y), line, fill=(255, 255, 255, 255), font=font_title)
        if hasattr(font_title, "getbbox"):
            curr_y += font_title.getbbox(line)[3] - font_title.getbbox(line)[1] + 6
        else:
            curr_y += 28
            
    # Add a tiny gap
    curr_y += 4
    
    # 4. Draw Body Text
    for line in body_lines[:3]:
        draw.text((card_x1 + 20, curr_y), line, fill=(209, 213, 219, 255), font=font_body)
        if hasattr(font_body, "getbbox"):
            curr_y += font_body.getbbox(line)[3] - font_body.getbbox(line)[1] + 4
        else:
            curr_y += 18
            
    # 5. Draw CTA Button
    cta_text = "SHOP NOW"
    cta_w, cta_h = 110, 32
    cta_x1 = card_x2 - cta_w - 20
    cta_y1 = card_y2 - cta_h - 20
    cta_x2 = card_x2 - 20
    cta_y2 = card_y2 - 20
    
    # Pill background
    draw.rounded_rectangle([cta_x1, cta_y1, cta_x2, cta_y2], radius=16, fill=(124, 58, 237, 255))
    
    # Text inside CTA
    if hasattr(font_cta, "getbbox"):
        bbox = font_cta.getbbox(cta_text)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    else:
        tw = len(cta_text) * 6
        th = 10
        
    tx = cta_x1 + (cta_w - tw) // 2
    ty = cta_y1 + (cta_h - th) // 2 - 1
    draw.text((tx, ty), cta_text, fill=(255, 255, 255, 255), font=font_cta)
    
    return image


def draw_fallback_image(headline: str, body: str) -> Image.Image:
    """Generates a highly creative, visually stunning fallback display ad image in PIL."""
    img = Image.new("RGB", (600, 600), "#0f172a")
    draw = ImageDraw.Draw(img, "RGBA")
    
    # Gradient background
    for y in range(600):
        ratio = y / 600.0
        r = int(124 * (1 - ratio) + 15 * ratio)
        g = int(58 * (1 - ratio) + 23 * ratio)
        b = int(237 * (1 - ratio) + 42 * ratio)
        draw.line([(0, y), (600, y)], fill=(r, g, b, 255))
        
    # Geometric shapes/glows
    draw.circle((500, 100), 180, fill=(217, 70, 239, 40))
    draw.circle((100, 300), 120, fill=(6, 182, 212, 30))
    
    for i in range(0, 600, 80):
        draw.line([(i, 0), (i + 150, 600)], fill=(255, 255, 255, 10), width=2)
        
    draw.rectangle([15, 15, 585, 585], outline=(139, 92, 246, 180), width=2)
    
    # Badge
    font_badge = None
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/HelveticaNeue.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                font_badge = ImageFont.truetype(path, 11)
                break
            except Exception:
                continue
    if font_badge is None:
        font_badge = ImageFont.load_default()
        
    badge_x1, badge_y1 = 36, 36
    badge_text = "⚡ AD PILOT OPTIMIZED"
    if hasattr(font_badge, "getbbox"):
        badge_w = font_badge.getbbox(badge_text)[2] - font_badge.getbbox(badge_text)[0] + 16
        badge_h = 22
    else:
        badge_w = len(badge_text) * 6 + 16
        badge_h = 22
        
    draw.rounded_rectangle([badge_x1, badge_y1, badge_x1 + badge_w, badge_y1 + badge_h], radius=11, fill=(255, 255, 255, 40), outline=(255, 255, 255, 100), width=1)
    draw.text((badge_x1 + 8, badge_y1 + 4), badge_text, fill=(255, 255, 255, 230), font=font_badge)
    
    return img

# Global cache for the stable diffusion pipeline to avoid reloading weights repeatedly
_local_sd_pipeline = None

def get_local_sd_pipeline():
    """Helper to lazily load the local Stable Diffusion pipeline on Apple Silicon (MPS) or CPU."""
    global _local_sd_pipeline
    if _local_sd_pipeline is not None:
        return _local_sd_pipeline

    import torch
    from diffusers import StableDiffusionPipeline

    # Load the model weights (defaults to runwayml/stable-diffusion-v1-5)
    model_id = "runwayml/stable-diffusion-v1-5"
    
    # Select device: MPS for Apple Silicon, CPU otherwise
    if torch.backends.mps.is_available():
        device = "mps"
        # float16 is faster and uses less memory
        torch_dtype = torch.float16
    else:
        device = "cpu"
        torch_dtype = torch.float32

    print(f"Loading local Stable Diffusion model ({model_id}) on device: {device}...")
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch_dtype,
        safety_checker=None, # Disable safety checker to reduce RAM usage locally
        requires_safety_checker=False
    )
    pipe = pipe.to(device)
    # Enable memory attention slicing to save memory on laptops
    pipe.enable_attention_slicing()
    
    _local_sd_pipeline = pipe
    return _local_sd_pipeline

def generate_and_save_ad_image(prompt: str, filename: str, headline: str, body: str) -> dict:
    """Generates a display ad image trying three sequential fallback tiers:
    
    1. Gemini Imagen API (Cloud Generation)
    2. Local Stable Diffusion Pipeline (via Hugging Face diffusers on MPS/CPU)
    3. Local PIL mockup drawing (No-ML local fallback)
    
    Args:
        prompt: The visual description for the background image.
        filename: The filename (e.g., 'ad_new.png') to save the image under.
        headline: The exact new headline text to render/overlay on the image.
        body: The exact new body text to render/overlay on the image.
        
    Returns:
        dict containing the status and absolute path of the generated image.
    """
    output_dir = os.path.join(BASE_DIR, "generated_ads")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)

    # Tier 1: Try Gemini Imagen API
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
            
        client = genai.Client(api_key=api_key)
        
        # Call imagen-3.0-generate-002
        print("Attempting Tier 1: Gemini Imagen API...")
        response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",
                output_mime_type="image/png"
            )
        )
        
        if response.generated_images:
            image_bytes = response.generated_images[0].image.image_bytes
            image = Image.open(BytesIO(image_bytes))
            image = image.resize((600, 600))
            image.save(filepath)
            return {
                "status": "success", 
                "filepath": filepath,
                "message": "Generated using Gemini Imagen API (Tier 1)"
            }
                
        raise ValueError("No image data returned from Gemini Imagen.")
    except Exception as e_imagen:
        # Tier 2: Try local Stable Diffusion
        try:
            print(f"Tier 1 (Gemini Imagen) failed: {str(e_imagen)}. Falling back to Tier 2 (Local Stable Diffusion)...")
            pipe = get_local_sd_pipeline()
            
            # Generate the image (512x512 is default and fastest for Stable Diffusion v1.5)
            result = pipe(
                prompt=prompt,
                num_inference_steps=20,
                height=512,
                width=512
            )
            
            if result.images:
                image = result.images[0]
                # Resize to the standard 600x600 expected by the ad-builder overlay template
                image = image.resize((600, 600))
                image.save(filepath)
                return {
                    "status": "success", 
                    "filepath": filepath,
                    "message": f"Generated using local Stable Diffusion v1.5 via diffusers (Tier 2). (Imagen error: {str(e_imagen)})"
                }
                    
            raise ValueError("No image returned from local Stable Diffusion pipeline.")
        except Exception as e_sd:
            # Tier 3: Fallback to local PIL image generation
            try:
                print(f"Tier 2 (Local SD) failed: {str(e_sd)}. Falling back to Tier 3 (Local PIL Drawing)...")
                image = draw_fallback_image(headline, body)
                image.save(filepath)
                return {
                    "status": "success", 
                    "filepath": filepath,
                    "message": f"Used local PIL mockup generator (Tier 3). (Imagen error: {str(e_imagen)}. Local SD error: {str(e_sd)})"
                }
            except Exception as local_err:
                return {
                    "status": "error", 
                    "message": f"All image generation tiers failed. Imagen: {str(e_imagen)}. Local SD: {str(e_sd)}. Local PIL: {str(local_err)}"
                }

# Read prompt from markdown file
PROMPT_PATH = os.path.join(BASE_DIR, "agents", "prompts", "creative_generator.md")
with open(PROMPT_PATH, "r") as f:
    creative_generator_instruction = f.read()

creative_generator_agent = Agent(
    name="automation_and_generation_actions",
    model="gemini-3.1-flash-lite",
    instruction=creative_generator_instruction,
    tools=[mcp_toolset, generate_and_save_ad_image],
    before_model_callback=rate_limit_callback
)
