# Scout Report ADK Agent

Football recruiting scout report generator using Google's Agent Development Kit (ADK).

## Setup

### 1. Install ADK
```bash
pip install google-adk
```

### 2. Set API Key

**Option A: Using .env file**
```bash
echo 'GOOGLE_API_KEY="your_api_key_here"' > .env
```

**Option B: Using Doppler**
```bash
doppler run -- adk run scout_report_adk
```

## Running

### Command-Line Interface

From the parent directory (kg-mcp):

```bash
adk run scout_report_adk
```

Or with Doppler:

```bash
doppler run -- adk run scout_report_adk
```

### Web Interface

```bash
adk web --port 8000
```

Or with Doppler:

```bash
doppler run -- adk web --port 8000
```

Then open http://localhost:8000 and select "scout_report_agent" from the dropdown.

## Usage

**Specific Query:**
```
Generate a scout report for Bryce Johnson, IOL, Redding High School
```

**Ambiguous Query (will request clarification):**
```
Scout report on John Smith
```

## Project Structure

```
scout_report_adk/
    agent.py                  # ADK root agent (entry point)
    parallel_scout_v5.py      # Multi-agent parallel research system
    scout_report_schema.py    # Pydantic schema
    __init__.py
    .env                      # API keys
```

## Features

- **Multi-Agent Architecture**: 6 specialized research agents running in parallel
- **40+ Citations**: Inline citations from 247Sports, On3, Rivals, MaxPreps, local news
- **Conditional Routing**: Requests clarification for ambiguous players
- **Structured Output**: JSON schema with player info, analysis, stats, citations
