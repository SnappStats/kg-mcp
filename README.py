
## Run locally

1. Make sure you are properly authenticated with Google Cloud:
```bash
gcloud auth application-default login
```
2. Run the MCP server:
```bash
uv run fastmcp run server.py --transport http --port 8001
```

## Test locally

1. Make sure your `.env` file has the following variables set:
```bash
KG_MCP_SERVER=http://127.0.0.1:8001/mcp
```
2. Run the MCP server locally (see above).
3. In another terminal, run the curation bot, which behaves like a root agent:
```bash
uv run python curation_bot.py
```

## Deploy

1. Merge to main branch, and git push.
2. Check that it shows up at: https://kg-mcp-762632998010.us-central1.run.app
