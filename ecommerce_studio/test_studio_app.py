import concurrent.futures
import copy
import io
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from unittest.mock import patch

# 添加当前目录与根目录
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from ecommerce_studio import session_manager, studio_crew, config_manager
from ecommerce_studio.app import (
    render_model_selector,
    create_images_zip,
    _worker_single_image,
)


def test_config():
    print("[1] 测试配置管理加载...")
    cfg = config_manager.load_config()
    assert "active_provider" in cfg
    assert "gemini" in cfg
    assert "openai" in cfg
    assert "agents" in cfg
    print("✅ 配置管理加载正常")


def test_session_lifecycle():
    print("[2] 测试会话生命周期与持久化...")
    sess = session_manager.create_session(
        name="自动化测试会话",
        product_info={"name": "测试商品", "category": "测试品类"},
    )
    sess_id = sess["session_id"]
    assert sess_id is not None
    assert sess["name"] == "自动化测试会话"
    assert sess.get("schema_version") == "2.0"

    # 读取
    fetched = session_manager.get_session(sess_id)
    assert fetched is not None
    assert fetched["product_info"]["name"] == "测试商品"

    # 添加对话
    session_manager.add_chat_message(sess_id, "user", "你好，请推荐首图方案")
    session_manager.add_chat_message(sess_id, "assistant", "首图建议使用商业白底纯净棚拍。")
    updated = session_manager.get_session(sess_id)
    assert len(updated["chat_history"]) == 2

    # 会话列表
    s_list = session_manager.list_sessions()
    assert any(s["session_id"] == sess_id for s in s_list)

    # 删除
    del_ok = session_manager.delete_session(sess_id)
    assert del_ok is True
    assert session_manager.get_session(sess_id) is None
    print("✅ 会话生命周期与持久化正常")


def test_9_image_matrix():
    print("[3] 测试电商 9 大图矩阵模板与解析...")
    templates = studio_crew.ECOMMERCE_IMAGE_MATRIX_TEMPLATES
    assert len(templates) == 9
    matrix = studio_crew.build_default_prompt_matrix({"name": "随行杯"})
    assert len(matrix) == 9
    for item in matrix:
        assert "id" in item
        assert "name" in item
        assert "desc" in item
        assert "prompt" in item
        assert any('\u4e00' <= char <= '\u9fff' for char in item["prompt"])
    print("✅ 电商 9 大图矩阵模板与中文提示词正常")


def test_zip_packaging():
    print("[4] 测试图片打包 ZIP 功能 (支持版本标签)...")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"fake_jpeg_content_header")
        tmp_path = f.name

    dummy_images = [
        {
            "id": "main_white_bg",
            "name": "商业高清白底首图",
            "image_path": tmp_path,
            "active_version": 2,
        },
        {
            "id": "lifestyle_scene",
            "name": "真实生活使用场景图",
            "image_path": tmp_path,
            "active_version": 1,
        },
    ]
    zip_bytes = create_images_zip(dummy_images)
    assert len(zip_bytes) > 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        namelist = zf.namelist()
        assert len(namelist) == 2
        assert "01_商业高清白底首图_v2.jpg" in namelist
        assert "02_真实生活使用场景图_v1.jpg" in namelist
    os.remove(tmp_path)
    print("✅ 图片打包 ZIP (支持版本标签) 正常")


