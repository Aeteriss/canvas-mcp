#!/usr/bin/env python3
"""
Canvas MCP Server - Always-On Railway Edition
"""

import argparse
import sys
import os
from mcp.server.fastmcp import FastMCP

from .core.config import get_config, validate_config
from .core.logging import log_error, log_info
from .resources import register_resources_and_prompts
from .tools import (
    register_accessibility_tools,
    register_assignment_tools,
    register_code_execution_tools,
    register_course_tools,
    register_discovery_tools,
    register_discussion_tools,
    register_messaging_tools,
    register_other_tools,
    register_peer_review_comment_tools,
    register_peer_review_tools,
    register_rubric_tools,
    register_student_tools,
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

def main() -> None:
    """Main entry point configured for Railway SSE deployment."""
    if not validate_config():
        print("\nPlease check your Railway Variables.", file=sys.stderr)
        sys.exit(1)

    config = get_config()
    mcp = create_server()
    register_all_tools(mcp)

    # Get the port from Railway environment variables
    port = int(os.getenv("PORT", 8080))

    log_info(f"Starting Canvas MCP server on port {port} using SSE...")
    
    try:
        from starlette.middleware.base import BaseHTTPMiddleware
        import uvicorn

        # 1. Create the base app
        starlette_app = mcp.sse_app()

        # 2. Add a "Host Fixer" Middleware
        # This tells the server: "Ignore the Host header Railway sends and just work."
        class HostFixerMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                # We wipe out the host validation by forcing it to a neutral state
                request.scope["headers"] = [
                    (k, v) for k, v in request.scope["headers"] 
                    if k.lower() != b"host"
                ]
                request.scope["headers"].append((b"host", b"0.0.0.0"))
                return await call_next(request)

        starlette_app.add_middleware(HostFixerMiddleware)

        port = int(os.getenv("PORT", 8080))
        log_info(f"🚀 Final Launch on port {port}")

        # 3. Run with full proxy trust
        uvicorn.run(
            starlette_app, 
            host="0.0.0.0", 
            port=port, 
            proxy_headers=True,
            forwarded_allow_ips="*"
        )
        
    except Exception as e:
        log_error("Server error", exc=e)
        sys.exit(1)

if __name__ == "__main__":
    main()
