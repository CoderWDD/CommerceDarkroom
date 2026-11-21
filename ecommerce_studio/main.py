"""
Entrypoint for Render, Koyeb, Docker or direct uvicorn execution.
Enables running `uvicorn ecommerce_studio.main:app` or `python3 -m uvicorn ecommerce_studio.main:app`.
"""
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from ecommerce_studio.api.main import app

__all__ = ["app"]
