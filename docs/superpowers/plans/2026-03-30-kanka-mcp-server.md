# Kanka MCP Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python MCP server that exposes Kanka's REST API as MCP tools over SSE transport, allowing AI assistants to manage worldbuilding campaign data.

**Architecture:** Single Python package using `FastMCP` from the `mcp` SDK for tool registration and SSE transport. An async `KankaClient` class wraps httpx to call the Kanka REST API. The server runs via uvicorn with Starlette handling HTTP routing.

**Tech Stack:** Python 3.10+, `mcp` SDK (FastMCP + SSE), `httpx` (async HTTP), `python-dotenv` (env loading), `uvicorn` (ASGI server)

---

## File Structure

| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Package metadata, dependencies, entry point |
| `kanka_mcp_server/__init__.py` | Package marker, version |
| `kanka_mcp_server/client.py` | `KankaClient` — async Kanka API wrapper |
| `kanka_mcp_server/server.py` | `FastMCP` server, all 10 tool handlers |
| `kanka_mcp_server/__main__.py` | CLI entry point, env loading, uvicorn startup |
| `tests/test_client.py` | Unit tests for KankaClient |
| `tests/test_tools.py` | Unit tests for MCP tool handlers |
| `tests/conftest.py` | Shared fixtures |

**Note:** The spec puts everything in `server.py`. This plan splits the Kanka API client into `client.py` for testability — the client can be tested independently of MCP, and tool handlers can be tested with a mocked client.

---

### Task 1: Project Skeleton and Configuration

**Files:**
- Create: `pyproject.toml`
- Create: `kanka_mcp_server/__init__.py`
- Create: `kanka_mcp_server/__main__.py` (stub)
- Create: `tests/__init__.py`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "kanka-mcp-server"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0",
    "httpx>=0.27",
    "python-dotenv>=1.0",
    "uvicorn>=0.27",
]

[project.scripts]
kanka-mcp-server = "kanka_mcp_server.__main__:main"
```

- [ ] **Step 2: Create `kanka_mcp_server/__init__.py`**

```python
"""Kanka MCP Server — exposes Kanka API as MCP tools over SSE."""
```

- [ ] **Step 3: Create `kanka_mcp_server/__main__.py` (stub)**

```python
def main() -> None:
    print("kanka-mcp-server: not yet implemented")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create `tests/__init__.py`**

Empty file.

- [ ] **Step 5: Install the package in editable mode**

Run: `pip install -e '.[dev]'` (or `pip install -e .` if no dev extras yet)

Verify: `kanka-mcp-server` prints "not yet implemented"

- [ ] **Step 6: Initialize git and commit**

```bash
git init
git add pyproject.toml kanka_mcp_server/__init__.py kanka_mcp_server/__main__.py tests/__init__.py
git commit -m "chore: project skeleton with pyproject.toml and package structure"
```

---

### Task 2: Kanka API Client

**Files:**
- Create: `kanka_mcp_server/client.py`
- Create: `tests/conftest.py`
- Create: `tests/test_client.py`

The `KankaClient` class wraps all Kanka REST API calls. It uses `httpx.AsyncClient` internally and raises no exceptions — instead it returns error dicts that tool handlers can pass through to the user.

- [ ] **Step 1: Write failing tests for KankaClient entity operations**

Create `tests/conftest.py`:

```python
import pytest


FAKE_TOKEN = "test-token-abc123"
FAKE_CAMPAIGN_ID = "12345"
```

Create `tests/test_client.py`:

