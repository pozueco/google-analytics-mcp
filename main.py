#!/usr/bin/env python

# Copyright 2026 Google LLC All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Cloud Run entry point for serving Analytics MCP over HTTP transports."""

import os

import uvicorn
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

from analytics_mcp.coordinator import app as mcp_server


async def healthz(_: Request) -> JSONResponse:
    """Lightweight health endpoint for container probes."""
    return JSONResponse({"status": "ok"})


if hasattr(mcp_server, "streamable_http_app"):
    app = mcp_server.streamable_http_app(
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        host="0.0.0.0",
        custom_starlette_routes=[
            Route("/", endpoint=healthz, methods=["GET"]),
            Route("/healthz", endpoint=healthz, methods=["GET"]),
        ],
    )
else:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp_server.run(
                streams[0],
                streams[1],
                mcp_server.create_initialization_options(),
            )
        return Response()

    app = Starlette(
        routes=[
            Route("/", endpoint=healthz, methods=["GET"]),
            Route("/healthz", endpoint=healthz, methods=["GET"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ]
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
