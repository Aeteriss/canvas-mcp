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
        # This converts the MCP server into a standard web application
        starlette_app = mcp.sse_app()
        
        import uvicorn
        port = int(os.getenv("PORT", 8080))
        
        log_info(f"🚀 Manual Uvicorn startup on port {port}")
        
        # This is the industry standard way to run a web server on Railway
        uvicorn.run(starlette_app, host="0.0.0.0", port=port)
        
    except Exception as e:
        log_error("Server error during Uvicorn startup", exc=e)
        sys.exit(1)

if __name__ == "__main__":
    main()
