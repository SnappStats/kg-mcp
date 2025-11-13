# Scout Report Agent - ADK Project

This is a Google Agent Development Kit (ADK) project for generating comprehensive football recruiting scout reports.

## Project Structure

```
scout_report_agent/
    agent.py                  # ADK root agent (entry point)
    parallel_scout_v5.py      # Multi-agent parallel research system
    scout_report_schema.py    # Pydantic schema for scout reports
    test_parallel_v5.py       # Test script
    .env                      # API keys (or use Doppler)
    __init__.py
```

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

**Option B: Using Doppler (recommended)**
```bash
doppler setup
```

## Running the Agent

### Command-Line Interface

Run from the parent directory (kg-mcp):

```bash
adk run scout_report_agent
```

Or with Doppler:

```bash
doppler run -- adk run scout_report_agent
```

### Web Interface

Start the web UI:

```bash
adk web --port 8000
```

Or with Doppler:

```bash
doppler run -- adk web --port 8000
```

Then open http://localhost:8000 and select "scout_report_agent" from the dropdown.

## Usage Examples

### Specific Player Query
```
User: Generate a scout report for Bryce Johnson, IOL, Redding High School
```

### Ambiguous Query (requires clarification)
```
User: Scout report on John Smith
Agent: I found multiple players named John Smith. Could you provide the high school, position, or graduation year?
User: John Smith, QB, Lincoln High, class of 2026
```

## Features

- **Multi-Agent Architecture**: 6 specialized research agents running in parallel
  - Baseline: Player identification
  - Physical: Measurables, athletic testing, camp circuit
  - Performance: Stats, key games, team context
  - Recruiting: Rankings, offers, visits, NIL
  - Background: Identity, family, academics, media
  - Intangibles: Leadership, character, projections

- **Grounding Metadata**: 40+ inline citations from verified sources
  - 247Sports, On3, Rivals, ESPN
  - MaxPreps, local news, athletic.net
  - Citations formatted as: ([Source Name](url))

- **Conditional Routing**: Requests clarification for ambiguous players

- **Structured Output**: JSON schema with player info, analysis, stats, citations

## Testing

You can still use the original test script:

```bash
python test_parallel_v5.py
```

Or with Doppler:

```bash
doppler run -- python test_parallel_v5.py
```

## Architecture

The `root_agent` in `agent.py` wraps the two-phase execution system from `parallel_scout_v5.py`:

1. **Phase 1**: Baseline agent identifies the player
   - If ambiguous: returns clarification request
   - If clear: proceeds to Phase 2

2. **Phase 2**: Parallel research + formatting
   - 5 specialized agents run in parallel
   - Formatter synthesizes into structured JSON
   - Citations converted to inline markdown

This architecture preserves grounding metadata (40+ citations) while maintaining conditional routing capabilities.
