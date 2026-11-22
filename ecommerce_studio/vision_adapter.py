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

ACTUAL_PHOTO_SYSTEM_PROMPT = """你是一位世界顶尖的电商工业设计专家与产品形态质检总监。
用户提供了一张【产品实拍图】（实际生产制造的产品真实照片，可能为手机随手拍、白底实拍或工程样机照）。
你的首要任务是【精准锚定该产品的真实物理形态与材质】，提炼出真实物理特征，杜绝后续出图货不对板！
请仔细审视实物，进行逆向工程分析，输出严格合规的 JSON 对象，严禁包裹任何额外说明文字或 Markdown 标记！

【JSON输出结构规范】：
{
  "product_name": "精确商业品名（突出实物真实材质、功能与外观形态）",
  "category": "细分行业品类",
  "material_features": "真实表面物理材质、加工工艺、表面涂层触感、接缝与结构细节（如医用不锈钢、微米级磨砂喷漆、精密阻尼转轴等）",
  "target_users": "目标客群年龄、社会角色、消费动机",
  "pain_points": "买家决策最担心的核心短板或使用抗拒点（如做工掉漆、密封防漏、握持手感）",
  "visual_tags": ["#实拍物理形体", "#真实表面材质", "#核心工艺细节", "#物理防伪锁模标签"],
  "color_palette": ["#16位色阶 配色名称1", "#16位色阶 配色名称2", "#16位色阶 配色名称3"]
}"""

COMPETITOR_PHOTO_SYSTEM_PROMPT = """你是一位享誉国际的电商爆款视觉总监与竞品分析专家。
用户提供了一张【对标商品图】（电商平台上其他品牌/厂家的成熟电商高转化主图或大片）。
你的首要任务是【深度解析该对标图的商业构图、高级布光、展台场景与卖点呈现技巧】，汲取其高点击率与高转化视觉精华！
请仔细审视该电商图，进行视觉策划逆向工程，输出严格合规的 JSON 对象，严禁包裹任何额外说明文字或 Markdown 标记！

【JSON输出结构规范】：
{
  "product_name": "对标商品品名（结合其展示的品类特征）",
  "category": "细分电商热销品类",
  "material_features": "对标大片所呈现的高级视觉质感与材质表现手法",
  "target_users": "该电商图靶向的高价值消费客群画像",
  "pain_points": "该电商图通过构图和场景成功击穿的买家顾虑",
  "visual_tags": ["#对标高质感构图", "#商业摄影光影", "#大牌展台布景", "#买家心智转化点"],
  "color_palette": ["#16位色阶 商业大片主色1", "#16位色阶 空间环境色2", "#16位色阶 重点提亮色3"]
}"""

VISION_EXTRACTION_SYSTEM_PROMPT = ACTUAL_PHOTO_SYSTEM_PROMPT


