import base64
import concurrent.futures
import io
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from PIL import Image

logger = logging.getLogger("ecommerce_studio.studio_crew")

from ecommerce_studio.tools.image_tool import (
    generate_ecommerce_image,
    generate_ecommerce_images_batch,
)
from ecommerce_studio.style_presets import get_style_preset
from ecommerce_studio.prompt_compiler import (
    PromptMatrixCompiler,
    PERSPECTIVE_DEFINITIONS,
    get_perspective_strategy_data,
    is_complex_mechanical_product,
    detect_product_vertical,
)

# 电商 9 大图视觉矩阵标准规范定义
ECOMMERCE_IMAGE_MATRIX_TEMPLATES: List[Dict[str, str]] = [
    {
        "id": "main_white_bg",
        "name": "商业高清白底首图",
        "desc": "纯净白底、商业摄影顶级棚拍布光、完整商品主体居中、通透倒影、极清工业细节，适用于电商检索与主图高点击转化",
    },
    {
        "id": "lifestyle_scene",
        "name": "真实生活使用场景图",
        "desc": "融入真实家居/办公/户外自然环境，柔和自然晨光侧射，营造优雅舒适的生活格调与真实使用代入感",
    },
    {
        "id": "core_feature",
        "name": "核心卖点与功能特写图",
        "desc": "中近景特写定焦于商品最具差异化的核心功能区域，配合专业轮廓光强化科技感与功能价值",
    },
    {
        "id": "material_detail",
        "name": "材质工艺与微距细节图",
        "desc": "极近微距摄影，浅景深虚化，极致凸显金属拉丝/磨砂亲肤/精工接缝等材质纹理与顶级工艺手感",
    },
    {
        "id": "pain_point_solution",
        "name": "痛点场景攻坚图",
        "desc": "直击买家最大抗拒痛点，高速快门多机位抓拍硬核实测瞬间，用不可辩驳的视觉证据打消下单顾虑",
    },
    {
        "id": "portable_commute",
        "name": "便携携带与通勤场景图",
        "desc": "与日常真实参照物或手部交互同框，直观展现真实人体工学比例与空间体量感知",
    },
    {
        "id": "structure_cutaway",
        "name": "结构卖点与内胆透视图",
        "desc": "科技感艺术分层拆解或半透视光效，根据商品物理属性清晰呈现核心材质用料、内部结构或工序工艺",
    },
    {
        "id": "unboxing_gift",
        "name": "包装礼盒与配件开箱图",
        "desc": "高档定制礼盒半开平铺陈列，商品主体、定制配件与说明书精致有序排布，拉满开箱仪式感与送礼体面感",
    },
    {
        "id": "model_interaction",
        "name": "真实模特生活方式交互图",
        "desc": "符合目标人群画像的年轻都市模特自然交互手持使用，真实微表情与场景氛围，传递品牌高阶情绪价值",
    },
]


MATRIX_JSON_SCHEMA_EXAMPLE = """```json
[
  {
    "id": "main_white_bg",
    "name": "商业高清白底首图",
    "desc": "纯净白底、商业摄影顶级棚拍布光、完整商品主体居中、通透倒影、极清工业细节",
    "prompt": "高端商业静物摄影，正视微俯角，主体为..."
  },
  {
    "id": "lifestyle_scene",
    "name": "真实生活使用场景图",
    "desc": "融入真实家居/办公/户外自然环境，柔和自然晨光侧射",
    "prompt": "真实生活方式摄影，中景构图..."
  },
  {
    "id": "core_feature",
    "name": "核心卖点与功能特写图",
    "desc": "中近景特写定焦于商品最具差异化的核心功能区域",
    "prompt": "商业产品功能特写摄影，近景定焦..."
  },
  {
    "id": "material_detail",
    "name": "材质工艺与微距细节图",
    "desc": "极近微距摄影，浅景深虚化，极致凸显材质纹理与顶级工艺手感",
    "prompt": "大师级商业微距摄影，极限超近景..."
  },
  {
    "id": "pain_point_solution",
    "name": "痛点场景攻坚图",
    "desc": "直击买家最大抗拒痛点，高速快门动感抓拍硬核实测瞬间",
    "prompt": "商业硬核功能测试场景摄影，针对买家痛点..."
  },
  {
    "id": "portable_commute",
    "name": "便携携带与通勤场景图",
    "desc": "与日常随身物品同框或手持随行，体现真实比例与人体工学体量",
    "prompt": "都市生活实景摄影，手持轻巧收纳..."
  },
  {
    "id": "structure_cutaway",
    "name": "结构卖点与内胆透视图",
    "desc": "艺术分层拆解或透视光效，清晰呈现核心材质用料或内部精密结构",
    "prompt": "未来科技感艺术透视摄影，三维艺术半透视呈现..."
  },
  {
    "id": "unboxing_gift",
    "name": "包装礼盒与配件开箱图",
    "desc": "高档定制礼盒半开平铺陈列，商品主体与配件精致有序排布",
    "prompt": "顶级奢华礼盒开箱摄影，俯视45度角平铺拍摄..."
  },
  {
    "id": "model_interaction",
    "name": "真实模特生活方式交互图",
    "desc": "符合目标受众的高颜值模特优雅手持或使用商品，自然传递情绪价值",
    "prompt": "高端商业人像与产品互动摄影，年轻都市模特自然交互..."
  }
]
```"""


def _pil_to_base64_data_uri(image: Image.Image) -> str:
    """将 PIL Image 转为 Base64 data URI"""
    buffered = io.BytesIO()
    fmt = image.format or "JPEG"
    image.save(buffered, format=fmt)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    mime = "image/jpeg" if fmt.upper() in ["JPG", "JPEG"] else f"image/{fmt.lower()}"
    return f"data:{mime};base64,{img_str}"


