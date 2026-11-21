"""
Ecommerce Studio - Comprehensive FastAPI Endpoints Test Suite
Air-tight, high-coverage integration and edge-case tests for all Studio API endpoints.
"""

import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure project and studio roots are on sys.path
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from fastapi.testclient import TestClient
from ecommerce_studio.api.main import app
from ecommerce_studio.api.service import canonicalize_perspective_id, studio_service
from ecommerce_studio import config_manager, session_manager, studio_crew


class TestFastAPIEndpointsComprehensive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.base_dir = Path(__file__).resolve().parent
        cls.output_dir = cls.base_dir / "output"
        cls.output_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.created_sessions = []
        self.created_temp_dirs = []

    def tearDown(self):
        for sid in self.created_sessions:
            try:
                session_manager.delete_session(sid)
            except Exception:
                pass
        for tdir in self.created_temp_dirs:
            shutil.rmtree(tdir, ignore_errors=True)

    # =========================================================================
    # 1. Root & Health Check Endpoints
    # =========================================================================

    def test_root_and_health_check(self):
        """测试根路径元数据与健康检查响应结构"""
        root_res = self.client.get("/")
        self.assertEqual(root_res.status_code, 200)
        root_data = root_res.json()
        self.assertEqual(root_data.get("status"), "online")
        self.assertIn("version", root_data)
        self.assertIn("service", root_data)

        health_res = self.client.get("/api/v1/studio/health")
        self.assertEqual(health_res.status_code, 200)
        h_data = health_res.json()
        self.assertEqual(h_data.get("status"), "ok")
        self.assertIn("active_provider", h_data)
        self.assertIn("timestamp", h_data)

    # =========================================================================
    # 2. Session Lifecycle & Boundary Edge Cases
    # =========================================================================

    def test_session_lifecycle_crud(self):
        """测试专案生命周期全流程：空专案创建、指定信息创建、列表查询与删除"""
        # 1. 默认空请求创建
        res_empty = self.client.post("/api/v1/studio/sessions", json={})
        self.assertEqual(res_empty.status_code, 200)
        s_empty = res_empty.json()
        sid_empty = s_empty["session_id"]
        self.created_sessions.append(sid_empty)
        self.assertTrue(sid_empty.startswith("sess_"))
        self.assertEqual(len(s_empty.get("perspectives", [])), 9)

        # 2. 携带完整商业信息创建
        payload = {
            "name": "极简钛空杯策划案",
            "product_info": {
                "name": "钛空保温杯",
                "category": "精品水具",
                "material_features": "316医用不锈钢",
                "target_audience": "职场精英",
                "pain_points": "倒置易漏水",
            },
        }
        res_full = self.client.post("/api/v1/studio/sessions", json=payload)
        self.assertEqual(res_full.status_code, 200)
        s_full = res_full.json()
        sid_full = s_full["session_id"]
        self.created_sessions.append(sid_full)
        self.assertEqual(s_full["name"], "极简钛空杯策划案")
        self.assertEqual(s_full["product_info"]["name"], "钛空保温杯")

        # 3. 列表查询验证
        list_res = self.client.get("/api/v1/studio/sessions")
        self.assertEqual(list_res.status_code, 200)
        sessions_list = list_res.json()
        session_ids = [s["session_id"] for s in sessions_list]
        self.assertIn(sid_empty, session_ids)
        self.assertIn(sid_full, session_ids)

        # 4. 获取单个专案
        get_res = self.client.get(f"/api/v1/studio/sessions/{sid_full}")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["session_id"], sid_full)

        # 5. 删除专案
        del_res = self.client.delete(f"/api/v1/studio/sessions/{sid_full}")
        self.assertEqual(del_res.status_code, 200)
        self.assertTrue(del_res.json()["success"])

        # 再次获取应当 404
        get_after = self.client.get(f"/api/v1/studio/sessions/{sid_full}")
        self.assertEqual(get_after.status_code, 404)

    def test_session_boundary_not_found_cases(self):
        """测试对不存在 session_id 的各种操作均返回 404 或边界拦截"""
        fake_id = "sess_non_existent_999999"

        # 1. 获取不存在专案
        res_get = self.client.get(f"/api/v1/studio/sessions/{fake_id}")
        self.assertEqual(res_get.status_code, 404)

        # 2. 删除不存在专案
        res_del = self.client.delete(f"/api/v1/studio/sessions/{fake_id}")
        self.assertEqual(res_del.status_code, 404)

        # 3. 上传资产到不存在专案
        res_upload = self.client.post(
            f"/api/v1/studio/sessions/{fake_id}/assets/upload",
            files={"file": ("test.jpg", b"dummy_content", "image/jpeg")},
        )
        self.assertEqual(res_upload.status_code, 404)

        # 4. 更新不存在专案的提示词
        res_update_p = self.client.put(
            f"/api/v1/studio/sessions/{fake_id}/perspectives/01_white_bg/prompt",
            json={"prompt_zh": "新提示词"},
        )
        self.assertEqual(res_update_p.status_code, 404)

        # 5. 润色不存在专案的提示词
        res_refine = self.client.post(
            f"/api/v1/studio/sessions/{fake_id}/perspectives/01_white_bg/refine-prompt",
            json={"instruction": "增强质感"},
        )
        self.assertEqual(res_refine.status_code, 404)

        # 6. 单视角渲染不存在的专案
        res_render = self.client.post(
            f"/api/v1/studio/sessions/{fake_id}/perspectives/01_white_bg/render-version",
            json={"prompt_zh": "测试渲染"},
        )
        self.assertEqual(res_render.status_code, 404)

        # 7. 回滚不存在的专案
        res_rollback = self.client.post(
            f"/api/v1/studio/sessions/{fake_id}/perspectives/01_white_bg/rollback",
            json={"version_id": "v1"},
        )
        self.assertEqual(res_rollback.status_code, 404)

        # 8. 导出不存在的专案 ZIP 与 Markdown
        res_zip = self.client.get(f"/api/v1/studio/sessions/{fake_id}/export/zip")
        self.assertEqual(res_zip.status_code, 404)
        res_md = self.client.get(f"/api/v1/studio/sessions/{fake_id}/export/markdown")
        self.assertEqual(res_md.status_code, 404)

    # =========================================================================
    # 3. /api/v1/studio/plan Validation & Error Handling
    # =========================================================================

    def test_plan_validation_errors(self):
        """测试 /plan 接口参数校验失败时的 422 响应"""
        # 1. 缺少 product_info 关键字段
        res = self.client.post("/api/v1/studio/plan", json={})
        self.assertEqual(res.status_code, 422)

        # 2. product_info 类型非法 (期望 dict，传入 string)
        res_bad_type = self.client.post("/api/v1/studio/plan", json={"product_info": "not_a_dict"})
        self.assertEqual(res_bad_type.status_code, 422)

    @patch("ecommerce_studio.studio_crew.run_phase_one")
    def test_plan_sync_and_stream_success(self, mock_phase_one):
        """测试 /plan 同步与 SSE 流式推演正确返回 9 视角与策划摘要"""
        prod_info = {
            "name": "降噪无线头戴耳机",
            "category": "数码影音",
            "material_features": "蛋白皮耳罩、磨砂碳纤维头梁",
            "target_audience": "通勤音乐发烧友",
            "pain_points": "压头夹耳、降噪耳压感强",
        }
        mock_matrix = studio_crew.build_default_prompt_matrix(prod_info)
        mock_phase_one.return_value = ("耳机深度商业洞察方案", mock_matrix)

        # 1. 同步生成
        res_sync = self.client.post(
            "/api/v1/studio/plan",
            json={"product_info": prod_info, "stream": False},
        )
        self.assertEqual(res_sync.status_code, 200)
        data = res_sync.json()
        sid = data["session_id"]
        self.created_sessions.append(sid)

        self.assertEqual(len(data.get("perspectives", [])), 9)
        self.assertIn("strategy_summary", data)
        self.assertTrue(len(data["strategy_summary"].get("color_palette", [])) > 0)

        # 2. SSE 流式推演
        res_stream = self.client.post(
            "/api/v1/studio/plan",
            json={"session_id": sid, "product_info": prod_info, "stream": True},
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(res_stream.status_code, 200)
        self.assertIn("text/event-stream", res_stream.headers.get("content-type", ""))
        stream_text = res_stream.text
        self.assertIn("event: progress", stream_text)
        self.assertIn("stage", stream_text)
        self.assertIn("event: complete", stream_text)

    @patch("ecommerce_studio.studio_crew.run_phase_one")
    def test_plan_fallback_on_model_exception(self, mock_phase_one):
        """测试大模型推演发生异常时，接口通过模板引擎优雅兜底不崩溃"""
        mock_phase_one.side_effect = RuntimeError("LLM API Rate Limit Exceeded")
        prod_info = {"name": "自发热眼罩", "category": "个护健康"}

        res = self.client.post(
            "/api/v1/studio/plan",
            json={"product_info": prod_info, "stream": False},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.created_sessions.append(data["session_id"])
        # 验证兜底生成了完整的 9 视角
        self.assertEqual(len(data.get("perspectives", [])), 9)
        self.assertIn("自发热眼罩", data["perspectives"][0]["prompt_zh"])

    # =========================================================================
    # 4. /api/v1/studio/render-batch Parameter Boundaries & SSE Format
    # =========================================================================

    def test_render_batch_validation_and_missing_session(self):
        """测试 /render-batch 参数缺失与非存在 session 时的校验"""
        # 缺少 session_id
        res_missing = self.client.post("/api/v1/studio/render-batch", json={})
        self.assertEqual(res_missing.status_code, 422)

        # 传入不存在的 session_id，SSE 应当推送 event: error
        res_fake = self.client.post(
            "/api/v1/studio/render-batch",
            json={"session_id": "sess_fake_not_exists"},
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(res_fake.status_code, 200)
        self.assertIn("event: error", res_fake.text)
        self.assertIn("不存在", res_fake.text)

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_render_batch_boundaries_and_sse_events(self, mock_generate_image):
        """测试批量出图的并发边界、画幅比例、机位过滤与完整的 SSE 事件流格式"""
        # 准备假图文件
        tdir = tempfile.mkdtemp()
        self.created_temp_dirs.append(tdir)
        fake_img = os.path.join(tdir, "test_render.jpg")
        with open(fake_img, "wb") as f:
            f.write(b"fake_image_bytes")
        mock_generate_image.return_value = fake_img

        # 创建测试专案
        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "批量边界测试专案"})
        sid = create_res.json()["session_id"]
        self.created_sessions.append(sid)

        # 1. 测试指定 perspective_ids 过滤与并发度、画幅比例边界
        sse_res = self.client.post(
            "/api/v1/studio/render-batch",
            json={
                "session_id": sid,
                "aspect_ratio": "16:9",
                "concurrency": 2,
                "perspective_ids": ["01_white_bg", "03_detail"],
            },
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(sse_res.status_code, 200)
        self.assertIn("text/event-stream", sse_res.headers.get("content-type", ""))
        text = sse_res.text

        # 验证 SSE 标准事件流规范
        self.assertIn("event: start\ndata:", text)
        self.assertIn('"total": 2', text)
        self.assertIn('"aspect_ratio": "16:9"', text)
        self.assertIn("event: perspective_start\ndata:", text)
        self.assertIn("event: perspective_success\ndata:", text)
        self.assertIn("event: complete\ndata:", text)

        # 2. 测试当生图工具抛出异常时的 perspective_error 事件
        mock_generate_image.side_effect = Exception("GPU out of memory")
        sse_err_res = self.client.post(
            "/api/v1/studio/render-batch",
            json={
                "session_id": sid,
                "concurrency": 1,
                "perspective_ids": ["02_scene"],
            },
        )
        self.assertEqual(sse_err_res.status_code, 200)
        err_text = sse_err_res.text
        self.assertIn("event: perspective_error\ndata:", err_text)
        self.assertIn("GPU out of memory", err_text)
        self.assertIn("event: complete\ndata:", err_text)

    # =========================================================================
    # 5. /api/v1/studio/refine-slot & Render Version
    # =========================================================================

    def test_refine_slot_parameter_boundaries(self):
        """测试 refine-slot 缺少必要参数时的校验"""
        # 1. 缺少 session_id 或 perspective_id
        res_missing = self.client.post("/api/v1/studio/refine-slot", json={})
        self.assertEqual(res_missing.status_code, 400)

        # 2. 只有 session_id 缺少 perspective_id
        res_no_pid = self.client.post(
            "/api/v1/studio/refine-slot", json={"session_id": "some_sess"}
        )
        self.assertEqual(res_no_pid.status_code, 400)

        # 3. 只有 perspective_id 缺少 session_id
        res_no_sid = self.client.post(
            "/api/v1/studio/refine-slot", json={"perspective_id": "01_white_bg"}
        )
        self.assertEqual(res_no_sid.status_code, 400)

    @patch("ecommerce_studio.studio_crew.refine_prompt_with_ai")
    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_refine_slot_with_custom_feedback(self, mock_gen_img, mock_refine_ai):
        """测试 refine-slot 携带用户自定义指令时的 AI 润色与出图新版本追加"""
        mock_refine_ai.return_value = "润色后的商业摄影提示词：增加暖光侧影与微距金属倒角。"
        tdir = tempfile.mkdtemp()
        self.created_temp_dirs.append(tdir)
        fake_img = os.path.join(tdir, "refine_v1.jpg")
        with open(fake_img, "wb") as f:
            f.write(b"refine_v1_bytes")
        mock_gen_img.return_value = fake_img

        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "微调专案"})
        sid = create_res.json()["session_id"]
        self.created_sessions.append(sid)

        # 带有 user_feedback / instruction 的 refine-slot
        res = self.client.post(
            "/api/v1/studio/refine-slot",
            json={
                "session_id": sid,
                "perspective_id": "01_white_bg",
                "instruction": "增强侧逆光暖阳与金属光泽",
                "aspect_ratio": "3:4",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        ver = data["version"]
        self.assertEqual(ver["version_id"], "v1")
        self.assertEqual(ver["aspect_ratio"], "3:4")
        self.assertIn("AI微调重绘", ver["change_reason"])

        # 带有 instruction 以及前端透传的现有 prompt_zh 时，同样能触发 AI 润色并出图
        res_with_prompt = self.client.post(
            "/api/v1/studio/refine-slot",
            json={
                "session_id": sid,
                "perspective_id": "01_white_bg",
                "prompt_zh": "旧版白底图提示词",
                "instruction": "背景换成大理石",
                "aspect_ratio": "1:1",
            },
        )
        self.assertEqual(res_with_prompt.status_code, 200)
        data2 = res_with_prompt.json()
        self.assertEqual(data2["version"]["version_id"], "v2")

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_refine_slot_auto_heals_unpersisted_session_and_aliases(self, mock_gen_img):
        """测试 refine-slot 对前端临时未落盘 session_id 的自愈创建及前端别名(如 03_macro)的自动归一化"""
        tdir = tempfile.mkdtemp()
        self.created_temp_dirs.append(tdir)
        fake_img = os.path.join(tdir, "macro_v1.jpg")
        with open(fake_img, "wb") as f:
            f.write(b"macro_v1_bytes")
        mock_gen_img.return_value = fake_img

        unpersisted_sid = f"sess_{int(time.time())}_init"
        self.created_sessions.append(unpersisted_sid)

        # 客户端未落盘 session 且使用前端别名 03_macro 触发单镜头微调渲染
        res = self.client.post(
            "/api/v1/studio/refine-slot",
            json={
                "session_id": unpersisted_sid,
                "perspective_id": "03_macro",
                "instruction": "突出金属边缘微距高光",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        # 验证别名被正确归一化为 03_detail
        self.assertEqual(data["perspective_id"], "03_detail")
        self.assertIsNotNone(data["version"])
        self.assertEqual(data["version"]["version_id"], "v1")

    # =========================================================================
    # 6. /api/v1/studio/rollback Edge Cases & Rejected Version ID
    # =========================================================================

    def test_rollback_parameter_validation(self):
        """测试回滚接口参数缺失拦截"""
        # 缺少 version_id
        res_no_vid = self.client.post(
            "/api/v1/studio/rollback",
            json={"session_id": "sess_1", "perspective_id": "01_white_bg"},
        )
        self.assertEqual(res_no_vid.status_code, 422)

        # 缺少 session_id
        res_no_sid = self.client.post(
            "/api/v1/studio/rollback",
            json={"perspective_id": "01_white_bg", "version_id": "v1"},
        )
        self.assertEqual(res_no_sid.status_code, 400)

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_rollback_invalid_version_rejected(self, mock_gen_img):
        """核心 edge case：测试回滚至不存在的非法版本 ID 时被 404 正确拒绝"""
        tdir = tempfile.mkdtemp()
        self.created_temp_dirs.append(tdir)
        f_img = os.path.join(tdir, "v1.jpg")
        with open(f_img, "wb") as f:
            f.write(b"v1_data")
        mock_gen_img.return_value = f_img

        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "回滚边界专案"})
        sid = create_res.json()["session_id"]
        self.created_sessions.append(sid)

        # 先出第 1 版
        self.client.post(
            f"/api/v1/studio/sessions/{sid}/perspectives/01_white_bg/render-version",
            json={"prompt_zh": "v1 prompt", "change_reason": "init"},
        )

        # 尝试回滚到不存在的 v999 -> 必须返回 404
        rb_fake = self.client.post(
            "/api/v1/studio/rollback",
            json={
                "session_id": sid,
                "perspective_id": "01_white_bg",
                "version_id": "v999",
            },
        )
        self.assertEqual(rb_fake.status_code, 404)
        self.assertIn("未找到", rb_fake.json().get("detail", ""))

        # 尝试回滚不存在的 perspective_id -> 必须返回 404
        rb_fake_pid = self.client.post(
            "/api/v1/studio/rollback",
            json={
                "session_id": sid,
                "perspective_id": "invalid_perspective_99",
                "version_id": "v1",
            },
        )
        self.assertEqual(rb_fake_pid.status_code, 404)

    # =========================================================================
    # 7. /api/v1/studio/config GET, PUT, POST & Persistence
    # =========================================================================

    def test_config_endpoints_get_put_post_persistence(self):
        """测试系统配置获取（密钥脱敏）、PUT/POST 更新与持久化保存"""
        # 1. GET 配置检查脱敏
        get_res = self.client.get("/api/v1/studio/config")
        self.assertEqual(get_res.status_code, 200)
        cfg = get_res.json()
        self.assertIn("active_provider", cfg)
        orig_provider = cfg.get("active_provider")

        # 2. PUT 更新 active_provider
        target_provider = "openai" if orig_provider != "openai" else "gemini"
        put_res = self.client.put(
            "/api/v1/studio/config",
            json={"active_provider": target_provider},
        )
        self.assertEqual(put_res.status_code, 200)
        self.assertTrue(put_res.json().get("success"))
        self.assertEqual(put_res.json().get("active_provider"), target_provider)

        # 验证 GET 反映了更新
        cfg_after_put = self.client.get("/api/v1/studio/config").json()
        self.assertEqual(cfg_after_put.get("active_provider"), target_provider)

        # 3. POST 更新并验证持久化
        post_res = self.client.post(
            "/api/v1/studio/config",
            json={"active_provider": orig_provider},
        )
        self.assertEqual(post_res.status_code, 200)
        self.assertEqual(post_res.json().get("active_provider"), orig_provider)

        # 验证磁盘持久化 user_config.json
        user_cfg_path = Path(__file__).resolve().parent / "user_config.json"
        self.assertTrue(user_cfg_path.exists())
        with open(user_cfg_path, "r", encoding="utf-8") as f:
            disk_data = json.load(f)
        self.assertEqual(disk_data.get("active_provider"), orig_provider)

    # =========================================================================
    # 8. /api/v1/studio/copilot/chat with Session Context & History
    # =========================================================================

    def test_copilot_chat_missing_session(self):
        """测试 copilot chat 缺失 session_id 或 session 不存在时的响应"""
        # 缺失 session_id
        res_no_sid = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={"message": "你好"},
        )
        self.assertEqual(res_no_sid.status_code, 422)

        # 同步调用非存在的 session
        res_fake_sync = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={"session_id": "sess_fake_999", "message": "你好", "stream": False},
        )
        self.assertEqual(res_fake_sync.status_code, 404)

        # SSE 流式调用非存在的 session -> 返回 event: error
        res_fake_stream = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={"session_id": "sess_fake_999", "message": "你好", "stream": True},
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(res_fake_stream.status_code, 200)
        self.assertIn("event: error", res_fake_stream.text)

    @patch("ecommerce_studio.session_manager.chat_with_agent")
    def test_copilot_chat_sync_and_stream_with_context(self, mock_chat):
        """测试 copilot 对话（同步与流式）的情境感知与 ActionChip 方案注入"""
        mock_chat.return_value = (
            "顾问回复：建议微调布光。\n"
            "【推荐镜头方案】：深色大理石台面，杯身凝结晨间水珠，45度侧光，8k超清。"
        )
        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "顾问情境专案"})
        sid = create_res.json()["session_id"]
        self.created_sessions.append(sid)

        # 1. 同步请求，验证历史记录追加
        sync_res = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={
                "session_id": sid,
                "message": "01 白底图如何更有质感？",
                "context": {"step": 2, "active_perspective_id": "01_white_bg"},
                "stream": False,
            },
        )
        self.assertEqual(sync_res.status_code, 200)
        sync_data = sync_res.json()
        self.assertEqual(sync_data["role"], "assistant")
        self.assertIn("建议微调布光", sync_data["content"])

        # 检查专案数据中包含两条对话历史
        sess_data = self.client.get(f"/api/v1/studio/sessions/{sid}").json()
        self.assertEqual(len(sess_data.get("chat_history", [])), 2)

        # 2. SSE 流式请求，验证 delta, action_chip 和 done 事件
        stream_res = self.client.post(
            "/api/v1/studio/copilot/chat",
            json={
                "session_id": sid,
                "message": "请为当前机位推荐布景",
                "context": {"step": 3, "active_perspective_id": "01_white_bg"},
                "stream": True,
            },
            headers={"Accept": "text/event-stream"},
        )
        self.assertEqual(stream_res.status_code, 200)
        text = stream_res.text
        self.assertIn("event: delta\ndata:", text)
        self.assertIn("event: action_chip\ndata:", text)
        self.assertIn("event: done\ndata:", text)

    # =========================================================================
    # 9. /export/zip & /export/plan Deliverables
    # =========================================================================

    @patch("ecommerce_studio.api.service.generate_ecommerce_image")
    def test_export_zip_and_plan_deliverables(self, mock_gen_img):
        """测试定稿 ZIP 物料包（有效 zip 二进制文件结构）与全案策划 Markdown 导出"""
        tdir = tempfile.mkdtemp()
        self.created_temp_dirs.append(tdir)
        f_img = os.path.join(tdir, "pic1.jpg")
        with open(f_img, "wb") as f:
            f.write(b"valid_jpg_content_12345")
        mock_gen_img.return_value = f_img

        create_res = self.client.post(
            "/api/v1/studio/sessions",
            json={
                "name": "物料导出交付专案",
                "product_info": {"name": "商务手冲咖啡壶", "category": "精品厨电"},
            },
        )
        sid = create_res.json()["session_id"]
        self.created_sessions.append(sid)

        # 出一张图以确保有物理物料
        self.client.post(
            f"/api/v1/studio/sessions/{sid}/perspectives/01_white_bg/render-version",
            json={"prompt_zh": "测试首图", "change_reason": "交付导出测试"},
        )

        # 1. 测试标准路径 /sessions/{session_id}/export/zip
        zip_res = self.client.get(f"/api/v1/studio/sessions/{sid}/export/zip")
        self.assertEqual(zip_res.status_code, 200)
        self.assertEqual(zip_res.headers.get("content-type"), "application/zip")
        self.assertIn(f'filename="ecommerce_studio_{sid}.zip"', zip_res.headers.get("content-disposition", ""))

        # 验证返回内容是合法的 ZIP 压缩流
        with zipfile.ZipFile(io.BytesIO(zip_res.content), "r") as zf:
            file_names = zf.namelist()
            self.assertTrue(len(file_names) > 0)
            self.assertTrue(any("01_white_bg" in fn or "01_" in fn for fn in file_names))

        # 2. 测试快捷别名路由 /api/v1/studio/export/zip?session_id=...
        zip_alias = self.client.get(f"/api/v1/studio/export/zip?session_id={sid}")
        self.assertEqual(zip_alias.status_code, 200)
        self.assertEqual(zip_alias.headers.get("content-type"), "application/zip")

        # 3. 测试全案方案导出 /sessions/{session_id}/export/markdown
        md_res = self.client.get(f"/api/v1/studio/sessions/{sid}/export/markdown")
        self.assertEqual(md_res.status_code, 200)
        self.assertIn("text/markdown", md_res.headers.get("content-type", ""))
        md_text = md_res.text
        self.assertIn("# 商业级电商视觉全案策划报告", md_text)
        self.assertIn("商务手冲咖啡壶", md_text)
        self.assertIn("## 一、 商品商业画像与痛点解构", md_text)
        self.assertIn("## 二、 视觉总监策划全案摘要", md_text)
        self.assertIn("## 三、 9大商业转化视觉镜头指令矩阵", md_text)

        # 4. 测试全案导出别名路径 /export/plan 和 /sessions/{session_id}/export/plan
        plan_res1 = self.client.get(f"/api/v1/studio/sessions/{sid}/export/plan")
        self.assertEqual(plan_res1.status_code, 200)
        self.assertIn("# 商业级电商视觉全案策划报告", plan_res1.text)

        plan_res2 = self.client.get(f"/api/v1/studio/export/plan?session_id={sid}")
        self.assertEqual(plan_res2.status_code, 200)
        self.assertIn("# 商业级电商视觉全案策划报告", plan_res2.text)

        # 5. 测试缺少 session_id 时的 400
        res_no_sid = self.client.get("/api/v1/studio/export/zip")
        self.assertEqual(res_no_sid.status_code, 400)
        res_no_sid_plan = self.client.get("/api/v1/studio/export/plan")
        self.assertEqual(res_no_sid_plan.status_code, 400)

    # =========================================================================
    # 10. Static File Mounts & Path Safety
    # =========================================================================

    def test_static_file_mounts_and_path_safety(self):
        """测试静态资源挂载 (/output, /api/v1/studio/output) 及路径遍历安全性"""
        # 在 output 目录下创建临时静态测试文件
        test_filename = f"static_test_{int(time.time())}.txt"
        test_file_path = self.output_dir / test_filename
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("ecommerce_studio_static_ok")

        try:
            # 1. 验证 /output 静态挂载正常读取
            resp1 = self.client.get(f"/output/{test_filename}")
            self.assertEqual(resp1.status_code, 200)
            self.assertEqual(resp1.text, "ecommerce_studio_static_ok")

            # 2. 验证 /api/v1/studio/output 静态挂载正常读取
            resp2 = self.client.get(f"/api/v1/studio/output/{test_filename}")
            self.assertEqual(resp2.status_code, 200)
            self.assertEqual(resp2.text, "ecommerce_studio_static_ok")

            # 3. 访问不存在的静态文件 -> 404
            resp_404 = self.client.get("/output/non_existent_file_xyz123.jpg")
            self.assertEqual(resp_404.status_code, 404)

            # 4. 路径遍历安全测试 (Directory Traversal Attack Prevention)
            resp_traversal_1 = self.client.get("/output/../../server.py")
            self.assertIn(resp_traversal_1.status_code, [400, 404])

            resp_traversal_2 = self.client.get("/output/%2e%2e/%2e%2e/server.py")
            self.assertIn(resp_traversal_2.status_code, [400, 404])

            resp_traversal_3 = self.client.get("/api/v1/studio/output/../../server.py")
            self.assertIn(resp_traversal_3.status_code, [400, 404])

        finally:
            if test_file_path.exists():
                test_file_path.unlink()

    # =========================================================================
    # 11. Refine-Prompt Endpoint Edge Cases
    # =========================================================================

    @patch("ecommerce_studio.studio_crew.refine_prompt_with_ai")
    def test_refine_prompt_endpoint(self, mock_refine_ai):
        """测试 /refine-prompt 接口的参数校验与正常商业摄影行话润色"""
        mock_refine_ai.return_value = "顶级伦勃朗布光，右侧柔光箱反射，微弱倒影，8k清晰度。"

        create_res = self.client.post("/api/v1/studio/sessions", json={"name": "提示词润色专案"})
        sid = create_res.json()["session_id"]
        self.created_sessions.append(sid)

        # 缺少 session_id 或 perspective_id 报 400
        bad_req = self.client.post("/api/v1/studio/refine-prompt", json={})
        self.assertEqual(bad_req.status_code, 400)

        # 正常调用
        ok_res = self.client.post(
            "/api/v1/studio/refine-prompt",
            json={
                "session_id": sid,
                "perspective_id": "01_white_bg",
                "instruction": "加强伦勃朗光影",
            },
        )
        self.assertEqual(ok_res.status_code, 200)
        self.assertEqual(ok_res.json()["refined_prompt"], "顶级伦勃朗布光，右侧柔光箱反射，微弱倒影，8k清晰度。")


if __name__ == "__main__":
    unittest.main()
