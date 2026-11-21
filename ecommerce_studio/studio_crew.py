import base64
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
        "desc": "直击买家最大抗拒点（如密封倒置滴水不漏、持久保温冷凝水珠、防刮耐磨），用强视觉冲击消除下单顾虑",
    },
    {
        "id": "portable_commute",
        "name": "便携携带与通勤场景图",
        "desc": "手持随行、放于车载杯架或收纳于商务通勤背包侧袋，体现轻便易携、单手握持与人体工学设计",
    },
    {
        "id": "structure_cutaway",
        "name": "结构卖点与内胆透视图",
        "desc": "科技感艺术分层拆解或半透视光效，清晰呈现多层保温隔热内胆、抑菌涂层与精密机械结构",
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
    "desc": "直击买家最大抗拒点（如密封倒置不漏水、保温冷凝、防刮耐磨）",
    "prompt": "商业硬核功能测试场景摄影，针对买家痛点..."
  },
  {
    "id": "portable_commute",
    "name": "便携携带与通勤场景图",
    "desc": "手持随行、车载杯架或收纳于通勤背包，体现轻便易携",
    "prompt": "都市通勤实景摄影，手持轻巧收纳..."
  },
  {
    "id": "structure_cutaway",
    "name": "结构卖点与内胆透视图",
    "desc": "科技感艺术分层拆解或半透视光效，清晰呈现多层内胆与精密机械结构",
    "prompt": "未来科技感艺术透视与爆炸图摄影，三维艺术半透视呈现..."
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


def build_default_prompt_matrix(product_info: Dict[str, str]) -> List[Dict[str, str]]:
    """
    根据商品信息，智能生成高质量商业摄影级 9 大图全套中文提示词（内置高质量兜底模板）
    """
    name = product_info.get("name", "高端电商产品")
    category = product_info.get("category", "数码科技/生活良品")
    audience = product_info.get("target_audience", "追求品质生活的消费者")
    pain_points = product_info.get("pain_points", "密封耐用与做工细节")

    prompts_map = {
        "main_white_bg": (
            f"高端商业广告静物摄影，正视微俯30度全景，主体为一款极具现代设计感的{name}（属于{category}品类）。"
            f"放置在纯白色极简哑光展台上，无杂乱背景，底部带有自然通透的镜面微倒影。"
            f"商业静物柔光箱三点布光，顶部柔光均匀漫射，两侧轮廓高光细腻勾勒出机身圆润线条与精致质感。"
            f"8k极致超清分辨率，锐利对焦，真实工业级材质细节，无任何杂物与水印，纯正电商首图风格。"
        ),
        "lifestyle_scene": (
            f"真实生活方式摄影，中景构图，{name}优雅放置于现代化极简原木办公桌或清晨厨房大理石台面上。"
            f"清晨自然暖阳穿透百叶窗，在桌面上投下斑驳光影，背景自然虚化可见青翠绿植与精致陶瓷器皿。"
            f"氛围温暖惬意、宁静典雅，符合{audience}的高品位生活方式。浅景深胶片质感，顶级商业杂志静物摄影，超高清细节。"
        ),
        "core_feature": (
            f"商业产品核心功能特写摄影，近景斜侧45度角聚焦{name}的核心功能按键/智能显示屏/出水出风口。"
            f"镜头紧密定焦于功能结构件，边缘带有精密机械微缝与指示灯微弱冷色柔光，其余部分柔美渐进虚化。"
            f"深色低调背景，专业静物点光源高精度打光，凸显高科技感与精工实用价值，8k清晰画质。"
        ),
        "material_detail": (
            f"大师级商业微距摄影，极限超近景，定焦于{name}的机身表面材质与精工做工。"
            f"展现细腻的航空级哑光磨砂涂层与高精度阳极氧化金属拉丝倒角，光影在微观金属边缘流淌跃动。"
            f"极浅景深，微米级清晰纹理质感，色彩饱满深沉，顶级工业设计微距大片，无噪点，超写实质感。"
        ),
        "pain_point_solution": (
            f"商业功能硬核测试攻坚场景摄影，针对买家痛点（{pain_points}），多机位动感抓拍{name}。"
            f"例如商品被倒置倾斜剧烈晃动却滴水不漏，或者在冷热交替环境下瓶身干爽无任何冷凝渗漏水珠，飞溅的微细水花定格在空中。"
            f"高速快门抓拍，清澈透明的水滴与高反差专业影棚侧逆光，极具视觉冲击力与可靠信赖感，8k超清画质。"
        ),
        "portable_commute": (
            f"都市通勤实景摄影，{name}被轻巧地握在一只年轻商务白领手中，或优雅插在极简皮质商务双肩包侧袋/置于现代智能轿车杯架中。"
            f"背景为略带虚化的现代都会高楼玻璃幕墙或地铁明亮空间，展现轻巧易收纳与便携随行的人体工学优势。"
            f"自然日光采光，色彩干净利落，现代轻商务氛围，真实生动，商业级通勤场景摄影。"
        ),
        "structure_cutaway": (
            f"未来科技感艺术透视与爆炸图摄影，三维艺术半透视呈现{name}的内部精密多层结构。"
            f"清晰展现多层隔热/抑菌内胆、密封硅胶密封圈与智能电路感应模块，各组件沿轴线悬浮展开并带有微弱极光蓝导光线条。"
            f"深灰极简纯净背景，专业科幻工业渲染质感，光影通透，结构严谨，展现核心黑科技用料与匠心品质。"
        ),
        "unboxing_gift": (
            f"顶级奢华礼盒开箱摄影，俯视45度角平铺拍摄，高档哑光天地盖硬质礼品盒呈半开状态。"
            f"{name}主体被精心嵌在定制高密度黑色EVA海绵内衬中，旁边整齐陈列着定制配件、质感说明书与烫金品牌卡片。"
            f"暖金色环境柔光与精美包装丝带，开箱仪式感拉满，尊贵送礼首选，极简高级电商礼盒大片。"
        ),
        "model_interaction": (
            f"高端商业人像与产品互动摄影，一位气质优雅、着装得体的年轻都市模特（契合{audience}画像），面带从容自信微笑，单手自然握持并使用{name}。"
            f"半身人像构图，视线焦点兼顾人物自然神态与商品清晰质感。柔美环境光漫射，浅景深虚化背景中的现代生活空间。"
            f"高阶品牌广告大片质感，传递健康、自信与品质情绪价值，8k胶片级人像摄影。"
        ),
    }

    results = []
    for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES:
        t_id = tpl["id"]
        results.append({
            "id": t_id,
            "name": tpl["name"],
            "desc": tpl["desc"],
            "prompt": prompts_map.get(t_id, f"商业级电商摄影，{name}，高质感细节，8k画质。"),
        })
    return results


def parse_prompt_matrix_from_text(text: str, product_info: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """
    从大模型生成的策划案文本中智能提取 9 大图全套中文提示词矩阵。
    如果模型未完全遵循 JSON 或有缺失项，使用商品信息与模板智能补齐，确保 100% 返回 9 组规范数据。
    """
    defaults = build_default_prompt_matrix(product_info or {})
    default_dict = {item["id"]: item for item in defaults}

    parsed_items: Dict[str, Dict[str, str]] = {}

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
                            parsed_items[target_id] = {
                                "id": target_id,
                                "name": default_dict[target_id]["name"],
                                "desc": e_desc or default_dict[target_id]["desc"],
                                "prompt": e_prompt,
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
            # 匹配形如 "1. 商业高清白底首图" 或 "【商业高清白底首图】" 下方的提示词
            pattern = (
                rf"(?:(?:#|\*|\d+[\.\、\s]*)*{re.escape(name)}[\s\S]*?)"
                rf"(?:提示词|Prompt|生图描述)[\s:：]*([^\n]+(?:\n(?!(?:#|\d+[\.\、]|【|\[))[^\n]+){{0,4}})"
            )
            match = re.search(pattern, text)
            if match:
                cand = match.group(1).strip()
                # 过滤掉 markdown 标记
                cand = re.sub(r"^[`*\"']+|[`*\"']+$", "", cand).strip()
                if len(cand) >= 20:
                    parsed_items[t_id] = {
                        "id": t_id,
                        "name": name,
                        "desc": tpl["desc"],
                        "prompt": cand,
                    }

    # 3. 组合并按标准顺序输出 9 大图，缺失项用高质量默认模板补齐
    final_matrix: List[Dict[str, str]] = []
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


def run_phase_one(
    product_info: Dict[str, str],
    pil_images: List[Image.Image],
    config: Dict[str, Any],
    status_callback: Optional[Callable[[str], None]] = None,
) -> Tuple[str, List[Dict[str, str]]]:
    """
    执行阶段一：多模态商品图理解 + 多智能体痛点挖掘与场景构思
    生成包含电商 9 大图视觉矩阵的高质量中文提示词方案

    :param product_info: 商品文字信息（商品名称、品类、目标群体、竞品短板）
    :param pil_images: 上传的实拍商品图 PIL 列表
    :param config: 系统配置字典
    :param status_callback: 状态日志回调函数
    :return: (结构化策划案全文, 结构化9组中文提示词列表)
    """
    def log(msg: str):
        if status_callback:
            status_callback(msg)

    t0 = time.time()
    logger.info(f"🚀 [run_phase_one Start] product='{product_info.get('name')}', images={len(pil_images)}")

    provider = config.get("active_provider", "gemini").lower()
    agents_cfg = config.get("agents", {})

    market_agent = agents_cfg.get("market_researcher", {})
    art_agent = agents_cfg.get("art_director", {})
    visual_agent = agents_cfg.get("visual_engineer", {})

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
3. 必须在方案第 3 模块中，按照以下标准 JSON 数组代码块格式，完整输出指定 9 类电商核心图片的中文生图提示词矩阵：

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
    prompts_matrix = parse_prompt_matrix_from_text(analysis_text, product_info)
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
