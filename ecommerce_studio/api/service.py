import asyncio
import copy
import io
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

logger = logging.getLogger("ecommerce_studio.api.service")

from ecommerce_studio import config_manager, session_manager, studio_crew
from ecommerce_studio.studio_crew import ECOMMERCE_IMAGE_MATRIX_TEMPLATES, build_default_prompt_matrix
from ecommerce_studio.tools.image_tool import generate_ecommerce_image

# 9 大黄金商业视角元数据规范 (Next.js + FastAPI PRD 标准)
PERSPECTIVE_DEFINITIONS: List[Dict[str, str]] = [
    {
        "id": "01_white_bg",
        "alt_id": "main_white_bg",
        "name": "商业纯净白底首图",
        "tag": "CTR点击率收割机",
        "category": "主图转化",
        "desc": "纯白无影摄影棚顶光与双侧柔光箱、商品主体居中微俯视15°、通透镜面微倒影、高动态范围HDR",
    },
    {
        "id": "02_scene",
        "alt_id": "lifestyle_scene",
        "name": "真实生活使用场景图",
        "tag": "生活代入与身份认同",
        "category": "场景共情",
        "desc": "融入真实目标场域（极简晨光厨房/现代写字楼/户外露营），柔和侧逆自然光，搭配生活化道具",
    },
    {
        "id": "03_detail",
        "alt_id": "material_detail",
        "name": "材质工艺与微距细节图",
        "tag": "精工品质与消除廉价感",
        "category": "品质背书",
        "desc": "85mm~100mm微距特写，超浅景深虚化背景，硬光侧打凸显金属拉丝、亲肤磨砂颗粒或皮革缝线",
    },
    {
        "id": "04_structure",
        "alt_id": "structure_cutaway",
        "name": "黑科技解构与爆炸透视图",
        "tag": "技术壁垒与内部硬核",
        "category": "科技信任",
        "desc": "零件悬浮爆炸视图(Exploded View)、轴向线性排布、冷色科技轮廓光、半透明材质透光感与技术标线感",
    },
    {
        "id": "05_pain_killer",
        "alt_id": "pain_point_solution",
        "name": "痛点直击与抗拒点攻破图",
        "tag": "消灭退货与打消顾虑",
        "category": "决策攻坚",
        "desc": "针对买家最大顾虑（倒置剧烈晃动滴水不漏测试、刀划无痕防刮、冰块不化对比），具象化视觉证言",
    },
    {
        "id": "06_size",
        "alt_id": "portable_commute",
        "name": "人体工学与真实比例图",
        "tag": "尺码锚定与真实参照",
        "category": "实用认知",
        "desc": "手部自然握持、放入通勤包侧袋或置于车载杯架，以日常参照物建立直观尺码感知与携带便利感",
    },
    {
        "id": "07_emotional",
        "alt_id": "core_feature",
        "name": "品牌情绪与故事氛围图",
        "tag": "品牌溢价与高级格调",
        "category": "品牌溢价",
        "desc": "电影感宽画幅光影（丁达尔光束、深色暖影调、蓝调黄昏），弱化商品棱角，强化环境意境渲染",
    },
    {
        "id": "08_color",
        "alt_id": "unboxing_gift",
        "name": "全系配色与陈列矩阵图",
        "tag": "多色激发与家族感",
        "category": "矩阵陈列",
        "desc": "现代艺术展台陈列，高低错落几何台阶，全系经典配色一字排开，统一侧光保证色彩精准无色差",
    },
    {
        "id": "09_buyer_show",
        "alt_id": "model_interaction",
        "name": "真实买家秀与社交种草图",
        "tag": "真实口碑与生活种草",
        "category": "社交种草",
        "desc": "自然手持第一人称视角、自然非影棚光、生活化真实环境背景、轻微胶片颗粒感与随性构图",
    },
]

# ID 别名映射字典 (包含后端规范 ID、旧版 alt_id 与前端 constants.ts 别名)
ID_CANONICAL_MAP: Dict[str, str] = {
    # 规范自身映射
    "01_white_bg": "01_white_bg",
    "02_scene": "02_scene",
    "03_detail": "03_detail",
    "04_structure": "04_structure",
    "05_pain_killer": "05_pain_killer",
    "06_size": "06_size",
    "07_emotional": "07_emotional",
    "08_color": "08_color",
    "09_buyer_show": "09_buyer_show",
    # 经典 alt_id 映射
    "main_white_bg": "01_white_bg",
    "lifestyle_scene": "02_scene",
    "material_detail": "03_detail",
    "structure_cutaway": "04_structure",
    "pain_point_solution": "05_pain_killer",
    "portable_commute": "06_size",
    "core_feature": "07_emotional",
    "unboxing_gift": "08_color",
    "model_interaction": "09_buyer_show",
    # 前端 constants.ts 命名别名
    "03_macro": "03_detail",
    "04_exploded": "04_structure",
    "05_pain_point": "05_pain_killer",
    "06_scale": "06_size",
    "07_atmosphere": "07_emotional",
    "08_variants": "08_color",
    "09_social": "09_buyer_show",
}
for p in PERSPECTIVE_DEFINITIONS:
    ID_CANONICAL_MAP[p["id"]] = p["id"]
    ID_CANONICAL_MAP[p["alt_id"]] = p["id"]


def canonicalize_perspective_id(p_id: str) -> str:
    """归一化视角ID为规范 01_white_bg 格式"""
    clean = (p_id or "").strip()
    if clean in ID_CANONICAL_MAP:
        return ID_CANONICAL_MAP[clean]
    # 尝试按前缀序号 (01..09) 匹配
    if len(clean) >= 2 and clean[:2].isdigit():
        prefix = clean[:2]
        for canon_id in [
            "01_white_bg", "02_scene", "03_detail", "04_structure",
            "05_pain_killer", "06_size", "07_emotional", "08_color", "09_buyer_show"
        ]:
            if canon_id.startswith(prefix):
                return canon_id
    return clean


def path_to_asset_url(path_str: Optional[str]) -> Optional[str]:
    """将本地绝对/相对图片路径映射为前端可访问的 /output/... 静态URL"""
    if not path_str:
        return None
    p = Path(path_str)
    # 如果路径包含 output，提取其后相对部分
    parts = p.parts
    if "output" in parts:
        idx = parts.index("output")
        rel_path = "/".join(parts[idx:])
        return f"/{rel_path}"
    # 兜底直接返回 /output/<filename>
    return f"/output/{p.name}"