def build_default_prompt_matrix(
    product_info: Dict[str, str],
    style_preset_id: Optional[str] = "minimalist_muji",
) -> List[Dict[str, str]]:
    """
    根据商品信息与选定爆款风格流派，智能生成高质量商业摄影级 9 大图全套中文提示词（内置高质量防漂移模板）
    """
    style = get_style_preset(style_preset_id)
    name = product_info.get("name") or product_info.get("product_name") or "高端电商产品"
    category = product_info.get("category", "数码科技/生活良品")
    audience = product_info.get("target_audience") or product_info.get("target_users", "追求品质生活的消费者")
    pain_points = product_info.get("pain_points", "密封耐用与做工细节")
    material = product_info.get("material_features", "高精密工业材质与精湛表面工艺")

    # 视角模板 ID 到规范 ID 的映射
    tpl_to_canon = {
        "main_white_bg": "01_white_bg",
        "lifestyle_scene": "02_scene",
        "core_feature": "07_emotional",
        "material_detail": "03_detail",
        "pain_point_solution": "05_pain_killer",
        "portable_commute": "06_size",
        "structure_cutaway": "04_structure",
        "unboxing_gift": "08_color",
        "model_interaction": "09_buyer_show",
    }

    negative_rules = "，".join(style.anti_drift_rules)

    prompts_map = {}
    is_complex = is_complex_mechanical_product(name, category, material)
    for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES:
        t_id = tpl["id"]
        c_id = tpl_to_canon.get(t_id, t_id)
        enhancement = style.perspective_enhancements.get(c_id) or style.perspective_enhancements.get(t_id, "")

        tpl_desc = tpl["desc"]
        if t_id == "structure_cutaway" and not is_complex:
            tpl_desc = "核心材质用料与耐用抗拉扯/抗磨损分层工序工艺解析图，微距透视呈现扎实用料与工序细节"

        base = (
            f"【商业广告摄影】{tpl['name']}。主体为一款极具现代设计感的{name}（属于{category}品类）。"
            f"【工业与材质特征】：{material}。"
            f"【构图与视角】：{tpl_desc}，{style.camera}。"
            f"【商业布光与光影】：{style.lighting}。"
            f"【空间与道具布景】：{style.environment}。"
            f"【色彩与调性风格】：{style.color_tone}。"
        )

        if enhancement:
            base += f"【流派专属强化】：{enhancement}。"

        if t_id == "pain_point_solution":
            base += f"【痛点攻坚场景】：针对买家核心顾虑（{pain_points}），多机位动感抓拍具象化消除顾虑，极具视觉冲击力与可靠信赖感。"
        elif t_id in ("lifestyle_scene", "model_interaction", "portable_commute"):
            base += f"【目标客群代入】：生动融入符合（{audience}）生活品位的高阶氛围中。"

        base += f"【画质与防漂移规范】：8k超清分辨率，锐利对焦，真实质感，严禁出现：{negative_rules}。"
        prompts_map[t_id] = base

    results = []
    for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES:
        t_id = tpl["id"]
        c_id = tpl_to_canon.get(t_id, t_id)
        strat = get_perspective_strategy_data(c_id, product_info, style_preset_id=style_preset_id)
        p_val = prompts_map.get(t_id, f"商业级电商摄影，{name}，高质感细节，8k画质。")
        results.append({
            "id": t_id,
            "alt_id": c_id,
            "name": tpl["name"],
            "desc": tpl["desc"],
            "scene_highlight": strat["scene_highlight"],
            "commercial_strategy": strat["commercial_strategy"],
            "quick_tweaks": strat["quick_tweaks"],
            "quick_tweak_pills": strat["quick_tweak_pills"],
            "prompt": p_val,
            "prompt_zh": p_val,
        })
    return results


def parse_prompt_matrix_from_text(
    text: str,
    product_info: Optional[Dict[str, str]] = None,
    style_preset_id: Optional[str] = "minimalist_muji",
) -> List[Dict[str, Any]]:
    """
    从大模型生成的策划案文本中智能提取 9 大图全套中文提示词矩阵。
    如果模型未完全遵循 JSON 或有缺失项，使用商品信息与模板智能补齐，确保 100% 返回 9 组规范数据。
    """
    defaults = build_default_prompt_matrix(product_info or {}, style_preset_id=style_preset_id)
    default_dict = {item["id"]: item for item in defaults}

    parsed_items: Dict[str, Dict[str, Any]] = {}

    # 1. 尝试寻找 ```json ... ``` 代码块中的数组
    json_blocks = re.findall(r"```(?:json)?\s*(\[\s*\{[\s\S]*?\}\s*\])\s*```", text, re.IGNORECASE)
    for block in json_blocks:
        try:
            data = json.loads(block)
            if isinstance(data, list):
                for elem in data:
                    if isinstance(elem, dict):
                        e_id = elem.get("id", "").strip()
                        e_name = elem.get("name", "").strip()
                        e_prompt = elem.get("prompt", "").strip()
                        e_desc = elem.get("desc", "").strip()

                        # 映射 id
                        target_id = None
                        if e_id in default_dict:
                            target_id = e_id
                        else:
                            for def_id, def_val in default_dict.items():
                                if def_val["name"] in e_name or e_name in def_val["name"]:
                                    target_id = def_id
                                    break

                        if target_id and e_prompt and len(e_prompt) >= 15:
                            def_item = default_dict[target_id]
                            e_hl = elem.get("scene_highlight", "").strip() or def_item.get("scene_highlight", "")
                            e_comm = elem.get("commercial_strategy", "").strip() or def_item.get("commercial_strategy", "")
                            e_qt = elem.get("quick_tweaks") or def_item.get("quick_tweaks", [])
                            e_qtp = elem.get("quick_tweak_pills") or def_item.get("quick_tweak_pills", [])
                            parsed_items[target_id] = {
                                "id": target_id,
                                "alt_id": def_item.get("alt_id"),
                                "name": def_item["name"],
                                "desc": e_desc or def_item["desc"],
                                "scene_highlight": e_hl,
                                "commercial_strategy": e_comm,
                                "quick_tweaks": e_qt,
                                "quick_tweak_pills": e_qtp,
                                "prompt": e_prompt,
                                "prompt_zh": e_prompt,
                            }
        except Exception:
            continue

    # 2. 如果 JSON 未完全匹配出 9 项，尝试正则提取各个分类名称及紧随的中文提示词
    if len(parsed_items) < len(ECOMMERCE_IMAGE_MATRIX_TEMPLATES):
        for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES:
            t_id = tpl["id"]
            if t_id in parsed_items:
                continue

            name = tpl["name"]
            pattern = (
                rf"(?:(?:#|\*|\d+[\.\、\s]*)*{re.escape(name)}[\s\S]*?)"
                rf"(?:提示词|Prompt|生图描述)[\s:：]*([^\n]+(?:\n(?!(?:#|\d+[\.\、]|【|\[))[^\n]+){{0,4}})"
            )
            match = re.search(pattern, text)
            if match:
                cand = match.group(1).strip()
                cand = re.sub(r"^[`*\"']+|[`*\"']+$", "", cand).strip()
                if len(cand) >= 20:
                    def_item = default_dict[t_id]
                    parsed_items[t_id] = {
                        "id": t_id,
                        "alt_id": def_item.get("alt_id"),
                        "name": name,
                        "desc": tpl["desc"],
                        "scene_highlight": def_item.get("scene_highlight", ""),
                        "commercial_strategy": def_item.get("commercial_strategy", ""),
                        "quick_tweaks": def_item.get("quick_tweaks", []),
                        "quick_tweak_pills": def_item.get("quick_tweak_pills", []),
                        "prompt": cand,
                        "prompt_zh": cand,
                    }

    # 3. 组合并按标准顺序输出 9 大图，缺失项用高质量默认模板补齐
    final_matrix: List[Dict[str, Any]] = []
    for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES:
        t_id = tpl["id"]
        if t_id in parsed_items and parsed_items[t_id].get("prompt"):
            final_matrix.append(parsed_items[t_id])
        else:
            final_matrix.append(default_dict[t_id])

    return final_matrix


