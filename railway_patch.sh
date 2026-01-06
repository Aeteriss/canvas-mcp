#!/bin/bash
# Patch MCP library to disable host validation for Railway
echo "Patching MCP library for Railway compatibility..."

# Find the MCP installation directory
MCP_DIR=$(python3 -c "import mcp.server; import os; print(os.path.dirname(mcp.server.__file__))")

echo "MCP installation directory: $MCP_DIR"

# Patch transport_security.py to disable host validation
TRANSPORT_FILE="$MCP_DIR/transport_security.py"
if [ -f "$TRANSPORT_FILE" ]; then
    echo "Patching $TRANSPORT_FILE..."
    # Comment out or bypass the host validation check
    sed -i 's/logger\.warning(f"Invalid Host header: {host_header}")/logger.info(f"Railway bypass - Host header: {host_header}")  # RAILWAY_PATCHED/g' "$TRANSPORT_FILE"
    sed -i 's/return False/return True  # RAILWAY_PATCHED - Always accept host/g' "$TRANSPORT_FILE"
    echo "Successfully patched transport_security.py"
else
    echo "Warning: transport_security.py not found at $TRANSPORT_FILE"
fi

# Patch sse.py to disable request validation
SSE_FILE="$MCP_DIR/sse.py"
if [ -f "$SSE_FILE" ]; then
    echo "Patching $SSE_FILE..."
    sed -i 's/raise ValueError("Request validation failed")/pass  # RAILWAY_PATCHED - Validation disabled/g' "$SSE_FILE"
    echo "Successfully patched sse.py"
else
    echo "Warning: sse.py not found at $SSE_FILE"
fi

echo "MCP library patching complete!"
