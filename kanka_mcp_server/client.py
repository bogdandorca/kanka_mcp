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
