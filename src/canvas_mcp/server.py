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
        # Railway automatically provides this variable
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "canvas-mcp-production-8183.up.railway.app")
        
        # Create a new headers list with corrected host
        new_headers = []
        host_set = False
        
        for name, value in request.scope["headers"]:
            if name == b"host":
                # Replace with the correct Railway domain
                new_headers.append((b"host", railway_domain.encode() if isinstance(railway_domain, str) else railway_domain))
                host_set = True
            else:
                new_headers.append((name, value))
        
        # Ensure host header exists
        if not host_set:
            new_headers.append((b"host", railway_domain.encode() if isinstance(railway_domain, str) else railway_domain))
        
        # Update the scope with corrected headers
        request.scope["headers"] = new_headers
        
        # Also update server name and port to match
        request.scope["server"] = (railway_domain if isinstance(railway_domain, str) else railway_domain.decode(), 443)
        request.scope["scheme"] = "https"
            
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
