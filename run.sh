#!/usr/bin/env bash
# ============================================================
#  Smart Travel Intelligence Platform — Dev Server
# ============================================================
set -e

# Activate venv if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source venv/bin/activate
fi

echo "🚀 Starting Smart Travel API in development mode..."
echo "   Swagger UI  →  http://localhost:8000/docs"
echo "   Health      →  http://localhost:8000/health"
echo ""

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --reload-dir app \
    --log-level info
