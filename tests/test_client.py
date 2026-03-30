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