def extract_prompt_from_plan(text: str) -> str:
    """向后兼容接口：从策划文本中提取首图或核心生图中文提示词"""
    matrix = parse_prompt_matrix_from_text(text)
    if matrix and matrix[0].get("prompt"):
        return matrix[0]["prompt"]
    return "商业级高清电商静物摄影，现代科技与生活质感，顶级棚拍柔光，超清细节，8k画质。"


def refine_prompt_with_ai(
    original_prompt: str,
    user_feedback: str,
    config: Dict[str, Any],
    image_type_name: str = "",
) -> str:
    """
    接收用户针对某张图片的修改要求（如“把背景改成晚霞黄昏”、“杯盖加上冷光数显特效”），
    结合原中文 Prompt 与修改意见，调用 Gemini / OpenAI 生成优化后的新版中文 Prompt。

    :param original_prompt: 原始中文提示词
    :param user_feedback: 用户提出的调整修改意见
    :param config: 全局配置字典
    :param image_type_name: 当前图片类型名称（如“商业高清白底首图”、“痛点场景攻坚图”）
    :return: 优化后的高质量中文商业生图 Prompt
    """
    t0 = time.time()
    if not user_feedback or not user_feedback.strip():
        return original_prompt

    logger.info(f"🎨 [refine_prompt_with_ai Start] type='{image_type_name}', feedback='{user_feedback[:50]}'")

    type_info = f"当前图片类别：【{image_type_name}】\n" if image_type_name else ""

    system_instruction = """你是一位顶尖电商商业视觉摄影总监兼 AI 生图提示词大师（精通 Imagen 3 与商业电商视觉工程）。
你的核心任务是：根据用户的修改意见，对原有的【中文商业生图提示词】进行二次精准迭代与润色。

【执行标准】：
1. 语言：必须输出 100% 高质量中文商业摄影提示词。
2. 传承性：必须保留原提示词中的商品核心主体特征、材质细节与商业级画质要求（如 8k、棚拍布光、质感光影等）。
3. 精准融入：将用户的具体微调诉求（如背景环境变更、光影氛围调整、特效增加、构图改变、细节增删等）无缝且自然地融合成一段完整的商业摄影指令。
4. 输出格式：直接输出润色后的纯文本提示词，严禁输出任何解释、客套话、引号或 Markdown 代码块！"""

    user_query = f"""{type_info}
【原始中文提示词】：
{original_prompt}

【用户微调修改意见】：
{user_feedback}

请输出润色优化后的全新中文商业生图提示词："""

    provider = config.get("active_provider", "gemini").lower()

    # 智能通道探测与故障自愈：若当前激活服务商未配置 Key，自动回退至其他已配置密钥的可用通道
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

    if not cand_key:
        for fallback_p in ["openai", "custom_openai", "gemini"]:
            fb_cfg = config.get(fallback_p, {})
            fb_key = (
                fb_cfg.get("api_key")
                or os.environ.get(f"{fallback_p.upper()}_API_KEY")
                or (os.environ.get("OPENAI_API_KEY") if fallback_p in ["openai", "custom_openai"] else None)
            )
            if fb_key:
                provider = fallback_p
                break

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
            response = client.models.generate_content(
                model=model_name,
                contents=[user_query],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.6,
                ),
            )
            result = (response.text or "").strip()
            # 移除可能的多余包裹
            result = re.sub(r"^```(?:text|markdown)?\s*", "", result)
            result = re.sub(r"\s*```$", "", result).strip()
            elapsed = time.time() - t0
            logger.info(f"✨ [refine_prompt_with_ai Done] provider=gemini, elapsed={elapsed:.2f}s")
            return result or original_prompt

        except Exception as e:
            raise RuntimeError(f"Gemini 二次微调提示词失败: {str(e)}")

    elif provider in ["openai", "custom_openai"]:
        openai_cfg = config.get(provider, {})
        fallback_cfg = config.get("openai", {})
        api_key = (
            openai_cfg.get("api_key")
            or fallback_cfg.get("api_key")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("CUSTOM_OPENAI_API_KEY")
        )
        base_url = (
            openai_cfg.get("base_url")
            or fallback_cfg.get("base_url")
            or os.environ.get("OPENAI_BASE_URL")
            or os.environ.get("CUSTOM_OPENAI_BASE_URL")
            or "https://api.openai.com/v1"
        )

        if not api_key:
            raise ValueError(f"请先在配置中填写 {provider} API Key！")

        model_name = openai_cfg.get("model") or fallback_cfg.get("model") or "gpt-4o"
        timeout_val = float(openai_cfg.get("timeout") or 30.0)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_val)

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_query},
                ],
                temperature=0.6,
            )
            result = (response.choices[0].message.content or "").strip()
            result = re.sub(r"^```(?:text|markdown)?\s*", "", result)
            result = re.sub(r"\s*```$", "", result).strip()
            elapsed = time.time() - t0
            logger.info(f"✨ [refine_prompt_with_ai Done] provider={provider}, elapsed={elapsed:.2f}s")
            return result or original_prompt

        except Exception as e:
            raise RuntimeError(f"{provider} 二次微调提示词失败: {str(e)}")

    else:
        raise ValueError(f"不支持的 Provider: {provider}")


