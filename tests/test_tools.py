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


async def call_tool(server, name, arguments):
    """Helper that calls a tool and returns the list of content items."""
    result = await server.call_tool(name, arguments)
    # FastMCP.call_tool returns a tuple (content_list, raw_dict)
    if isinstance(result, tuple):
        return result[0]
    return result


@pytest.mark.asyncio
async def test_find_entities(server, mock_client):
    mock_client.list_entities.return_value = {
        "data": [{"id": 1, "name": "Arwen"}]
    }

    result = await call_tool(
        server,
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

    result = await call_tool(
        server,
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

    result = await call_tool(
        server,
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

    result = await call_tool(
        server,
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

    result = await call_tool(
        server,
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

    result = await call_tool(
        server,
        "search_entities",
        {"query": "dragon"},
    )
    mock_client.search.assert_called_once_with("dragon")
    data = json.loads(result[0].text)
    assert data["data"][0]["name"] == "Dragon Lord"
