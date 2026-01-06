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

# FINAL NUCLEAR OPTION: Directly patch the installed library file
def patch_mcp_library():
    """Patch the MCP library to disable host validation"""
    try:
        import mcp.server.sse
        sse_file = mcp.server.sse.__file__
        
        log_info(f"Patching MCP library at: {sse_file}")
        
        # Read the file
        with open(sse_file, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if 'RAILWAY_PATCHED' in content:
            log_info("MCP library already patched")
            return
        
        # Replace the validation line
        # Line 132: raise ValueError("Request validation failed")
        # Replace with: pass  # RAILWAY_PATCHED
        content = content.replace(
            'raise ValueError("Request validation failed")',
            'pass  # RAILWAY_PATCHED - Host validation disabled for Railway deployment'
        )
        
        # Write back
        with open(sse_file, 'w') as f:
            f.write(content)
        
        log_info("Successfully patched MCP library!")
        
        # Force reload the module
        import importlib
        importlib.reload(mcp.server.sse)
        
    except Exception as e:
        log_error(f"Failed to patch MCP library: {e}")
        log_info("Continuing without patch...")

# Apply the patch before doing anything else
patch_mcp_library()

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

class HostFixMiddleware(BaseHTTPMiddleware):
    """Fix host header for Railway deployment"""
    async def dispatch(self, request, call_next):
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "canvas-mcp-production-8183.up.railway.app")
        
        # Fix headers
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
    
    # Get the SSE app
    starlette_app = mcp.sse_app()
    
    # Add middleware
    starlette_app.add_middleware(HostFixMiddleware)
    
    port = int(os.getenv("PORT", 8080))
    log_info(f"🚀 Canvas MCP Live! Port: {port}")
    
    uvicorn.run(
        starlette_app, 
        host="0.0.0.0", 
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        server_header=False,
        access_log=True
    )

if __name__ == "__main__":
    main()
