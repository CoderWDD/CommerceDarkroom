import base64
import concurrent.futures
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger("ecommerce_studio.image_tool")


def _format_image_generation_error(err: Exception, provider: str, model_name: str, base_url: str) -> str:
    err_str = str(err)
    lower_err = err_str.lower()

    if "404" in err_str or "not found" in lower_err or "unsupported route" in lower_err or "404 page not found" in lower_err:
        return (
            f"当前中继端点 ({base_url}) 未开通或不支持生图接口 (/v1/images/generate)。"
            f"建议在设置中切换为 Gemini 或支持 DALL-E 3 生图的中继端点。"
        )
    if "401" in err_str or "unauthorized" in lower_err or "invalid_api_key" in lower_err:
        return f"接口认证失败 (401 Unauthorized)：API Key 无效或未授权，请检查配置中心密钥。"
    if "402" in err_str or "429" in err_str or "quota" in lower_err or "insufficient" in lower_err or "balance" in lower_err or "credit" in lower_err:
        return f"中继账户额度不足或触发频控限制 (402/429)：{err_str}。请检查中转站余额或配额。"
    if "timeout" in lower_err or "timed out" in lower_err:
        return f"请求中继生图接口超时（已达 60.0s 超时熔断上限）。中转网络挂起或不可达，请检查代理网络。"

    return f"调用 {provider} ({model_name}) 生成图片失败: {err_str}"


