import json
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_SESSION_LOCK = threading.RLock()


def get_sessions_dir() -> Path:
    """获取会话存储目录，默认在 ecommerce_studio/sessions"""
    base_dir = Path(__file__).resolve().parent
    sessions_dir = base_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    return sessions_dir


def _get_session_path(session_id: str) -> Path:
    """获取单个 session 文件的完整路径"""
    safe_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_"))
    if not safe_id:
        safe_id = "default_session"
    return get_sessions_dir() / f"{safe_id}.json"


def create_session(
    session_id: Optional[str] = None,
    name: str = "",
    product_info: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    style_preset: Optional[str] = "minimalist_muji",
) -> Dict[str, Any]:
    """
    创建一个新的电商策划会话
    """
    now = int(time.time())
    if not session_id:
        random_suffix = uuid.uuid4().hex[:8]
        session_id = f"sess_{now}_{random_suffix}"

    display_name = name.strip() or f"策划方案_{time.strftime('%m%d_%H%M', time.localtime(now))}"

    session_data: Dict[str, Any] = {
        "session_id": session_id,
        "name": display_name,
        "created_at": now,
        "updated_at": now,
        "product_info": product_info or {},
        "style_preset": style_preset or "minimalist_muji",
        "analysis_result": "",
        "prompts_matrix": [],
        "generated_images": [],
        "chat_history": [],
        "metadata": metadata or {},
        "schema_version": "2.0",
    }

    save_session(session_data)
    return session_data


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    读取指定 session_id 的会话数据，若不存在返回 None，并自动迁移至 v2 结构
    """
    path = _get_session_path(session_id)
    if not path.is_file():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return migrate_session_to_v2(data)
    except Exception as e:
        print(f"读取会话 {session_id} 失败: {e}")
        return None


def save_session(session_data: Dict[str, Any]) -> str:
    """
    保存会话数据到 sessions/<session_id>.json，更新 updated_at
    返回 session 文件的绝对路径（线程安全与原子写入）
    """
    session_id = session_data.get("session_id")
    if not session_id:
        raise ValueError("session_data 缺少 session_id 字段！")

    session_data["updated_at"] = int(time.time())
    path = _get_session_path(session_id)

    unique_suffix = f".tmp_{os.getpid()}_{uuid.uuid4().hex}"
    tmp_path = path.with_suffix(unique_suffix)

    with _SESSION_LOCK:
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            tmp_path.replace(path)
        except Exception:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass
            raise

    return str(path)


def list_sessions() -> List[Dict[str, Any]]:
    """
    获取所有会话列表，按更新时间降序排列
    """
    sessions_dir = get_sessions_dir()
    results = []

    for item in sessions_dir.glob("*.json"):
        try:
            with open(item, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append({
                    "session_id": data.get("session_id", item.stem),
                    "name": data.get("name", "未命名方案"),
                    "created_at": data.get("created_at", 0),
                    "updated_at": data.get("updated_at", 0),
                    "product_name": data.get("product_info", {}).get("name", ""),
                    "style_preset": data.get("style_preset", "minimalist_muji"),
                    "images_count": len(data.get("generated_images", [])),
                    "chat_count": len(data.get("chat_history", [])),
                    "path": str(item),
                })
        except Exception:
            continue

    results.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
    return results


def delete_session(session_id: str) -> bool:
    """
    删除指定 session_id 的会话文件
    """
    path = _get_session_path(session_id)
    if path.is_file():
        try:
            path.unlink()
            return True
        except Exception as e:
            print(f"删除会话 {session_id} 失败: {e}")
            return False
    return False


def migrate_session_to_v2(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将老版本扁平结构自动无缝升级适配为 v2 非破坏性版本链条结构
    向后兼容老 session 数据，历史已生成的图片自动转为 v1 初始版本
    """
    if not isinstance(session_data, dict):
        return session_data

    gen_images = session_data.get("generated_images", [])
    if not isinstance(gen_images, list):
        gen_images = []
        session_data["generated_images"] = []

    # 检查是否已是完整 v2 结构
    is_v2 = (
        session_data.get("schema_version") == "2.0"
        and all(isinstance(img, dict) and "versions" in img for img in gen_images)
    )
    if is_v2:
        session_data.setdefault("style_preset", "minimalist_muji")
        return session_data

    migrated_images = []
    updated_ts = session_data.get("updated_at") or int(time.time())
    created_time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(updated_ts))

    for item in gen_images:
        if not isinstance(item, dict):
            continue

        p_id = item.get("id", "")
        name = item.get("name", "")
        desc = item.get("desc", "")
        img_path = item.get("image_path")
        prompt = item.get("prompt", "")

        # 如果已有 versions 列表且非空，则保留
        if "versions" in item and isinstance(item["versions"], list):
            versions = item["versions"]
            active_v = item.get("active_version")
            if not active_v and versions:
                active_v = versions[-1].get("version_num", 1)
            active_v_tag = f"v{active_v}" if active_v else None
            migrated_images.append({
                "id": p_id,
                "name": name,
                "desc": desc,
                "prompt": item.get("prompt", ""),
                "image_path": item.get("image_path"),
                "status": item.get("status", "success" if img_path else "pending"),
                "error": item.get("error"),
                "versions": versions,
                "active_version": active_v,
                "active_version_id": active_v_tag,
            })
            continue

        # 旧结构迁移为包含 versions 的结构
        versions = []
        if img_path and os.path.exists(img_path):
            versions.append({
                "version_id": 1,
                "version_tag": "v1",
                "version_num": 1,
                "image_path": img_path,
                "prompt": prompt,
                "prompt_zh": prompt,
                "timestamp": updated_ts,
                "created_at_fmt": created_time_str,
                "note": "初始全套商业渲染",
                "aspect_ratio": "1:1",
            })
            active_v = 1
            active_v_tag = "v1"
            status = "success"
        else:
            active_v = None
            active_v_tag = None
            status = item.get("status", "pending")

        migrated_images.append({
            "id": p_id,
            "name": name,
            "desc": desc,
            "prompt": prompt,
            "image_path": img_path if (img_path and os.path.exists(img_path)) else None,
            "status": status,
            "error": item.get("error"),
            "versions": versions,
            "active_version": active_v,
            "active_version_id": active_v_tag,
        })

    session_data["generated_images"] = migrated_images
    session_data["schema_version"] = "2.0"
    return session_data