```python
import json

import httpx
import pytest

from tests.conftest import FAKE_CAMPAIGN_ID, FAKE_TOKEN
from kanka_mcp_server.client import KankaClient


@pytest.fixture
def mock_transport():
    """Returns a list of (request, response) tuples and an httpx.MockTransport."""
    responses = {}

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, str(request.url))
        if key in responses:
            status, data = responses[key]
            return httpx.Response(status, json=data)
        return httpx.Response(404, json={"error": "not mocked"})

    return responses, httpx.MockTransport(handler)


@pytest.fixture
def client(mock_transport):
    responses, transport = mock_transport
    http_client = httpx.AsyncClient(transport=transport)
    c = KankaClient(
        token=FAKE_TOKEN,
        campaign_id=FAKE_CAMPAIGN_ID,
        http_client=http_client,
    )
    return c, responses


@pytest.mark.asyncio
async def test_list_entities(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters"
    responses[("GET", url)] = (200, {"data": [{"id": 1, "name": "Arwen"}]})

    result = await c.list_entities("characters")
    assert result == {"data": [{"id": 1, "name": "Arwen"}]}


@pytest.mark.asyncio
async def test_list_entities_with_filters(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters?name=Arwen&page=2"
    responses[("GET", url)] = (200, {"data": [{"id": 1, "name": "Arwen"}]})

    result = await c.list_entities("characters", name="Arwen", page=2)
    assert result == {"data": [{"id": 1, "name": "Arwen"}]}


@pytest.mark.asyncio
async def test_get_entity(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters/1"
    responses[("GET", url)] = (200, {"data": {"id": 1, "name": "Arwen"}})

    result = await c.get_entity("characters", 1)
    assert result == {"data": {"id": 1, "name": "Arwen"}}


@pytest.mark.asyncio
async def test_create_entity(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters"
    responses[("POST", url)] = (201, {"data": {"id": 2, "name": "Legolas"}})

    result = await c.create_entity("characters", name="Legolas", entry="An elf")
    assert result == {"data": {"id": 2, "name": "Legolas"}}


@pytest.mark.asyncio
async def test_update_entity(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters/1"
    responses[("PUT", url)] = (200, {"data": {"id": 1, "name": "Arwen Updated"}})

    result = await c.update_entity("characters", 1, name="Arwen Updated")
    assert result == {"data": {"id": 1, "name": "Arwen Updated"}}


@pytest.mark.asyncio
async def test_delete_entity(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters/1"
    responses[("DELETE", url)] = (204, None)

    result = await c.delete_entity("characters", 1)
    assert result == {"message": "Entity deleted successfully"}


@pytest.mark.asyncio
async def test_http_error_returns_error_dict(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/characters/999"
    responses[("GET", url)] = (404, {"message": "Model not found"})

    result = await c.get_entity("characters", 999)
    assert "error" in result
    assert result["status_code"] == 404
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`
Expected: ImportError — `kanka_mcp_server.client` does not exist

- [ ] **Step 3: Implement `KankaClient`**

Create `kanka_mcp_server/client.py`:

