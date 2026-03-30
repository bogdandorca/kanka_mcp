# Kanka MCP Server — Design Spec

## Overview

A Python MCP server exposing Kanka's REST API as MCP tools over SSE/HTTP transport, allowing remote AI assistants to manage worldbuilding campaign data.

## Architecture

Single Python package (`kanka_mcp_server/`) with three files:

- `__init__.py` — package marker
- `server.py` — MCP server definition, Kanka API client class, all 10 tool handlers
- `__main__.py` — CLI entry point (`--host`/`--port`), env loading, uvicorn startup

### Transport

- SSE transport via `mcp` SDK's `SseServerTransport`
- HTTP layer: Starlette + Uvicorn
- Routes:
  - `GET /sse` — SSE connection endpoint
  - `POST /messages/` — MCP message handling
  - `GET /health` — health check returning `{"status": "ok", "campaign_id": "..."}`

### Kanka API Client

- Async HTTP client using `httpx.AsyncClient`
- Base URL: `https://kanka.io/api/1.0`
- Auth: Bearer token via `Authorization` header
- All endpoints scoped to `/campaigns/{campaign_id}/`
- Error handling: catch `httpx.HTTPStatusError`, return error details as `TextContent`

## Configuration

Environment variables loaded from `~/.config/mcp-kanka/.env`:

| Variable | Description |
|----------|-------------|
| `KANKA_TOKEN` | Bearer token for Kanka API |
| `KANKA_CAMPAIGN_ID` | Campaign ID to operate on |

Server defaults: `127.0.0.1:8765`, overridable via `--host`/`--port` CLI args.

## MCP Tools

### Entity Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `find_entities` | List/search entities | `entity_type` (required), `name` (partial match), `tags` (array of IDs, AND logic), `last_sync` (ISO 8601, maps to `lastSync`), `page`, `per_page` |
| `get_entity` | Get single entity | `entity_type`, `entity_id`, `include_posts` (bool) |
| `create_entity` | Create entity | `entity_type`, `name`, `entry`, `type`, `tags`, `is_private` |
| `update_entity` | Update entity | `entity_type`, `entity_id`, `name`, `entry`, `type`, `tags`, `is_private` |
| `delete_entity` | Delete entity | `entity_type`, `entity_id` |
| `search_entities` | Full-text search | `query` — via `/campaigns/{id}/search/{query}` |

### Post Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `list_posts` | List posts on entity | `entity_id` |
| `create_post` | Create post | `entity_id`, `name`, `entry`, `is_private` |
| `update_post` | Update post | `entity_id`, `post_id`, `name`, `entry`, `is_private` |
| `delete_post` | Delete post | `entity_id`, `post_id` |

### Supported Entity Types

`characters`, `locations`, `organisations`, `notes`, `journals`, `quests`, `races`, `creatures`, `families`, `items`, `events`, `calendars`, `maps`, `tags`

## Project Structure

```
~/dev/kanka_mcp/
├── kanka_mcp_server/
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py
├── pyproject.toml
├── kanka-mcp-server.service
├── nginx-kanka-mcp.conf
└── README.md
```

## Dependencies

- Python 3.10+
- `mcp` — MCP SDK (SSE transport)
- `starlette` — ASGI framework
- `uvicorn` — ASGI server
- `httpx` — async HTTP client
- `python-dotenv` — env file loading

## Deployment

1. Install: `pip install -e ~/dev/kanka_mcp/`
2. Systemd user service (`kanka-mcp-server.service`) for process management
3. Nginx reverse proxy on `mcp.bogdandorca.com`
4. SSL via Certbot/Let's Encrypt
5. Client connection: `claude mcp add kanka --transport sse https://mcp.bogdandorca.com/sse`

## Error Handling

- `httpx.HTTPStatusError` caught and returned as error JSON in `TextContent`
- Missing/invalid env vars fail fast at startup with clear error messages