def generate_vision_matrix_with_ai(
    product_info: Dict[str, Any],
    style_preset_id: Optional[str] = "minimalist_muji",
    config: Optional[Dict[str, Any]] = None,
    force_fallback: bool = False,
    timeout: float = 25.0,
) -> List[Dict[str, Any]]:
    """
    由大模型（Gemini / OpenAI）扮演享誉国际的资深商业广告摄影总监，
    根据商品档案（品类、材质、痛点、客群）与视觉流派，全自主推理生成 9 大黄金商业视角矩阵。

    双引擎容灾：
    - 主推：大模型自主结构化推理（全品类适应度，杜绝死板模板冲突）
    - 保底：若未配置 API Key、超时(>25s)或解析异常，平稳回退至 PromptMatrixCompiler
    """
    t0 = time.time()
    preset = get_style_preset(style_preset_id)
    prod_name = product_info.get("name") or product_info.get("product_name") or "高端电商产品"
    category = product_info.get("category", "通用电商产品")
    material = product_info.get("material_features", "高品质精工材质")
    audience = product_info.get("target_audience") or product_info.get("target_users", "追求生活品质的消费者")
    pain_points = product_info.get("pain_points", "做工、实用性与耐用细节")

    if force_fallback:
        logger.info(f"🔄 [AI Vision Director] 强制触发引擎 B (规则装配引擎兜底)")
        return PromptMatrixCompiler.compile_matrix(product_info, style_preset_id=style_preset_id)

    if config is None:
        try:
            from ecommerce_studio.config_manager import load_config
            config = load_config()
        except Exception:
            config = {}

    provider = config.get("active_provider", "gemini").lower()

    # 探测可用 provider 与 api_key
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

    if not cand_key:
        for fallback_p in ["gemini", "openai", "custom_openai"]:
            fb_cfg = config.get(fallback_p, {})
            fb_key = (
                fb_cfg.get("api_key")
                or os.environ.get(f"{fallback_p.upper()}_API_KEY")
                or (os.environ.get("OPENAI_API_KEY") if fallback_p in ["openai", "custom_openai"] else None)
            )
            if fb_key:
                provider = fallback_p
                cand_key = fb_key
                break

    if not cand_key:
        logger.info(f"⚡ [AI Vision Director] 未检测到任何可用 API Key，0秒熔断平稳回退至本地编译引擎")
        return PromptMatrixCompiler.compile_matrix(product_info, style_preset_id=style_preset_id)

    # 构造专业摄影总监 Prompt，严格执行 3W1H 物理具象化法则
    system_instruction = f"""你是享誉国际的资深商业广告摄影总监与电商爆款视觉策划专家。
你的任务是根据传入的待策划商品【{prod_name}】的真实档案（品类、材质、买家核心抗拒点）与指定的视觉美学流派，为电商 9 大黄金商业视角矩阵量身导演 9 个【完全独立、场景各异、绝不雷同】的顶级商业摄影方案。

【核心铁律：3W1H 物理场景具象化法则】（每个视角的 scene_highlight 必须严格遵守，绝对围绕【{prod_name}】真实物理形态）：
1. What Component (聚焦真实物理构件/用料细节)：必须指明聚焦于【{prod_name}】本身的真实物理结构、材质表面、接缝工艺或受力部位（如外层材质肌理、握持手柄防滑纹路、精密衔接处、柔性受力韧性节点等），严禁脱离商品本身的物理常识，严禁泛泛说“展现商品”；
2. Where Environment (专属生活场域与质感软装)：必须根据【{prod_name}】真实使用场域推导自然合规空间（如日常家居客厅木地板、洗漱台大理石台面、专业办公书桌、户外草地等），场景光影自然协调，严禁空间错配；
3. What Action/Evidence (真实交互动线与极限实测证言)：必须呈现使用者/爱宠与【{prod_name}】的真实物理交互或核心买家痛点的实测瞬间（如手部舒适握持、动态互动抓拍、耐磨抗拉扯实测、密闭防漏测试等），形成无可辩驳的视觉证据；
4. How Visual (专业摄影镜头焦段与光感大白话)：用大白话通俗讲清摄影机位、焦段与光感（如“85mm微距浅景深虚化背景”、“高速快门定格动态瞬间”、“晨光透过纱帘洒下斑驳光影”）。

【最高红线警示（违者方案作废）】：
1. 绝对严禁单品形态错配与偏见迁移：严禁将某一具体商品特征（例如将宠物用品统统套写为猫砂盆/猫砂/滤踏板/除臭滤芯，将美妆统统套写为滴管精华/50张吸油纸，将数码统统套写为耳机/声学腔体，将服饰统统套写为高压水枪喷淋等）强加到不相干商品上！所有构思必须 100% 紧扣当前传入的待策划商品【{prod_name}】。
2. 物理形态自适应（04_structure 视角红线）：对于非复杂组装/非精密机械的商品（如逗猫棒、羽绒服、餐盘、玩具、日常百货等），04_structure 严禁凭空捏造复杂的机械零件/芯片/齿轮轴向爆炸图，必须自适应生成“核心材质用料与耐用抗拉扯/抗磨损分层工序工艺解析图”；仅对复杂机械/数码/智能家电等具备内部机电组装的商品，才生成精密组件结构悬浮爆炸图。
3. 严禁使用死板模板拼接！每一张图的场景、机位焦段、光影与道具必须根据【{prod_name}】全自主构想。
4. 必须深度融入选定流派【{preset.name}】的色彩、质感与防漂移规范（严禁出现：{', '.join(preset.anti_drift_rules)}）。
5. 负向套话黑名单：严禁出现“极具现代感”、“尽显高端品质”、“彰显生活品位”、“展现独特魅力”、“精工细作打造”、“高品质呈现”、“科技感十足”等无意义空话。
6. 所有提示词必须 100% 使用高质量中文商业摄影语言。
7. 严格输出标准 JSON 数组，包含且仅包含 9 个视角的 JSON 对象。格式如下：
```json
[
  {{
    "id": "01_white_bg",
    "name": "商业纯净白底首图",
    "scene_highlight": "大白话画面构想（20~40字，严格按 3W1H 描写，严禁空话）",
    "commercial_strategy": "商业心智转化策略（阐述如何击穿买家心理）",
    "prompt": "高质量独立中文商业生图提示词",
    "quick_tweaks": [
      {{"id": "tweak_1", "label": "💡 调亮无影顶光", "tweakText": "调亮无影棚顶光与双侧柔光箱，强化主体通透洁净感"}},
      {{"id": "tweak_2", "label": "🪞 加镜面通透倒影", "tweakText": "展台表层增加极浅镜面接触微倒影，凸显高级通透倒影质感"}},
      {{"id": "tweak_3", "label": "✨ 强化边缘轮廓光", "tweakText": "边缘轮廓增加精致微光勾边，拉开主体与纯白背景的反差"}}
    ]
  }},
  ...
]
```"""

    user_query = f"""【待策划商品档案】：
- 商品名称：{prod_name}
- 品类属性：{category}
- 核心材质与做工：{material}
- 目标消费客群：{audience}
- 核心买家顾虑/痛点：{pain_points}
- 选定视觉美学流派：{preset.name} ({preset.en_name})
  * 风格定位：{preset.tagline}
  * 光影方案：{preset.lighting}
  * 空间布景：{preset.environment}
  * 镜头机位：{preset.camera}
  * 调性色彩：{preset.color_tone}
  * 防漂移规则：{", ".join(preset.anti_drift_rules)}

请根据上述商品档案与流派，作为商业摄影总监全自主推理生成 9 大黄金商业视角的结构化 JSON 方案："""

    def _call_model() -> str:
        if provider == "gemini":
            from google import genai
            from google.genai import types
            gemini_cfg = config.get("gemini", {})
            model_name = gemini_cfg.get("model") or "gemini-2.0-flash"
            client = genai.Client(api_key=cand_key)
            resp = client.models.generate_content(
                model=model_name,
                contents=[user_query],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
            return resp.text or ""
        else:
            from openai import OpenAI
            p_cfg = config.get(provider, {})
            fallback_cfg = config.get("openai", {})
            base_url = (
                p_cfg.get("base_url")
                or fallback_cfg.get("base_url")
                or os.environ.get(f"{provider.upper()}_BASE_URL")
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1"
            )
            model_name = p_cfg.get("model") or fallback_cfg.get("model") or "gpt-4o"
            client = OpenAI(api_key=cand_key, base_url=base_url, timeout=timeout, max_retries=0)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_query},
                ],
                temperature=0.7,
            )
            return resp.choices[0].message.content or ""

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_model)
            raw_text = future.result(timeout=timeout)

        # 提取并解析 JSON
        json_match = re.search(r"(\[\s*\{[\s\S]*\}\s*\])", raw_text)
        if not json_match:
            dict_match = re.search(r"(\{\s*\"perspectives\"[\s\S]*\}\s*)", raw_text)
            if dict_match:
                parsed_data = json.loads(dict_match.group(1)).get("perspectives", [])
            else:
                raise ValueError("未在模型输出中找到 JSON 数组")
        else:
            parsed_data = json.loads(json_match.group(1))

        if not isinstance(parsed_data, list) or len(parsed_data) == 0:
            raise ValueError("解析到的 JSON 并非有效数组")

        fallback_matrix = PromptMatrixCompiler.compile_matrix(product_info, style_preset_id=style_preset_id)
        fallback_map = {item["id"]: item for item in fallback_matrix}

        result_map: Dict[str, Dict[str, Any]] = {}
        for elem in parsed_data:
            if not isinstance(elem, dict):
                continue
            raw_id = (elem.get("id") or "").strip()
            matched_canon_id = None
            for p_def in PERSPECTIVE_DEFINITIONS:
                if p_def["id"] == raw_id or p_def["alt_id"] == raw_id:
                    matched_canon_id = p_def["id"]
                    break
            if not matched_canon_id:
                for p_def in PERSPECTIVE_DEFINITIONS:
                    if p_def["name"] in elem.get("name", "") or elem.get("name", "") in p_def["name"]:
                        matched_canon_id = p_def["id"]
                        break

            if matched_canon_id and matched_canon_id not in result_map:
                fb_item = fallback_map.get(matched_canon_id, {})
                prompt_val = elem.get("prompt") or elem.get("prompt_zh") or fb_item.get("prompt", "")
                raw_tweaks = elem.get("quick_tweaks")
                if not isinstance(raw_tweaks, list) or len(raw_tweaks) == 0:
                    raw_tweaks = fb_item.get("quick_tweaks", [])
                pills = [t.get("label", "") for t in raw_tweaks if isinstance(t, dict) and t.get("label")]
                if not pills:
                    pills = fb_item.get("quick_tweak_pills", [])

                result_map[matched_canon_id] = {
                    "id": matched_canon_id,
                    "alt_id": fb_item.get("alt_id"),
                    "name": elem.get("name") or fb_item.get("name"),
                    "desc": fb_item.get("desc", ""),
                    "tag": fb_item.get("tag", ""),
                    "category": fb_item.get("category", ""),
                    "scene_highlight": elem.get("scene_highlight") or fb_item.get("scene_highlight", ""),
                    "commercial_strategy": elem.get("commercial_strategy") or fb_item.get("commercial_strategy", ""),
                    "prompt": prompt_val,
                    "prompt_zh": prompt_val,
                    "quick_tweaks": raw_tweaks,
                    "quick_tweak_pills": pills,
                }

        final_list: List[Dict[str, Any]] = []
        for p_def in PERSPECTIVE_DEFINITIONS:
            pid = p_def["id"]
            if pid in result_map:
                final_list.append(result_map[pid])
            else:
                final_list.append(fallback_map[pid])

        elapsed = time.time() - t0
        logger.info(f"✨ [AI Vision Director Success] 成功全自主推理 9 大视角矩阵，耗时={elapsed:.2f}s, provider={provider}")
        return final_list

    except Exception as e:
        logger.warning(f"⚠️ [AI Vision Director Warning] 大模型推理异常或超时 ({e})，0秒熔断平稳回退至本地编译引擎")
        return PromptMatrixCompiler.compile_matrix(product_info, style_preset_id=style_preset_id)