```python
from typing import Any

import httpx


BASE_URL = "https://kanka.io/api/1.0"


class KankaClient:
    """Async client for the Kanka REST API."""

    def __init__(
        self,
        token: str,
        campaign_id: str,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.campaign_id = campaign_id
        self._http = http_client or httpx.AsyncClient(
            base_url=BASE_URL,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        # If user provided their own client, still set headers
        if http_client is not None:
            self._http.headers.update({
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            })

    def _url(self, path: str) -> str:
        return f"{BASE_URL}/campaigns/{self.campaign_id}/{path}"

    async def _request(
        self, method: str, path: str, **kwargs: Any
    ) -> dict[str, Any]:
        try:
            response = await self._http.request(method, self._url(path), **kwargs)
            response.raise_for_status()
            if response.status_code == 204:
                return {"message": "Entity deleted successfully"}
            return response.json()
        except httpx.HTTPStatusError as e:
            body = {}
            try:
                body = e.response.json()
            except Exception:
                pass
            return {
                "error": body.get("message", str(e)),
                "status_code": e.response.status_code,
            }

    async def list_entities(
        self,
        entity_type: str,
        *,
        name: str | None = None,
        tags: list[int] | None = None,
        last_sync: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if tags is not None:
            for i, tag_id in enumerate(tags):
                params[f"tags[{i}]"] = tag_id
        if last_sync is not None:
            params["lastSync"] = last_sync
        if page is not None:
            params["page"] = page
        if per_page is not None:
            params["per_page"] = per_page
        return await self._request("GET", entity_type, params=params)

    async def get_entity(
        self,
        entity_type: str,
        entity_id: int,
        include_posts: bool = False,
    ) -> dict[str, Any]:
        params = {}
        if include_posts:
            params["related"] = 1
        return await self._request(
            "GET", f"{entity_type}/{entity_id}", params=params or None
        )

    async def create_entity(
        self, entity_type: str, **fields: Any
    ) -> dict[str, Any]:
        return await self._request("POST", entity_type, json=fields)

    async def update_entity(
        self, entity_type: str, entity_id: int, **fields: Any
    ) -> dict[str, Any]:
        return await self._request(
            "PUT", f"{entity_type}/{entity_id}", json=fields
        )

    async def delete_entity(
        self, entity_type: str, entity_id: int
    ) -> dict[str, Any]:
        return await self._request("DELETE", f"{entity_type}/{entity_id}")

    async def search(self, query: str) -> dict[str, Any]:
        return await self._request(
            "GET", f"search/{query}"
        )

    async def list_posts(self, entity_id: int) -> dict[str, Any]:
        return await self._request("GET", f"entities/{entity_id}/posts")

    async def create_post(
        self, entity_id: int, **fields: Any
    ) -> dict[str, Any]:
        return await self._request(
            "POST", f"entities/{entity_id}/posts", json=fields
        )

    async def update_post(
        self, entity_id: int, post_id: int, **fields: Any
    ) -> dict[str, Any]:
        return await self._request(
            "PUT", f"entities/{entity_id}/posts/{post_id}", json=fields
        )

    async def delete_post(
        self, entity_id: int, post_id: int
    ) -> dict[str, Any]:
        return await self._request(
            "DELETE", f"entities/{entity_id}/posts/{post_id}"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: All 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add kanka_mcp_server/client.py tests/conftest.py tests/test_client.py
git commit -m "feat: add KankaClient with async Kanka API wrapper"
```

---

### Task 3: Post Operations Tests

**Files:**
- Modify: `tests/test_client.py`

- [ ] **Step 1: Add tests for post operations**

Append to `tests/test_client.py`:

```python
@pytest.mark.asyncio
async def test_search(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/search/dragon"
    responses[("GET", url)] = (200, {"data": [{"id": 5, "name": "Dragon Lord"}]})

    result = await c.search("dragon")
    assert result == {"data": [{"id": 5, "name": "Dragon Lord"}]}


@pytest.mark.asyncio
async def test_list_posts(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/entities/1/posts"
    responses[("GET", url)] = (200, {"data": [{"id": 10, "name": "Backstory"}]})

    result = await c.list_posts(1)
    assert result == {"data": [{"id": 10, "name": "Backstory"}]}


@pytest.mark.asyncio
async def test_create_post(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/entities/1/posts"
    responses[("POST", url)] = (201, {"data": {"id": 11, "name": "New Note"}})

    result = await c.create_post(1, name="New Note", entry="Some text")
    assert result == {"data": {"id": 11, "name": "New Note"}}


@pytest.mark.asyncio
async def test_update_post(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/entities/1/posts/10"
    responses[("PUT", url)] = (200, {"data": {"id": 10, "name": "Updated"}})

    result = await c.update_post(1, 10, name="Updated")
    assert result == {"data": {"id": 10, "name": "Updated"}}


@pytest.mark.asyncio
async def test_delete_post(client):
    c, responses = client
    url = f"https://kanka.io/api/1.0/campaigns/{FAKE_CAMPAIGN_ID}/entities/1/posts/10"
    responses[("DELETE", url)] = (204, None)

    result = await c.delete_post(1, 10)
    assert result == {"message": "Entity deleted successfully"}
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`
Expected: All 12 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_client.py
git commit -m "test: add post and search operation tests for KankaClient"
```

---

### Task 4: MCP Server with Entity Tools

**Files:**
- Create: `kanka_mcp_server/server.py`
- Create: `tests/test_tools.py`

- [ ] **Step 1: Write failing tests for entity tools**

Create `tests/test_tools.py`:

```python
import json
from unittest.mock import AsyncMock, patch

