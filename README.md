# KG MCP

This project hosts an mcp that provides tools to extract/search and insert sports associated information into a knowledge graph, and to generate scout reports for players.

## Local Development

### Setup Python

It is recommended to use [pyenv](https://github.com/pyenv/pyenv) for managing versions of python.

- Install pyenv:

```bash
brew install pyenv
```

- Download and install the python version specified in [.python-version](./.python-version)

```bash
pyenv install
```

- Start using the installed python version:

```bash
pyenv local
```

### Environment Variables

We use [Doppler](https://www.doppler.com/) for most environment variables.

- Log in to Doppler in your web browser. The credentials for Doppler are in the 1Password vault.

- Install the Doppler CLI:

```bash
brew install dopplerhq/cli/doppler
# or make install-doppler
```

- Log in to the Doppler CLI:

```bash
doppler login
```

- Configure environment variables for an application:

```bash
doppler setup
```

In general, keep environment variables -- especially secrets -- in Doppler. Use
`.env` only for local overrides.

### Run the mcp server

```bash
uv run poe dev
```

### Test locally using an mcp client

1. Make sure your `.env` file has the following variables set:
```bash
KG_MCP_SERVER=http://127.0.0.1:8001/mcp
```
2. Run the MCP server locally (see above).
3. In another terminal, run the curation bot, which behaves like a root agent:
```bash
uv run python curation_bot.py
```

## Test Coverage

> Run all tests

```bash
uv run poe test
```

> Execute a specific test

```bash
uv run poe test_file tests/<path_to_file>.py
```

All tests should go inside the `tests` folder sitting at the root of the directory

## Deploy

1. Merge to main branch, and git push.
2. Check that it shows up at: https://kg-mcp-762632998010.us-central1.run.app