def generate_ecommerce_image(
    prompt: str,
    provider: str = "gemini",
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    aspect_ratio: str = "1:1",
    filename_prefix: Optional[str] = None,
) -> str:
    """
    电商商业图生成函数，严格支持高质量中文生图提示词
    :param prompt: 用于生图的提示词（支持中文商业摄影级描述）
    :param provider: 'gemini', 'openai', 'custom_openai', 'ollama'
    :param config: 全局配置字典（包含 API Key、模型名称等）
    :param output_dir: 本地保存图片的目录
    :param aspect_ratio: 图片比例，如 '1:1', '3:4', '4:3', '9:16', '16:9'
    :param filename_prefix: 文件名前缀，用于区分不同批次或图片类型
    :return: 生成的本地图片绝对路径
    """
    if not prompt or not prompt.strip():
        raise ValueError("生图 Prompt 不能为空！")

    if output_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
        output_dir = str(base_dir / "output")

    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    unique_tag = uuid.uuid4().hex[:6]
    total_start_time = time.time()
    clean_prefix = "".join(c for c in (filename_prefix or "product") if c.isalnum() or c in ("-", "_"))
    file_path = os.path.join(output_dir, f"{clean_prefix}_{timestamp}_{unique_tag}.jpg")

    prompt_preview = (prompt[:60] + "...") if len(prompt) > 60 else prompt
    logger.info(
        f"🎨 [GEN START] 生成图片任务启动 | 目标: {clean_prefix} | 比例: {aspect_ratio} | 提示词预览: {prompt_preview}"
    )

    provider = (provider or "gemini").lower().strip()

    # 智能通道探测与故障自愈：若当前激活服务商未配置 Key，自动回退至其他已配置密钥的可用通道
    if config:
        cand_key = ""
        if provider == "gemini":
            cand_key = (config.get("gemini") or {}).get("api_key") or os.environ.get("GEMINI_API_KEY")
        elif provider in ["openai", "custom_openai"]:
            cand_key = (
                (config.get(provider) or {}).get("api_key")
                or (config.get("openai") or {}).get("api_key")
                or os.environ.get(f"{provider.upper()}_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
            )
        elif provider == "ollama":
            cand_key = "ollama"

        if not cand_key:
            for fallback_p in ["openai", "custom_openai", "gemini", "ollama"]:
                fb_cfg = (config or {}).get(fallback_p, {})
                fb_key = (
                    fb_cfg.get("api_key")
                    or os.environ.get(f"{fallback_p.upper()}_API_KEY")
                    or (os.environ.get("OPENAI_API_KEY") if fallback_p in ["openai", "custom_openai"] else None)
                )
                if fallback_p == "ollama" and fb_cfg.get("base_url"):
                    provider = fallback_p
                    break
                elif fb_key:
                    provider = fallback_p
                    break

    if provider == "gemini":
        gemini_cfg = (config or {}).get("gemini", {})
        api_key = gemini_cfg.get("api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("未检测到 Gemini API Key，请在侧边栏配置或设置 GEMINI_API_KEY 环境变量！")

        model_name = gemini_cfg.get("image_model") or "imagen-3.0-generate-002"

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            # Imagen 3 支持的 aspect_ratio: "1:1", "3:4", "4:3", "9:16", "16:9"
            valid_ratios = ["1:1", "3:4", "4:3", "9:16", "16:9"]
            target_ratio = aspect_ratio if aspect_ratio in valid_ratios else "1:1"

            logger.info(f"📡 [API REQUEST] 正在调用 Google Imagen 3 模型 [{model_name}] 比例 [{target_ratio}]...")
            api_start = time.time()
            response = client.models.generate_images(
                model=model_name,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio=target_ratio,
                    person_generation="allow_adult",
                    output_mime_type="image/jpeg",
                ),
            )
            api_elapsed = time.time() - api_start
            logger.info(f"📥 [API RESPONSE] Imagen 3 接口返回 (耗时: {api_elapsed:.2f}s)")

            if not response.generated_images:
                raise RuntimeError("Imagen 3 未能生成任何图片，可能触发了内容安全过滤或配额限制。")

            image_bytes = response.generated_images[0].image.image_bytes
            disk_start = time.time()
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            disk_elapsed = time.time() - disk_start
            total_elapsed = time.time() - total_start_time
            logger.info(
                f"💾 [FILE SAVED] 图片落盘成功: {file_path} ({len(image_bytes)/1024:.1f} KB, 写盘耗时: {disk_elapsed:.3f}s, 生图总耗时: {total_elapsed:.2f}s)"
            )

            return file_path

        except Exception as e:
            raise RuntimeError(f"调用 Google Imagen 3 生成图片失败: {str(e)}")

    elif provider in ["openai", "custom_openai", "ollama"]:
        prov_cfg = (config or {}).get(provider, {})
        fallback_openai_cfg = (config or {}).get("openai", {})

        if provider == "custom_openai":
            api_key = (
                prov_cfg.get("api_key")
                or fallback_openai_cfg.get("api_key")
                or os.environ.get("CUSTOM_OPENAI_API_KEY")
                or os.environ.get("OPENAI_API_KEY")
            )
            base_url = (
                prov_cfg.get("base_url")
                or fallback_openai_cfg.get("base_url")
                or os.environ.get("CUSTOM_OPENAI_BASE_URL")
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1"
            )
            model_name = (
                prov_cfg.get("image_model")
                or fallback_openai_cfg.get("image_model")
                or "dall-e-3"
            )
        elif provider == "ollama":
            api_key = prov_cfg.get("api_key") or "ollama"
            base_url = prov_cfg.get("base_url") or "http://localhost:11434/v1"
            model_name = prov_cfg.get("image_model") or "dall-e-3"
        else:  # "openai"
            api_key = prov_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
            base_url = (
                prov_cfg.get("base_url")
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1"
            )
            model_name = prov_cfg.get("image_model") or "dall-e-3"

        if provider != "ollama" and not api_key:
            raise ValueError(f"未检测到 {provider} API Key，请在模型设置中配置或设置对应环境变量！")

        # DALL-E 3 尺寸规范: 1024x1024, 1024x1792, 1792x1024
        size = "1024x1024"
        if aspect_ratio in ["9:16", "3:4"]:
            size = "1024x1792"
        elif aspect_ratio in ["16:9", "4:3"]:
            size = "1792x1024"

        try:
            from openai import OpenAI

            # 严密配置 60.0s 超时熔断，杜绝代理挂起无响应
            timeout_val = float(prov_cfg.get("timeout") or 60.0)
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_val)

            logger.info(
                f"📡 [API REQUEST] 正在调用 {provider} 端点 ({base_url}) | 模型: [{model_name}] | 尺寸: [{size}] | 超时: {timeout_val}s..."
            )
            api_start = time.time()
            image_bytes: Optional[bytes] = None
            last_call_error: Optional[Exception] = None

            # 策略 1: 优先尝试 b64_json 模式
            try:
                response = client.images.generate(
                    model=model_name,
                    prompt=prompt,
                    size=size,
                    quality="standard",
                    n=1,
                    response_format="b64_json",
                )
                if response and response.data:
                    img_data = response.data[0]
                    if hasattr(img_data, "b64_json") and img_data.b64_json:
                        image_bytes = base64.b64decode(img_data.b64_json)
                    elif hasattr(img_data, "url") and img_data.url:
                        dl_start = time.time()
                        resp = requests.get(img_data.url, timeout=30)
                        if resp.status_code == 200:
                            image_bytes = resp.content
                            logger.info(f"📥 [IMAGE DOWNLOAD] 异步下载图片成功 (耗时: {time.time()-dl_start:.2f}s)")
            except Exception as e:
                last_call_error = e
                logger.warn(f"⚠️ [API WARN] {provider} b64_json 模式报错，准备回退: {str(e)}")

            # 策略 2: 自适应降级回退（很多第三方中继代理不支持 response_format="b64_json"，回退为默认 URL 模式）
            if not image_bytes:
                try:
                    logger.info(f"🔄 [API FALLBACK] 正在使用标准 URL 模式请求中继生图接口...")
                    fallback_response = client.images.generate(
                        model=model_name,
                        prompt=prompt,
                        size=size,
                        n=1,
                    )
                    if fallback_response and fallback_response.data:
                        img_data = fallback_response.data[0]
                        if hasattr(img_data, "url") and img_data.url:
                            dl_start = time.time()
                            resp = requests.get(img_data.url, timeout=30)
                            if resp.status_code == 200:
                                image_bytes = resp.content
                                logger.info(f"📥 [IMAGE DOWNLOAD] 异步回退下载图片成功 (耗时: {time.time()-dl_start:.2f}s)")
                        elif hasattr(img_data, "b64_json") and img_data.b64_json:
                            image_bytes = base64.b64decode(img_data.b64_json)
                except Exception as e_fallback:
                    last_call_error = e_fallback

            api_elapsed = time.time() - api_start
            if not image_bytes:
                logger.error(f"❌ [API ERR] {provider} 生图失败 (耗时: {api_elapsed:.2f}s): {last_call_error}")
                formatted_msg = _format_image_generation_error(
                    last_call_error or RuntimeError("上游返回图片数据为空"),
                    provider,
                    model_name,
                    base_url,
                )
                raise RuntimeError(formatted_msg)

            logger.info(
                f"📥 [API SUCCESS] {provider} 生成图片数据成功 (耗时: {api_elapsed:.2f}s, 大小: {len(image_bytes)/1024:.1f} KB)"
            )

            disk_start = time.time()
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            disk_elapsed = time.time() - disk_start
            total_elapsed = time.time() - total_start_time
            logger.info(
                f"💾 [FILE SAVED] 本地落盘成功: {file_path} (写盘耗时: {disk_elapsed:.3f}s, 生图总耗时: {total_elapsed:.2f}s)"
            )

            return file_path

        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            formatted_msg = _format_image_generation_error(e, provider, model_name, base_url)
            raise RuntimeError(formatted_msg)

    else:
        raise ValueError(
            f"不支持的生图 Provider: {provider}。目前支持 'gemini', 'openai', 'custom_openai', 'ollama'。"
        )