import pytest

from kanka_mcp_server.server import create_server


@pytest.fixture
def mock_client():
    client = AsyncMock()
    return client


@pytest.fixture
def server(mock_client):
    return create_server(mock_client)


@pytest.mark.asyncio
async def test_find_entities(server, mock_client):
    mock_client.list_entities.return_value = {
        "data": [{"id": 1, "name": "Arwen"}]
    }

    result = await server.call_tool(
        "find_entities",
        {"entity_type": "characters", "name": "Arwen"},
    )
    mock_client.list_entities.assert_called_once_with(
        "characters", name="Arwen", tags=None, last_sync=None, page=None, per_page=None
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["data"][0]["name"] == "Arwen"


@pytest.mark.asyncio
async def test_get_entity(server, mock_client):
    mock_client.get_entity.return_value = {
        "data": {"id": 1, "name": "Arwen"}
    }

    result = await server.call_tool(
        "get_entity",
        {"entity_type": "characters", "entity_id": 1},
    )
    mock_client.get_entity.assert_called_once_with("characters", 1, include_posts=False)
    data = json.loads(result[0].text)
    assert data["data"]["name"] == "Arwen"


@pytest.mark.asyncio
async def test_create_entity(server, mock_client):
    mock_client.create_entity.return_value = {
        "data": {"id": 2, "name": "Legolas"}
    }

    result = await server.call_tool(
        "create_entity",
        {"entity_type": "characters", "name": "Legolas", "entry": "An elf prince"},
    )
    mock_client.create_entity.assert_called_once_with(
        "characters", name="Legolas", entry="An elf prince"
    )
    data = json.loads(result[0].text)
    assert data["data"]["name"] == "Legolas"


@pytest.mark.asyncio
async def test_update_entity(server, mock_client):
    mock_client.update_entity.return_value = {
        "data": {"id": 1, "name": "Arwen Updated"}
    }

    result = await server.call_tool(
        "update_entity",
        {"entity_type": "characters", "entity_id": 1, "name": "Arwen Updated"},
    )
    mock_client.update_entity.assert_called_once_with(
        "characters", 1, name="Arwen Updated"
    )
    data = json.loads(result[0].text)
    assert data["data"]["name"] == "Arwen Updated"


@pytest.mark.asyncio
async def test_delete_entity(server, mock_client):
    mock_client.delete_entity.return_value = {"message": "Entity deleted successfully"}

    result = await server.call_tool(
        "delete_entity",
        {"entity_type": "characters", "entity_id": 1},
    )
    mock_client.delete_entity.assert_called_once_with("characters", 1)
    data = json.loads(result[0].text)
    assert data["message"] == "Entity deleted successfully"


@pytest.mark.asyncio
async def test_search_entities(server, mock_client):
    mock_client.search.return_value = {
        "data": [{"id": 5, "name": "Dragon Lord"}]
    }

    result = await server.call_tool(
        "search_entities",
        {"query": "dragon"},
    )
    mock_client.search.assert_called_once_with("dragon")
    data = json.loads(result[0].text)
    assert data["data"][0]["name"] == "Dragon Lord"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools.py -v`
Expected: ImportError — `create_server` does not exist

- [ ] **Step 3: Implement MCP server with entity tools**

Create `kanka_mcp_server/server.py`:

```python
import json
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from kanka_mcp_server.client import KankaClient


ENTITY_TYPES = [
    "characters", "locations", "organisations", "notes", "journals",
    "quests", "races", "creatures", "families", "items", "events",
    "calendars", "maps", "tags",
]

ENTITY_TYPES_DESC = ", ".join(ENTITY_TYPES)


def _text(data: Any) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps(data, indent=2))]


