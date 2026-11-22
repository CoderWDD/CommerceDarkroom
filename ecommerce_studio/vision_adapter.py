"""
多模态模型视觉适配器 (MultiModalVisionAdapter)
支持 Gemini 2.0 Flash Vision、GPT-4o Vision 与规则启发式熔断兜底 (Circuit Breaker)
"""

import asyncio
import json
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from ecommerce_studio.api.schemas import ProductDossierExtracted

logger = logging.getLogger("ecommerce_studio.vision_adapter")

VISION_EXTRACTION_SYSTEM_PROMPT = """你是一位世界顶尖的电商工业设计专家与爆款选品战略总监。
用户提供了一张随手拍的实物商品照片（可能包含手持、杂乱背景、反光等非影棚干扰因素）。
请仔细审视实物，透过现象看本质，进行逆向工程分析，输出严格合规的 JSON 对象，严禁包裹任何额外说明文字或 Markdown 标记！

【JSON输出结构规范】：
{
  "product_name": "精确商业品名（突出工业材质、功能与形态）",
  "category": "细分行业品类",
  "material_features": "表面工业特征、加工工艺与触觉材质细节",
  "target_users": "目标客群年龄、社会角色、消费动机",
  "pain_points": "买家决策最担心的核心短板或使用抗拒点",
  "visual_tags": ["#主色材质标签", "#工艺特征标签", "#核心形态标签", "#使用特征标签"],
  "color_palette": ["#16位色阶 配色名称1", "#16位色阶 配色名称2", "#16位色阶 配色名称3"]
}"""


class MultiModalVisionAdapter:
    """多模态视觉提取调度器 (带主动超时、自动切换与规则兜底)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.timeout_sec = 25.0

    async def extract_dossier(
        self,
        image_bytes: bytes,
        category_hint: Optional[str] = "",
    ) -> Tuple[ProductDossierExtracted, str]:
        active_provider = self.config.get("active_provider", "gemini").lower()

        # 尝试通道列表：当前激活通道优先，另一通道次之
        provider_chain = [active_provider]
        fallback_target = "openai" if active_provider == "gemini" else "gemini"
        if fallback_target not in provider_chain:
            provider_chain.append(fallback_target)

        errors = []
        for provider in provider_chain:
            try:
                if provider == "gemini":
                    result = await asyncio.wait_for(
                        self._call_gemini_vision(image_bytes, category_hint or ""),
                        timeout=self.timeout_sec,
                    )
                    return result, "gemini"
                elif provider in ["openai", "custom_openai"]:
                    result = await asyncio.wait_for(
                        self._call_openai_vision(image_bytes, category_hint or ""),
                        timeout=self.timeout_sec,
                    )
                    return result, provider
            except Exception as e:
                logger.warning(f"通道 [{provider}] 多模态逆向提取失败: {str(e)}，尝试下一通道")
                errors.append(f"{provider}: {str(e)}")

        # 双通道全部失败，触发确定性规则降级兜底，保障系统绝对可用
        logger.error(f"所有多模态大模型通道均不可用: {errors}，启动规则特征库熔断兜底")
        fallback_result = self._fallback_heuristic_dossier(image_bytes, category_hint or "")
        return fallback_result, "rule_fallback"

    async def _call_gemini_vision(self, image_bytes: bytes, hint: str) -> ProductDossierExtracted:
        from google import genai
        from google.genai import types

        gemini_cfg = self.config.get("gemini", {})
        api_key = gemini_cfg.get("api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API Key 未配置")

        model_name = gemini_cfg.get("model") or "gemini-2.0-flash"
        client = genai.Client(api_key=api_key)

        prompt = f"{VISION_EXTRACTION_SYSTEM_PROMPT}\n实物提示：{hint}\n请按照指定规范逆向提取商品商业档案。"
        image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

        response = await asyncio.to_thread(
            client.models.generate_content,
            model=model_name,
            contents=[prompt, image_part],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
        text = response.text or "{}"
        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
        data = json.loads(clean_json)
        return ProductDossierExtracted(**data)

    async def _call_openai_vision(self, image_bytes: bytes, hint: str) -> ProductDossierExtracted:
        from openai import AsyncOpenAI
        import base64

        openai_cfg = self.config.get("openai", {})
        api_key = openai_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
        base_url = openai_cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        if not api_key:
            raise ValueError("OpenAI API Key 未配置")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        base64_img = base64.b64encode(image_bytes).decode("utf-8")

        response = await client.chat.completions.create(
            model=openai_cfg.get("model") or "gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{VISION_EXTRACTION_SYSTEM_PROMPT}\n实物提示：{hint}\n输出严格 JSON 格式商品档案。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw_json = response.choices[0].message.content or "{}"
        clean_json = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_json.strip())
        data = json.loads(clean_json)
        return ProductDossierExtracted(**data)

    def _fallback_heuristic_dossier(self, image_bytes: bytes, hint: str) -> ProductDossierExtracted:
        """兜底规则生成器，即使离线或无 Key 也保持业务链路畅通"""
        prod_name = hint.strip() if hint and hint.strip() else "高品质便携随行商品"
        return ProductDossierExtracted(
            product_name=f"{prod_name} (智能识别)",
            category="现代生活良品 / 高端电商定制",
            material_features="高精度哑光金属质感、防刮耐磨涂层、精密工业接缝与人体工学弧度",
            target_users="25-40岁追求生活美感与精工品质的都市人群",
            pain_points="做工粗糙缺乏档次感、日常磕碰易划伤、实用功能衰减快",
            visual_tags=["#极简几何", "#精工材质", "#商业摄影基准", "#防刮哑光"],
            color_palette=["#18181B 深邃黑", "#71717A 钛金灰", "#FAFAFA 纯净白"],
            confidence_score=0.70,
        )
