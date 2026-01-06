#!/usr/bin/env python3
"""
Canvas MCP Server - Always-On Railway Edition
"""
import argparse
import sys
import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.middleware.base import BaseHTTPMiddleware

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

# CRITICAL FIX: Monkey patch the MCP transport security to disable host validation
import mcp.server.sse as mcp_sse

original_connect_sse = mcp_sse.connect_sse

async def patched_connect_sse(scope, receive, send, *, handle_request):
    # Remove the host validation that's causing the 421 errors
    # by not calling the original validation
    try:
        async with original_connect_sse(scope, receive, send, handle_request=handle_request) as session:
            yield session
    except ValueError as e:
        if "Request validation failed" in str(e):
            # Bypass the validation error and continue anyway
            log_info("Bypassing host validation for Railway/Poke compatibility")
            # Create a minimal session without validation
            from mcp.server.sse import SseServerSession
            from starlette.requests import Request
            request = Request(scope, receive, send)
            session = SseServerSession(request, handle_request)
            yield session
        else:
            raise

# Apply the monkey patch
mcp_sse.connect_sse = patched_connect_sse

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

class PokeCompatibilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Get Railway domain
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "canvas-mcp-production-8183.up.railway.app")
        
        # Fix the host header before any validation happens
        new_headers = []
        for name, value in request.scope["headers"]:
            if name == b"host":
                new_headers.append((b"host", railway_domain.encode()))
            else:
                new_headers.append((name, value))
        
        request.scope["headers"] = new_headers
        request.scope["scheme"] = "https"
        request.scope["server"] = (railway_domain, 443)
            
        return await call_next(request)

def main() -> None:
    """Main entry point configured for Railway SSE deployment."""
    if not validate_config():
        print("\nPlease check your Railway Variables.", file=sys.stderr)
        sys.exit(1)

    mcp = create_server()
    register_all_tools(mcp)
    
    # Convert FastMCP to a web app and add our Poke-fix middleware
    starlette_app = mcp.sse_app()
    starlette_app.add_middleware(PokeCompatibilityMiddleware)
    
    port = int(os.getenv("PORT", 8080))
    log_info(f"🚀 Canvas MCP Live! Port: {port}")
    
    uvicorn.run(
        starlette_app, 
        host="0.0.0.0", 
        port=port, 
        proxy_headers=True,
        forwarded_allow_ips="*",
        server_header=False
    )

if __name__ == "__main__":
    main()