def create_server(client: KankaClient) -> FastMCP:
    mcp = FastMCP("Kanka MCP Server")

    @mcp.tool()
    async def find_entities(
        entity_type: str,
        name: str | None = None,
        tags: list[int] | None = None,
        last_sync: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> list[TextContent]:
        """List/search entities in the campaign.

        Args:
            entity_type: One of: {ENTITY_TYPES_DESC}
            name: Partial name match filter
            tags: Array of tag IDs (AND logic)
            last_sync: ISO 8601 datetime — only return entities modified after this time
            page: Page number for pagination
            per_page: Results per page
        """
        result = await client.list_entities(
            entity_type, name=name, tags=tags, last_sync=last_sync,
            page=page, per_page=per_page,
        )
        return _text(result)

    @mcp.tool()
    async def get_entity(
        entity_type: str,
        entity_id: int,
        include_posts: bool = False,
    ) -> list[TextContent]:
        """Get a single entity by ID.

        Args:
            entity_type: One of: {ENTITY_TYPES_DESC}
            entity_id: The entity's ID
            include_posts: Whether to include the entity's posts
        """
        result = await client.get_entity(entity_type, entity_id, include_posts=include_posts)
        return _text(result)

    @mcp.tool()
    async def create_entity(
        entity_type: str,
        name: str,
        entry: str | None = None,
        type: str | None = None,
        tags: list[int] | None = None,
        is_private: bool | None = None,
    ) -> list[TextContent]:
        """Create a new entity in the campaign.

        Args:
            entity_type: One of: {ENTITY_TYPES_DESC}
            name: Entity name
            entry: Entity description/content (HTML)
            type: Sub-type of the entity
            tags: Array of tag IDs to attach
            is_private: Whether the entity is private
        """
        fields: dict[str, Any] = {"name": name}
        if entry is not None:
            fields["entry"] = entry
        if type is not None:
            fields["type"] = type
        if tags is not None:
            fields["tags"] = tags
        if is_private is not None:
            fields["is_private"] = is_private
        result = await client.create_entity(entity_type, **fields)
        return _text(result)

    @mcp.tool()
    async def update_entity(
        entity_type: str,
        entity_id: int,
        name: str | None = None,
        entry: str | None = None,
        type: str | None = None,
        tags: list[int] | None = None,
        is_private: bool | None = None,
    ) -> list[TextContent]:
        """Update an existing entity.

        Args:
            entity_type: One of: {ENTITY_TYPES_DESC}
            entity_id: The entity's ID
            name: Updated name
            entry: Updated description/content (HTML)
            type: Updated sub-type
            tags: Updated tag IDs
            is_private: Updated privacy setting
        """
        fields: dict[str, Any] = {}
        if name is not None:
            fields["name"] = name
        if entry is not None:
            fields["entry"] = entry
        if type is not None:
            fields["type"] = type
        if tags is not None:
            fields["tags"] = tags
        if is_private is not None:
            fields["is_private"] = is_private
        result = await client.update_entity(entity_type, entity_id, **fields)
        return _text(result)

    @mcp.tool()
    async def delete_entity(
        entity_type: str,
        entity_id: int,
    ) -> list[TextContent]:
        """Delete an entity from the campaign.

        Args:
            entity_type: One of: {ENTITY_TYPES_DESC}
            entity_id: The entity's ID
        """
        result = await client.delete_entity(entity_type, entity_id)
        return _text(result)

    @mcp.tool()
    async def search_entities(
        query: str,
    ) -> list[TextContent]:
        """Full-text search across all entities in the campaign.

        Args:
            query: Search query string
        """
        result = await client.search(query)
        return _text(result)

    @mcp.tool()
    async def list_posts(
        entity_id: int,
    ) -> list[TextContent]:
        """List all posts on an entity.

        Args:
            entity_id: The entity's ID (not the typed entity ID — use the top-level entity ID)
        """
        result = await client.list_posts(entity_id)
        return _text(result)

    @mcp.tool()
    async def create_post(
        entity_id: int,
        name: str,
        entry: str | None = None,
        is_private: bool | None = None,
    ) -> list[TextContent]:
        """Create a new post on an entity.

        Args:
            entity_id: The entity's ID
            name: Post title
            entry: Post content (HTML)
            is_private: Whether the post is private
        """
        fields: dict[str, Any] = {"name": name}
        if entry is not None:
            fields["entry"] = entry
        if is_private is not None:
            fields["is_private"] = is_private
        result = await client.create_post(entity_id, **fields)
        return _text(result)

    @mcp.tool()
    async def update_post(
        entity_id: int,
        post_id: int,
        name: str | None = None,
        entry: str | None = None,
        is_private: bool | None = None,
    ) -> list[TextContent]:
        """Update an existing post on an entity.

        Args:
            entity_id: The entity's ID
            post_id: The post's ID
            name: Updated title
            entry: Updated content (HTML)
            is_private: Updated privacy setting
        """
        fields: dict[str, Any] = {}
        if name is not None:
            fields["name"] = name
        if entry is not None:
            fields["entry"] = entry
        if is_private is not None:
            fields["is_private"] = is_private
        result = await client.update_post(entity_id, post_id, **fields)
        return _text(result)

    @mcp.tool()
    async def delete_post(
        entity_id: int,
        post_id: int,
    ) -> list[TextContent]:
        """Delete a post from an entity.

        Args:
            entity_id: The entity's ID
            post_id: The post's ID
        """
        result = await client.delete_post(entity_id, post_id)
        return _text(result)

    return mcp
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add kanka_mcp_server/server.py tests/test_tools.py
git commit -m "feat: add MCP server with entity and post tools"
```

---

### Task 5: Post Tool Tests

**Files:**
- Modify: `tests/test_tools.py`

- [ ] **Step 1: Add tests for post tools**

Append to `tests/test_tools.py`:

```python
@pytest.mark.asyncio
async def test_list_posts(server, mock_client):
    mock_client.list_posts.return_value = {
        "data": [{"id": 10, "name": "Backstory"}]
    }

    result = await server.call_tool("list_posts", {"entity_id": 1})
    mock_client.list_posts.assert_called_once_with(1)
    data = json.loads(result[0].text)
    assert data["data"][0]["name"] == "Backstory"


@pytest.mark.asyncio
async def test_create_post(server, mock_client):
    mock_client.create_post.return_value = {
        "data": {"id": 11, "name": "New Note"}
    }

    result = await server.call_tool(
        "create_post",
        {"entity_id": 1, "name": "New Note", "entry": "Content"},
    )
    mock_client.create_post.assert_called_once_with(1, name="New Note", entry="Content")
    data = json.loads(result[0].text)
    assert data["data"]["name"] == "New Note"


@pytest.mark.asyncio
async def test_update_post(server, mock_client):
    mock_client.update_post.return_value = {
        "data": {"id": 10, "name": "Updated"}
    }

    result = await server.call_tool(
        "update_post",
        {"entity_id": 1, "post_id": 10, "name": "Updated"},
    )
    mock_client.update_post.assert_called_once_with(1, 10, name="Updated")
    data = json.loads(result[0].text)
    assert data["data"]["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_post(server, mock_client):
    mock_client.delete_post.return_value = {"message": "Entity deleted successfully"}

    result = await server.call_tool(
        "delete_post",
        {"entity_id": 1, "post_id": 10},
    )
    mock_client.delete_post.assert_called_once_with(1, 10)
    data = json.loads(result[0].text)
    assert data["message"] == "Entity deleted successfully"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `pytest tests/test_tools.py -v`
Expected: All 10 tests PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_tools.py
git commit -m "test: add post tool tests"
```

---

### Task 6: CLI Entry Point and Health Check

**Files:**
- Modify: `kanka_mcp_server/__main__.py`

- [ ] **Step 1: Implement the CLI entry point**

Replace `kanka_mcp_server/__main__.py` with:

```python
import argparse
import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from kanka_mcp_server.client import KankaClient
from kanka_mcp_server.server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Kanka MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind to")
    args = parser.parse_args()

    env_path = Path.home() / ".config" / "mcp-kanka" / ".env"
    load_dotenv(env_path)

    token = os.environ.get("KANKA_TOKEN")
    campaign_id = os.environ.get("KANKA_CAMPAIGN_ID")

    if not token:
        print("Error: KANKA_TOKEN not set. Set it in ~/.config/mcp-kanka/.env", file=sys.stderr)
        sys.exit(1)
    if not campaign_id:
        print("Error: KANKA_CAMPAIGN_ID not set. Set it in ~/.config/mcp-kanka/.env", file=sys.stderr)
        sys.exit(1)

    client = KankaClient(token=token, campaign_id=campaign_id)
    mcp = create_server(client)

    async def health(request):
        return JSONResponse({"status": "ok", "campaign_id": campaign_id})

    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/", app=mcp.sse_app()),
        ],
    )

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify the CLI starts (manual smoke test)**

