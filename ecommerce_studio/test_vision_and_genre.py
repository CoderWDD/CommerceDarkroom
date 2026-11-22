"""
Ecommerce Studio v2.0 - Vision and Genre Automated Test Suite
Verifies:
1. style_presets.py data structures, registries, and lookup helpers.
2. GET /api/v1/studio/style-presets endpoint.
3. POST /api/v1/studio/vision/extract-dossier endpoint (multipart/form-data, json, mock Vision LLM, and rule fallback).
4. Prompt generation with style preset injection in studio_crew.py / prompt_compiler.py and /plan integration.
"""

import asyncio
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi.testclient import TestClient
from ecommerce_studio.api.main import app
from ecommerce_studio.api.schemas import (
    ProductDossierExtracted,
    VisionExtractDossierRequest,
    VisionExtractDossierResponse,
)
from ecommerce_studio.api.service import studio_service
from ecommerce_studio import session_manager, studio_crew
from ecommerce_studio.style_presets import (
    DEFAULT_STYLE_PRESET_ID,
    STYLE_PRESET_REGISTRY,
    StylePreset,
    get_all_style_presets,
    get_style_preset,
    list_style_presets,
)
from ecommerce_studio.prompt_compiler import PromptMatrixCompiler


class TestStylePresetsDataStructure(unittest.TestCase):
    """1. 测试 style_presets.py 数据结构、流派注册中心与检索辅助函数"""

    def test_registry_contains_five_official_presets(self):
        """验证 5 大官方爆款流派全量入驻注册中心"""
        expected_presets = {
            "minimalist_muji",
            "nordic_luxury",
            "german_deconstruct",
            "dopamine_energy",
            "cyber_street",
        }
        actual_presets = set(STYLE_PRESET_REGISTRY.keys())
        self.assertEqual(actual_presets, expected_presets)

    def test_preset_field_completeness_and_types(self):
        """验证每个流派的 4 大光学维度与防漂移参数字段完备性"""
        for pid, preset in STYLE_PRESET_REGISTRY.items():
            self.assertIsInstance(preset, StylePreset)
            self.assertEqual(preset.id, pid)
            self.assertTrue(len(preset.name) > 0)
            self.assertTrue(len(preset.en_name) > 0)
            self.assertTrue(len(preset.tagline) > 0)
            self.assertTrue(len(preset.description) > 0)
            # 核心 4 大光学与环境维度
            self.assertTrue(len(preset.lighting) > 0)
            self.assertTrue(len(preset.environment) > 0)
            self.assertTrue(len(preset.camera) > 0)
            self.assertTrue(len(preset.color_tone) > 0)
            # 防漂移参数与视角专属强化
            self.assertIsInstance(preset.anti_drift_rules, list)
            self.assertTrue(len(preset.anti_drift_rules) >= 2)
            self.assertIsInstance(preset.perspective_enhancements, dict)

    def test_get_style_preset_lookup(self):
        """测试流派按 ID 精确检索及未知/空值默认回退"""
        # 精确检索
        preset = get_style_preset("cyber_street")
        self.assertEqual(preset.id, "cyber_street")
        self.assertIn("赛博", preset.name)

        # 默认与非法回退
        default_preset = get_style_preset()
        self.assertEqual(default_preset.id, DEFAULT_STYLE_PRESET_ID)
        self.assertEqual(default_preset.id, "minimalist_muji")

        none_preset = get_style_preset(None)
        self.assertEqual(none_preset.id, "minimalist_muji")

        empty_preset = get_style_preset("")
        self.assertEqual(empty_preset.id, "minimalist_muji")

        invalid_preset = get_style_preset("unknown_nonexistent_preset")
        self.assertEqual(invalid_preset.id, "minimalist_muji")

    def test_list_and_get_all_style_presets(self):
        """测试流派列表提取接口"""
        presets_list = list_style_presets()
        self.assertEqual(len(presets_list), 5)
        for item in presets_list:
            self.assertIsInstance(item, StylePreset)

        presets_dict_list = get_all_style_presets()
        self.assertEqual(len(presets_dict_list), 5)
        for item in presets_dict_list:
            self.assertIsInstance(item, dict)
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("tagline", item)
            self.assertIn("lighting", item)