class MultiModalVisionAdapter:
    """多模态视觉提取调度器 (支持产品实拍图与对标商品图分类解析，带主动超时与规则兜底)"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.timeout_sec = 25.0

    async def extract_dossier(
        self,
        image_bytes: bytes,
        category_hint: Optional[str] = "",
        asset_type: str = "actual",
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
                        self._call_gemini_vision(image_bytes, category_hint or "", asset_type=asset_type),
                        timeout=self.timeout_sec,
                    )
                    return result, "gemini"
                elif provider in ["openai", "custom_openai"]:
                    result = await asyncio.wait_for(
                        self._call_openai_vision(image_bytes, category_hint or "", asset_type=asset_type),
                        timeout=self.timeout_sec,
                    )
                    return result, provider
            except Exception as e:
                logger.warning(f"通道 [{provider}] 多模态逆向提取失败: {str(e)}，尝试下一通道")
                errors.append(f"{provider}: {str(e)}")

        # 双通道全部失败，触发确定性规则降级兜底，保障系统绝对可用
        logger.error(f"所有多模态大模型通道均不可用: {errors}，启动规则特征库熔断兜底")
        fallback_result = self._fallback_heuristic_dossier(image_bytes, category_hint or "", asset_type=asset_type)
        return fallback_result, "rule_fallback"

    async def _call_gemini_vision(self, image_bytes: bytes, hint: str, asset_type: str = "actual") -> ProductDossierExtracted:
        from google import genai
        from google.genai import types

        gemini_cfg = self.config.get("gemini", {})
        api_key = gemini_cfg.get("api_key") or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Gemini API Key 未配置")

        model_name = gemini_cfg.get("model") or "gemini-2.0-flash"
        client = genai.Client(api_key=api_key)

        sys_prompt = ACTUAL_PHOTO_SYSTEM_PROMPT if asset_type != "competitor" else COMPETITOR_PHOTO_SYSTEM_PROMPT
        prompt = f"{sys_prompt}\n资产类型：{'【产品实拍图(真实原貌)】' if asset_type != 'competitor' else '【对标商品图(电商大片参考)】'}\n实物提示：{hint}\n请按照指定规范逆向提取商品商业档案。"
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

    async def _call_openai_vision(self, image_bytes: bytes, hint: str, asset_type: str = "actual") -> ProductDossierExtracted:
        from openai import AsyncOpenAI
        import base64

        openai_cfg = self.config.get("openai", {})
        api_key = openai_cfg.get("api_key") or os.environ.get("OPENAI_API_KEY")
        base_url = openai_cfg.get("base_url") or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"
        if not api_key:
            raise ValueError("OpenAI API Key 未配置")

        client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        base64_img = base64.b64encode(image_bytes).decode("utf-8")

        sys_prompt = ACTUAL_PHOTO_SYSTEM_PROMPT if asset_type != "competitor" else COMPETITOR_PHOTO_SYSTEM_PROMPT
        response = await client.chat.completions.create(
            model=openai_cfg.get("model") or "gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{sys_prompt}\n资产类型：{'【产品实拍图(真实原貌)】' if asset_type != 'competitor' else '【对标商品图(电商大片参考)】'}\n实物提示：{hint}\n输出严格 JSON 格式商品档案。"},
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

    def _fallback_heuristic_dossier(self, image_bytes: bytes, hint: str, asset_type: str = "actual") -> ProductDossierExtracted:
        """兜底规则生成器，即使离线或无 Key 也保持业务链路畅通"""
        prod_name = hint.strip() if hint and hint.strip() else "高品质便携随行商品"
        if asset_type == "competitor":
            return ProductDossierExtracted(
                product_name=f"{prod_name} (对标电商大片)",
                category="热销爆款视觉 / 高转化电商矩阵",
                material_features="高反差通透漫射光感、大理石纯净展台衬托、通透微倒影、高质感边缘轮廓光",
                target_users="25-40岁注重视觉审美与品牌质感的中产消费人群",
                pain_points="低端廉价感、画面杂乱无法凸显核心卖点、缺乏高级生活方式代入感",
                visual_tags=["#大牌纯净展台", "#商业高反差布光", "#微倒影质感", "#视觉中心焦点"],
                color_palette=["#18181B 纯粹黑", "#E4E4E7 哑光灰白", "#3B82F6 科技微蓝"],
                confidence_score=0.75,
            )
        return ProductDossierExtracted(
            product_name=f"{prod_name} (实物智能识别)",
            category="现代生活良品 / 实体制造工规",
            material_features="高精度哑光金属质感、防刮耐磨涂层、精密工业接缝与人体工学弧度（实物保真基准）",
            target_users="25-40岁追求生活美感与精工品质的都市人群",
            pain_points="做工粗糙缺乏档次感、日常磕碰易划伤、实用功能衰减快",
            visual_tags=["#实物精密结构", "#精工材质细节", "#物理防走样锁模", "#防刮哑光涂层"],
            color_palette=["#18181B 深邃黑", "#71717A 钛金灰", "#FAFAFA 纯净白"],
            confidence_score=0.70,
        )