Prerequisite: Create `~/.config/mcp-kanka/.env` with:
```
KANKA_TOKEN=your-token-here
KANKA_CAMPAIGN_ID=your-campaign-id
```

Run: `python -m kanka_mcp_server --help`
Expected: Shows help text with `--host` and `--port` options

Run: `python -m kanka_mcp_server` (Ctrl+C to stop after verifying startup)
Expected: Uvicorn starts on `127.0.0.1:8765`

- [ ] **Step 3: Commit**

```bash
git add kanka_mcp_server/__main__.py
git commit -m "feat: add CLI entry point with env loading and health check"
```

---

### Task 7: Deployment Files

**Files:**
- Create: `kanka-mcp-server.service`
- Create: `nginx-kanka-mcp.conf`

- [ ] **Step 1: Create systemd user service file**

Create `kanka-mcp-server.service`:

```ini
[Unit]
Description=Kanka MCP Server
After=network.target

[Service]
Type=simple
ExecStart=%h/.local/bin/kanka-mcp-server --host 127.0.0.1 --port 8765
Restart=on-failure
RestartSec=5
Environment=PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin

[Install]
WantedBy=default.target
```

- [ ] **Step 2: Create nginx config**

Create `nginx-kanka-mcp.conf`:

```nginx
server {
    listen 443 ssl;
    server_name mcp.bogdandorca.com;

    ssl_certificate /etc/letsencrypt/live/mcp.bogdandorca.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mcp.bogdandorca.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE support
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        chunked_transfer_encoding off;
        proxy_read_timeout 86400s;
    }
}

server {
    listen 80;
    server_name mcp.bogdandorca.com;
    return 301 https://$host$request_uri;
}
```