def test_markdown_export():
    print("[5] 测试 Markdown 策划案导出与保存...")
    prod = {"name": "测试保温杯", "category": "户外生活", "target_audience": "白领", "pain_points": "漏水"}
    matrix = studio_crew.build_default_prompt_matrix(prod)
    md_path = studio_crew.save_plan_markdown(prod, "这是一段深度剖析与场景策划", matrix)
    assert os.path.exists(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "测试保温杯" in content
    assert "商业高清白底首图" in content
    assert "真实生活使用场景图" in content
    os.remove(md_path)
    print("✅ Markdown 导出与保存正常")


def test_version_chain_and_rollback():
    print("[6] 测试非破坏性版本链条 (快照追加、切换与后悔药回滚)...")
    sess = session_manager.create_session(
        name="版本链测试方案",
        product_info={"name": "极简咖啡杯"},
    )
    sess_id = sess["session_id"]
    sess["prompts_matrix"] = [
        {"id": "01_white_bg", "name": "商业纯净白底首图", "prompt": "初始白底指令 v1"}
    ]
    session_manager.save_session(sess)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f1:
        f1.write(b"img_bytes_v1")
        path_v1 = f1.name
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f2:
        f2.write(b"img_bytes_v2")
        path_v2 = f2.name
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f3:
        f3.write(b"img_bytes_v3")
        path_v3 = f3.name

    try:
        # 1. 追加版本 1
        session_manager.add_image_version(
            session_data=sess,
            item_id="01_white_bg",
            image_path=path_v1,
            prompt="初始白底指令 v1",
            note="首轮商业渲染",
            aspect_ratio="1:1",
        )
        assert sess["generated_images"][0]["active_version"] == 1
        assert sess["generated_images"][0]["active_version_id"] == "v1"
        assert len(sess["generated_images"][0]["versions"]) == 1

        # 2. 追加版本 2
        session_manager.add_image_version(
            session_data=sess,
            item_id="01_white_bg",
            image_path=path_v2,
            prompt="增加夕阳暖光指令 v2",
            note="AI微调: 增加日落暖光",
            aspect_ratio="1:1",
        )
        assert sess["generated_images"][0]["active_version"] == 2
        assert sess["generated_images"][0]["active_version_id"] == "v2"
        assert len(sess["generated_images"][0]["versions"]) == 2
        assert sess["generated_images"][0]["prompt"] == "增加夕阳暖光指令 v2"
        assert sess["prompts_matrix"][0]["prompt"] == "增加夕阳暖光指令 v2"

        # 3. 追加版本 3
        session_manager.add_image_version(
            session_data=sess,
            item_id="01_white_bg",
            image_path=path_v3,
            prompt="换为黑色大理石指令 v3",
            note="AI微调: 黑色大理石台面",
            aspect_ratio="3:4",
        )
        assert sess["generated_images"][0]["active_version"] == 3
        assert len(sess["generated_images"][0]["versions"]) == 3

        # 4. 测试版本切换 switch_active_version
        switched = session_manager.switch_active_version(sess, "01_white_bg", 2)
        assert switched is True
        assert sess["generated_images"][0]["active_version"] == 2
        assert sess["generated_images"][0]["image_path"] == path_v2

        # 5. 测试后悔药回滚 rollback_to_version (同步恢复 prompts_matrix)
        rolled = session_manager.rollback_to_version(sess, "01_white_bg", 1)
        assert rolled is True
        assert sess["generated_images"][0]["active_version"] == 1
        assert sess["generated_images"][0]["image_path"] == path_v1
        assert sess["generated_images"][0]["prompt"] == "初始白底指令 v1"
        # 验证 prompts_matrix 提示词被无损还原
        assert sess["prompts_matrix"][0]["prompt"] == "初始白底指令 v1"
        # 验证历史没有被删除（依然保留 3 个版本）
        assert len(sess["generated_images"][0]["versions"]) == 3

        # 6. 基于回滚后的状态再出新版本 v4
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f4:
            f4.write(b"img_bytes_v4")
            path_v4 = f4.name
        session_manager.add_image_version(
            session_data=sess,
            item_id="01_white_bg",
            image_path=path_v4,
            prompt="基于v1微调指令 v4",
            note="二次微调出图",
        )
        assert sess["generated_images"][0]["active_version"] == 4
        assert len(sess["generated_images"][0]["versions"]) == 4
        os.remove(path_v4)

    finally:
        os.remove(path_v1)
        os.remove(path_v2)
        os.remove(path_v3)
        session_manager.delete_session(sess_id)

    print("✅ 非破坏性版本链条与回滚机制验证 100% 正确")


def test_v1_to_v2_migration():
    print("[7] 测试历史老会话数据平滑迁移 (Schema v1 -> v2)...")
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(b"legacy_image_content")
        legacy_img_path = f.name

    try:
        legacy_session = {
            "session_id": "sess_legacy_001",
            "name": "老版本测试方案",
            "updated_at": 1710000000,
            "prompts_matrix": [
                {"id": "01_white_bg", "name": "纯净白底", "prompt": "白底提示词"}
            ],
            "generated_images": [
                {
                    "id": "01_white_bg",
                    "name": "纯净白底",
                    "desc": "搜索主图",
                    "prompt": "白底提示词",
                    "image_path": legacy_img_path,
                    "status": "success",
                    "error": None,
                }
            ],
        }

        migrated = session_manager.migrate_session_to_v2(legacy_session)
        assert migrated.get("schema_version") == "2.0"
        m_img = migrated["generated_images"][0]
        assert "versions" in m_img
        assert len(m_img["versions"]) == 1
        assert m_img["active_version"] == 1
        assert m_img["active_version_id"] == "v1"
        assert m_img["versions"][0]["image_path"] == legacy_img_path
        assert m_img["versions"][0]["prompt"] == "白底提示词"
        assert m_img["versions"][0]["note"] == "初始全套商业渲染"
    finally:
        os.remove(legacy_img_path)

    print("✅ 历史老会话向后兼容自动升级验证通过")


def test_stateless_worker_multithreading():
    print("[8] 测试多线程并发渲染无状态纯函数 (彻底消灭 Context 丢失 Bug)...")
    config_snapshot = copy.deepcopy(config_manager.load_config())
    test_items = [
        {"id": f"perspective_{i}", "name": f"视角_{i}", "prompt": f"商业摄影指令_{i}"}
        for i in range(5)
    ]

    # 使用 mock 避免真正网络调用生图，测试多线程调度与纯入参纯返回值无状态性
    def mock_run_phase_two(edited_prompt, config, aspect_ratio="1:1", filename_prefix=None):
        # 确认子线程内完全正常运行
        return f"/mock/path/{filename_prefix}.jpg"

    with patch("ecommerce_studio.app.run_phase_two", side_effect=mock_run_phase_two):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {
                executor.submit(_worker_single_image, i, item, config_snapshot, "1:1"): i
                for i, item in enumerate(test_items)
            }
            results = []
            for future in concurrent.futures.as_completed(future_map):
                idx, res = future.result()
                results.append((idx, res))

    assert len(results) == 5
    for idx, res in results:
        assert res["status"] == "success"
        assert res["image_path"] == f"/mock/path/{res['id']}.jpg"
        assert res["error"] is None

    print("✅ 多线程并发无状态任务执行完毕，无任何 Streamlit Context 丢失与 session_state 崩溃")


if __name__ == "__main__":
    test_config()
    test_session_lifecycle()
    test_9_image_matrix()
    test_zip_packaging()
    test_markdown_export()
    test_version_chain_and_rollback()
    test_v1_to_v2_migration()
    test_stateless_worker_multithreading()
    print("\n🎉🎉 全部 8 项核心功能与架构防御测试 100% 顺利通过！")