def add_image_version(
    session_data: Dict[str, Any],
    item_id: str,
    image_path: str,
    prompt: str,
    note: str = "AI调整重绘",
    aspect_ratio: str = "1:1",
) -> Dict[str, Any]:
    """
    为指定图片视角项追加新的不可变版本快照，不覆盖任何历史版本，并将新版本设为当前激活版本
    """
    migrate_session_to_v2(session_data)
    gen_images = session_data.setdefault("generated_images", [])

    target_item = None
    for item in gen_images:
        if item.get("id") == item_id:
            target_item = item
            break

    if target_item is None:
        # 尝试从 prompts_matrix 获取元数据
        name = f"视角_{item_id}"
        desc = ""
        for p in session_data.get("prompts_matrix", []):
            if p.get("id") == item_id:
                name = p.get("name", name)
                desc = p.get("desc", desc)
                break
        target_item = {
            "id": item_id,
            "name": name,
            "desc": desc,
            "prompt": prompt,
            "image_path": image_path,
            "status": "success",
            "error": None,
            "versions": [],
            "active_version": None,
            "active_version_id": None,
        }
        gen_images.append(target_item)

    versions = target_item.setdefault("versions", [])
    new_v_num = len(versions) + 1
    now = int(time.time())
    now_fmt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))

    new_version_obj = {
        "version_id": new_v_num,
        "version_tag": f"v{new_v_num}",
        "version_num": new_v_num,
        "image_path": image_path,
        "prompt": prompt,
        "prompt_zh": prompt,
        "timestamp": now,
        "created_at_fmt": now_fmt,
        "note": note,
        "aspect_ratio": aspect_ratio,
    }
    versions.append(new_version_obj)

    # 将活跃指针指向新生成的版本
    target_item["active_version"] = new_v_num
    target_item["active_version_id"] = f"v{new_v_num}"
    target_item["image_path"] = image_path
    target_item["prompt"] = prompt
    target_item["status"] = "success"
    target_item["error"] = None

    # 同步更新 prompts_matrix 对应提示词
    for p_elem in session_data.get("prompts_matrix", []):
        if p_elem.get("id") == item_id:
            p_elem["prompt"] = prompt
            break

    save_session(session_data)
    return session_data


def switch_active_version(
    session_data: Dict[str, Any],
    item_id: str,
    target_version_id: Any,
) -> bool:
    """
    切换指定图片视角的活跃展示版本（支持 int 或 'v1' 等字符串），不改变历史数据
    """
    migrate_session_to_v2(session_data)
    target_str = str(target_version_id).strip().lower()
    if target_str.startswith("v"):
        target_str = target_str[1:]

    for item in session_data.get("generated_images", []):
        if item.get("id") == item_id:
            versions = item.get("versions", [])
            for v in versions:
                v_num_str = str(v.get("version_num", ""))
                v_id_str = str(v.get("version_id", ""))
                if v_num_str == target_str or v_id_str == target_str:
                    item["active_version"] = v["version_num"]
                    item["active_version_id"] = f"v{v['version_num']}"
                    item["image_path"] = v["image_path"]
                    item["prompt"] = v.get("prompt", "")
                    save_session(session_data)
                    return True
            return False
    return False


