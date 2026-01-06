FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the patch script
COPY railway_patch.sh /tmp/railway_patch.sh
RUN chmod +x /tmp/railway_patch.sh

# Apply the patch to the MCP library
RUN /tmp/railway_patch.sh

# Copy the application code
COPY . .

# Install the application
RUN pip install -e .

# Expose the port
EXPOSE 8080

# Run the server
CMD ["canvas-mcp-server"]
