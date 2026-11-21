import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ecommerce_studio.studio_crew import (
    ECOMMERCE_IMAGE_MATRIX_TEMPLATES,
    build_default_prompt_matrix,
    parse_prompt_matrix_from_text,
    extract_prompt_from_plan,
    refine_prompt_with_ai,
    save_plan_markdown,
)
from ecommerce_studio.tools.image_tool import (
    generate_ecommerce_images_batch,
    generate_ecommerce_image,
)
from ecommerce_studio import session_manager


class TestEcommerceStudioCore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config = {
            "active_provider": "gemini",
            "gemini": {
                "api_key": "mock_gemini_key",
                "model": "gemini-2.0-flash",
                "image_model": "imagen-3.0-generate-002",
            },
            "openai": {
                "api_key": "mock_openai_key",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o",
                "image_model": "dall-e-3",
            },
            "agents": {
                "market_researcher": {"name": "商品洞察专家", "system_prompt": "深入剖析痛点"},
                "art_director": {"name": "视觉创意总监", "system_prompt": "场景与视觉故事推演"},
                "visual_engineer": {"name": "AI 制图工程师", "system_prompt": "输出高质量中文Prompt"},
            },
        }
        self.product_info = {
            "name": "极简智能控温咖啡杯",
            "category": "生活小家电/水具",
            "target_audience": "25-35岁都市白领与通勤族",
            "pain_points": "普通保温杯易漏水、保温时长不足、做工廉价",
        }

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_build_default_prompt_matrix_nine_items(self):
        """测试 9 大图模板矩阵生成"""
        matrix = build_default_prompt_matrix(self.product_info)
        self.assertEqual(len(matrix), 9)
        expected_ids = [tpl["id"] for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES]
        actual_ids = [item["id"] for item in matrix]
        self.assertEqual(actual_ids, expected_ids)

        # 检查是否全部包含中文高质量提示词
        for item in matrix:
            self.assertIn("id", item)
            self.assertIn("name", item)
            self.assertIn("desc", item)
            self.assertIn("prompt", item)
            self.assertTrue(len(item["prompt"]) > 20)
            self.assertIn("咖啡杯", item["prompt"])

    def test_parse_prompt_matrix_from_json_block(self):
        """测试从包含 JSON 代码块的文本中正确提取 9 大图提示词"""
        sample_json_text = """
# 策划方案
### 3. 视觉提示词矩阵
```json
[
  {
    "id": "main_white_bg",
    "name": "商业高清白底首图",
    "desc": "纯净白底",
    "prompt": "高端商业静物摄影，极简智能控温咖啡杯，纯白背景，柔光箱高光勾勒，8k超清。"
  },
  {
    "id": "lifestyle_scene",
    "name": "真实生活使用场景图",
    "desc": "晨光办公场景",
    "prompt": "真实生活方式摄影，极简智能控温咖啡杯放置于晨光穿透的原木办公桌上，浅景深。"
  }
]
```
"""
        matrix = parse_prompt_matrix_from_text(sample_json_text, self.product_info)
        self.assertEqual(len(matrix), 9)

        # 验证前两项被精准解析，后七项被自动补齐
        self.assertEqual(matrix[0]["id"], "main_white_bg")
        self.assertIn("纯白背景", matrix[0]["prompt"])
        self.assertEqual(matrix[1]["id"], "lifestyle_scene")
        self.assertIn("原木办公桌", matrix[1]["prompt"])

        # 验证其余缺失项由兜底补齐且属于标准 9 大图
        ids = [item["id"] for item in matrix]
        self.assertEqual(ids, [tpl["id"] for tpl in ECOMMERCE_IMAGE_MATRIX_TEMPLATES])

    def test_extract_prompt_from_plan(self):
        """测试向后兼容的单条提示词提取接口"""
        text = "一些前置策划案..."
        prompt = extract_prompt_from_plan(text)
        self.assertTrue(isinstance(prompt, str))
        self.assertTrue(len(prompt) > 10)

    @patch("google.genai.Client")
    def test_refine_prompt_with_ai_gemini(self, mock_client_cls):
        """测试使用 Gemini 进行二次 AI 提示词微调"""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "优化后的中文商业摄影提示词：极简智能控温咖啡杯，背景替换为暮色晚霞，冷光数显高亮，8k画质。"
        mock_client.models.generate_content.return_value = mock_response

        orig = "极简智能控温咖啡杯，纯白底，8k超清"
        feedback = "把背景改成晚霞黄昏，杯盖加上冷光数显特效"
        refined = refine_prompt_with_ai(orig, feedback, self.mock_config, "商业高清白底首图")

        self.assertIn("晚霞", refined)
        self.assertIn("冷光数显", refined)
        mock_client.models.generate_content.assert_called_once()

    @patch("openai.OpenAI")
    def test_refine_prompt_with_ai_openai(self, mock_openai_cls):
        """测试使用 OpenAI 进行二次 AI 提示词微调"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "优化后的中文提示词：咖啡杯放置于露营帐篷前，黄昏落日，暖调柔光。"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        cfg = dict(self.mock_config)
        cfg["active_provider"] = "openai"

        orig = "极简智能控温咖啡杯，办公室桌面"
        feedback = "改成户外露营场景，黄昏暖光"
        refined = refine_prompt_with_ai(orig, feedback, cfg, "真实生活使用场景图")

        self.assertIn("露营", refined)
        mock_client.chat.completions.create.assert_called_once()

    def test_save_plan_markdown_matrix(self):
        """测试将 9 大图矩阵保存为 Markdown 文件"""
        matrix = build_default_prompt_matrix(self.product_info)
        saved_path = save_plan_markdown(
            product_info=self.product_info,
            analysis_text="多智能体深度分析文本内容...",
            prompt_or_matrix=matrix,
            output_dir=self.temp_dir,
        )
        self.assertTrue(os.path.isfile(saved_path))
        with open(saved_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("极简智能控温咖啡杯", content)
        self.assertIn("商业高清白底首图", content)
        self.assertIn("真实模特生活方式交互图", content)

    @patch("ecommerce_studio.tools.image_tool.generate_ecommerce_image")
    def test_generate_ecommerce_images_batch(self, mock_gen_single):
        """测试并发批量生成图片及容错设计"""
        # 模拟生成行为：前两张成功，第三张抛异常
        def side_effect(prompt, *args, **kwargs):
            if "fail" in prompt:
                raise RuntimeError("API Rate Limit exceeded")
            return f"{self.temp_dir}/fake_{kwargs.get('filename_prefix', 'img')}.jpg"

        mock_gen_single.side_effect = side_effect

        items = [
            {"id": "main_white_bg", "name": "商业高清白底首图", "prompt": "咖啡杯白底图"},
            {"id": "lifestyle_scene", "name": "真实生活使用场景图", "prompt": "办公室生活场景图"},
            {"id": "pain_point_solution", "name": "痛点场景攻坚图", "prompt": "fail_test_prompt"},
        ]

        results = generate_ecommerce_images_batch(
            items=items,
            provider="gemini",
            config=self.mock_config,
            output_dir=self.temp_dir,
            aspect_ratio="1:1",
            max_workers=2,
        )

        self.assertEqual(len(results), 3)
        # 第一张成功
        self.assertEqual(results[0]["status"], "success")
        self.assertIsNotNone(results[0]["image_path"])
        self.assertEqual(results[0]["id"], "main_white_bg")

        # 第二张成功
        self.assertEqual(results[1]["status"], "success")
        self.assertIsNotNone(results[1]["image_path"])
        self.assertEqual(results[1]["id"], "lifestyle_scene")

        # 第三张失败但不阻碍整个流程
        self.assertEqual(results[2]["status"], "failed")
        self.assertIsNone(results[2]["image_path"])
        self.assertIn("Rate Limit", results[2]["error"])

    def test_session_manager_crud(self):
        """测试 session_manager 的创建、查询、更新、列表和删除"""
        with patch("ecommerce_studio.session_manager.get_sessions_dir") as mock_dir:
            from pathlib import Path
            temp_sessions_path = Path(self.temp_dir) / "sessions"
            temp_sessions_path.mkdir(parents=True, exist_ok=True)
            mock_dir.return_value = temp_sessions_path

            # 1. 创建 session
            session = session_manager.create_session(
                session_id="test_sess_001",
                name="咖啡杯新品上市方案",
                product_info=self.product_info,
            )
            self.assertEqual(session["session_id"], "test_sess_001")
            self.assertEqual(session["name"], "咖啡杯新品上市方案")

            # 2. 读取 session
            loaded = session_manager.get_session("test_sess_001")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["product_info"]["name"], "极简智能控温咖啡杯")

            # 3. 添加聊天消息
            updated_sess = session_manager.add_chat_message("test_sess_001", "user", "请问首图光影如何微调？")
            self.assertEqual(len(updated_sess["chat_history"]), 1)
            self.assertEqual(updated_sess["chat_history"][0]["content"], "请问首图光影如何微调？")

            # 4. 再次获取验证持久化生效
            reloaded = session_manager.get_session("test_sess_001")
            self.assertEqual(len(reloaded["chat_history"]), 1)

            # 5. 列出所有会话
            sessions_list = session_manager.list_sessions()
            self.assertEqual(len(sessions_list), 1)
            self.assertEqual(sessions_list[0]["session_id"], "test_sess_001")

            # 6. 删除会话
            del_result = session_manager.delete_session("test_sess_001")
            self.assertTrue(del_result)
            self.assertIsNone(session_manager.get_session("test_sess_001"))

    @patch("google.genai.Client")
    def test_chat_with_agent_gemini(self, mock_client_cls):
        """测试 chat_with_agent 多轮对话上下文与 Gemini 调用"""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "建议将首图改为 45 度微俯视视角，并在不锈钢杯口处增设一束聚光灯以凸显金属拉丝工艺。"
        mock_client.models.generate_content.return_value = mock_response

        session_data = {
            "session_id": "sess_123",
            "product_info": self.product_info,
            "analysis_result": "这是保温杯的完整策划案...",
            "prompts_matrix": build_default_prompt_matrix(self.product_info),
            "chat_history": [
                {"role": "user", "content": "你好，我想针对都市通勤受众进行微调。"},
                {"role": "assistant", "content": "收到，通勤场景可强化单手开盖与车载杯架适配。"},
            ],
        }

        reply = session_manager.chat_with_agent(
            session_data=session_data,
            user_message="请问首图的金属材质怎么表现更高级？",
            config=self.mock_config,
        )

        self.assertIn("聚光灯", reply)
        mock_client.models.generate_content.assert_called_once()

    @patch("openai.OpenAI")
    def test_chat_with_agent_openai(self, mock_openai_cls):
        """测试 chat_with_agent 多轮对话上下文与 OpenAI 调用"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_choice = MagicMock()
        mock_choice.message.content = "OpenAI 建议详情页痛点图采用倒置滴水不漏动效对比。"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        cfg = dict(self.mock_config)
        cfg["active_provider"] = "openai"

        session_data = {
            "session_id": "sess_openai_001",
            "product_info": self.product_info,
            "analysis_result": "策划案内容...",
            "prompts_matrix": [],
            "chat_history": [],
        }

        reply = session_manager.chat_with_agent(
            session_data=session_data,
            user_message="详情页痛点怎么排版更好？",
            config=cfg,
        )

        self.assertIn("倒置滴水不漏", reply)
        mock_client.chat.completions.create.assert_called_once()

    def test_refine_prompt_empty_feedback(self):
        """测试用户修改意见为空时，原样返回原提示词"""
        orig = "极简保温杯白底图"
        res = refine_prompt_with_ai(orig, "", self.mock_config)
        self.assertEqual(res, orig)
        res_space = refine_prompt_with_ai(orig, "   ", self.mock_config)
        self.assertEqual(res_space, orig)

    def test_batch_generate_empty_list(self):
        """测试批量生成传入空列表"""
        res = generate_ecommerce_images_batch([], provider="gemini", config=self.mock_config)
        self.assertEqual(res, [])

    @patch("openai.OpenAI")
    def test_generate_image_custom_openai_success(self, mock_openai_cls):
        """测试 custom_openai 正确读取自定义配置与超时，完成图片生成"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        mock_img = MagicMock()
        mock_img.b64_json = "aGVsbG8="  # "hello" in base64
        mock_resp = MagicMock()
        mock_resp.data = [mock_img]
        mock_client.images.generate.return_value = mock_resp

        custom_cfg = {
            "active_provider": "custom_openai",
            "custom_openai": {
                "api_key": "custom_key_123",
                "base_url": "https://api.oneapi-proxy.com/v1",
                "image_model": "dall-e-3",
                "timeout": 45.0,
            },
        }

        path = generate_ecommerce_image(
            prompt="极简智能保温杯，8k",
            provider="custom_openai",
            config=custom_cfg,
            output_dir=self.temp_dir,
        )

        self.assertTrue(os.path.exists(path))
        mock_openai_cls.assert_called_once_with(
            api_key="custom_key_123",
            base_url="https://api.oneapi-proxy.com/v1",
            timeout=45.0,
        )

    @patch("requests.get")
    @patch("openai.OpenAI")
    def test_generate_image_custom_openai_adaptive_fallback(self, mock_openai_cls, mock_req_get):
        """测试 custom_openai 当 b64_json 失败时自适应降级为 URL 模式"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client

        # 第一次调用 (b64_json) 模拟第三方中继抛出 400 格式不支持错误
        # 第二次调用 (url fallback) 返回带 url 的数据
        mock_url_img = MagicMock()
        mock_url_img.b64_json = None
        mock_url_img.url = "https://cdn.image.com/fake.png"
        mock_fallback_resp = MagicMock()
        mock_fallback_resp.data = [mock_url_img]

        mock_client.images.generate.side_effect = [
            Exception("Invalid response_format: only url is supported by this upstream channel"),
            mock_fallback_resp,
        ]

        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.content = b"fake_downloaded_image_bytes"
        mock_req_get.return_value = mock_http_resp

        custom_cfg = {
            "active_provider": "custom_openai",
            "custom_openai": {
                "api_key": "custom_key_123",
                "base_url": "https://api.oneapi-proxy.com/v1",
            },
        }

        path = generate_ecommerce_image(
            prompt="高端电饭煲，商业棚拍",
            provider="custom_openai",
            config=custom_cfg,
            output_dir=self.temp_dir,
        )

        self.assertTrue(os.path.exists(path))
        self.assertEqual(mock_client.images.generate.call_count, 2)
        mock_req_get.assert_called_once_with("https://cdn.image.com/fake.png", timeout=30)

    @patch("openai.OpenAI")
    def test_generate_image_custom_openai_friendly_error_on_404(self, mock_openai_cls):
        """测试当中继代理端点不支持生图接口时，返回极其友好的诊断错误信息"""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.images.generate.side_effect = Exception("404 page not found / unsupported route /v1/images/generate")

        custom_cfg = {
            "custom_openai": {
                "api_key": "custom_key_123",
                "base_url": "https://api.text-only-proxy.com/v1",
            },
        }

        with self.assertRaises(RuntimeError) as ctx:
            generate_ecommerce_image(
                prompt="测试",
                provider="custom_openai",
                config=custom_cfg,
                output_dir=self.temp_dir,
            )

        err_msg = str(ctx.exception)
        self.assertIn("未开通或不支持生图接口", err_msg)
        self.assertIn("Gemini", err_msg)


if __name__ == "__main__":
    unittest.main()