- [ ] **Step 3: Commit**

```bash
git add kanka-mcp-server.service nginx-kanka-mcp.conf
git commit -m "chore: add systemd service and nginx config for deployment"
```

---

### Task 8: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

Create `README.md`:

```markdown
# Kanka MCP Server

An MCP server that exposes [Kanka](https://kanka.io)'s REST API as MCP tools over SSE transport, allowing AI assistants to manage worldbuilding campaign data.

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

3. Run:
   ```bash
   kanka-mcp-server
   # or with custom host/port:
   kanka-mcp-server --host 0.0.0.0 --port 9000
   ```

4. Connect Claude Code:
   ```bash
   claude mcp add kanka --transport sse https://mcp.bogdandorca.com/sse
   ```

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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| Python package structure | Task 1 |
| KankaClient (async httpx, auth, error handling) | Task 2, 3 |
| 6 entity tools (find, get, create, update, delete, search) | Task 4 |
| 4 post tools (list, create, update, delete) | Task 5 |
| CLI entry point (--host, --port, env loading) | Task 6 |
| Health check endpoint | Task 6 |
| SSE transport via FastMCP | Task 6 |
| Systemd service file | Task 7 |
| Nginx reverse proxy config | Task 7 |
| README | Task 8 |
| 14 supported entity types | Task 4 (ENTITY_TYPES list) |
| Config from ~/.config/mcp-kanka/.env | Task 6 |
| Error handling (HTTPStatusError -> error dict) | Task 2 |
