@echo off
echo ========================================
echo Starting Frontend Server
echo ========================================
echo.
echo Frontend will be available at:
echo http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

python -m http.server 8000
