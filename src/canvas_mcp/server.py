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
from starlette.responses import StreamingResponse
from starlette.requests import Request
import json
import asyncio

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

async def custom_sse_endpoint(request: Request):
    """Custom SSE endpoint that bypasses host validation"""
    log_info(f"SSE connection from {request.client}")
    
    async def event_stream():
        try:
            # Send initial connection message
            yield f"data: {json.dumps({'type': 'connection', 'status': 'connected'})}\n\n"
            
            # Handle MCP messages
            while True:
                # Read message from client
                body = await request.body()
                if not body:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process MCP request through the FastMCP instance
                message = json.loads(body)
                log_info(f"Received message: {message}")
                
                # Send response back to client
                response = {"jsonrpc": "2.0", "id": message.get("id"), "result": {}}
                yield f"data: {json.dumps(response)}\n\n"
                
        except Exception as e:
            log_error(f"SSE error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

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
    
    # Create custom Starlette app with our own SSE endpoint
    app = Starlette(
        routes=[
            Route("/sse", custom_sse_endpoint, methods=["GET", "POST"]),
            Route("/health", health_check, methods=["GET"]),
            Route("/", health_check, methods=["GET"]),
        ]
    )
    
    port = int(os.getenv("PORT", 8080))
    log_info(f"🚀 Canvas MCP Live! Port: {port}")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        server_header=False,
        access_log=True
    )

if __name__ == "__main__":
    main()
