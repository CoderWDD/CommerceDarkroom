import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from ecommerce_studio.api.main import app
from ecommerce_studio.api.service import studio_service
from ecommerce_studio.prompt_compiler import PromptMatrixCompiler
from ecommerce_studio.tools.image_tool import generate_ecommerce_image


class TestDualAssetAndFidelity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.test_dir = tempfile.mkdtemp()
        self.dummy_img_path = os.path.join(self.test_dir, "sample_actual.jpg")
        with open(self.dummy_img_path, "wb") as f:
            f.write(b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_01_extract_dossier_dual_assets(self):
        """1. 测试 extract-dossier 区分实拍图与对标商品图"""
        # 实拍图提取
        with open(self.dummy_img_path, "rb") as f:
            res_actual = self.client.post(
                "/api/v1/studio/vision/extract-dossier",
                files={"file": ("actual.jpg", f, "image/jpeg")},
                data={"category_hint": "保温杯", "asset_type": "actual"},
            )
        self.assertEqual(res_actual.status_code, 200)
        data_actual = res_actual.json()
        self.assertEqual(data_actual.get("asset_type"), "actual")
        tags_actual = data_actual["dossier"]["visual_tags"]
        self.assertTrue(any("实物" in t or "材质" in t or "结构" in t or "极简" in t for t in tags_actual))

        # 对标商品图提取
        with open(self.dummy_img_path, "rb") as f:
            res_comp = self.client.post(
                "/api/v1/studio/vision/extract-dossier",
                files={"file": ("competitor.jpg", f, "image/jpeg")},
                data={"category_hint": "保温杯", "asset_type": "competitor"},
            )
        self.assertEqual(res_comp.status_code, 200)
        data_comp = res_comp.json()
        self.assertEqual(data_comp.get("asset_type"), "competitor")
        tags_comp = data_comp["dossier"]["visual_tags"]
        self.assertTrue(any("对标" in t or "布光" in t or "展台" in t or "商业" in t for t in tags_comp))

    def test_02_upload_asset_dual_types(self):
        """2. 测试 assets/upload 支持实拍图与对标商品图"""
        sess_res = self.client.post("/api/v1/studio/sessions", json={"name": "测试双图专案"})
        sess_id = sess_res.json()["session_id"]

        with open(self.dummy_img_path, "rb") as f:
            up_actual = self.client.post(
                f"/api/v1/studio/sessions/{sess_id}/assets/upload",
                files={"file": ("prod_actual.jpg", f, "image/jpeg")},
                data={"asset_type": "actual", "is_primary": "true"},
            )
        self.assertEqual(up_actual.status_code, 200)
        self.assertEqual(up_actual.json()["asset_type"], "actual")

        with open(self.dummy_img_path, "rb") as f:
            up_comp = self.client.post(
                f"/api/v1/studio/sessions/{sess_id}/assets/upload",
                files={"file": ("comp_banner.jpg", f, "image/jpeg")},
                data={"asset_type": "competitor", "is_primary": "false"},
            )
        self.assertEqual(up_comp.status_code, 200)
        self.assertEqual(up_comp.json()["asset_type"], "competitor")

    def test_03_step2_prompt_compiler_references_dual_assets(self):
        """3. 测试 Step 2 生成提示词时同时参考实拍图(锁模)与对标商品图(构图)"""
        prod_info = {
            "name": "钛合金极简保温杯",
            "category": "户外便携保温杯",
            "material_features": "TC4航空钛合金表面微弧氧化",
            "reference_images": [
                {
                    "id": "act_1",
                    "url": "/output/uploads/sample_actual.jpg",
                    "asset_type": "actual",
                    "is_primary": True,
                    "vision_tags": ["#真实钛合金灰", "#微弧氧化质感", "#圆柱机身"],
                },
                {
                    "id": "comp_1",
                    "url": "/output/uploads/sample_comp.jpg",
                    "asset_type": "competitor",
                    "is_primary": False,
                    "vision_tags": ["#大牌无影白底", "#通透极浅倒影"],
                },
            ],
        }

        matrix = PromptMatrixCompiler.compile_matrix(prod_info, style_preset_id="minimalist_muji")
        self.assertEqual(len(matrix), 9)

        # 检查提示词中是否同时注入了实拍图保真锁模与对标商品图构图吸收
        first_prompt = matrix[0]["prompt"]
        self.assertIn("产品实拍图保真锁模", first_prompt)
        self.assertIn("#真实钛合金灰", first_prompt)
        self.assertIn("对标商品图构图吸收", first_prompt)
        self.assertIn("#大牌无影白底", first_prompt)

    def test_04_step3_image_generation_reference_lock(self):
        """4. 测试 Step 3 出图时如果有实拍图，自动引用并注入防走样锁模指令"""
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            mock_resp = MagicMock()
            mock_img_item = MagicMock()
            mock_img_item.image.image_bytes = b"fake_rendered_image_bytes"
            mock_resp.generated_images = [mock_img_item]
            mock_client.models.generate_images.return_value = mock_resp

            out_img = generate_ecommerce_image(
                prompt="商业白底首图",
                provider="gemini",
                config={"gemini": {"api_key": "test_key"}},
                output_dir=self.test_dir,
                reference_image_path=self.dummy_img_path,
            )

            self.assertTrue(os.path.exists(out_img))
            # 验证传给底层模型接口的 Prompt 中显式包含了实拍保真锁模指令
            called_kwargs = mock_client.models.generate_images.call_args[1]
            called_prompt = called_kwargs.get("prompt", "")
            self.assertIn("商品实拍图绝对保真锁模", called_prompt)
            self.assertIn("真实物理轮廓", called_prompt)


if __name__ == "__main__":
    unittest.main()
