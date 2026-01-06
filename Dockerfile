FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install the application
RUN pip install -e .

# Copy and run the patch script AFTER installing dependencies
COPY railway_patch.sh /tmp/railway_patch.sh
RUN chmod +x /tmp/railway_patch.sh && /tmp/railway_patch.sh

# Expose the port
EXPOSE 8080

# Run the server
CMD ["canvas-mcp-server"]