def regenerate_single_perspective_with_ai(
    product_info: Dict[str, Any],
    perspective_id: str,
    style_preset_id: Optional[str] = "minimalist_muji",
    instruction: str = "",
    current_prompt: str = "",
    config: Optional[Dict[str, Any]] = None,
    timeout: float = 15.0,
) -> Dict[str, Any]:
    """
    单卡级 AI 视觉导演全自主重新构思与生成。
    用户可输入极简指示（如“换一个户外雪山背景”），AI 针对单个视角的场景、镜头逻辑与微调胶囊全自主重新推演。
    """
    t0 = time.time()
    matched_def = None
    clean_id = (perspective_id or "").strip()
    for p_def in PERSPECTIVE_DEFINITIONS:
        if p_def["id"] == clean_id or p_def["alt_id"] == clean_id:
            matched_def = p_def
            break
    if not matched_def:
        matched_def = PERSPECTIVE_DEFINITIONS[0]

    canon_id = matched_def["id"]
    preset = get_style_preset(style_preset_id)
    prod_name = product_info.get("name") or product_info.get("product_name") or "高端电商产品"
    category = product_info.get("category", "通用电商产品")
    material = product_info.get("material_features", "高品质精工材质")
    audience = product_info.get("target_audience") or product_info.get("target_users", "追求生活品质的消费者")
    pain_points = product_info.get("pain_points", "做工、实用性与耐用细节")

    strat_fallback = get_perspective_strategy_data(canon_id, product_info, style_preset_id=style_preset_id)

    if config is None:
        try:
            from ecommerce_studio.config_manager import load_config
            config = load_config()
        except Exception:
            config = {}

    provider = config.get("active_provider", "gemini").lower()
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

    if not cand_key:
        for fallback_p in ["gemini", "openai", "custom_openai"]:
            fb_cfg = config.get(fallback_p, {})
            fb_key = (
                fb_cfg.get("api_key")
                or os.environ.get(f"{fallback_p.upper()}_API_KEY")
                or (os.environ.get("OPENAI_API_KEY") if fallback_p in ["openai", "custom_openai"] else None)
            )
            if fb_key:
                provider = fallback_p
                cand_key = fb_key
                break

    if not cand_key:
        new_prompt = current_prompt or f"商业级电商摄影，{prod_name}，顶级棚拍光影，8k超清。"
        if instruction:
            new_prompt = f"{new_prompt}。微调指导：{instruction}。大师级商业棚拍质感，8k画质。"
        return {
            "id": canon_id,
            "alt_id": matched_def.get("alt_id"),
            "name": matched_def["name"],
            "desc": matched_def["desc"],
            "tag": matched_def.get("tag", ""),
            "category": matched_def.get("category", ""),
            "scene_highlight": strat_fallback["scene_highlight"],
            "commercial_strategy": strat_fallback["commercial_strategy"],
            "prompt": new_prompt,
            "prompt_zh": new_prompt,
            "quick_tweaks": strat_fallback["quick_tweaks"],
            "quick_tweak_pills": strat_fallback["quick_tweak_pills"],
        }

    system_instruction = f"""你是享誉国际的资深商业广告摄影总监与电商爆款视觉策划专家。
当前需要对待策划商品【{prod_name}】在电商 9 大图中的【{matched_def['name']}】（ID: {canon_id}）进行单卡级 AI 重新构思。
视角核心使命：{matched_def['desc']}
流派风格：{preset.name} ({preset.lighting}, {preset.environment})

【硬性要求与红线规范】：
1. 严禁单品偏见迁移：严禁将某一具体商品特征（如将宠物用品误写为猫砂盆/猫砂/滤踏板，将美妆误写为滴管精华）泛化套用到【{prod_name}】上，必须 100% 紧扣【{prod_name}】本身的物理属性与品类特性。
2. 3W1H 物理场景具象法则：scene_highlight 必须指明具体的构件部位、符合常识的使用场域、真实的交互动作/实测瞬间以及专业机位焦段光感，严禁空话套话。
3. 结构形态自适应：若当前为 04_structure 且商品属于非复杂机械装配（如逗猫棒、服装、玩具、百货等），必须聚焦核心用料、工艺节点与耐用防损分层解析，严禁捏造荒谬的机械零件爆炸图。
4. 语言：必须 100% 输出高质量中文商业摄影语言。
5. 结合用户的微调指示（如有）与商品档案，全自主构思全新的画面高光、商业转化心智、专业提示词以及 3~4 个微调胶囊。
6. 严格输出标准单个 JSON 对象：
```json
{{
  "id": "{canon_id}",
  "name": "{matched_def['name']}",
  "scene_highlight": "大白话画面构想（20~40字，符合 3W1H，严禁空话）",
  "commercial_strategy": "商业心智转化策略",
  "prompt": "高质量独立中文商业生图提示词",
  "quick_tweaks": [
    {{"id": "tweak_1", "label": "🏷️ 标签", "tweakText": "追加微调"}}
  ]
}}
```"""

    user_query = f"""【待重构商品档案】：
- 商品名称：{prod_name}
- 品类属性：{category}
- 核心材质与做工：{material}
- 核心买家顾虑/痛点：{pain_points}
- 当前指导词：{current_prompt}
- 用户重构指示：{instruction or "全自主重新构思此视角的创意画面与镜头光影"}

请输出单个 JSON 对象："""

    def _call_model() -> str:
        if provider == "gemini":
            from google import genai
            from google.genai import types
            gemini_cfg = config.get("gemini", {})
            model_name = gemini_cfg.get("model") or "gemini-2.0-flash"
            client = genai.Client(api_key=cand_key)
            resp = client.models.generate_content(
                model=model_name,
                contents=[user_query],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7,
                ),
            )
            return resp.text or ""
        else:
            from openai import OpenAI
            p_cfg = config.get(provider, {})
            fallback_cfg = config.get("openai", {})
            base_url = (
                p_cfg.get("base_url")
                or fallback_cfg.get("base_url")
                or os.environ.get(f"{provider.upper()}_BASE_URL")
                or os.environ.get("OPENAI_BASE_URL")
                or "https://api.openai.com/v1"
            )
            model_name = p_cfg.get("model") or fallback_cfg.get("model") or "gpt-4o"
            client = OpenAI(api_key=cand_key, base_url=base_url, timeout=timeout, max_retries=0)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_query},
                ],
                temperature=0.7,
            )
            return resp.choices[0].message.content or ""

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_model)
            raw_text = future.result(timeout=timeout)

        json_match = re.search(r"(\{\s*\"id\"[\s\S]*\}\s*)", raw_text)
        if not json_match:
            raise ValueError("未在单卡模型输出中找到 JSON 对象")
        elem = json.loads(json_match.group(1))

        prompt_val = elem.get("prompt") or elem.get("prompt_zh") or current_prompt
        raw_tweaks = elem.get("quick_tweaks")
        if not isinstance(raw_tweaks, list) or len(raw_tweaks) == 0:
            raw_tweaks = strat_fallback["quick_tweaks"]
        pills = [t.get("label", "") for t in raw_tweaks if isinstance(t, dict) and t.get("label")]
        if not pills:
            pills = strat_fallback["quick_tweak_pills"]

        return {
            "id": canon_id,
            "alt_id": matched_def.get("alt_id"),
            "name": elem.get("name") or matched_def["name"],
            "desc": matched_def["desc"],
            "tag": matched_def.get("tag", ""),
            "category": matched_def.get("category", ""),
            "scene_highlight": elem.get("scene_highlight") or strat_fallback["scene_highlight"],
            "commercial_strategy": elem.get("commercial_strategy") or strat_fallback["commercial_strategy"],
            "prompt": prompt_val,
            "prompt_zh": prompt_val,
            "quick_tweaks": raw_tweaks,
            "quick_tweak_pills": pills,
        }
    except Exception as e:
        logger.warning(f"⚠️ [Single Perspective Reimagining Fallback] 单卡AI重构降级: {e}")
        new_prompt = current_prompt or f"商业级电商摄影，{prod_name}，顶级棚拍光影，8k超清。"
        if instruction:
            new_prompt = f"{new_prompt}。微调指导：{instruction}。大师级商业棚拍质感，8k画质。"
        return {
            "id": canon_id,
            "alt_id": matched_def.get("alt_id"),
            "name": matched_def["name"],
            "desc": matched_def["desc"],
            "tag": matched_def.get("tag", ""),
            "category": matched_def.get("category", ""),
            "scene_highlight": strat_fallback["scene_highlight"],
            "commercial_strategy": strat_fallback["commercial_strategy"],
            "prompt": new_prompt,
            "prompt_zh": new_prompt,
            "quick_tweaks": strat_fallback["quick_tweaks"],
            "quick_tweak_pills": strat_fallback["quick_tweak_pills"],
        }


