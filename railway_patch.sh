#!/bin/bash
# Patch MCP library to disable host validation for Railway
echo "Patching MCP library for Railway compatibility..."

SSE_FILE="/usr/local/lib/python3.12/site-packages/mcp/server/sse.py"

if [ -f "$SSE_FILE" ]; then
    # Replace the validation error with a pass statement
    sed -i 's/raise ValueError("Request validation failed")/pass  # RAILWAY_PATCHED/g' "$SSE_FILE"
    echo "Successfully patched MCP library"
else
    echo "Warning: MCP library file not found at $SSE_FILE"
fi
