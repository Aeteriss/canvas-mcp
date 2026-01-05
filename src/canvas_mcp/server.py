#!/usr/bin/env python3
import argparse
import sys
import os
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uvicorn

# Import your existing tool registrations
from .core.config import get_config, validate_config
from .core.logging import log_error, log_info
from .resources import register_resources_and_prompts
from .tools import (
    register_accessibility_tools, register_assignment_tools,
    register_code_execution_tools, register_course_tools,
    register_discovery_tools, register_discussion_tools,
    register_messaging_tools, register_other_tools,
    register_peer_review_comment_tools, register_peer_review_tools,
    register_rubric_tools, register_student_tools,
)

def create_server() -> FastMCP:
    config = get_config()
    mcp = FastMCP(config.mcp_server_name)
    return mcp

def register_all_tools(mcp: FastMCP) -> None:
    log_info("Registering Canvas MCP tools...")
    register_course_tools(mcp)
    register_assignment_tools(mcp)
    register_discussion_tools(mcp)
    register_other_tools(mcp)
    register_rubric_tools(mcp)
    register_peer_review_tools(mcp)
    register_peer_review_comment_tools(mcp)
    register_messaging_tools(mcp)
    register_student_tools(mcp)
    register_accessibility_tools(mcp)
    register_discovery_tools(mcp)
    register_code_execution_tools(mcp)
    register_resources_and_prompts(mcp)
    log_info("All Canvas MCP tools registered successfully!")

# --- THE POKE & RAILWAY FIX ---
class PokeCompatibilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 1. Fix the "Host" validation error (The 421/ValueError Fix)
        # We strip the Host/Origin headers so the SDK doesn't reject them
        new_headers = [(k, v) for k, v in request.scope["headers"] 
                       if k.lower() not in [b"host", b"origin", b"referer"]]
        request.scope["headers"] = new_headers
        
        # 2. Fix the "POST /sse" 405 error (The Poke Method Fix)
        # If Poke tries to POST to /sse, we redirect it internally to /messages
        if request.method == "POST" and request.url.path == "/sse":
            request.scope["path"] = "/messages"
            
        return await call_next(request)

def main() -> None:
    if not validate_config():
        sys.exit(1)

    mcp = create_server()
    register_all_tools(mcp)

    # Get the Starlette app from FastMCP
    app = mcp.sse_app()
    
    # Apply our "Poke Fix"
    app.add_middleware(PokeCompatibilityMiddleware)

    port = int(os.getenv("PORT", 8080))
    log_info(f"🚀 Canvas MCP Live! Port: {port}")

    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port, 
        proxy_headers=True,
        forwarded_allow_ips="*"
    )

if __name__ == "__main__":
    main()
