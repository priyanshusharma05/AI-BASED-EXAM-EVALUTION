# FastAPI Server Startup Script (Linux/Mac)
# This script activates the virtual environment and starts the FastAPI server

#!/bin/bash
# FastAPI Server Startup Script (Linux/Mac)
# This script activates the virtual environment and starts the FastAPI server

echo "========================================"
echo "Starting FastAPI Backend Server"
echo "========================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "WARNING: GEMINI_API_KEY is not set!"
    echo "AI evaluation features will not work without it."
    echo "Set it with: export GEMINI_API_KEY=your_api_key_here"
    echo ""
fi

# Start FastAPI server with uvicorn
# Use PORT env var if present (Render provides $PORT)
: "${PORT:=5000}"
echo "Starting server at http://0.0.0.0:${PORT}"
echo "Press Ctrl+C to stop the server"
echo ""
echo "API Documentation will be available at:"
echo "- Swagger UI: http://0.0.0.0:${PORT}/docs"
echo "- ReDoc: http://0.0.0.0:${PORT}/redoc"
echo ""
uvicorn fastapi_app:app --reload --host 0.0.0.0 --port ${PORT}
