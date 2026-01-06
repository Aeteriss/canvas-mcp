#!/usr/bin/env python3
"""
Canvas MCP Server - Always-On Railway Edition
"""
import argparse
import sys
import os
import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import Response
from starlette.requests import Request
import json

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

# Global MCP instance
mcp_instance = None

async def sse_endpoint(request: Request):
    """SSE endpoint that bypasses host validation and properly handles MCP protocol"""
    log_info(f"SSE connection from {request.client}")
    
    # Use the FastMCP instance's actual SSE handler but bypass validation
    # by modifying the request scope before it reaches validation
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "canvas-mcp-production-8183.up.railway.app")
    
    # Fix the scope headers
    new_headers = []
    for name, value in request.scope["headers"]:
        if name == b"host":
            new_headers.append((b"host", railway_domain.encode()))
        else:
            new_headers.append((name, value))
    
    request.scope["headers"] = new_headers
    request.scope["scheme"] = "https"
    request.scope["server"] = (railway_domain, 443)
    
    # Now call the actual MCP SSE handler with the fixed scope
    from mcp.server.fastmcp.server import handle_sse
    
    try:
        return await handle_sse(request.scope, request.receive, request._send)
    except ValueError as e:
        if "Request validation failed" in str(e):
            log_error(f"Host validation failed: {e}")
            # Return a proper error response
            return Response(
                content=json.dumps({"error": "Host validation failed", "details": str(e)}),
                status_code=500,
                media_type="application/json"
            )
        raise

async def health_check(request: Request):
    """Health check endpoint"""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "service": "canvas-mcp"})

def main() -> None:
    """Main entry point configured for Railway SSE deployment."""
    global mcp_instance
    
    if not validate_config():
        print("\nPlease check your Railway Variables.", file=sys.stderr)
        sys.exit(1)

    mcp_instance = create_server()
    register_all_tools(mcp_instance)
    
    # Get the actual FastMCP SSE app
    starlette_app = mcp_instance.sse_app()
    
    # Create a wrapper app that fixes headers before passing to FastMCP
    async def fixed_app(scope, receive, send):
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "canvas-mcp-production-8183.up.railway.app")
        
        # Fix headers in scope
        new_headers = []
        for name, value in scope.get("headers", []):
            if name == b"host":
                new_headers.append((b"host", railway_domain.encode()))
            else:
                new_headers.append((name, value))
        
        scope["headers"] = new_headers
        scope["scheme"] = "https"
        scope["server"] = (railway_domain, 443)
        
        # Pass to the real FastMCP app
        await starlette_app(scope, receive, send)
    
    port = int(os.getenv("PORT", 8080))
    log_info(f"🚀 Canvas MCP Live! Port: {port}")
    
    uvicorn.run(
        fixed_app, 
        host="0.0.0.0", 
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        server_header=False,
        access_log=True
    )

if __name__ == "__main__":
    main()
