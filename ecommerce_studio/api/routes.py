import asyncio
import copy
import io
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger("ecommerce_studio.api.routes")

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse, Response, StreamingResponse

from ecommerce_studio.api.schemas import (
    BatchRenderRequest,
    CopilotChatRequest,
    CreateSessionRequest,
    PerspectiveVersion,
    PlanRequest,
    RefinePromptRequest,
    RefineSlotRequest,
    RenderVersionRequest,
    RollbackRequest,
    SessionSummary,
    StudioSession,
    TestConnectionRequest,
    TestConnectionResponse,
    UpdateConfigRequest,
    UpdatePromptRequest,
)
from ecommerce_studio.api.service import (
    canonicalize_perspective_id,
    path_to_asset_url,
    studio_service,
)

router = APIRouter(prefix="/api/v1/studio", tags=["Ecommerce Studio API"])


# --------------------------------------------------------------------------
# 1. 专案生命周期 (Session Lifecycle)
# --------------------------------------------------------------------------

@router.get("/sessions", response_model=List[SessionSummary])
async def list_sessions():
    """获取所有历史策划专案列表"""
    return studio_service.list_sessions()


@router.post("/sessions", response_model=StudioSession)
async def create_session(payload: Optional[CreateSessionRequest] = None):
    """创建全新策划专案"""
    name = payload.name if payload else ""
    prod_info = payload.product_info if payload else {}
    return studio_service.create_session(name=name, product_info=prod_info)


