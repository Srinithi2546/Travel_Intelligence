#!/usr/bin/env bash
# ============================================================
#  Smart Travel Intelligence Platform — Local Setup Script
#  No Docker required. Runs on macOS / Ubuntu / Debian.
# ============================================================
set -e

echo ""
echo "=================================================="
echo "  🗺️  Smart Travel Intelligence Platform Setup"
echo "=================================================="
echo ""

# ── 1. Python version check ───────────────────────────────
PYTHON=$(command -v python3 || command -v python)
PY_VER=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "✔  Python $PY_VER found"

# ── 2. Virtual environment ────────────────────────────────
if [ ! -d "venv" ]; then
    echo "→  Creating virtual environment..."
    $PYTHON -m venv venv
fi
source venv/bin/activate
echo "✔  Virtual environment activated"

# ── 3. Install dependencies ───────────────────────────────
echo "→  Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✔  Dependencies installed"

# ── 4. Environment file ───────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✔  .env created from .env.example"
    echo "⚠️  Edit .env and set your DATABASE_URL and SECRET_KEY before starting"
else
    echo "✔  .env already exists"
fi

echo ""
echo "=================================================="
echo "  ✅  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Edit .env with your PostgreSQL credentials"
echo "  2. Run:  source venv/bin/activate"
echo "  3. Run:  uvicorn app.main:app --reload"
echo "  4. Open: http://localhost:8000/docs"
echo "=================================================="