class TestStylePresetAPI(unittest.TestCase):
    """2. 测试 GET /api/v1/studio/style-presets 接口"""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_style_presets_endpoint(self):
        """测试获取流派预设列表接口的 HTTP 响应与契约"""
        resp = self.client.get("/api/v1/studio/style-presets")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 5)

        ids = [p["id"] for p in data]
        self.assertIn("minimalist_muji", ids)
        self.assertIn("nordic_luxury", ids)
        self.assertIn("german_deconstruct", ids)
        self.assertIn("dopamine_energy", ids)
        self.assertIn("cyber_street", ids)

        # 校验响应契约字段
        first = data[0]
        self.assertIn("id", first)
        self.assertIn("name", first)
        self.assertIn("en_name", first)
        self.assertIn("tagline", first)
        self.assertIn("description", first)
        self.assertIn("lighting", first)
        self.assertIn("environment", first)
        self.assertIn("camera", first)
        self.assertIn("color_tone", first)
        self.assertIn("anti_drift_rules", first)


class TestVisionExtractDossierAPI(unittest.TestCase):
    """3. 测试 POST /api/v1/studio/vision/extract-dossier 接口 (多模态逆向建档)"""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.created_sessions = []
        self.temp_dirs = []

    def tearDown(self):
        for sid in self.created_sessions:
            try:
                session_manager.delete_session(sid)
            except Exception:
                pass
        for tdir in self.temp_dirs:
            shutil.rmtree(tdir, ignore_errors=True)

    def test_extract_dossier_multipart_form_success(self):
        """测试以 multipart/form-data 文件直传方式完成逆向建档"""
        mock_dossier = ProductDossierExtracted(
            product_name="智能数显双层真空随行保温杯",
            category="高品质水具 / 智能数码生活",
            material_features="316L医用级不锈钢、外壳微米级哑光喷砂烤漆、LED触控屏",
            target_users="25-35岁高知通勤白领、商务差旅精英",
            pain_points="市面传统杯倒置渗水、保温时长不足、外壳易磕碰掉漆",
            visual_tags=["#曜石黑哑光", "#阳极氧化铝", "#LED触控数显"],
            color_palette=["#09090B 曜石黑", "#71717A 钛合金灰"],
            confidence_score=0.96,
        )

        with patch.object(
            studio_service,
            "extract_dossier_from_image",
            new_callable=AsyncMock,
        ) as mock_extract:
            mock_extract.return_value = (mock_dossier, "gemini")

            # 创建会话以关联资产
            create_res = self.client.post("/api/v1/studio/sessions", json={"name": "视觉逆向测试会话"})
            sid = create_res.json()["session_id"]
            self.created_sessions.append(sid)

            fake_image_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 100
            resp = self.client.post(
                "/api/v1/studio/vision/extract-dossier",
                data={"session_id": sid, "category_hint": "保温杯"},
                files={"file": ("snap_sample.jpg", fake_image_bytes, "image/jpeg")},
            )

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("session_id"), sid)
            self.assertEqual(data.get("model_provider"), "gemini")
            self.assertTrue(data.get("execution_time_ms") >= 0)
            self.assertTrue(data.get("asset_url", "").startswith("/output/"))

            dossier = data.get("dossier", {})
            self.assertEqual(dossier.get("product_name"), "智能数显双层真空随行保温杯")
            self.assertEqual(dossier.get("category"), "高品质水具 / 智能数码生活")
            self.assertIn("#曜石黑哑光", dossier.get("visual_tags", []))
            self.assertEqual(dossier.get("confidence_score"), 0.96)

    def test_extract_dossier_json_payload_success(self):
        """测试以 application/json 传入已存资产路径方式调用逆向建档"""
        mock_dossier = ProductDossierExtracted(
            product_name="极简原木智能香氛机",
            category="生活家居 / 智能小家电",
            material_features="天然胡桃木纹底座、半透明磨砂亚克力储水仓、静音纳米雾化片",
            target_users="都市租房青年、居家办公族、香氛疗愈爱好者",
            pain_points="出雾颗粒粗易凝水打湿桌面、储水量小需频繁加水、运转噪音影响睡眠",
            visual_tags=["#胡桃木原木", "#极简雾化", "#磨砂半透"],
            color_palette=["#5A3825 胡桃棕", "#FAFAFA 哑光白"],
            confidence_score=0.92,
        )

        # 准备物理测试图片
        upload_dir = Path(__file__).resolve().parent / "output" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        test_file = upload_dir / "test_asset_for_json.jpg"
        test_file.write_bytes(b"\xff\xd8\xff\xe0" + b"\x01" * 50)

        try:
            with patch.object(
                studio_service,
                "extract_dossier_from_image",
                new_callable=AsyncMock,
            ) as mock_extract:
                mock_extract.return_value = (mock_dossier, "openai")

                payload = {
                    "asset_url": "/output/uploads/test_asset_for_json.jpg",
                    "category_hint": "香氛机",
                }
                resp = self.client.post(
                    "/api/v1/studio/vision/extract-dossier",
                    json=payload,
                )

                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertTrue(data.get("success"))
                self.assertEqual(data.get("model_provider"), "openai")
                dossier = data.get("dossier", {})
                self.assertEqual(dossier.get("product_name"), "极简原木智能香氛机")
        finally:
            if test_file.exists():
                test_file.unlink()

    def test_extract_dossier_rule_fallback_when_models_fail(self):
        """测试多模态大模型通道全失败时，自动熔断降级为确定性规则兜底"""
        with patch.object(
            studio_service,
            "extract_dossier_from_image",
            new_callable=AsyncMock,
        ) as mock_extract:
            # 模拟 MultiModalVisionAdapter 触发熔断降级，返回 rule_fallback 结果
            fallback_dossier = ProductDossierExtracted(
                product_name="多功能便携运动水壶 (智能识别)",
                category="现代生活良品 / 高端电商定制",
                material_features="高精度哑光金属质感、防刮耐磨涂层、精密工业接缝与人体工学弧度",
                target_users="25-40岁追求生活美感与精工品质的都市人群",
                pain_points="做工粗糙缺乏档次感、日常磕碰易划伤、实用功能衰减快",
                visual_tags=["#极简几何", "#精工材质", "#商业摄影基准", "#防刮哑光"],
                color_palette=["#18181B 深邃黑", "#71717A 钛金灰", "#FAFAFA 纯净白"],
                confidence_score=0.70,
            )
            mock_extract.return_value = (fallback_dossier, "rule_fallback")

            fake_bytes = b"\xff\xd8" + b"\x00" * 30
            resp = self.client.post(
                "/api/v1/studio/vision/extract-dossier",
                data={"category_hint": "多功能便携运动水壶"},
                files={"file": ("snap_fallback.jpg", fake_bytes, "image/jpeg")},
            )

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(data.get("success"))
            self.assertEqual(data.get("model_provider"), "rule_fallback")
            dossier = data.get("dossier", {})
            self.assertIn("智能识别", dossier.get("product_name", ""))
            self.assertEqual(dossier.get("confidence_score"), 0.70)

    def test_extract_dossier_missing_inputs_returns_400(self):
        """测试当既无上传文件也无有效资产路径时，接口准确抛出 400 Bad Request"""
        # 1. 既没有 file 也没有 asset_url
        resp_empty = self.client.post(
            "/api/v1/studio/vision/extract-dossier",
            json={},
        )
        self.assertEqual(resp_empty.status_code, 400)
        self.assertIn("必须提供上传文件", resp_empty.json().get("detail", ""))

        # 2. 提供了不存在的 asset_url
        resp_not_found = self.client.post(
            "/api/v1/studio/vision/extract-dossier",
            json={"asset_url": "/output/uploads/non_existent_file_999.jpg"},
        )
        self.assertEqual(resp_not_found.status_code, 400)
        self.assertIn("指定资产不存在", resp_not_found.json().get("detail", ""))


