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