def run_phase_one(
    product_info: Dict[str, str],
    pil_images: List[Image.Image],
    config: Dict[str, Any],
    status_callback: Optional[Callable[[str], None]] = None,
    style_preset_id: Optional[str] = "minimalist_muji",
) -> Tuple[str, List[Dict[str, str]]]:
    """
    执行阶段一：多模态商品图理解 + 多智能体痛点挖掘与场景构思
    生成包含电商 9 大图视觉矩阵的高质量中文提示词方案

    :param product_info: 商品文字信息（商品名称、品类、目标群体、竞品短板）
    :param pil_images: 上传的实拍商品图 PIL 列表
    :param config: 系统配置字典
    :param status_callback: 状态日志回调函数
    :param style_preset_id: 爆款视觉风格流派ID
    :return: (结构化策划案全文, 结构化9组中文提示词列表)
    """
    def log(msg: str):
        if status_callback:
            status_callback(msg)

    t0 = time.time()
    logger.info(f"🚀 [run_phase_one Start] product='{product_info.get('name')}', images={len(pil_images)}, style='{style_preset_id}'")

    provider = config.get("active_provider", "gemini").lower()
    agents_cfg = config.get("agents", {})

    market_agent = agents_cfg.get("market_researcher", {})
    art_agent = agents_cfg.get("art_director", {})
    visual_agent = agents_cfg.get("visual_engineer", {})

    preset = get_style_preset(style_preset_id)

    product_name = product_info.get("name", "未命名商品")
    category = product_info.get("category", "通用电商产品")
    target_audience = product_info.get("target_audience", "大众消费者")
    pain_points_raw = product_info.get("pain_points", "无特定竞品短板")

    user_text_context = f"""
【商品名称】：{product_name}
【品类属性】：{category}
【目标消费群体】：{target_audience}
【已知竞品短板/买家顾虑】：{pain_points_raw}
【上传实物图数量】：{len(pil_images)} 张
【选定商业视觉流派】：{preset.name} ({preset.en_name})
- 流派定位：{preset.tagline}
- 核心布光方案：{preset.lighting}
- 空间布景与道具：{preset.environment}
- 镜头机位与焦段：{preset.camera}
- 色彩与质感基调：{preset.color_tone}
- 防漂移排除项：{", ".join(preset.anti_drift_rules)}
"""

    master_system_instruction = f"""你是由三位顶尖电商与视觉专家组成的多智能体协同智囊团：
1. **{market_agent.get('name', '商品洞察专家')}**：{market_agent.get('system_prompt', '')}
2. **{art_agent.get('name', '视觉创意总监')}**：{art_agent.get('system_prompt', '')}
3. **{visual_agent.get('name', 'AI 制图工程师')}**：{visual_agent.get('system_prompt', '')}

你的任务是：
仔细审视用户上传的 {len(pil_images)} 张商品实拍图与文字信息，深入洞察实物工业材质、结构与消费痛点，输出专业营销策划案及电商运营必备的【9 大图视觉中文生图提示词矩阵】。

【极其重要的硬性要求】：
1. **所有生图提示词必须 100% 全部使用高质量中文提示词**，严禁使用英文提示词！
2. 每个提示词必须具备商业广告摄影级水准，详细包含：商品主体特征、材质质感（如磨砂/拉丝/透明/高光）、背景生活/棚拍环境、构图与机位视角、专业光影布光参数、景深与情绪氛围。
3. 必须深度融入选定的商业视觉流派【{preset.name}】的光影、布景、镜头与色彩规范，并在提示词末尾强制加入防漂移画质锁（严禁出现：{", ".join(preset.anti_drift_rules)}）。
4. 必须在方案第 3 模块中，按照以下标准 JSON 数组代码块格式，完整输出指定 9 类电商核心图片的中文生图提示词矩阵：

{MATRIX_JSON_SCHEMA_EXAMPLE}

严格按照以下结构化 Markdown 输出完整方案：
# 📦 电商营销策划与 9 大图视觉矩阵方案

### 1. 🔍 实物视觉特征与买家痛点深度剖析 (由 {market_agent.get('name', '商品洞察专家')} 输出)
- **实物外观及材质还原**：（精准识别实拍图中的轮廓配色、材质光泽与物理细节）
- **买家抗拒点与消费心理**：（深度剖析痛点）
- **第一杀手级卖点 (USP)**：（提炼一句最能消除顾虑的核心卖点）

### 2. 🎬 视觉场景推演与故事线 (由 {art_agent.get('name', '视觉创意总监')} 输出)
- **具象使用生活场景**：（描述具体生活/工作场景，拒绝虚无背景）
- **构图与光影基调**：（指定视角机位与商业光影基调）
- **核心营销文案标语**：（1~2句高转化率中文主副标语）

### 3. 🎨 电商 9 大图视觉提示词矩阵 (中文商业级摄影描述，由 {visual_agent.get('name', 'AI 制图工程师')} 输出)
（必须在此插入上述完整的 9 组中文生图提示词 JSON 代码块，并在后文对 9 张图的视觉构思进行分项解析说明）
"""

    log("🔍 多模态大脑正在审视商品细节并启动 Agent 深度推理...")

    if provider == "gemini":
        gemini_cfg = config.get("gemini", {})
        api_key = gemini_cfg.get("api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("请先在侧边栏配置 Gemini API Key！")

        model_name = gemini_cfg.get("model") or "gemini-2.0-flash"

        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            contents = [
                master_system_instruction,
                f"这是当前待分析的商品信息：\n{user_text_context}\n请结合上传的实拍图，生成完整策划案及 9 大图全套中文生图提示词矩阵：",
            ]
            contents.extend(pil_images)

            log(f"🧠 调用 Gemini 模型 ({model_name}) 进行多模态图文解析与 9 大图矩阵构建...")
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
            )
            analysis_text = response.text or ""

        except Exception as e:
            raise RuntimeError(f"Gemini 多模态策划失败: {str(e)}")

    elif provider == "openai":
        openai_cfg = config.get("openai", {})
        api_key = openai_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
        base_url = openai_cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"

        if not api_key:
            raise ValueError("请先在侧边栏配置 OpenAI API Key！")

        model_name = openai_cfg.get("model") or "gpt-4o"

        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)

            content_blocks = [
                {"type": "text", "text": f"{master_system_instruction}\n\n待分析商品：\n{user_text_context}"}
            ]
            for img in pil_images:
                data_uri = _pil_to_base64_data_uri(img)
                content_blocks.append({
                    "type": "image_url",
                    "image_url": {"url": data_uri, "detail": "high"}
                })

            log(f"🧠 调用 OpenAI 模型 ({model_name}) 进行多模态图文解析与 9 大图矩阵构建...")
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": content_blocks}
                ],
                temperature=0.7,
            )
            analysis_text = response.choices[0].message.content or ""

        except Exception as e:
            raise RuntimeError(f"OpenAI 多模态策划失败: {str(e)}")

    else:
        raise ValueError(f"未知的 Provider: {provider}")

    log("✨ 策划案生成完成，正在智能提取与校验 9 大图中文提示词矩阵...")
    prompts_matrix = parse_prompt_matrix_from_text(analysis_text, product_info, style_preset_id=style_preset_id)
    elapsed = time.time() - t0
    logger.info(f"✅ [run_phase_one Done] matrices={len(prompts_matrix)}, elapsed={elapsed:.2f}s")

    return analysis_text, prompts_matrix


