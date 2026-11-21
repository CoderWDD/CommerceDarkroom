import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 将项目根目录与 studio 目录加入 Python 路径
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi.testclient import TestClient
from ecommerce_studio.api.main import app
from ecommerce_studio.api.service import canonicalize_perspective_id, normalize_session_data
from ecommerce_studio import session_manager, studio_crew


class TestFastAPIBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
        self.created_sessions = []

    def tearDown(self):
        for sid in self.created_sessions:
            session_manager.delete_session(sid)

    def test_01_health_and_root(self):
        """测试根路由与健康检查端点"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "online")
        self.assertEqual(data.get("service"), "Ecommerce Studio Commercial API Gateway")

        health_resp = self.client.get("/api/v1/studio/health")
        self.assertEqual(health_resp.status_code, 200)
        h_data = health_resp.json()
        self.assertEqual(h_data.get("status"), "ok")
        self.assertIn("active_provider", h_data)

    def test_02_config_endpoints(self):
        """测试系统配置获取与更新（含密钥脱敏）"""
        get_res = self.client.get("/api/v1/studio/config")
        self.assertEqual(get_res.status_code, 200)
        cfg = get_res.json()
        self.assertIn("active_provider", cfg)
        if cfg.get("gemini", {}).get("api_key"):
            self.assertIn("****", cfg["gemini"]["api_key"])

        # 测试更新配置
        put_res = self.client.put("/api/v1/studio/config", json={"active_provider": "gemini"})
        self.assertEqual(put_res.status_code, 200)
        self.assertEqual(put_res.json().get("active_provider"), "gemini")

    def test_03_session_lifecycle(self):
        """测试专案的创建、查询、获取与删除"""
        # 1. 创建
        create_res = self.client.post(
            "/api/v1/studio/sessions",
            json={
                "name": "钛空舱保温杯商业策划专案",
                "product_info": {
                    "product_name": "钛空舱智能温控咖啡保温杯",
                    "category": "水具/智能家居",
                    "material_features": "316L医用级不锈钢内胆，哑光喷砂曜石黑，LED数显杯盖",
                    "target_users": "25-35岁都市白领与手冲咖啡爱好者",
                    "pain_points": "传统保温杯倒置易漏水，杯口难清洗，开盖容易烫嘴",
                },
            },
        )
        self.assertEqual(create_res.status_code, 200)
        session = create_res.json()
        session_id = session.get("session_id")
        self.assertTrue(session_id.startswith("sess_"))
        self.created_sessions.append(session_id)

        # 检查是否自动补齐 9 大商业视角
        perspectives = session.get("perspectives", [])
        self.assertEqual(len(perspectives), 9)
        self.assertEqual(perspectives[0]["id"], "01_white_bg")
        self.assertEqual(perspectives[0]["name"], "商业纯净白底首图")
        self.assertEqual(perspectives[0]["tag"], "CTR点击率收割机")

        # 2. 列表查询
        list_res = self.client.get("/api/v1/studio/sessions")
        self.assertEqual(list_res.status_code, 200)
        sessions_list = list_res.json()
        self.assertTrue(any(s["session_id"] == session_id for s in sessions_list))

        # 3. 单个获取
        get_res = self.client.get(f"/api/v1/studio/sessions/{session_id}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["name"], "钛空舱保温杯商业策划专案")

        # 4. 删除
        del_res = self.client.delete(f"/api/v1/studio/sessions/{session_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # 再次获取应当 404
        get_after = self.client.get(f"/api/v1/studio/sessions/{session_id}")
        self.assertEqual(get_after.status_code, 404)

    @patch("ecommerce_studio.studio_crew.run_phase_one")
    def test_04_plan_generation_sync_and_stream(self, mock_phase_one):
        """测试 Step 1 9 大商业视觉矩阵策划推演 (JSON & SSE)"""
        prod_info = {
            "name": "钛空舱极简保温杯",
            "category": "精品水具",
            "target_audience": "都市通勤白领",
            "pain_points": "倒置易漏水、杯底掉漆",
        }
        mock_phase_one.return_value = (
            "多智能体深度洞察：钛空舱极简保温杯商业策划案",
            studio_crew.build_default_prompt_matrix(prod_info),
        )

        # 1. 同步 JSON 推演
        plan_res = self.client.post(
            "/api/v1/studio/plan",
            json={"product_info": prod_info, "stream": False},
        )
        self.assertEqual(plan_res.status_code, 200)
        plan_data = plan_res.json()
        session_id = plan_data["session_id"]
        self.created_sessions.append(session_id)

        perspectives = plan_data.get("perspectives", [])
        self.assertEqual(len(perspectives), 9)
        # 验证提示词为中文商业摄影指令且包含商品名称
        self.assertIn("保温杯", perspectives[0]["prompt_zh"])

        # 验证 strategy_summary
        strat = plan_data.get("strategy_summary", {})
        self.assertIn("tone", strat)
        self.assertIn("usp", strat)
        self.assertTrue(len(strat.get("color_palette", [])) > 0)

        # 2. SSE 流式推演
        stream_res = self.client.post(
            "/api/v1/studio/plan",
            json={"session_id": session_id, "product_info": prod_info, "stream": True},
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(stream_res.status_code, 200)
        self.assertIn("text/event-stream", stream_res.headers.get("content-type", ""))
        stream_text = stream_res.text
        self.assertIn("event: progress", stream_text)
        self.assertIn("event: complete", stream_text)

    @patch("ecommerce_studio.studio_crew.refine_prompt_with_ai")
    def test_05_prompt_editing_and_ai_refinement(self, mock_refine_ai):
        """测试中文镜头语言手动更新与 AI 灵感润色"""
        mock_refine_ai.return_value = "商业摄影棚高端布光，深色曜石台面，侧逆暖阳丁达尔光束，8k超清。"
        create_res = self.client.post(
            "/api/v1/studio/sessions",
            json={"name": "测试提示词编辑专案"},
        )
        session_id = create_res.json()["session_id"]
        self.created_sessions.append(session_id)

        # 1. PUT 手动编辑
        new_prompt = "商业纯白无影摄影棚背景，钛空舱保温杯居中站立，右侧45度轮廓柔光箱，镜面倒影通透细腻，8k分辨率。"
        edit_res = self.client.put(
            f"/api/v1/studio/sessions/{session_id}/perspectives/01_white_bg/prompt",
            json={"prompt_zh": new_prompt},
        )
        self.assertEqual(edit_res.status_code, 200)
        self.assertEqual(edit_res.json()["prompt_zh"], new_prompt)

        # 获取 session 验证更新持久化
        sess_get = self.client.get(f"/api/v1/studio/sessions/{session_id}").json()
        self.assertEqual(sess_get["perspectives"][0]["prompt_zh"], new_prompt)

        # 2. AI 顾问润色
        refine_res = self.client.post(
            f"/api/v1/studio/sessions/{session_id}/perspectives/01_white_bg/refine-prompt",
            json={"instruction": "将背景改为深色曜石台面，增加一缕清晨侧逆暖阳丁达尔光束"},
        )
        self.assertEqual(refine_res.status_code, 200)
        refined_text = refine_res.json()["refined_prompt"]
        self.assertTrue(len(refined_text) > 20)

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_06_non_destructive_versioning_and_rollback(self, mock_generate_image):
        """
        核心验收测试：非破坏性版本快照生成 (v1 -> v2) 与双向后悔药一键回滚
        """
        # 创建临时伪造图片
        tmp_dir = tempfile.mkdtemp()
        v1_file = os.path.join(tmp_dir, "v1_test.jpg")
        v2_file = os.path.join(tmp_dir, "v2_test.jpg")
        with open(v1_file, "wb") as f:
            f.write(b"mock_v1_image_bytes")
        with open(v2_file, "wb") as f:
            f.write(b"mock_v2_image_bytes")

        # 1. 创建会话
        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "版本回滚专案"})
        session_id = create_res.json()["session_id"]
        self.created_sessions.append(session_id)

        # 2. 渲染第 1 版 (v1)
        mock_generate_image.return_value = v1_file
        v1_prompt = "商业纯净白底首图 v1 镜头语言"
        render_v1_res = self.client.post(
            f"/api/v1/studio/sessions/{session_id}/perspectives/01_white_bg/render-version",
            json={
                "prompt_zh": v1_prompt,
                "change_reason": "初始大片首轮渲染",
                "trigger_type": "batch_initial",
            },
        )
        self.assertEqual(render_v1_res.status_code, 200)
        v1_data = render_v1_res.json()
        self.assertEqual(v1_data["version"]["version_id"], "v1")
        self.assertEqual(v1_data["version"]["version_num"], 1)
        self.assertIn("/output/", v1_data["version"]["image_url"])

        # 3. 渲染第 2 版 (v2) - AI 微调出图
        mock_generate_image.return_value = v2_file
        v2_prompt = "商业纯净白底首图 v2 增加幽蓝LED数显微光"
        render_v2_res = self.client.post(
            "/api/v1/studio/refine-slot",
            json={
                "session_id": session_id,
                "perspective_id": "01_white_bg",
                "prompt_zh": v2_prompt,
                "change_reason": "二次调词：增加幽蓝数显",
                "trigger_type": "manual_edit",
            },
        )
        self.assertEqual(render_v2_res.status_code, 200)
        v2_data = render_v2_res.json()
        self.assertEqual(v2_data["version"]["version_id"], "v2")
        self.assertEqual(v2_data["version"]["version_num"], 2)

        # 验证会话中 versions 包含两个版本，且 active_version_id == "v2"
        sess = self.client.get(f"/api/v1/studio/sessions/{session_id}").json()
        card = sess["perspectives"][0]
        self.assertEqual(card["active_version_id"], "v2")
        self.assertEqual(len(card["versions"]), 2)
        self.assertEqual(card["versions"][0]["version_id"], "v1")
        self.assertEqual(card["versions"][1]["version_id"], "v2")
        self.assertEqual(card["prompt_zh"], v2_prompt)

        # 4. 执行双向后悔药回滚 -> 回滚至 v1
        rollback_res = self.client.post(
            "/api/v1/studio/rollback",
            json={
                "session_id": session_id,
                "perspective_id": "01_white_bg",
                "version_id": "v1",
            },
        )
        self.assertEqual(rollback_res.status_code, 200)
        rb_data = rollback_res.json()
        self.assertTrue(rb_data["success"])
        self.assertEqual(rb_data["active_version_id"], "v1")
        self.assertEqual(rb_data["restored_prompt"], v1_prompt)

        # 5. 验证回滚后：active_version_id恢复为v1，prompt恢复为v1，且versions中的v2依然完好保留！
        sess_after = self.client.get(f"/api/v1/studio/sessions/{session_id}").json()
        card_after = sess_after["perspectives"][0]
        self.assertEqual(card_after["active_version_id"], "v1")
        self.assertEqual(card_after["prompt_zh"], v1_prompt)
        self.assertEqual(len(card_after["versions"]), 2, "回滚后必须完整保留全部历史版本快照链条！")

        shutil.rmtree(tmp_dir, ignore_errors=True)

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_07_batch_render_stream_sse(self, mock_generate_image):
        """测试 3x3 批量出图 SSE 流式渐进传输"""
        tmp_dir = tempfile.mkdtemp()
        mock_file = os.path.join(tmp_dir, "batch_test.jpg")
        with open(mock_file, "wb") as f:
            f.write(b"mock_batch_image_bytes")
        mock_generate_image.return_value = mock_file

        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "批量出图专案"})
        session_id = create_res.json()["session_id"]
        self.created_sessions.append(session_id)

        # 针对前 2 个机位进行批量并发渲染
        sse_res = self.client.post(
            "/api/v1/studio/render-batch",
            json={
                "session_id": session_id,
                "concurrency": 2,
                "perspective_ids": ["01_white_bg", "02_scene"],
            },
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(sse_res.status_code, 200)
        self.assertIn("text/event-stream", sse_res.headers.get("content-type", ""))
        text = sse_res.text
        self.assertIn("event: start", text)
        self.assertIn("event: perspective_start", text)
        self.assertIn("event: perspective_success", text)
        self.assertIn("event: complete", text)

        shutil.rmtree(tmp_dir, ignore_errors=True)

    @patch("ecommerce_studio.session_manager.chat_with_agent")
    def test_08_copilot_chat(self, mock_chat):
        """测试首席视觉顾问对话与 ActionChip 镜头建议注入"""
        mock_chat.return_value = (
            "主理人您好，我是您的首席视觉顾问。建议针对当前机位加强侧光对比。\n"
            "【推荐镜头方案】：极简商业摄影棚背景，钛空舱保温杯居中，水珠飞溅定格，8k超清画质。"
        )
        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "顾问对话专案"})
        session_id = create_res.json()["session_id"]
        self.created_sessions.append(session_id)

        # 1. 同步 JSON 对话
        chat_res = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={
                "session_id": session_id,
                "message": "针对 05 痛点直击机位，如何通过视觉表现展现绝对防漏？",
                "context": {"step": 3, "active_perspective_id": "05_pain_killer"},
                "stream": False,
            },
        )
        self.assertEqual(chat_res.status_code, 200)
        c_data = chat_res.json()
        self.assertEqual(c_data["role"], "assistant")
        self.assertTrue(len(c_data["content"]) > 10)

        # 2. SSE 流式对话
        stream_chat = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={
                "session_id": session_id,
                "message": "请优化当前机位的光影",
                "context": {"step": 3, "active_perspective_id": "01_white_bg"},
                "stream": True,
            },
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(stream_chat.status_code, 200)
        self.assertIn("text/event-stream", stream_chat.headers.get("content-type", ""))
        self.assertIn("event: delta", stream_chat.text)
        self.assertIn("event: done", stream_chat.text)

    def test_09_asset_upload(self):
        """测试实物资产上传与多模态标签解析"""
        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "资产上传专案"})
        session_id = create_res.json()["session_id"]
        self.created_sessions.append(session_id)

        fake_file_content = b"fake_jpg_binary_content"
        upload_res = self.client.post(
            f"/api/v1/studio/sessions/{session_id}/assets/upload",
            files={"file": ("product_ref.jpg", io.BytesIO(fake_file_content), "image/jpeg")},
            data={"is_primary": "true"},
        )
        self.assertEqual(upload_res.status_code, 200)
        up_data = upload_res.json()
        self.assertTrue(up_data["success"])
        self.assertTrue(up_data["is_primary"])
        self.assertIn("/output/uploads/", up_data["url"])
        self.assertTrue(len(up_data["vision_tags"]) >= 2)

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_10_export_zip_and_markdown(self, mock_generate_image):
        """测试全套定稿物料 ZIP 规范打包与 Markdown 报告导出"""
        tmp_dir = tempfile.mkdtemp()
        mock_file = os.path.join(tmp_dir, "export_test.jpg")
        with open(mock_file, "wb") as f:
            f.write(b"mock_image_data_for_zip")
        mock_generate_image.return_value = mock_file

        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "导出测试专案"})
        session_id = create_res.json()["session_id"]
        self.created_sessions.append(session_id)

        # 渲染 1 张图以便打包
        self.client.post(
            f"/api/v1/studio/sessions/{session_id}/perspectives/01_white_bg/render-version",
            json={"prompt_zh": "测试首图", "change_reason": "出图用于导出"},
        )

        # 1. 导出 ZIP
        zip_res = self.client.get(f"/api/v1/studio/sessions/{session_id}/export/zip")
        self.assertEqual(zip_res.status_code, 200)
        self.assertEqual(zip_res.headers.get("content-type"), "application/zip")
        self.assertTrue(len(zip_res.content) > 0)

        # 2. 导出 Markdown
        md_res = self.client.get(f"/api/v1/studio/sessions/{session_id}/export/markdown")
        self.assertEqual(md_res.status_code, 200)
        self.assertIn("text/markdown", md_res.headers.get("content-type", ""))
        self.assertIn("商业级电商视觉全案策划报告", md_res.text)
        self.assertIn("01_white_bg", md_res.text)

        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