def normalize_session_data(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度归一化 Session 数据模型：
    1. 确保 session 具有完整的 perspectives 数组（包含 9 大视角与历史版本快照链条）；
    2. 同步老结构的 prompts_matrix 与 generated_images，保障双向兼容；
    3. 补全 strategy_summary 与 image_count；
    4. 将图片路径转换为前端可直连加载的 image_url (/output/...)。
    """
    if not isinstance(session_data, dict):
        return {}

    # 1. 迁移老结构
    session_data = session_manager.migrate_session_to_v2(session_data)
    session_data["style_preset"] = session_data.get("style_preset") or "minimalist_muji"
    product_info = session_data.get("product_info") or {}

    # 兼容字段
    if "name" not in product_info and "product_name" in product_info:
        product_info["name"] = product_info["product_name"]
    if "target_audience" not in product_info and "target_users" in product_info:
        product_info["target_audience"] = product_info["target_users"]
    session_data["product_info"] = product_info

    # 2. 提取已生成的图像数据字典
    gen_images = session_data.get("generated_images") or []
    img_by_id: Dict[str, Dict[str, Any]] = {}
    for item in gen_images:
        if isinstance(item, dict):
            i_id = item.get("id", "")
            img_by_id[canonicalize_perspective_id(i_id)] = item
            img_by_id[i_id] = item

    # 3. 提取已有的提示词矩阵
    prompts_matrix = session_data.get("prompts_matrix") or []
    prompt_by_id: Dict[str, str] = {}
    for p in prompts_matrix:
        if isinstance(p, dict):
            p_id = p.get("id", "")
            prompt_by_id[canonicalize_perspective_id(p_id)] = p.get("prompt", "")
            prompt_by_id[p_id] = p.get("prompt", "")

    # 4. 如果没有 prompts_matrix，用默认高质量模板兜底生成
    if not prompts_matrix:
        default_matrix = build_default_prompt_matrix(product_info)
        session_data["prompts_matrix"] = default_matrix
        for p in default_matrix:
            p_id = p.get("id", "")
            prompt_by_id[canonicalize_perspective_id(p_id)] = p.get("prompt", "")

    # 5. 构建规范化的 perspectives 列表 (9个)
    perspectives: List[Dict[str, Any]] = []
    total_images = 0

    for meta in PERSPECTIVE_DEFINITIONS:
        p_canon_id = meta["id"]
        p_alt_id = meta["alt_id"]

        matched_img = img_by_id.get(p_canon_id) or img_by_id.get(p_alt_id) or {}
        curr_prompt = (
            matched_img.get("prompt")
            or prompt_by_id.get(p_canon_id)
            or prompt_by_id.get(p_alt_id)
            or ""
        )

        raw_versions = matched_img.get("versions") or []
        normalized_versions = []
        for v in raw_versions:
            if not isinstance(v, dict):
                continue
            v_num = v.get("version_num") or v.get("version_id") or 1
            if isinstance(v_num, str) and v_num.startswith("v"):
                try:
                    v_num = int(v_num[1:])
                except ValueError:
                    v_num = 1
            v_tag = f"v{v_num}"
            raw_path = v.get("image_path")
            normalized_versions.append({
                "version_id": v_tag,
                "version_num": int(v_num),
                "image_url": path_to_asset_url(raw_path),
                "image_path": raw_path,
                "prompt_zh": v.get("prompt_zh") or v.get("prompt") or curr_prompt,
                "timestamp": v.get("timestamp") or session_data.get("updated_at", int(time.time())),
                "created_at_fmt": v.get("created_at_fmt") or "",
                "trigger_type": v.get("trigger_type") or "manual_edit",
                "change_reason": v.get("change_reason") or v.get("note") or "商业大片渲染快照",
                "aspect_ratio": v.get("aspect_ratio") or "1:1",
                "status": "success" if (raw_path and os.path.exists(raw_path)) else "pending",
                "error": v.get("error"),
            })

        active_v = matched_img.get("active_version")
        if active_v:
            active_v_id = f"v{active_v}" if not str(active_v).startswith("v") else str(active_v)
        elif normalized_versions:
            active_v_id = normalized_versions[-1]["version_id"]
        else:
            active_v_id = None

        card_status = "idle"
        if normalized_versions:
            card_status = "success"
        elif matched_img.get("status") in ("pending", "rendering"):
            card_status = "rendering"
        elif matched_img.get("status") == "failed":
            card_status = "error"

        active_img_url = None
        active_img_path = None
        for v in normalized_versions:
            if v["version_id"] == active_v_id:
                active_img_url = v.get("image_url")
                active_img_path = v.get("image_path")
                break
        if not active_img_url and normalized_versions:
            active_img_url = normalized_versions[-1].get("image_url")
            active_img_path = normalized_versions[-1].get("image_path")

        matched_matrix: Dict[str, Any] = {}
        for pm in prompts_matrix:
            if isinstance(pm, dict) and canonicalize_perspective_id(pm.get("id", "")) in (p_canon_id, p_alt_id):
                matched_matrix = pm
                break

        scene_hl = matched_matrix.get("scene_highlight") or matched_img.get("scene_highlight")
        comm_strat = matched_matrix.get("commercial_strategy") or matched_img.get("commercial_strategy")
        qt = matched_matrix.get("quick_tweaks") or matched_img.get("quick_tweaks")
        qtp = matched_matrix.get("quick_tweak_pills") or matched_img.get("quick_tweak_pills")

        perspectives.append({
            "id": p_canon_id,
            "alt_id": p_alt_id,
            "name": meta["name"],
            "desc": meta["desc"],
            "tag": meta["tag"],
            "category": meta["category"],
            "prompt_zh": curr_prompt,
            "active_version_id": active_v_id,
            "image_url": active_img_url,
            "image_path": active_img_path,
            "render_status": card_status,
            "render_progress": 100 if card_status == "success" else 0,
            "versions": normalized_versions,
            "scene_highlight": scene_hl,
            "commercial_strategy": comm_strat,
            "quick_tweaks": qt,
            "quick_tweak_pills": qtp,
            "status": card_status,
            "error": matched_img.get("error"),
        })

        total_images += len(normalized_versions)

    session_data["perspectives"] = perspectives
    session_data["image_count"] = total_images
    session_data["images_count"] = total_images

    # 6. 构造 strategy_summary
    if not session_data.get("strategy_summary"):
        prod_name = product_info.get("name") or "主推商品"
        session_data["strategy_summary"] = {
            "tone": "商业极简、顶级精工与生活格调",
            "usp": f"针对【{product_info.get('pain_points', '核心抗拒点')}】构建差异化视觉证言，提升转化率",
            "color_palette": [
                "#09090B 曜石深空黑",
                "#71717A 哑光钛合金灰",
                "#0EA5E9 幽蓝科技冷光",
                "#10B981 就绪翡翠绿",
            ],
        }

    session_data["id"] = session_data.get("session_id")
    return session_data


class StudioBackendService:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=8)

    def get_config(self) -> Dict[str, Any]:
        return config_manager.load_config()

    def get_sanitized_config(self) -> Dict[str, Any]:
        cfg = copy.deepcopy(self.get_config())
        if "gemini" not in cfg:
            cfg["gemini"] = {"model": "gemini-2.0-flash", "image_model": "imagen-3.0-generate-002"}
        if "openai" not in cfg:
            cfg["openai"] = {"base_url": "https://api.openai.com/v1", "model": "gpt-4o", "image_model": "dall-e-3"}
        if "custom_openai" not in cfg:
            cfg["custom_openai"] = {"base_url": "", "model": "deepseek-chat", "image_model": "dall-e-3"}
        if "ollama" not in cfg:
            cfg["ollama"] = {"base_url": "http://localhost:11434/v1", "model": "llama3.2-vision:latest", "image_model": ""}

        for p in ["gemini", "openai", "custom_openai", "ollama"]:
            sub = cfg.get(p)
            if isinstance(sub, dict):
                raw_key = sub.get("api_key", "")
                sub["is_configured"] = bool(str(raw_key).strip())
                if raw_key and len(raw_key) > 8:
                    sub["api_key"] = raw_key[:4] + "****" + raw_key[-4:]
                elif raw_key:
                    sub["api_key"] = "****"

        cfg["system_env_status"] = {
            "has_gemini_env": bool(os.environ.get("GEMINI_API_KEY")),
            "has_openai_env": bool(os.environ.get("OPENAI_API_KEY")),
        }
        return cfg

    def update_config(self, new_cfg: Dict[str, Any]) -> Dict[str, Any]:
        curr = self.get_config()
        if "active_provider" in new_cfg and new_cfg["active_provider"]:
            curr["active_provider"] = new_cfg["active_provider"]
        for p in ["gemini", "openai", "custom_openai", "ollama"]:
            if p in new_cfg and isinstance(new_cfg[p], dict):
                sub = curr.setdefault(p, {})
                for k, v in new_cfg[p].items():
                    if k == "api_key" and ("*" in str(v) or not str(v).strip()):
                        if sub.get("api_key") and "*" not in str(sub["api_key"]):
                            continue
                    sub[k] = v
        config_manager.save_config(curr)
        return curr

    def reset_to_defaults(self) -> Dict[str, Any]:
        return config_manager.reset_to_defaults()

    async def test_provider_connectivity(self, req: Any) -> Dict[str, Any]:
        t0 = time.time()
        provider = req.provider.lower()
        existing_cfg = self.get_config()

        target_key = (req.api_key or "").strip()
        if not target_key or "*" in target_key:
            target_key = existing_cfg.get(provider, {}).get("api_key", "")

        base_url = (req.base_url or "").strip() or existing_cfg.get(provider, {}).get("base_url", "")
        model_name = (req.model or "").strip() or existing_cfg.get(provider, {}).get("model", "")

        try:
            if provider == "gemini":
                if not target_key:
                    return {
                        "success": False,
                        "provider": provider,
                        "latency_ms": int((time.time() - t0) * 1000),
                        "message": "未检测到有效 Gemini API Key",
                        "error_code": "INVALID_API_KEY",
                        "details": {"raw_error": "API Key 为空，请配置后再测试"},
                    }
                try:
                    from google import genai
                    client = genai.Client(api_key=target_key)
                    resp = client.models.generate_content(
                        model=model_name or "gemini-2.0-flash",
                        contents="ping",
                    )
                    latency = max(1, int((time.time() - t0) * 1000))
                    return {
                        "success": True,
                        "provider": provider,
                        "latency_ms": latency,
                        "message": f"Gemini 握手成功，模型 ({model_name or 'gemini-2.0-flash'}) 响应就绪",
                        "details": {"auth_ok": True, "probe_response_excerpt": getattr(resp, "text", "")[:30]},
                    }
                except Exception as e:
                    latency = max(1, int((time.time() - t0) * 1000))
                    err_msg = str(e)
                    return {
                        "success": False,
                        "provider": provider,
                        "latency_ms": latency,
                        "message": f"Gemini 连接失败: {err_msg[:60]}",
                        "error_code": "CONNECTION_FAILED",
                        "details": {"raw_error": err_msg},
                    }

            elif provider in ["openai", "custom_openai", "ollama"]:
                final_key = target_key or ("ollama" if provider == "ollama" else "")
                if provider != "ollama" and not final_key:
                    return {
                        "success": False,
                        "provider": provider,
                        "latency_ms": int((time.time() - t0) * 1000),
                        "message": "未提供 API Key",
                        "error_code": "INVALID_API_KEY",
                        "details": {"raw_error": "API Key 不能为空"},
                    }

                default_base = (
                    "https://api.openai.com/v1" if provider == "openai"
                    else "http://localhost:11434/v1" if provider == "ollama"
                    else "https://api.your-proxy.com/v1"
                )
                final_base = base_url or default_base
                target_model = model_name or ("gpt-4o" if provider == "openai" else "llama3.2-vision:latest" if provider == "ollama" else "deepseek-chat")

                try:
                    from openai import OpenAI
                    client = OpenAI(
                        api_key=final_key,
                        base_url=final_base,
                        timeout=5.0,
                    )
                    resp = client.chat.completions.create(
                        model=target_model,
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=2,
                    )
                    latency = max(1, int((time.time() - t0) * 1000))
                    content = resp.choices[0].message.content if resp.choices else ""
                    return {
                        "success": True,
                        "provider": provider,
                        "latency_ms": latency,
                        "message": f"连接成功，文本模型 ({target_model}) 响应正常 (耗时 {latency}ms)。注意：商业生图需代理端点支持 DALL-E 3 图像接口与充足额度。",
                        "details": {
                            "auth_ok": True,
                            "probe_response_excerpt": content,
                            "image_api_note": "生图功能调用 /v1/images/generate，若代理中继未开通图像权限或额度不足可能导致生图失败，建议在设置中确认或切换 Gemini。"
                        },
                    }
                except Exception as e:
                    latency = max(1, int((time.time() - t0) * 1000))
                    err_msg = str(e)
                    return {
                        "success": False,
                        "provider": provider,
                        "latency_ms": latency,
                        "message": f"端点测试失败: {err_msg[:60]}",
                        "error_code": "CONNECTION_FAILED",
                        "details": {"raw_error": err_msg},
                    }
            else:
                return {
                    "success": False,
                    "provider": provider,
                    "latency_ms": 0,
                    "message": f"未知提供商: {provider}",
                    "error_code": "UNKNOWN_PROVIDER",
                }
        except Exception as e:
            return {
                "success": False,
                "provider": provider,
                "latency_ms": int((time.time() - t0) * 1000),
                "message": f"探测异常: {str(e)}",
                "error_code": "PROBE_EXCEPTION",
                "details": {"raw_error": str(e)},
            }

    def list_sessions(self) -> List[Dict[str, Any]]:
        raw_list = session_manager.list_sessions()
        summaries = []
        for s in raw_list:
            summaries.append({
                "session_id": s.get("session_id"),
                "name": s.get("name"),
                "created_at": s.get("created_at"),
                "updated_at": s.get("updated_at"),
                "product_name": s.get("product_name", ""),
                "style_preset": s.get("style_preset", "minimalist_muji"),
                "image_count": s.get("images_count", 0),
                "images_count": s.get("images_count", 0),
                "chat_count": s.get("chat_count", 0),
            })
        return summaries

    def create_session(
        self,
        name: str = "",
        product_info: Optional[Dict[str, Any]] = None,
        style_preset: Optional[str] = "minimalist_muji",
    ) -> Dict[str, Any]:
        data = session_manager.create_session(
            name=name, product_info=product_info or {}, style_preset=style_preset or "minimalist_muji"
        )
        return normalize_session_data(data)

    def save_upload_asset(self, session_id: Optional[str], filename: str, file_bytes: bytes) -> Tuple[str, str]:
        """保存上传的资产文件，返回 (rel_url, abs_path)"""
        target_sid = session_id or "common"
        base_dir = Path(__file__).resolve().parent.parent
        upload_dir = base_dir / "output" / "uploads" / target_sid
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c for c in filename if c.isalnum() or c in (".", "-", "_"))
        if not safe_name:
            safe_name = f"snap_{int(time.time())}.jpg"
        dest_path = upload_dir / safe_name

        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        rel_url = f"/output/uploads/{target_sid}/{safe_name}"
        return rel_url, str(dest_path)

    def resolve_asset_path(self, asset_url: str) -> str:
        """解析资产 URL 为本地物理绝对路径"""
        if not asset_url:
            return ""
        if os.path.isabs(asset_url) and os.path.exists(asset_url):
            return asset_url

        base_dir = Path(__file__).resolve().parent.parent
        clean_url = asset_url.lstrip("/")
        if clean_url.startswith("output/"):
            abs_path = base_dir / clean_url
        else:
            abs_path = base_dir / "output" / clean_url
        return str(abs_path)

    async def extract_dossier_from_image(
        self,
        image_bytes: bytes,
        category_hint: Optional[str] = "",
        session_id: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Tuple[Any, str]:
        """随手拍多模态逆向萃取商品商业档案 (多模型容错与规则熔断兜底)"""
        from ecommerce_studio.vision_adapter import MultiModalVisionAdapter
        config = self.get_config()
        adapter = MultiModalVisionAdapter(config)
        dossier, provider = await adapter.extract_dossier(image_bytes, category_hint=category_hint)
        return dossier, provider

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        data = session_manager.get_session(session_id)
        if not data:
            return None
        return normalize_session_data(data)

    def _get_or_create_session(
        self, session_id: str, default_product_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取已有会话；若磁盘不存在则自动自愈创建，避免前端客户端临时会话或刷新后未落盘导致 404"""
        data = session_manager.get_session(session_id)
        if not data:
            data = session_manager.create_session(
                session_id=session_id,
                name="智能电商视觉全案",
                product_info=default_product_info
                or {
                    "name": "智能数显真空气密随行保温杯",
                    "category": "316L医用不锈钢 / 哑光亲肤磨砂黑 / 触控数显杯盖",
                    "target_audience": "25-38岁都市白领、商务通勤人士、注重生活质感的咖啡/茶饮爱好者",
                    "pain_points": "市面竞品保温时长短、放在背包里容易渗水、杯口易烫嘴、瓶身容易刮花掉漆",
                    "material_features": "316L医用级不锈钢内胆，外壁曜石黑亲肤喷砂烤漆，高精度LED数显触控屏",
                },
                style_preset="minimalist_muji",
            )
            if not data.get("prompts_matrix"):
                data["prompts_matrix"] = build_default_prompt_matrix(data.get("product_info", {}))
                session_manager.save_session(data)
        return data

    def delete_session(self, session_id: str) -> bool:
        return session_manager.delete_session(session_id)

    def update_prompt(self, session_id: str, perspective_id: str, new_prompt: str) -> Dict[str, Any]:
        data = session_manager.get_session(session_id)
        if not data:
            raise ValueError(f"会话 {session_id} 不存在")

        canon_id = canonicalize_perspective_id(perspective_id)
        found = False

        # 更新 prompts_matrix
        for item in data.get("prompts_matrix", []):
            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                item["prompt"] = new_prompt
                found = True

        # 更新 generated_images 当前提示词
        for item in data.get("generated_images", []):
            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                item["prompt"] = new_prompt
                found = True

        if not found:
            data.setdefault("prompts_matrix", []).append({
                "id": canon_id,
                "name": f"视角_{canon_id}",
                "desc": "",
                "prompt": new_prompt,
            })

        session_manager.save_session(data)
        return {"success": True, "perspective_id": canon_id, "prompt_zh": new_prompt}

    def generate_plan_sync(
        self,
        session_id: Optional[str],
        product_info: Dict[str, Any],
        style_preset: Optional[str] = "minimalist_muji",
    ) -> Dict[str, Any]:
        t0 = time.time()
        prod_name = product_info.get("name") or product_info.get("product_name") or "未命名商品"
        logger.info(f"📋 [Generate Plan Start] session={session_id}, product='{prod_name}', style={style_preset}")
        config = self.get_config()
        if session_id:
            session_data = session_manager.get_session(session_id)
            if not session_data:
                session_data = session_manager.create_session(
                    session_id=session_id, product_info=product_info, style_preset=style_preset
                )
        else:
            session_data = session_manager.create_session(product_info=product_info, style_preset=style_preset)
            session_id = session_data["session_id"]

        old_prod_name = (session_data.get("product_info") or {}).get("name")
        new_prod_name = product_info.get("name") or product_info.get("product_name")
        # 若更换了商品名称，清理旧商品的历史生成图片快照，防止旧商品图片或提示词残留
        if old_prod_name and new_prod_name and old_prod_name.strip() != new_prod_name.strip():
            session_data["generated_images"] = []

        target_style = style_preset or session_data.get("style_preset", "minimalist_muji")
        session_data["style_preset"] = target_style
        session_data["product_info"] = product_info

        # 直接调用 AI 商业视觉导演全自主深度推理引擎
        try:
            logger.info(f"🧠 [AI Vision Director Start] product='{prod_name}', style={target_style}")
            matrix = studio_crew.generate_vision_matrix_with_ai(
                product_info=product_info,
                style_preset_id=target_style,
                config=config,
            )
            session_data["analysis_result"] = f"AI 商业视觉导演已针对《{prod_name}》深度推演 9 大黄金商业视角提示词与全案策略。"
            session_data["prompts_matrix"] = matrix
        except Exception as e:
            # 优雅兜底方案：调用 AI 视觉导演全自主编译兜底
            logger.warning(f"⚠️ [Generate Plan Warning] 大模型推演降级，使用模板矩阵兜底: {e}")
            matrix = studio_crew.generate_vision_matrix_with_ai(
                product_info=product_info,
                style_preset_id=target_style,
                config=config,
                force_fallback=True,
            )
            session_data["prompts_matrix"] = matrix
            session_data["analysis_result"] = f"推演已就绪（规则引擎兜底）。产品画像：{product_info.get('name', '商品')}"

        # 同步更新已存在 generated_images 中的 prompt 为最新推演矩阵提示词
        for item in matrix:
            c_id = canonicalize_perspective_id(item.get("id", ""))
            for g in session_data.get("generated_images", []):
                if canonicalize_perspective_id(g.get("id", "")) == c_id:
                    g["prompt"] = item.get("prompt", "")

        session_manager.save_session(session_data)
        elapsed = time.time() - t0
        logger.info(f"🎯 [Generate Plan Done] session={session_id}, matrices={len(matrix)}, elapsed={elapsed:.2f}s")
        return normalize_session_data(session_data)

    async def generate_plan_stream(
        self,
        session_id: Optional[str],
        product_info: Dict[str, Any],
        style_preset: Optional[str] = "minimalist_muji",
    ) -> AsyncGenerator[str, None]:
        """SSE 流式推演 Step 1 & Step 2 全案"""
        yield f"event: progress\ndata: {json.dumps({'stage': 'init', 'percent': 10, 'message': '正在读取商品资产与客群画像...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        yield f"event: progress\ndata: {json.dumps({'stage': 'market', 'percent': 35, 'message': '商品洞察专家正在深挖买家核心抗拒点与消费心理...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.1)

        yield f"event: progress\ndata: {json.dumps({'stage': 'creative', 'percent': 65, 'message': '视觉创意总监正在规划 9 大转化动线与商业光影美学...'}, ensure_ascii=False)}\n\n"

        loop = asyncio.get_event_loop()
        normalized_data = await loop.run_in_executor(
            self._executor, self.generate_plan_sync, session_id, product_info, style_preset
        )

        yield f"event: progress\ndata: {json.dumps({'stage': 'scripting', 'percent': 90, 'message': 'AI 制图工程师已完成 9 大商业摄影镜头脚本编译...'}, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.05)

        yield f"event: complete\ndata: {json.dumps(normalized_data, ensure_ascii=False)}\n\n"

    def refine_prompt(
        self, session_id: str, perspective_id: str, instruction: str, auto_create: bool = False
    ) -> Dict[str, Any]:
        """AI 顾问润色单视角镜头指导词"""
        t0 = time.time()
        data = session_manager.get_session(session_id)
        if not data:
            if not auto_create:
                raise ValueError(f"会话 {session_id} 不存在")
            logger.info(f"🔄 [Single Render Self-Healing] 会话 {session_id} 尚未落盘，自动自愈创建...")
            data = self._get_or_create_session(session_id)

        config = self.get_config()
        canon_id = canonicalize_perspective_id(perspective_id)
        logger.info(f"🧠 [Refine Prompt Start] session={session_id}, perspective={canon_id}, instruction='{instruction[:60]}'")

        # 找到当前提示词与视角名称
        curr_prompt = ""
        p_name = ""
        for p in PERSPECTIVE_DEFINITIONS:
            if p["id"] == canon_id:
                p_name = p["name"]
                break

        for item in data.get("prompts_matrix", []):
            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                curr_prompt = item.get("prompt", "")
                break

        if not curr_prompt:
            for item in data.get("generated_images", []):
                if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                    curr_prompt = item.get("prompt", "")
                    break

        if not curr_prompt:
            curr_prompt = f"商业级电商摄影，{data.get('product_info', {}).get('name', '商品')}，顶级棚拍光影，8k超清。"

        try:
            refined = studio_crew.refine_prompt_with_ai(
                original_prompt=curr_prompt,
                user_feedback=instruction,
                config=config,
                image_type_name=p_name,
            )
        except Exception:
            # 规则润色兜底
            refined = f"{curr_prompt}。微调指导：{instruction}。注重顶光柔和漫射与材质真实还原，8k画质。"

        # 更新回会话
        self.update_prompt(session_id, canon_id, refined)
        elapsed = time.time() - t0
        logger.info(f"✨ [Refine Prompt Done] session={session_id}, perspective={canon_id}, elapsed={elapsed:.2f}s")
        return {"success": True, "perspective_id": canon_id, "refined_prompt": refined, "prompt_zh": refined}

    def regenerate_perspective_script(
        self,
        session_id: str,
        perspective_id: str,
        instruction: str = "",
        auto_create: bool = False,
    ) -> Dict[str, Any]:
        """
        AI 视觉导演全自主单卡重新构思：
        根据用户输入的指示或灵感换一换，针对单个视角全自主重新推导提示词、画面构想、转化策略与微调胶囊。
        """
        t0 = time.time()
        data = session_manager.get_session(session_id)
        if not data:
            if not auto_create:
                raise ValueError(f"会话 {session_id} 不存在")
            data = self._get_or_create_session(session_id)

        config = self.get_config()
        canon_id = canonicalize_perspective_id(perspective_id)
        product_info = data.get("product_info") or {}
        style_preset_id = data.get("style_preset", "minimalist_muji")

        # 获取已有提示词
        curr_prompt = ""
        for item in data.get("prompts_matrix", []):
            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                curr_prompt = item.get("prompt", "")
                break

        res = studio_crew.regenerate_single_perspective_with_ai(
            product_info=product_info,
            perspective_id=canon_id,
            style_preset_id=style_preset_id,
            instruction=instruction,
            current_prompt=curr_prompt,
            config=config,
        )

        # 更新回 session.prompts_matrix
        updated = False
        for item in data.setdefault("prompts_matrix", []):
            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                item["prompt"] = res["prompt"]
                item["prompt_zh"] = res["prompt_zh"]
                item["scene_highlight"] = res["scene_highlight"]
                item["commercial_strategy"] = res["commercial_strategy"]
                item["quick_tweaks"] = res["quick_tweaks"]
                item["quick_tweak_pills"] = res["quick_tweak_pills"]
                updated = True
                break

        if not updated:
            data["prompts_matrix"].append(res)

        # 同步更新 generated_images
        for g in data.setdefault("generated_images", []):
            if canonicalize_perspective_id(g.get("id", "")) == canon_id:
                g["prompt"] = res["prompt"]

        session_manager.save_session(data)
        elapsed = time.time() - t0
        logger.info(f"✨ [Regenerate Perspective Script Done] session={session_id}, perspective={canon_id}, elapsed={elapsed:.2f}s")

        return {
            "success": True,
            "session_id": session_id,
            "perspective_id": canon_id,
            "name": res["name"],
            "scene_highlight": res["scene_highlight"],
            "commercial_strategy": res["commercial_strategy"],
            "prompt_zh": res["prompt_zh"],
            "quick_tweaks": res["quick_tweaks"],
            "quick_tweak_pills": res["quick_tweak_pills"],
        }

    def render_single_version_sync(
        self,
        session_id: str,
        perspective_id: str,
        prompt_zh: Optional[str] = None,
        change_reason: str = "单视角二次调词出图",
        trigger_type: str = "manual_edit",
        aspect_ratio: str = "1:1",
        auto_create: bool = False,
    ) -> Dict[str, Any]:
        """
        单视角渲染出图并产生不可变新版本快照
        """
        t0 = time.time()
        data = session_manager.get_session(session_id)
        if not data:
            if not auto_create:
                raise ValueError(f"会话 {session_id} 不存在")
            logger.info(f"🔄 [Single Render Self-Healing] 会话 {session_id} 尚未落盘，自动自愈创建...")
            data = self._get_or_create_session(session_id)

        canon_id = canonicalize_perspective_id(perspective_id)
        config = self.get_config()

        # 确定使用的 prompt
        target_prompt = (prompt_zh or "").strip()
        if not target_prompt:
            for item in data.get("prompts_matrix", []):
                if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                    target_prompt = item.get("prompt", "")
                    break
        if not target_prompt:
            target_prompt = f"高端商业广告摄影，{data.get('product_info', {}).get('name', '精品电商商品')}，顶级柔光箱布光，8k清晰度。"

        logger.info(f"🎨 [Single Render Start] session={session_id}, perspective={canon_id}, ratio={aspect_ratio}, prompt='{target_prompt[:60]}...'")

        # 准备输出目录: output/{session_id}/{canon_id}
        base_dir = Path(__file__).resolve().parent.parent
        out_dir = str(base_dir / "output" / session_id / canon_id)
        os.makedirs(out_dir, exist_ok=True)

        # 出图调用
        active_p = config.get("active_provider", "gemini")
        try:
            img_path = generate_ecommerce_image(
                prompt=target_prompt,
                provider=active_p,
                config=config,
                output_dir=out_dir,
                aspect_ratio=aspect_ratio,
                filename_prefix=canon_id,
            )
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"❌ [Single Render Error] session={session_id}, perspective={canon_id}, provider={active_p}, failed after {elapsed:.2f}s: {e}")
            raw_err = str(e)
            if "当前中继端点" not in raw_err and "超时" not in raw_err and "额度不足" not in raw_err and "未开通" not in raw_err:
                err_msg = f"生成图片失败 [{active_p}]: {raw_err}。建议检查代理生图配置，或在设置中切换为 Gemini。"
            else:
                err_msg = raw_err
            raise RuntimeError(err_msg) from e

        # 追加版本快照
        session_manager.add_image_version(
            session_data=data,
            item_id=canon_id,
            image_path=img_path,
            prompt=target_prompt,
            note=change_reason,
            aspect_ratio=aspect_ratio,
        )

        # 同时同步更新 prompts_matrix 中该视角的提示词，确保前后端数据一致
        for item in data.get("prompts_matrix", []):
            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                item["prompt"] = target_prompt

        # 返回最新 normalized session 和新版本对象
        updated_session = normalize_session_data(data)
        new_version = None
        for p in updated_session.get("perspectives", []):
            if p["id"] == canon_id:
                if p.get("versions"):
                    new_version = p["versions"][-1]
                break

        elapsed = time.time() - t0
        logger.info(f"✅ [Single Render Success] session={session_id}, perspective={canon_id}, elapsed={elapsed:.2f}s, img_path={img_path}")

        return {
            "success": True,
            "perspective_id": canon_id,
            "version": new_version,
            "session": updated_session,
        }

    def rollback_version(
        self, session_id: str, perspective_id: str, version_id: Union[str, int]
    ) -> Dict[str, Any]:
        """执行版本回滚"""
        data = session_manager.get_session(session_id)
        if not data:
            raise ValueError(f"会话 {session_id} 不存在")

        canon_id = canonicalize_perspective_id(perspective_id)
        ok = session_manager.rollback_to_version(data, canon_id, version_id)
        if not ok:
            # 兼容尝试 alt_id
            for p in PERSPECTIVE_DEFINITIONS:
                if p["id"] == canon_id:
                    ok = session_manager.rollback_to_version(data, p["alt_id"], version_id)
                    break

        if not ok:
            raise ValueError(f"回滚失败，未找到视角 {perspective_id} 对应的版本 {version_id}")

        # 同步更新 prompts_matrix 为目标回滚版本的 prompt
        for g in data.get("generated_images", []):
            if canonicalize_perspective_id(g.get("id", "")) == canon_id:
                for v in g.get("versions", []):
                    if str(v.get("version_id")) == str(version_id):
                        target_v_prompt = v.get("prompt", "")
                        for item in data.get("prompts_matrix", []):
                            if canonicalize_perspective_id(item.get("id", "")) == canon_id:
                                item["prompt"] = target_v_prompt
                        break

        updated = normalize_session_data(data)
        restored_prompt = ""
        active_v = "v1"
        for p in updated.get("perspectives", []):
            if p["id"] == canon_id:
                active_v = p.get("active_version_id", "v1")
                restored_prompt = p.get("prompt_zh", "")
                break

        return {
            "success": True,
            "perspective_id": canon_id,
            "active_version_id": active_v,
            "restored_prompt": restored_prompt,
            "session": updated,
        }

    async def render_batch_stream(
        self,
        session_id: str,
        aspect_ratio: str = "1:1",
        concurrency: int = 1,
        perspective_ids: Optional[List[str]] = None,
        prompts: Optional[Dict[str, str]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        SSE 流式渲染 9 大图矩阵。
        严格锁定并发为 1 (串行保活模式)，彻底规避中继代理服务商的 429 限流、并发阻塞与长连接中断，
        践行“功能可用比效率更有价值”的最高准则。
        """
        batch_t0 = time.time()
        data = session_manager.get_session(session_id)
        if not data:
            logger.warning(f"⚠️ [Batch Render Error] 会话 {session_id} 不存在")
            yield f"event: error\ndata: {json.dumps({'error': f'专案不存在: {session_id}'}, ensure_ascii=False)}\n\n"
            return

        # 同步前端传入的各视角当前最新镜头指导词
        if prompts and isinstance(prompts, dict):
            for pid, p_text in prompts.items():
                if p_text:
                    try:
                        self.update_prompt(session_id, pid, p_text)
                    except Exception as e:
                        logger.warning(f"⚠️ [Prompt Sync Warning] 同步视角 {pid} 指导词失败: {e}")
            data = session_manager.get_session(session_id)

        normalized = normalize_session_data(data)
        all_perspectives = normalized.get("perspectives", [])

        # 过滤目标 perspectives
        if perspective_ids:
            target_ids = {canonicalize_perspective_id(x) for x in perspective_ids}
            targets = [p for p in all_perspectives if p["id"] in target_ids]
        else:
            targets = all_perspectives

        total = len(targets)
        # 强制并发度为 1
        effective_concurrency = 1
        logger.info(
            f"🚀 [Batch Render Start] session={session_id}, total_targets={total}, "
            f"concurrency_locked=1, aspect_ratio={aspect_ratio}"
        )
        yield f"event: start\ndata: {json.dumps({'total': total, 'concurrency': effective_concurrency, 'aspect_ratio': aspect_ratio}, ensure_ascii=False)}\n\n"

        sem = asyncio.Semaphore(effective_concurrency)
        completed_count = 0
        loop = asyncio.get_event_loop()
        event_queue: asyncio.Queue = asyncio.Queue()

        async def _render_one(p_item: Dict[str, Any]):
            nonlocal completed_count
            p_id = p_item["id"]
            p_name = p_item["name"]
            p_prompt = p_item.get("prompt_zh") or f"商业级电商摄影，{p_name}，超清细节。"

            wait_t0 = time.time()
            logger.info(f"⏳ [Batch Queue] Perspective [{p_id}] ({p_name}) 进入排队队列...")

            async with sem:
                wait_s = time.time() - wait_t0
                render_t0 = time.time()
                logger.info(
                    f"🎬 [Batch Slot Acquired] Perspective [{p_id}] ({p_name}) 获取出图机位 "
                    f"(排队等待耗时: {wait_s:.2f}s)"
                )

                # 信号量就绪，立即向客户端流式推送单机位开始事件
                await event_queue.put(
                    f"event: perspective_start\ndata: {json.dumps({'event': 'perspective_start', 'perspective_id': p_id, 'name': p_name}, ensure_ascii=False)}\n\n"
                )

                try:
                    res = await loop.run_in_executor(
                        self._executor,
                        self.render_single_version_sync,
                        session_id,
                        p_id,
                        p_prompt,
                        "全套商业图首轮串行稳定渲染",
                        "batch_initial",
                        aspect_ratio,
                    )
                    completed_count += 1
                    render_s = time.time() - render_t0
                    ver = res.get("version") or {}
                    logger.info(
                        f"✅ [Batch Slot Success] Perspective [{p_id}] ({p_name}) 出图成功! "
                        f"机位渲染耗时: {render_s:.2f}s, 当前进度: {completed_count}/{total}"
                    )
                    await event_queue.put(
                        f"event: perspective_success\ndata: {json.dumps({'event': 'perspective_done', 'perspective_id': p_id, 'name': p_name, 'version': ver, 'image_url': ver.get('image_url'), 'completed': completed_count, 'total': total}, ensure_ascii=False)}\n\n"
                    )
                except Exception as ex:
                    completed_count += 1
                    render_s = time.time() - render_t0
                    logger.error(
                        f"❌ [Batch Slot Error] Perspective [{p_id}] ({p_name}) 出图失败! "
                        f"耗时: {render_s:.2f}s, 错误详情: {ex}"
                    )
                    await event_queue.put(
                        f"event: perspective_error\ndata: {json.dumps({'event': 'perspective_error', 'perspective_id': p_id, 'name': p_name, 'error': str(ex), 'completed': completed_count, 'total': total}, ensure_ascii=False)}\n\n"
                    )

        async def _run_all():
            tasks = [asyncio.create_task(_render_one(p)) for p in targets]
            await asyncio.gather(*tasks, return_exceptions=True)
            await event_queue.put(None)

        producer_task = asyncio.create_task(_run_all())

        try:
            while True:
                try:
                    item = await asyncio.wait_for(event_queue.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    # 持续双通道推送心跳：标准事件让 SSE Client 解析，注释行保持 TCP 管道与中间网关活跃
                    yield f"event: ping\ndata: {json.dumps({'event': 'ping', 'timestamp': int(time.time())})}\n\n"
                    yield ": ping\n\n"
                    continue

                if item is None:
                    break
                yield item
        finally:
            if not producer_task.done():
                producer_task.cancel()

        total_batch_s = time.time() - batch_t0
        logger.info(
            f"🏁 [Batch Render Complete] session={session_id}, completed={completed_count}/{total}, "
            f"全流程总耗时={total_batch_s:.2f}s"
        )

        # 渲染完结
        final_session = self.get_session(session_id)
        yield f"event: complete\ndata: {json.dumps({'event': 'batch_complete', 'completed': completed_count, 'total': total, 'session': final_session}, ensure_ascii=False)}\n\n"

    async def copilot_chat_stream(
        self,
        session_id: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        首席视觉顾问 SSE 流式对话与方案建议注入
        """
        data = session_manager.get_session(session_id)
        if not data:
            yield f"event: error\ndata: {json.dumps({'error': f'会话 {session_id} 不存在'}, ensure_ascii=False)}\n\n"
            return

        config = self.get_config()
        # 记录用户消息
        session_manager.add_chat_message(session_id, role="user", content=message)

        # 组装增强情境
        step = (context or {}).get("step", 3)
        active_pid = (context or {}).get("active_perspective_id")
        canon_active_pid = canonicalize_perspective_id(active_pid) if active_pid else None

        active_p_name = ""
        for p in PERSPECTIVE_DEFINITIONS:
            if p["id"] == canon_active_pid:
                active_p_name = p["name"]
                break

        context_prompt_enhancement = ""
        if canon_active_pid:
            context_prompt_enhancement = (
                f"\n【用户当前正聚焦视察的机位】：{active_p_name} ({canon_active_pid})\n"
                f"如果在回答中提出优化建议，请给出明确可用于生图的中文摄影布景指令，并以『【推荐镜头方案】：...』格式标明，以便一键应用。"
            )

        loop = asyncio.get_event_loop()
        try:
            full_response = await loop.run_in_executor(
                self._executor,
                session_manager.chat_with_agent,
                data,
                f"{message}\n{context_prompt_enhancement}",
                config,
            )
        except Exception as e:
            full_response = (
                f"主理人您好，我是您的首席视觉顾问。关于您提出的「{message[:20]}」，"
                f"建议在当前视觉中加强侧光对比度与通透感，以提升商品首图点击率与质感认同。"
            )

        # 持久化顾问回复
        session_manager.add_chat_message(session_id, role="assistant", content=full_response)

        # 模拟打字机平滑流式吐出
        chunk_size = 8
        for i in range(0, len(full_response), chunk_size):
            chunk = full_response[i : i + chunk_size]
            yield f"event: delta\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.02)

        # 检测是否有可供注入的 ActionChip 镜头方案
        plan_match = re.search(r"【推荐镜头方案】[：:]\s*([^\n]+)", full_response)
        if plan_match and canon_active_pid:
            action_prompt = plan_match.group(1).strip()
            yield f"event: action_chip\ndata: {json.dumps({'perspective_id': canon_active_pid, 'label': f'✨ 应用此镜头方案到 {active_p_name}', 'prompt_zh': action_prompt}, ensure_ascii=False)}\n\n"

        yield f"event: done\ndata: {json.dumps({'role': 'assistant', 'content': full_response}, ensure_ascii=False)}\n\n"

    def export_zip(self, session_id: str) -> bytes:
        """导出当前定稿商业大片规范命名 ZIP 压缩包"""
        data = session_manager.get_session(session_id)
        if not data:
            raise ValueError("会话不存在")

        normalized = normalize_session_data(data)
        perspectives = normalized.get("perspectives", [])

        # 提取 active_version 的图片路径
        images_for_zip = []
        for p in perspectives:
            active_vid = p.get("active_version_id")
            selected_v = None
            for v in p.get("versions", []):
                if v.get("version_id") == active_vid:
                    selected_v = v
                    break
            if not selected_v and p.get("versions"):
                selected_v = p["versions"][-1]

            if selected_v and selected_v.get("image_path"):
                images_for_zip.append({
                    "id": p["id"],
                    "name": p["name"],
                    "image_path": selected_v["image_path"],
                    "active_version": selected_v.get("version_num", 1),
                })

        from ecommerce_studio.app import create_images_zip
        return create_images_zip(images_for_zip)

    def export_markdown(self, session_id: str) -> str:
        """导出全套策划方案 Markdown 文本"""
        data = session_manager.get_session(session_id)
        if not data:
            raise ValueError("会话不存在")

        normalized = normalize_session_data(data)
        prod = normalized.get("product_info", {})
        strat = normalized.get("strategy_summary", {})
        perspectives = normalized.get("perspectives", [])

        lines = [
            f"# 商业级电商视觉全案策划报告",
            f"**专案名称**: {normalized.get('name', '电商摄影方案')}  ",
            f"**生成时间**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(normalized.get('updated_at', int(time.time()))))}  ",
            f"**会话ID**: `{session_id}`  \n",
            "---",
            "## 一、 商品商业画像与痛点解构",
            f"- **商品名称**: {prod.get('name', '未命名')}",
            f"- **所属品类**: {prod.get('category', '通用')}",
            f"- **材质工艺**: {prod.get('material_features', '优质用料')}",
            f"- **目标客群**: {prod.get('target_audience', '品质消费者')}",
            f"- **买家抗拒点**: {prod.get('pain_points', '无')}\n",
            "## 二、 视觉总监策划全案摘要",
            f"- **品牌视觉基调**: {strat.get('tone', '')}",
            f"- **核心击穿卖点 (USP)**: {strat.get('usp', '')}",
            f"- **色彩体系**: {', '.join(strat.get('color_palette', []))}\n",
            "## 三、 9大商业转化视觉镜头指令矩阵",
        ]

        for p in perspectives:
            lines.append(f"### {p['id']} · {p['name']} ({p.get('tag', '')})")
            lines.append(f"> **商业转化心理学**: {p.get('desc', '')}\n")
            lines.append(f"**镜头语言与布景指导**:\n```\n{p.get('prompt_zh', '')}\n```\n")

        return "\n".join(lines)


# 全局单例
studio_service = StudioBackendService()