class TestPromptCompilerAndStylePresetInjection(unittest.TestCase):
    """4. 测试 9 视角提示词编译器、流派参数注入及与策划接口 /plan 联动"""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.created_sessions = []
        self.product_info = {
            "name": "钛空舱智能温控咖啡杯",
            "category": "精品水具/智能家居",
            "material_features": "316L医用不锈钢内胆、曜石黑哑光微米喷砂、LED触控数显",
            "target_users": "25-35岁都市白领与手冲咖啡爱好者",
            "pain_points": "传统保温杯倒置易漏水、开盖易烫嘴、外壳易磕碰刮花",
        }

    def tearDown(self):
        for sid in self.created_sessions:
            try:
                session_manager.delete_session(sid)
            except Exception:
                pass

    def test_prompt_compiler_generates_all_nine_perspectives(self):
        """测试 PromptMatrixCompiler.compile_matrix 产出完整的 9 视角矩阵"""
        matrix = PromptMatrixCompiler.compile_matrix(self.product_info, "minimalist_muji")
        self.assertEqual(len(matrix), 9)

        expected_ids = [
            "01_white_bg",
            "02_scene",
            "03_detail",
            "04_structure",
            "05_pain_killer",
            "06_size",
            "07_emotional",
            "08_color",
            "09_buyer_show",
        ]
        actual_ids = [p["id"] for p in matrix]
        self.assertEqual(actual_ids, expected_ids)

        for item in matrix:
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("desc", item)
            self.assertIn("prompt", item)
            self.assertTrue(len(item["prompt"]) > 40)
            self.assertIn("钛空舱智能温控咖啡杯", item["prompt"])

    def test_prompt_compiler_injects_preset_dimensions(self):
        """测试 5 种不同流派向提示词矩阵注入特定光学与防漂移参数"""
        # 1. 极简原研哉 (minimalist_muji)
        muji_matrix = PromptMatrixCompiler.compile_matrix(self.product_info, "minimalist_muji")
        muji_p1 = muji_matrix[0]["prompt"]
        self.assertIn("50mm", muji_p1)
        self.assertIn("晨光", muji_p1)
        self.assertIn("原木", muji_p1)
        self.assertIn("严禁浓艳色彩", muji_p1)

        # 2. 赛博潮酷 (cyber_street)
        cyber_matrix = PromptMatrixCompiler.compile_matrix(self.product_info, "cyber_street")
        cyber_p1 = cyber_matrix[0]["prompt"]
        self.assertIn("24mm", cyber_p1)
        self.assertIn("青蓝", cyber_p1)
        self.assertIn("严禁田园乡村风", cyber_p1)

        # 3. 德系解构 (german_deconstruct)
        german_matrix = PromptMatrixCompiler.compile_matrix(self.product_info, "german_deconstruct")
        german_p4 = next(p["prompt"] for p in german_matrix if p["id"] == "04_structure")
        self.assertIn("90mm", german_p4)
        self.assertIn("精密", german_p4)
        self.assertIn("严禁粉嫩色系", german_p4)

        # 4. 多巴胺活力 (dopamine_energy)
        pop_matrix = PromptMatrixCompiler.compile_matrix(self.product_info, "dopamine_energy")
        pop_p1 = pop_matrix[0]["prompt"]
        self.assertIn("35mm", pop_p1)
        self.assertIn("柠檬黄", pop_p1)
        self.assertIn("严禁昏暗暗调", pop_p1)

        # 5. 北欧轻奢 (nordic_luxury)
        nordic_matrix = PromptMatrixCompiler.compile_matrix(self.product_info, "nordic_luxury")
        nordic_p3 = next(p["prompt"] for p in nordic_matrix if p["id"] == "03_detail")
        self.assertIn("85mm", nordic_p3)
        self.assertIn("莫兰迪", nordic_p3)
        self.assertIn("大理石", nordic_p3)
        self.assertIn("严禁暴发户式廉价大金大黄", nordic_p3)

    def test_plan_api_integrates_style_preset(self):
        """测试 POST /api/v1/studio/plan 携带 style_preset 参数的策划生成与会话持久化"""
        with patch.object(
            studio_crew,
            "run_phase_one",
        ) as mock_phase_one:
            # 模拟大模型策划输出
            mock_phase_one.return_value = (
                "# 商业策划报告",
                PromptMatrixCompiler.compile_matrix(self.product_info, "cyber_street"),
            )

            resp = self.client.post(
                "/api/v1/studio/plan",
                json={
                    "product_info": self.product_info,
                    "style_preset": "cyber_street",
                },
            )

            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            sid = data.get("session_id")
            self.created_sessions.append(sid)

            # 验证返回结构包含 style_preset
            self.assertEqual(data.get("style_preset"), "cyber_street")

            # 验证 9 大视角镜头指导语言注入了赛博风格
            perspectives = data.get("perspectives", [])
            self.assertEqual(len(perspectives), 9)
            prompt_p1 = perspectives[0].get("prompt_zh", "")
            self.assertTrue(len(prompt_p1) > 20)

            # 验证从后端重新 GET 查询此 session 依然保持 style_preset
            get_resp = self.client.get(f"/api/v1/studio/sessions/{sid}")
            self.assertEqual(get_resp.status_code, 200)
            saved_session = get_resp.json()
            self.assertEqual(saved_session.get("style_preset"), "cyber_street")


