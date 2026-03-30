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
            entity_type: One of: characters, locations, organisations, notes, journals, quests, races, creatures, families, items, events, calendars, maps, tags
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
            entity_type: One of: characters, locations, organisations, notes, journals, quests, races, creatures, families, items, events, calendars, maps, tags
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
            entity_type: One of: characters, locations, organisations, notes, journals, quests, races, creatures, families, items, events, calendars, maps, tags
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
            entity_type: One of: characters, locations, organisations, notes, journals, quests, races, creatures, families, items, events, calendars, maps, tags
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
            entity_type: One of: characters, locations, organisations, notes, journals, quests, races, creatures, families, items, events, calendars, maps, tags
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
