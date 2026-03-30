# Kanka MCP Server

An MCP server that exposes [Kanka](https://kanka.io)'s REST API as MCP tools over long-running HTTP transports, allowing AI assistants to manage worldbuilding campaign data from a permanently running server.

## Setup

1. Install:
   ```bash
   pip install -e ~/dev/kanka_mcp/
   ```

2. Configure credentials in `~/.config/mcp-kanka/.env`:
   ```
   KANKA_TOKEN=your-kanka-api-token
   KANKA_CAMPAIGN_ID=your-campaign-id
   ```

3. Run on your server:
   ```bash
   kanka-mcp-server
   # or with custom host/port:
   kanka-mcp-server --host 0.0.0.0 --port 9000
   ```

4. Put it behind a reverse proxy and keep the process running with your service manager of choice. An example `systemd --user` unit is included in `kanka-mcp-server.service`.

5. Connect clients:
   ```bash
   # Claude Code / SSE clients
   claude mcp add kanka --transport sse https://mcp.bogdandorca.com/sse

   # Codex / streamable HTTP clients
   # Point Codex at:
   # https://mcp.bogdandorca.com/mcp
   ```

## Endpoints

- `/health` - health check
- `/sse` - SSE transport for clients that expect SSE
- `/mcp` - streamable HTTP transport for clients like Codex

## Tools

### Entity Tools
- `find_entities` — List/search entities by type, name, tags, or last sync time
- `get_entity` — Get a single entity with optional posts
- `create_entity` — Create a new entity
- `update_entity` — Update an existing entity
- `delete_entity` — Delete an entity
- `search_entities` — Full-text search across all entities

### Post Tools
- `list_posts` — List posts on an entity
- `create_post` — Create a post on an entity
- `update_post` — Update a post
- `delete_post` — Delete a post

### Supported Entity Types

characters, locations, organisations, notes, journals, quests, races, creatures, families, items, events, calendars, maps, tags