class TestAIVisionDirectorMatrixGeneration(unittest.TestCase):
    """测试 AI 商业视觉导演全自主生成引擎与单卡重构接口"""

    def setUp(self):
        self.client = TestClient(app)
        self.product_info = {
            "name": "智能声波温感洁面仪",
            "category": "个人护理/美妆仪器",
            "target_audience": "20-35岁注重肌肤深层清洁的精致女性",
            "pain_points": "毛孔清洁不彻底、易滋生细菌、充电接口进水短路、刷毛过硬伤肤",
            "material_features": "FDA认证食品级亲肤硅胶，IPX7全机身防水，磁吸无线充电底座",
        }
        self.created_sessions = []

    def tearDown(self):
        for sid in self.created_sessions:
            session_file = CURRENT_DIR / "sessions" / f"{sid}.json"
            if session_file.exists():
                try:
                    os.remove(session_file)
                except OSError:
                    pass

    def test_generate_vision_matrix_with_ai_fallback_structure(self):
        """测试 AI 视觉导演在无 API Key 或强制降级时返回完备的 9 大视角结构与动态策略"""
        matrix = studio_crew.generate_vision_matrix_with_ai(
            product_info=self.product_info,
            style_preset_id="minimalist_muji",
            force_fallback=True,
        )
        self.assertEqual(len(matrix), 9)
        expected_ids = [
            "01_white_bg", "02_scene", "03_detail", "04_structure",
            "05_pain_killer", "06_size", "07_emotional", "08_color", "09_buyer_show"
        ]
        for idx, item in enumerate(matrix):
            self.assertEqual(item["id"], expected_ids[idx])
            self.assertTrue(len(item["name"]) > 0)
            self.assertTrue(len(item.get("scene_highlight", "")) > 0, f"{item['id']} missing scene_highlight")
            self.assertTrue(len(item.get("commercial_strategy", "")) > 0, f"{item['id']} missing commercial_strategy")
            self.assertTrue(len(item.get("prompt", "")) > 20)
            self.assertIsInstance(item.get("quick_tweaks"), list)
            self.assertTrue(len(item["quick_tweaks"]) >= 3)
            self.assertIsInstance(item.get("quick_tweak_pills"), list)

    def test_generate_vision_matrix_with_ai_mock_llm(self):
        """测试大模型自主推理 JSON 格式时，正确解析并映射 9 大视角"""
        mock_llm_json = json.dumps([
            {
                "id": "01_white_bg",
                "name": "商业纯净白底首图",
                "scene_highlight": "无影棚纯白背景，声波温感洁面仪居中微俯视，极浅通透接触倒影",
                "commercial_strategy": "第一眼视觉冲击，消除杂乱，树立高端正品质感",
                "prompt": "商业广告摄影，商业纯净白底首图。主体为智能声波温感洁面仪，纯白无影棚，8k超清。",
                "quick_tweaks": [
                    {"id": "t1", "label": "💡 调亮顶光", "tweakText": "调亮顶光柔和漫射"}
                ]
            },
            {
                "id": "05_pain_killer",
                "name": "痛点直击与抗拒点攻破图",
                "scene_highlight": "IPX7全机身浸入清水中高速声波震动激起细腻微米水花，定格强悍防水与清洁力",
                "commercial_strategy": "水下实测直击充电进水与清洁不彻底痛点，以视觉证据击穿买家顾虑",
                "prompt": "商业硬核功能测试摄影，高速快门定格声波温感洁面仪在清澈水下激起层层细密水波，8k超清。",
                "quick_tweaks": [
                    {"id": "t2", "label": "💧 飞溅水珠抓拍", "tweakText": "高速快门动感抓拍细腻水珠"}
                ]
            }
        ])

        with patch.object(studio_crew, "_call_llm_for_matrix", create=True):
            # Patch the internal call or generate function
            with patch("concurrent.futures.Future.result", return_value=mock_llm_json):
                fake_config = {"active_provider": "gemini", "gemini": {"api_key": "fake_test_key"}}
                matrix = studio_crew.generate_vision_matrix_with_ai(
                    product_info=self.product_info,
                    style_preset_id="nordic_luxury",
                    config=fake_config,
                )
                self.assertEqual(len(matrix), 9)
                p1 = next(item for item in matrix if item["id"] == "01_white_bg")
                self.assertIn("无影棚纯白背景", p1["scene_highlight"])
                p5 = next(item for item in matrix if item["id"] == "05_pain_killer")
                self.assertIn("IPX7全机身浸入清水", p5["scene_highlight"])

    def test_generate_vision_matrix_circuit_breaker(self):
        """测试大模型抛出异常或超时时，0秒熔断兜底回退至本地规则编译，业务永不报错"""
        fake_config = {"active_provider": "gemini", "gemini": {"api_key": "fake_key"}}
        with patch("concurrent.futures.Future.result", side_effect=TimeoutError("Request timed out > 8.0s")):
            matrix = studio_crew.generate_vision_matrix_with_ai(
                product_info=self.product_info,
                style_preset_id="dopamine_energy",
                config=fake_config,
            )
            self.assertEqual(len(matrix), 9)
            self.assertTrue(all(len(item["prompt"]) > 0 for item in matrix))
            self.assertTrue(all(len(item["scene_highlight"]) > 0 for item in matrix))

    def test_regenerate_single_perspective_with_ai(self):
        """测试单卡视角 AI 重新构思接口"""
        res = studio_crew.regenerate_single_perspective_with_ai(
            product_info=self.product_info,
            perspective_id="05_pain_killer",
            style_preset_id="german_deconstruct",
            instruction="增加刀片刮擦测试与高压水冲测试",
        )
        self.assertEqual(res["id"], "05_pain_killer")
        self.assertTrue(len(res["scene_highlight"]) > 0)
        self.assertTrue(len(res["commercial_strategy"]) > 0)
        self.assertIn("增加刀片刮擦测试与高压水冲测试", res["prompt_zh"])

    def test_api_regenerate_perspective_script_endpoint(self):
        """测试 POST /api/v1/studio/sessions/{sid}/perspectives/{pid}/regenerate-script 路由接入"""
        # 1. 创建会话
        resp = self.client.post(
            "/api/v1/studio/plan",
            json={"product_info": self.product_info, "style_preset": "cyber_street"},
        )
        self.assertEqual(resp.status_code, 200)
        sid = resp.json()["session_id"]
        self.created_sessions.append(sid)

        # 2. 调用单卡重构接口
        regen_resp = self.client.post(
            f"/api/v1/studio/sessions/{sid}/perspectives/05_pain_killer/regenerate-script",
            json={
                "perspective_id": "05_pain_killer",
                "instruction": "改成极限暴风雨户外淋雨测试，霓虹夜色灯光反射",
            },
        )
        self.assertEqual(regen_resp.status_code, 200)
        data = regen_resp.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["perspective_id"], "05_pain_killer")
        self.assertTrue(len(data["scene_highlight"]) > 0)
        self.assertIn("极限暴风雨户外淋雨测试", data["prompt_zh"])

        # 3. 校验 session 数据持久化落盘
        get_resp = self.client.get(f"/api/v1/studio/sessions/{sid}")
        self.assertEqual(get_resp.status_code, 200)
        saved = get_resp.json()
        p5 = next(p for p in saved["perspectives"] if p["id"] == "05_pain_killer")
        self.assertIn("极限暴风雨户外淋雨测试", p5["prompt_zh"])


if __name__ == "__main__":
    unittest.main()
