"""
Ecommerce Studio v2.0 - Frontend & Backend E2E Contract Integration Test Suite
Verifies end-to-end integration across Next.js 14 frontend contracts and FastAPI backend endpoints:
1. GET /api/v1/studio/style-presets matches frontend StylePreset TypeScript interface and constants.
2. POST /api/v1/studio/vision/extract-dossier matches VisionExtractDossierResponse interface and store actions.
3. POST /api/v1/studio/plan end-to-end session creation, style preset persistence, and 9-perspective matrix delivery.
"""

import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi.testclient import TestClient
from ecommerce_studio.api.main import app
from ecommerce_studio.api.schemas import ProductDossierExtracted
from ecommerce_studio.api.service import studio_service
from ecommerce_studio import session_manager, studio_crew
from ecommerce_studio.prompt_compiler import PromptMatrixCompiler


class TestFrontendBackendContractE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.created_sessions = []

    def tearDown(self):
        for sid in self.created_sessions:
            try:
                session_manager.delete_session(sid)
            except Exception:
                pass

    def test_01_style_presets_contract_matches_frontend_types(self):
        """验证后端 GET /style-presets 响应与前端 TypeScript StylePreset 接口 100% 对齐"""
        resp = self.client.get("/api/v1/studio/style-presets")
        self.assertEqual(resp.status_code, 200)
        presets = resp.json()

        # 前端定义的 5 大 StylePresetId
        frontend_preset_ids = [
            "minimalist_muji",
            "nordic_luxury",
            "german_deconstruct",
            "dopamine_energy",
            "cyber_street",
        ]
        self.assertEqual(len(presets), 5)

        for preset in presets:
            # 字段契约必须严格满足 frontend/src/types/session.ts 中的 StylePreset
            self.assertIn(preset["id"], frontend_preset_ids)
            self.assertIsInstance(preset["name"], str)
            self.assertIsInstance(preset["en_name"], str)
            self.assertIsInstance(preset["tagline"], str)
            self.assertIsInstance(preset["description"], str)
            self.assertIsInstance(preset["lighting"], str)
            self.assertIsInstance(preset["environment"], str)
            self.assertIsInstance(preset["camera"], str)
            self.assertIsInstance(preset["color_tone"], str)
            self.assertIsInstance(preset["anti_drift_rules"], list)
            self.assertIsInstance(preset["perspective_enhancements"], dict)

    def test_02_vision_extract_dossier_contract_matches_frontend_store(self):
        """验证 POST /vision/extract-dossier 响应与前端 useStudioStore 状态回填及高光标签完美兼容"""
        mock_dossier = ProductDossierExtracted(
            product_name="多功能轻量级随行温控杯",
            category="高品质水具 / 智能数码生活",
            material_features="食品级316不锈钢内胆、外壁微米级磨砂烤漆、LED触控数显",
            target_users="25-35岁高知通勤白领、商务差旅精英",
            pain_points="市面传统杯倒置渗水、保温时长不足、外壳易磕碰掉漆",
            visual_tags=["#曜石黑", "#磨砂质感", "#数显杯盖"],
            color_palette=["#09090B 曜石黑", "#71717A 钛合金灰"],
            confidence_score=0.95,
        )

        with patch.object(
            studio_service,
            "extract_dossier_from_image",
            new_callable=AsyncMock,
        ) as mock_extract:
            mock_extract.return_value = (mock_dossier, "gemini")

            fake_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 80
            resp = self.client.post(
                "/api/v1/studio/vision/extract-dossier",
                data={"category_hint": "保温杯"},
                files={"file": ("snap.jpg", fake_bytes, "image/jpeg")},
            )

            self.assertEqual(resp.status_code, 200)
            data = resp.json()

            # 前端 VisionExtractDossierResponse 结构验证
            self.assertTrue(data["success"])
            self.assertIsInstance(data["asset_url"], str)
            self.assertIsInstance(data["execution_time_ms"], int)
            self.assertIn(data["model_provider"], ["gemini", "openai", "rule_fallback"])

            # 前端 ProductDossierExtracted 结构验证
            dossier = data["dossier"]
            self.assertEqual(dossier["product_name"], "多功能轻量级随行温控杯")
            self.assertIsInstance(dossier["visual_tags"], list)
            self.assertEqual(dossier["visual_tags"], ["#曜石黑", "#磨砂质感", "#数显杯盖"])
            self.assertIsInstance(dossier["color_palette"], list)
            self.assertEqual(dossier["color_palette"], ["#09090B 曜石黑", "#71717A 钛合金灰"])

    def test_03_e2e_plan_with_style_preset_and_nine_perspectives(self):
        """验证前端 Step 1 提交选定流派后，后端策划推演与 9 视角提示词防漂移编译全流程"""
        product_info = {
            "name": "极简智能温控咖啡杯",
            "category": "精品水具/智能家居",
            "material_features": "316L医用不锈钢内胆、曜石黑哑光微米喷砂、LED触控数显",
            "target_users": "25-35岁都市白领与手冲咖啡爱好者",
            "pain_points": "传统保温杯倒置易漏水、开盖易烫嘴、外壳易磕碰刮花",
            "visual_tags": ["#曜石黑", "#磨砂质感"],
            "color_palette": ["#09090B 曜石黑"],
        }

        with patch.object(
            studio_crew,
            "run_phase_one",
        ) as mock_phase_one:
            mock_phase_one.return_value = (
                "# 商业全案策划报告",
                PromptMatrixCompiler.compile_matrix(product_info, "dopamine_energy"),
            )

            resp = self.client.post(
                "/api/v1/studio/plan",
                json={
                    "product_info": product_info,
                    "style_preset": "dopamine_energy",
                },
            )

            self.assertEqual(resp.status_code, 200)
            session = resp.json()
            sid = session["session_id"]
            self.created_sessions.append(sid)

            # 前端 StudioSession 必须持有 style_preset
            self.assertEqual(session["style_preset"], "dopamine_energy")
            self.assertEqual(len(session["perspectives"]), 9)

            # 验证多巴胺高饱和防漂移提示词注入
            p1_prompt = session["perspectives"][0]["prompt_zh"]
            self.assertIn("35mm", p1_prompt)
            self.assertIn("柠檬黄", p1_prompt)
            self.assertIn("波普", p1_prompt)
            self.assertIn("严禁昏暗暗调", p1_prompt)

            # 验证 GET /sessions 列表中 SessionSummary 包含 style_preset
            list_resp = self.client.get("/api/v1/studio/sessions")
            self.assertEqual(list_resp.status_code, 200)
            summaries = list_resp.json()
            target_summary = next((s for s in summaries if s["session_id"] == sid), None)
            self.assertIsNotNone(target_summary)
            self.assertEqual(target_summary.get("style_preset"), "dopamine_energy")


if __name__ == "__main__":
    unittest.main()
