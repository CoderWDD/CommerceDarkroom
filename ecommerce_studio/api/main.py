import logging
import os
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ecommerce_studio.api.routes import router

# 初始化统一日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ecommerce_studio.api")

# 确保 output 目录存在
BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="Ecommerce Studio Commercial API",
    description="商业级电商视觉工坊 FastAPI 异步高并发后端核心，支持非破坏性版本链条、SSE流式渐进渲染与首席视觉顾问",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 请求耗时监测中间件
@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    query = request.url.query
    query_str = f"?{query}" if query else ""

    logger.info(f"👉 [HTTP IN] {method} {path}{query_str}")
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        logger.info(
            f"⚡ [HTTP OUT] {method} {path} -> {response.status_code} (耗时: {duration:.3f}s)"
        )
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"❌ [HTTP ERR] {method} {path} 异常崩溃 (耗时: {duration:.3f}s): {str(e)}"
        )
        raise e

# 允许跨域 (支持 Next.js 开发服务器与任意前端客户端直连)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态资源路由: /output 与 /api/v1/studio/output 均指向物理 output 目录
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")
app.mount("/api/v1/studio/output", StaticFiles(directory=str(OUTPUT_DIR)), name="api_output")

# 注册核心路由
app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "Ecommerce Studio Commercial API Gateway",
        "version": "2.1.0",
        "docs": "/docs",
        "status": "online",
    }