def generate_ecommerce_images_batch(
    items: List[Dict[str, str]],
    provider: str = "gemini",
    config: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
    aspect_ratio: str = "1:1",
    max_workers: int = 1,
) -> List[Dict[str, Any]]:
    """
    批量并发生成电商营销图片（默认强制串行 max_workers=1 以规避代理限流与频控）
    - 使用 ThreadPoolExecutor 并发调用，加速多张图片生成
    - 严格支持中文 Prompt，自动保存到 output_dir
    - 容错设计：单个任务失败不影响其余任务，返回清晰的状态和错误日志

    :param items: 待生成的图片配置列表，每项形如 {"id": "...", "name": "...", "prompt": "...", "desc": "..."}
    :param provider: 'gemini' 或 'openai'
    :param config: 全局配置字典
    :param output_dir: 保存目录，默认为 ecommerce_studio/output
    :param aspect_ratio: 画幅比例
    :param max_workers: 最大并发线程数，默认 3
    :return: 包含每张图状态与路径的结构化列表
    """
    if not items:
        return []

    if output_dir is None:
        base_dir = Path(__file__).resolve().parent.parent
        output_dir = str(base_dir / "output")
    os.makedirs(output_dir, exist_ok=True)

    results: List[Dict[str, Any]] = [{} for _ in items]

    def _worker(idx: int, item: Dict[str, str]) -> Dict[str, Any]:
        item_id = item.get("id", f"item_{idx+1}")
        name = item.get("name", f"电商图_{idx+1}")
        desc = item.get("desc", "")
        prompt = (item.get("prompt") or "").strip()

        item_result = {
            "id": item_id,
            "name": name,
            "desc": desc,
            "prompt": prompt,
            "image_path": None,
            "status": "pending",
            "error": None,
        }

        if not prompt:
            item_result["status"] = "failed"
            item_result["error"] = "生图提示词为空，无法生成。"
            return item_result

        try:
            prefix = f"{item_id}_{idx+1}"
            img_path = generate_ecommerce_image(
                prompt=prompt,
                provider=provider,
                config=config,
                output_dir=output_dir,
                aspect_ratio=aspect_ratio,
                filename_prefix=prefix,
            )
            item_result["image_path"] = img_path
            item_result["status"] = "success"
        except Exception as e:
            item_result["status"] = "failed"
            item_result["error"] = str(e)

        return item_result

    # 限制并发数在合理范围内 (1 ~ 8)
    safe_workers = max(1, min(max_workers, 8, len(items)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=safe_workers) as executor:
        future_to_idx = {
            executor.submit(_worker, idx, item): idx
            for idx, item in enumerate(items)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                res = future.result()
                results[idx] = res
            except Exception as e:
                item = items[idx]
                results[idx] = {
                    "id": item.get("id", f"item_{idx+1}"),
                    "name": item.get("name", f"电商图_{idx+1}"),
                    "desc": item.get("desc", ""),
                    "prompt": item.get("prompt", ""),
                    "image_path": None,
                    "status": "failed",
                    "error": f"线程执行异常: {str(e)}",
                }

    return results