def rollback_to_version(
    session_data: Dict[str, Any],
    item_id: str,
    target_version_id: Any,
) -> bool:
    """
    【后悔药机制】一键回滚至指定历史快照版本：
    1. 激活指定历史版本的渲染图片；
    2. 同步恢复 prompts_matrix 中该视角的对应镜头提示词；
    3. 保留后续版本历史不被删除（非破坏性回滚）。
    """
    ok = switch_active_version(session_data, item_id, target_version_id)
    if not ok:
        return False

    # 同步恢复 prompts_matrix 提示词
    for item in session_data.get("generated_images", []):
        if item.get("id") == item_id:
            active_prompt = item.get("prompt", "")
            for p_elem in session_data.get("prompts_matrix", []):
                if p_elem.get("id") == item_id:
                    p_elem["prompt"] = active_prompt
                    break
            break

    save_session(session_data)
    return True


def add_chat_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    """
    向指定会话追加一条聊天记录并持久化
    """
    session_data = get_session(session_id)
    if not session_data:
        raise ValueError(f"未找到 session_id 为 {session_id} 的会话！")

    msg = {
        "role": role,
        "content": content,
        "timestamp": int(time.time()),
    }
    session_data.setdefault("chat_history", []).append(msg)
    save_session(session_data)
    return session_data


def chat_with_agent(session_data: Dict[str, Any], user_message: str, config: Dict[str, Any]) -> str:
    """
    支持用户围绕当前商品策划案进行多轮对话咨询和方案修改探讨。
    结合当前商品信息、策划案、9大图提示词矩阵及历史对话记录。
    """
    if not user_message or not user_message.strip():
        return "请输入您想咨询或探讨的策划问题。"

    product_info = session_data.get("product_info", {})
    prod_name = product_info.get("name", "当前商品")
    category = product_info.get("category", "未分类")
    target_audience = product_info.get("target_audience", "大众群体")
    pain_points = product_info.get("pain_points", "无")
    analysis_result = session_data.get("analysis_result", "暂未生成完整策划案")
    prompts_matrix = session_data.get("prompts_matrix", [])
    chat_history = session_data.get("chat_history", [])

    matrix_summary_lines = []
    for item in prompts_matrix:
        matrix_summary_lines.append(f"- 【{item.get('name', '')}】: {item.get('prompt', '')}")
    matrix_summary = "\n".join(matrix_summary_lines) if matrix_summary_lines else "暂无"

    system_instruction = f"""你是一名顶级电商视觉总监与资深品牌策划顾问（Ecommerce Creative Director & Marketing Strategist）。
你正在协助用户就当前商品的策划案、视觉设计、生图提示词优化以及电商详情页转化策略进行多轮深度对话。

【当前项目基本信息】：
- 商品名称：{prod_name}
- 商品品类：{category}
- 目标受众：{target_audience}
- 核心痛点与抗拒点：{pain_points}

【当前营销策划案摘要】：
{analysis_result[:2500]}

【当前电商 9 大图视觉提示词矩阵】：
{matrix_summary}

【对话指导原则】：
1. 始终基于当前商品特性、目标人群与痛点进行专业且有建设性的回答。
2. 当用户要求修改某张图的生图提示词时，提供具体的中文摄影级润色建议与完整中文提示词。
3. 当用户询问电商运营、文案、构图、详情页布局时，给出高转化率的实操方案。
4. 语言专业、精炼、清晰、富有条理。
"""

    provider = config.get("active_provider", "gemini").lower()

    if provider == "gemini":
        gemini_cfg = config.get("gemini", {})
        api_key = gemini_cfg.get("api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("请先在配置中填写 Gemini API Key！")

        model_name = gemini_cfg.get("model") or "gemini-2.0-flash"

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # 组装对话历史
            # 取最近 10 条历史以控制上下文长度
            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            contents = []

            for msg in recent_history:
                role = "user" if msg.get("role") == "user" else "model"
                contents.append(types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg.get("content", ""))]
                ))

            # 追加当前用户提问
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_message)]
            ))

            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
            return response.text or ""

        except Exception as e:
            raise RuntimeError(f"Gemini 会话对话失败: {str(e)}")

    elif provider == "openai":
        openai_cfg = config.get("openai", {})
        api_key = openai_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
        base_url = openai_cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"

        if not api_key:
            raise ValueError("请先在配置中填写 OpenAI API Key！")

        model_name = openai_cfg.get("model") or "gpt-4o"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)

            messages = [{"role": "system", "content": system_instruction}]

            recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
            for msg in recent_history:
                role = "user" if msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

            messages.append({"role": "user", "content": user_message})

            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            raise RuntimeError(f"OpenAI 会话对话失败: {str(e)}")

    else:
        raise ValueError(f"不支持的 Provider: {provider}")
