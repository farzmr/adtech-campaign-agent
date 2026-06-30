# ⚡ AdTech Multi-Agent Ad Optimizer

A multi-agent display ad optimization system built using **Google ADK**, **Gemini 2.5 Flash**, **Gemini Imagen**, and **Streamlit**. 

This system automates the creative review process, calculates ad performance highlights across device/time segment metrics, and automatically applies modifications (like pausing low-performing ads, writing new copy variants, and generating matching ad creatives).

---

## 🏗️ Project Architecture

The system consists of the following components:

### 1. The MCP Data Server (`mcp_server/server.py`)
Acts as the central data storage layer communicating over the standard stdio protocol. It exposes:
* `get_campaigns` and `get_ads`
* `get_performance_summary` (aggregates raw metrics like clicks, impressions, and conversions grouped by `device` and `time_of_day`)
* `update_ad_status` (enforces strict input validation on `active`/`paused` statuses)
* `create_ad` (handles strict parameter check and sequential ID assignment)

### 2. Specialized ADK Agents (`agents/`)
* **Creative Analyzer (`agents/creative_analyzer.py`)**: Reviews ad headline, copy, and tone to generate a 0–100 quality score and flag recommendations.
* **Performance Stats (`agents/performance_stats.py`)**: Analyzes MCP stats and highlights best segments (CTR, ROAS, conversions) according to the campaign's specific goal (conversions, traffic, or awareness).
* **Creative Generator (`agents/creative_generator.py`)**: Executes optimization actions: pauses weak ads, creates a new copy variant, and calls the unified Google GenAI SDK (`gemini-2.5-flash-image`) to save a new ad image.

### 3. Orchestration & Custom ADK Skill
* **Orchestrator (`orchestrator.py`)**: Chains the agents together in sequence inside an `InMemorySessionService`, passing intermediate findings forward to compile a complete campaign optimization run.
* **ADK Skill (`skills/optimize_campaign.py`)**: Wraps the orchestrator into a single callable function `optimize_campaign(campaign_id)` that is safe to trigger inside both async and sync scripts.

### 4. Streamlit Frontend (`app.py`)
Provides an interactive, dark-themed control center to configure optimizations, review agent audit results, and view newly generated ad display banners side-by-side.

---

## 🔒 Security & Guardrails

* **Active Ads Guardrail**: The orchestrator contains an interception layer that blocks the Generator from running if the campaign has 1 or fewer active ads left. This prevents the system from accidentally leaving a campaign with zero running ads.
* **Input Validation**: The MCP server strictly validates parameters for new ads (missing fields) and status changes (invalid values).
* **Credential Isolation**: All keys are retrieved dynamically using `python-dotenv` from the `.env` file and are never hardcoded.
* **Safety Confirmation**: Streamlit forces the user to check a parameter confirmation box before enabling the execution trigger.

---

## 🚀 Getting Started

### 1. Installation
Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the template file to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your Google API key:
```env
GEMINI_API_KEY=your_actual_gemini_key_here
```

### 3. Launch the Application
Run the Streamlit frontend locally:
```bash
streamlit run app.py
```
*Note: The app will automatically seed the `data/` directory with sample campaigns, ads, and performance metrics on first launch if they do not already exist.*
