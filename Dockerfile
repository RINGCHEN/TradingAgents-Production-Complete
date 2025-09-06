# TradingAgents Production Dockerfile with CORS Fix
FROM python:3.11.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run the application - Updated to use full TradingAgents app with portfolio features  
CMD ["python", "-m", "uvicorn", "tradingagents.app:app", "--host", "0.0.0.0", "--port", "8080"]