def run_phase_two(
    edited_prompt: str,
    config: Dict[str, Any],
    aspect_ratio: str = "1:1",
    output_dir: Optional[str] = None,
    filename_prefix: Optional[str] = None,
) -> str:
    """
    执行阶段二：调用生图引擎生成单张商业图并保存到本地
    """
    provider = config.get("active_provider", "gemini")
    return generate_ecommerce_image(
        prompt=edited_prompt,
        provider=provider,
        config=config,
        output_dir=output_dir,
        aspect_ratio=aspect_ratio,
        filename_prefix=filename_prefix,
    )


def run_phase_two_batch(
    items: List[Dict[str, str]],
    config: Dict[str, Any],
    aspect_ratio: str = "1:1",
    output_dir: Optional[str] = None,
    max_workers: int = 3,
) -> List[Dict[str, Any]]:
    """
    执行阶段二（批量模式）：并发批量生成电商 9 大图矩阵
    """
    provider = config.get("active_provider", "gemini")
    return generate_ecommerce_images_batch(
        items=items,
        provider=provider,
        config=config,
        output_dir=output_dir,
        aspect_ratio=aspect_ratio,
        max_workers=max_workers,
    )


def save_plan_markdown(
    product_info: Dict[str, str],
    analysis_text: str,
    prompt_or_matrix: Union[str, List[Dict[str, str]]],
    output_dir: Optional[str] = None,
) -> str:
    """保存结构化策划案为本地 Markdown 文件，包含 9 大图提示词矩阵"""
    if output_dir is None:
        base_dir = Path(__file__).resolve().parent
        output_dir = str(base_dir / "output")

    os.makedirs(output_dir, exist_ok=True)
    timestamp = int(time.time())
    prod_name = product_info.get("name", "product").replace(" ", "_")
    file_path = os.path.join(output_dir, f"plan_{prod_name}_{timestamp}.md")

    if isinstance(prompt_or_matrix, list):
        matrix_lines = []
        for idx, item in enumerate(prompt_or_matrix, start=1):
            matrix_lines.append(
                f"### {idx}. {item.get('name', '电商大图')}\n"
                f"- **定位说明**：{item.get('desc', '')}\n"
                f"- **中文生图提示词**：\n```text\n{item.get('prompt', '')}\n```\n"
            )
        prompts_section = "\n".join(matrix_lines)
    else:
        prompts_section = f"```text\n{prompt_or_matrix}\n```"

    content = f"""# 营销策划案交付物: {product_info.get('name', '电商商品')}
生成时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}

## 一、商品基本信息
- **商品名称**：{product_info.get('name', '')}
- **品类属性**：{product_info.get('category', '')}
- **目标人群**：{product_info.get('target_audience', '')}
- **竞品短板/买家痛点**：{product_info.get('pain_points', '')}

---

## 二、多智能体深度分析与视觉策划方案
{analysis_text}

---

## 三、电商 9 大图视觉生图提示词矩阵 (中文商业级摄影规格)
{prompts_section}
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    return file_path