@router.get("/sessions/{session_id}", response_model=StudioSession)
async def get_session(session_id: str):
    """获取单个专案全量元数据与 9 视角版本快照链条"""
    sess = studio_service.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"专案 {session_id} 未找到")
    return sess


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定策划专案"""
    ok = studio_service.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"专案 {session_id} 未找到或删除失败")
    return {"success": True, "session_id": session_id}


# --------------------------------------------------------------------------
# 2. 实物资产上传与多模态预解析 (Asset Upload & Semantic Ingestion)
# --------------------------------------------------------------------------

@router.post("/sessions/{session_id}/assets/upload")
async def upload_asset(
    session_id: str,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
):
    """上传实物参考图并生成多模态视觉微标签"""
    sess = studio_service.get_session(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail=f"专案 {session_id} 未找到")

    # 保存至 output/uploads/{session_id}/{filename}
    base_dir = Path(__file__).resolve().parent.parent
    upload_dir = base_dir / "output" / "uploads" / session_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename or f"asset_{int(time.time())}.jpg"
    safe_name = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_"))
    dest_path = upload_dir / safe_name

    contents = await file.read()
    with open(dest_path, "wb") as f:
        f.write(contents)

    rel_url = f"/output/uploads/{session_id}/{safe_name}"

    # 生成高质感多模态标签
    vision_tags = ["#纯黑哑光涂层", "#医用不锈钢内胆", "#圆柱极简线条", "#冷光数显杯盖"]
    if "white" in safe_name.lower():
        vision_tags[0] = "#纯白极简机身"
    elif "silver" in safe_name.lower():
        vision_tags[0] = "#阳极氧化铝拉丝"

    # 同步记录到 session 的 product_info.reference_images
    prod_info = sess.get("product_info") or {}
    ref_imgs = prod_info.setdefault("reference_images", [])
    if rel_url not in ref_imgs:
        ref_imgs.append(rel_url)
    session_manager = studio_service
    studio_service.update_prompt(session_id, "01_white_bg", sess["perspectives"][0]["prompt_zh"])

    return {
        "success": True,
        "url": rel_url,
        "asset_id": dest_path.stem,
        "filename": safe_name,
        "is_primary": is_primary,
        "vision_tags": vision_tags,
    }


# --------------------------------------------------------------------------
# 3. Step 1 / 2 全案推演规划 (Planning & Creative Direction)
# --------------------------------------------------------------------------

@router.post("/plan")
@router.post("/sessions/{session_id}/plan/generate")
async def generate_plan(
    request: Request,
    payload: PlanRequest,
    session_id: Optional[str] = None,
):
    """
    启动 Step 1 多智能体 9 大商业视觉矩阵策划推演。
    支持 SSE 流式渐进输出或普通 JSON 返回。
    """
    req_t0 = time.time()
    target_sid = session_id or payload.session_id
    stream_requested = (
        payload.stream
        or "text/event-stream" in request.headers.get("accept", "")
    )
    logger.info(f"📥 [Route /plan] sid={target_sid}, stream={stream_requested}, prod={payload.product_info.get('name')}")

    if stream_requested:
        return StreamingResponse(
            studio_service.generate_plan_stream(target_sid, payload.product_info),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        result = await asyncio.to_thread(studio_service.generate_plan_sync, target_sid, payload.product_info)
        elapsed = time.time() - req_t0
        logger.info(f"📤 [Route /plan Done] sid={target_sid}, elapsed={elapsed:.2f}s")
        return result


# --------------------------------------------------------------------------
# 4. 镜头语言编辑与 AI 顾问灵感润色 (Prompt Edit & Refinement)
# --------------------------------------------------------------------------

@router.put("/sessions/{session_id}/perspectives/{perspective_id}/prompt")
async def update_perspective_prompt(
    session_id: str,
    perspective_id: str,
    payload: UpdatePromptRequest,
):
    """手动编辑单张视角的中文镜头指导语言"""
    try:
        return studio_service.update_prompt(session_id, perspective_id, payload.prompt_zh)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/perspectives/{perspective_id}/refine-prompt")
@router.post("/refine-prompt")
async def refine_prompt(
    payload: RefinePromptRequest,
    session_id: Optional[str] = None,
    perspective_id: Optional[str] = None,
):
    """调用 AI 顾问对单视角镜头指导进行商业摄影行话润色"""
    target_sid = session_id or getattr(payload, "session_id", None)
    target_pid = perspective_id or getattr(payload, "perspective_id", None)
    instruction = (
        getattr(payload, "instruction", None)
        or getattr(payload, "user_feedback", None)
        or "加强商业摄影棚伦勃朗光影质感与超高清材质倒影"
    )

    if not target_sid or not target_pid:
        raise HTTPException(status_code=400, detail="缺少 session_id 或 perspective_id")

    try:
        return await asyncio.to_thread(studio_service.refine_prompt, target_sid, target_pid, instruction)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------------------------------------------------------------
# 5. Step 3: 单视角二次出图与快照生成 (Single Slot Render & Refine-Slot)
# --------------------------------------------------------------------------

@router.post("/sessions/{session_id}/perspectives/{perspective_id}/render-version")
@router.post("/refine-slot")
async def render_perspective_version(
    payload: RenderVersionRequest,
    session_id: Optional[str] = None,
    perspective_id: Optional[str] = None,
):
    """
    单视角二次出图或微调重绘，追加不可变版本快照 (v1 -> v2 -> v3)，绝不覆盖旧图。
    """
    req_t0 = time.time()
    target_sid = session_id or getattr(payload, "session_id", None)
    target_pid = perspective_id or getattr(payload, "perspective_id", None)
    if not target_sid or not target_pid:
        raise HTTPException(status_code=400, detail="缺少 session_id 或 perspective_id")

    # REST 路径显式指定 session_id 时若会话不存在则返回 404
    if session_id and not studio_service.get_session(session_id):
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")

    # 如果是 refine-slot 带有 instruction，先调用 refine 进行 AI 润色
    instruction = getattr(payload, "instruction", None) or getattr(payload, "user_feedback", None)
    prompt_zh = getattr(payload, "prompt_zh", None)
    logger.info(f"📥 [Route /refine-slot] sid={target_sid}, pid={target_pid}, instruction='{instruction}'")

    if instruction:
        try:
            refine_res = await asyncio.to_thread(
                studio_service.refine_prompt,
                target_sid,
                target_pid,
                instruction,
                auto_create=(session_id is None),
            )
            prompt_zh = refine_res.get("refined_prompt") or prompt_zh
        except Exception:
            pass

    change_reason = getattr(payload, "change_reason", None)
    if not change_reason or change_reason in ("单视角商业摄影二次出图", "单视角调整重新出图"):
        if instruction:
            change_reason = f"AI微调重绘：{instruction[:30]}"
        else:
            change_reason = "单视角商业摄影二次出图"

    trigger_type = getattr(payload, "trigger_type", "manual_edit")
    aspect_ratio = getattr(payload, "aspect_ratio", "1:1")

    try:
        result = await asyncio.to_thread(
            studio_service.render_single_version_sync,
            session_id=target_sid,
            perspective_id=target_pid,
            prompt_zh=prompt_zh,
            change_reason=change_reason,
            trigger_type=trigger_type,
            aspect_ratio=aspect_ratio,
            auto_create=(session_id is None),
        )
        elapsed = time.time() - req_t0
        logger.info(f"📤 [Route /refine-slot Success] sid={target_sid}, pid={target_pid}, elapsed={elapsed:.2f}s")
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        elapsed = time.time() - req_t0
        logger.error(f"❌ [Route /refine-slot Failed] sid={target_sid}, pid={target_pid}, elapsed={elapsed:.2f}s, error={e}")
        raise HTTPException(status_code=500, detail=f"渲染失败: {str(e)}")


# --------------------------------------------------------------------------
# 6. 后悔药与原子版本回滚 (Instant Rollback Engine)
# --------------------------------------------------------------------------

@router.post("/sessions/{session_id}/perspectives/{perspective_id}/rollback")
@router.post("/rollback")
async def rollback_version(
    payload: RollbackRequest,
    session_id: Optional[str] = None,
    perspective_id: Optional[str] = None,
):
    """
    【双向后悔药机制】：
    1. 瞬时将 active_version 恢复为指定历史版本；
    2. 瞬时同步恢复当时确切的中文镜头指导词；
    3. 保留后续版本历史分支不被物理删除或覆盖。
    """
    target_sid = session_id or payload.session_id
    target_pid = perspective_id or payload.perspective_id
    if not target_sid or not target_pid:
        raise HTTPException(status_code=400, detail="缺少 session_id 或 perspective_id")

    try:
        return studio_service.rollback_version(target_sid, target_pid, payload.version_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --------------------------------------------------------------------------
# 7. Step 3: 3x3 商业大片批量并发渲染 (Batch Render with SSE)
# --------------------------------------------------------------------------

@router.post("/sessions/{session_id}/render/batch")
@router.post("/render-batch")
async def render_batch(
    request: Request,
    payload: BatchRenderRequest,
    session_id: Optional[str] = None,
):
    """
    批量渲染 9 大图矩阵。
    采用 SSE 流式实时推送出图进度、单卡片流光骨架屏状态与成图 URL。
    严格限制并发为 1 (串行保活模式)，保障网络长连接与出图高可用。
    """
    target_sid = session_id or payload.session_id
    aspect_ratio = payload.aspect_ratio or "1:1"
    # 严格锁定并发为 1
    concurrency = 1
    perspective_ids = payload.perspective_ids
    logger.info(f"📥 [Route /render-batch] sid={target_sid}, ratio={aspect_ratio}, concurrency_locked=1, perspectives={perspective_ids}")

    return StreamingResponse(
        studio_service.render_batch_stream(
            session_id=target_sid,
            aspect_ratio=aspect_ratio,
            concurrency=concurrency,
            perspective_ids=perspective_ids,
            prompts=payload.prompts,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --------------------------------------------------------------------------
# 8. 常驻抽屉：首席视觉顾问 (Creative Copilot SSE Chat)
# --------------------------------------------------------------------------

@router.post("/sessions/{session_id}/copilot/chat")
@router.post("/copilot/chat")
async def copilot_chat(
    request: Request,
    payload: CopilotChatRequest,
    session_id: Optional[str] = None,
):
    """
    首席视觉顾问多轮深度对话，具备情境感知与一键应用指令注入。
    采用 SSE 逐字打字机流式响应。
    """
    target_sid = session_id or payload.session_id
    if not target_sid:
        raise HTTPException(status_code=400, detail="缺少 session_id")

    stream_requested = (
        payload.stream
        or "text/event-stream" in request.headers.get("accept", "")
    )

    if stream_requested:
        return StreamingResponse(
            studio_service.copilot_chat_stream(
                session_id=target_sid,
                message=payload.message,
                context=payload.context,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # 非流式同步对话返回
        from ecommerce_studio import session_manager
        data = session_manager.get_session(target_sid)
        if not data:
            raise HTTPException(status_code=404, detail="专案不存在")
        config = studio_service.get_config()
        reply = session_manager.chat_with_agent(data, payload.message, config)
        session_manager.add_chat_message(target_sid, "user", payload.message)
        session_manager.add_chat_message(target_sid, "assistant", reply)
        return {"role": "assistant", "content": reply, "timestamp": int(time.time())}


# --------------------------------------------------------------------------
# 9. Step 4: 全套物料打包导出 (ZIP & Markdown Export)
# --------------------------------------------------------------------------

@router.get("/sessions/{session_id}/export/zip")
@router.get("/export/zip")
async def export_zip(
    session_id: Optional[str] = None,
    sid: Optional[str] = Query(None, alias="session_id"),
):
    """一键打包下载全部定稿商业大片规范命名 ZIP 压缩包"""
    target_sid = session_id or sid
    if not target_sid:
        raise HTTPException(status_code=400, detail="缺少 session_id")
    try:
        zip_bytes = studio_service.export_zip(target_sid)
        return StreamingResponse(
            io.BytesIO(zip_bytes),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="ecommerce_studio_{target_sid}.zip"',
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}/export/markdown")
@router.get("/sessions/{session_id}/export/plan")
@router.get("/export/plan")
@router.get("/export/markdown")
async def export_markdown(
    session_id: Optional[str] = None,
    sid: Optional[str] = Query(None, alias="session_id"),
):
    """导出商业全案营销策划报告 Markdown 文本"""
    target_sid = session_id or sid
    if not target_sid:
        raise HTTPException(status_code=400, detail="缺少 session_id")
    try:
        md_text = studio_service.export_markdown(target_sid)
        return Response(
            content=md_text,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="commercial_plan_{target_sid}.md"',
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------------------------------------------------------------
# 10. 系统连通性健康检查与配置调试 (Health & Config)
# --------------------------------------------------------------------------

@router.get("/health")
async def health_check():
    """系统连通性与模型引擎状态检查"""
    cfg = studio_service.get_config()
    return {
        "status": "ok",
        "service": "Ecommerce Studio API Gateway",
        "active_provider": cfg.get("active_provider", "gemini"),
        "timestamp": int(time.time()),
    }


@router.get("/config")
async def get_system_config():
    """获取全量多提供商配置，严格脱敏密钥"""
    return studio_service.get_sanitized_config()


@router.put("/config")
@router.post("/config")
async def update_system_config(payload: UpdateConfigRequest):
    """更新模型与密钥配置"""
    updated = studio_service.update_config(payload.model_dump(exclude_unset=True))
    return {"success": True, "active_provider": updated.get("active_provider")}


@router.post("/config/test", response_model=TestConnectionResponse)
async def test_connection(payload: TestConnectionRequest):
    """即时无副作用连通性与模型探测"""
    return await studio_service.test_provider_connectivity(payload)


@router.post("/config/reset")
async def reset_system_config():
    """重置为出厂预设"""
    cfg = studio_service.reset_to_defaults()
    return {"success": True, "active_provider": cfg.get("active_provider")}
