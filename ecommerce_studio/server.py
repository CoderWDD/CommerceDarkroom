import argparse
import sys
import uvicorn
from pathlib import Path

# 将项目根目录与 studio 目录加入 Python 路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))


def main():
    parser = argparse.ArgumentParser(description="Ecommerce Studio FastAPI Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    args = parser.parse_args()

    print(f"🚀 Starting Ecommerce Studio FastAPI Server on http://{args.host}:{args.port}")
    uvicorn.run(
        "ecommerce_studio.api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=[str(CURRENT_DIR / "api")] if args.reload else None,
        reload_excludes=["*output*", "*.log", "*.jpg", "*.png", "*.json", "*sessions*"] if args.reload else None,
    )


if __name__ == "__main__":
    main()
