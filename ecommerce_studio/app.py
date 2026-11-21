import concurrent.futures
import copy
import io
import os
import sys
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image
import streamlit as st

# 将项目根目录添加到 sys.path 以便模块导入
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ecommerce_studio.config_manager import (
    load_config,
    save_config,
    reset_to_defaults,
)
from ecommerce_studio.session_manager import (
    create_session,
    get_session,
    save_session,
    list_sessions,
    delete_session,
    add_chat_message,
    chat_with_agent,
    migrate_session_to_v2,
    add_image_version,
    switch_active_version,
    rollback_to_version,
)
from ecommerce_studio.studio_crew import (
    ECOMMERCE_IMAGE_MATRIX_TEMPLATES,
    build_default_prompt_matrix,
    run_phase_one,
    run_phase_two,
    run_phase_two_batch,
    refine_prompt_with_ai,
    save_plan_markdown,
)

CUSTOM_MODEL_OPTION = "✏️ 自定义输入 / Custom"


# ----------------- 现代高级暗调设计规范 CSS -----------------
def inject_modern_studio_css():
    """注入现代 Clean SaaS 质感样式 (Apple / Linear / Midjourney Web 风格)"""
    st.markdown(
        """
        <style>
        /* 根变量与全局质感 */
        :root {
            --studio-bg-canvas: #0a0d12;
            --studio-bg-surface: #121721;
            --studio-bg-card: #161d2b;
            --studio-bg-elevated: #1e283b;
            --studio-border-subtle: rgba(255, 255, 255, 0.08);
            --studio-border-highlight: rgba(99, 102, 241, 0.4);
            --studio-accent-primary: #6366f1;
            --studio-accent-primary-hover: #4f46e5;
            --studio-accent-success: #10b981;
            --studio-text-main: #f8fafc;
            --studio-text-muted: #94a3b8;
            --studio-radius-card: 12px;
            --studio-radius-pill: 9999px;
        }

        /* 主容器与卡片统一 12px 黄金圆角与微透细边框 */
        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: var(--studio-bg-card);
            border: 1px solid var(--studio-border-subtle) !important;
            border-radius: var(--studio-radius-card) !important;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.45);
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(99, 102, 241, 0.35) !important;
            box-shadow: 0 8px 30px -4px rgba(0, 0, 0, 0.65);
        }

        /* 徽章 Badge & 胶囊 Pill 视觉规范 */
        .studio-pill {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 3px 12px;
            border-radius: var(--studio-radius-pill);
            font-size: 0.8rem;
            font-weight: 500;
            line-height: 1.4;
            letter-spacing: 0.02em;
        }

        .studio-pill-success {
            background: rgba(16, 185, 129, 0.12);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.28);
        }

        .studio-pill-active {
            background: rgba(99, 102, 241, 0.15);
            color: #a5b4fc;
            border: 1px solid rgba(99, 102, 241, 0.35);
        }

        .studio-pill-neutral {
            background: rgba(255, 255, 255, 0.05);
            color: #94a3b8;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        /* 顶部 Stepper 导航胶囊条 */
        .stepper-header-box {
            background: #111622;
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 20px;
        }

        /* 摄影画廊卡片头部标签 */
        .card-perspective-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 4px;
        }

        /* 胶卷版本指示条 */
        .version-strip-container {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            padding: 6px 10px;
            margin: 8px 0;
        }

        /* 提示词代码与文本展示区 */
        .prompt-preview-block {
            background: rgba(0, 0, 0, 0.35);
            border-left: 3px solid #6366f1;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.85rem;
            color: #cbd5e1;
            margin: 6px 0;
            line-height: 1.5;
        }

        /* 按钮微动效与圆角平滑 */
        button {
            border-radius: 8px !important;
            transition: transform 0.1s ease, box-shadow 0.2s ease !important;
        }
        button:active {
            transform: scale(0.98) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ----------------- 纯函数辅助工具 -----------------
def render_model_selector(
    label: str,
    current_value: str,
    preset_options: list[str],
    key_prefix: str,
    placeholder: str = "",
    help: str = "",
) -> str:
    """通用模型选择器组件，支持预置选择与自由自定义输入"""
    all_options = list(preset_options) + [CUSTOM_MODEL_OPTION]
    current_val_clean = (current_value or "").strip()
    is_custom = current_val_clean not in preset_options

    select_key = f"model_select_{key_prefix}"
    custom_input_key = f"model_custom_{key_prefix}"

    if select_key in st.session_state and st.session_state[select_key] not in all_options:
        del st.session_state[select_key]

    if select_key not in st.session_state:
        if is_custom and current_val_clean:
            st.session_state[select_key] = CUSTOM_MODEL_OPTION
        elif current_val_clean in preset_options:
            st.session_state[select_key] = current_val_clean
        else:
            st.session_state[select_key] = preset_options[0]

    if st.session_state.get(select_key) == CUSTOM_MODEL_OPTION:
        if custom_input_key not in st.session_state and is_custom and current_val_clean:
            st.session_state[custom_input_key] = current_val_clean

    selected_choice = st.selectbox(
        label,
        options=all_options,
        key=select_key,
        help=help or f"可从预置推荐列表中快速选择，或选择「{CUSTOM_MODEL_OPTION}」自由输入任意模型",
    )

    if selected_choice == CUSTOM_MODEL_OPTION:
        custom_model_val = st.text_input(
            f"✏️ 输入自定义模型名称 ({label})",
            key=custom_input_key,
            placeholder=placeholder or "例如：gemini-2.5-flash-preview / 自定义模型名称",
            help="请输入完整可用的模型名称/ID",
        )
        custom_model_clean = custom_model_val.strip()
        if not custom_model_clean:
            st.caption("⚠️ 模型名称不能为空，未输入前保留当前默认。")
            return current_val_clean if current_val_clean else preset_options[0]
        return custom_model_clean
    else:
        return selected_choice


def create_images_zip(images: List[Dict[str, Any]]) -> bytes:
    """
    将商业大片批量打包为 ZIP 内存二进制字节流。
    同时兼容老版本单图结构与 v2 版本快照结构，并在文件名附带清晰版本标签。
    """
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for idx, item in enumerate(images, start=1):
            img_path = item.get("image_path")
            if img_path and os.path.exists(img_path):
                ext = Path(img_path).suffix or ".jpg"
                name_clean = item.get("name", f"image_{idx}").replace(" ", "_")
                ver_num = item.get("active_version")
                ver_tag = f"_v{ver_num}" if ver_num else ""
                arcname = f"{idx:02d}_{name_clean}{ver_tag}{ext}"
                zip_file.write(img_path, arcname=arcname)
    buffer.seek(0)
    return buffer.getvalue()


def _worker_single_image(
    idx: int,
    item: Dict[str, Any],
    config_snapshot: Dict[str, Any],
    aspect_ratio: str,
) -> Tuple[int, Dict[str, Any]]:
    """
    【彻底根除多线程 Context 丢失 Bug 的无状态纯函数】
    严格要求：
    1. 绝不访问 streamlit 任何上下文 (st.* / st.session_state)；
    2. 完全基于显式参数 config_snapshot 与 aspect_ratio 运行；
    3. 返回独立纯字典供主线程在 as_completed 中安全持久化。
    """
    p = item.get("prompt", "").strip()
    t_id = item.get("id", f"item_{idx+1}")
    t_name = item.get("name", f"商业大片_{idx+1}")
    t_desc = item.get("desc", "")

    res = {
        "id": t_id,
        "name": t_name,
        "desc": t_desc,
        "prompt": p,
        "image_path": None,
        "status": "pending",
        "error": None,
        "aspect_ratio": aspect_ratio,
    }
    try:
        img_path = run_phase_two(
            edited_prompt=p,
            config=config_snapshot,
            aspect_ratio=aspect_ratio,
            filename_prefix=t_id,
        )
        res["image_path"] = img_path
        res["status"] = "success"
    except Exception as ex:
        res["status"] = "failed"
        res["error"] = str(ex)
    return idx, res


# ----------------- 主程序入口 -----------------
def main():
    st.set_page_config(
        page_title="Commercial Studio - 电商商业摄影与视觉策划工坊",
        page_icon="📸",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 注入高级暗调 Clean SaaS CSS
    inject_modern_studio_css()

    # 全局配置初始化
    if "config" not in st.session_state:
        st.session_state.config = load_config()

    # 读取并初始化会话
    all_sessions = list_sessions()
    if not all_sessions:
        default_sess = create_session(
            name="极简智能随行保温杯商业全案",
            product_info={
                "name": "极简智能真空气密随行保温杯",
                "category": "316L医用不锈钢内胆 / 哑光亲肤磨砂黑涂层 / LED触控镜面水温数显",
                "target_audience": "25-38岁都市通勤白领、精品咖啡爱好者、注重生活质感的商务出行人士",
                "pain_points": "传统保温杯密封圈易漏水异味、杯盖易烫嘴、外壳磨损掉漆、缺乏高质感设计",
            },
        )
        all_sessions = list_sessions()
        current_sess_id = default_sess["session_id"]
    else:
        current_sess_id = all_sessions[0]["session_id"]

    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = current_sess_id

    valid_ids = [s["session_id"] for s in all_sessions]
    if st.session_state.current_session_id not in valid_ids:
        st.session_state.current_session_id = valid_ids[0]

    # 加载并自动迁移至 v2 会话
    current_session = get_session(st.session_state.current_session_id)
    if not current_session:
        current_session = create_session()
        st.session_state.current_session_id = current_session["session_id"]

    # 当前步骤状态控制
    step_key = f"studio_step_{current_session['session_id']}"
    if step_key not in st.session_state:
        # 根据当前会话数据自动推荐起始步骤
        if current_session.get("generated_images") and any(
            img.get("image_path") for img in current_session.get("generated_images", [])
        ):
            st.session_state[step_key] = 3
        elif current_session.get("prompts_matrix"):
            st.session_state[step_key] = 2
        else:
            st.session_state[step_key] = 1

    current_step = st.session_state[step_key]

    # ----------------- 侧边栏：方案管理与模型工作台 -----------------
    with st.sidebar:
        st.markdown("### 🗂️ 方案工作区")
        st.caption("商用方案持久化存储，支持随时切换与历史回溯。")

        session_options = [s["session_id"] for s in all_sessions]
        session_map = {s["session_id"]: s for s in all_sessions}

        def _format_session_label(sid: str) -> str:
            s_data = session_map.get(sid, {})
            s_name = s_data.get("name") or "未命名专案"
            updated_ts = s_data.get("updated_at") or time.time()
            time_str = time.strftime("%m-%d %H:%M", time.localtime(updated_ts))
            img_count = s_data.get("images_count", 0)
            return f"{s_name} ({time_str}) 📸{img_count}"

        current_idx = (
            session_options.index(st.session_state.current_session_id)
            if st.session_state.current_session_id in session_options
            else 0
        )

        selected_sid = st.selectbox(
            "切换专案方案",
            options=session_options,
            index=current_idx,
            format_func=_format_session_label,
            key="session_selector_box",
            help="切换方案将自动装载商品特征、布景提示词、渲染图版本链与对话历史",
        )

        if selected_sid != st.session_state.current_session_id:
            st.session_state.current_session_id = selected_sid
            st.rerun()

        col_sess_btn1, col_sess_btn2 = st.columns(2)
        with col_sess_btn1:
            if st.button("➕ 新建策划专案", use_container_width=True, type="primary"):
                new_s = create_session()
                st.session_state.current_session_id = new_s["session_id"]
                st.session_state[f"studio_step_{new_s['session_id']}"] = 1
                st.toast("🎉 新商业策划专案已建立！", icon="✨")
                st.rerun()

        with col_sess_btn2:
            if st.button("🗑️ 删除当前专案", use_container_width=True):
                to_delete_id = st.session_state.current_session_id
                delete_session(to_delete_id)
                refreshed_list = list_sessions()
                if refreshed_list:
                    st.session_state.current_session_id = refreshed_list[0]["session_id"]
                else:
                    new_empty = create_session()
                    st.session_state.current_session_id = new_empty["session_id"]
                st.toast("🗑️ 专案已清理！", icon="⚠️")
                st.rerun()

        st.divider()

        # 侧边栏折叠：摄影渲染引擎与智能体模型配置
        with st.expander("⚙️ 商业摄影引擎配置", expanded=False):
            current_provider = st.session_state.config.get("active_provider", "gemini")
            provider_options = ["gemini", "openai"]
            provider_idx = provider_options.index(current_provider) if current_provider in provider_options else 0
            selected_provider = st.selectbox(
                "核心渲染驱动引擎",
                options=provider_options,
                index=provider_idx,
                help="推荐 Gemini：原生支持实拍多模态深度理解与 Imagen 3 顶级商业光影渲染",
            )
            st.session_state.config["active_provider"] = selected_provider

            if selected_provider == "gemini":
                gemini_key = st.text_input(
                    "Gemini API Key",
                    value=st.session_state.config.get("gemini", {}).get("api_key", ""),
                    type="password",
                    placeholder="AIzaSy...",
                )
                gemini_model = render_model_selector(
                    label="多模态洞察模型",
                    current_value=st.session_state.config.get("gemini", {}).get("model", "gemini-2.0-flash"),
                    preset_options=[
                        "gemini-2.5-flash-preview",
                        "gemini-2.0-flash",
                        "gemini-2.0-pro-exp-02-05",
                        "gemini-1.5-pro",
                    ],
                    key_prefix="gemini_model",
                )
                gemini_image_model = render_model_selector(
                    label="商业大片渲染模型 (Imagen)",
                    current_value=st.session_state.config.get("gemini", {}).get("image_model", "imagen-3.0-generate-002"),
                    preset_options=[
                        "imagen-3.0-generate-002",
                        "imagen-3.0-fast-generate-001",
                    ],
                    key_prefix="gemini_image_model",
                )
                st.session_state.config["gemini"]["api_key"] = gemini_key
                st.session_state.config["gemini"]["model"] = gemini_model
                st.session_state.config["gemini"]["image_model"] = gemini_image_model
            else:
                openai_key = st.text_input(
                    "OpenAI API Key",
                    value=st.session_state.config.get("openai", {}).get("api_key", ""),
                    type="password",
                    placeholder="sk-...",
                )
                openai_base = st.text_input(
                    "OpenAI Base URL",
                    value=st.session_state.config.get("openai", {}).get("base_url", "https://api.openai.com/v1"),
                )
                openai_model = render_model_selector(
                    label="多模态洞察模型",
                    current_value=st.session_state.config.get("openai", {}).get("model", "gpt-4o"),
                    preset_options=["gpt-4o", "gpt-4o-mini"],
                    key_prefix="openai_model",
                )
                openai_image_model = render_model_selector(
                    label="商业大片渲染模型 (DALL-E)",
                    current_value=st.session_state.config.get("openai", {}).get("image_model", "dall-e-3"),
                    preset_options=["dall-e-3", "dall-e-2"],
                    key_prefix="openai_image_model",
                )
                st.session_state.config["openai"]["api_key"] = openai_key
                st.session_state.config["openai"]["base_url"] = openai_base
                st.session_state.config["openai"]["model"] = openai_model
                st.session_state.config["openai"]["image_model"] = openai_image_model

            col_cfg1, col_cfg2 = st.columns(2)
            with col_cfg1:
                if st.button("💾 保存配置", use_container_width=True):
                    save_config(st.session_state.config)
                    st.toast("✅ 引擎配置已持久化保存！", icon="💾")
            with col_cfg2:
                if st.button("🔄 恢复默认", use_container_width=True):
                    st.session_state.config = reset_to_defaults()
                    st.rerun()

        # 侧边栏常驻：首席视觉创意顾问
        st.divider()
        st.markdown("### 💬 首席视觉创意顾问")
        st.caption("商业视觉总监与转化战略智囊，随时解答构图与营销文案。")
        chat_history = current_session.get("chat_history", [])

        with st.expander(f"展开对话面板 ({len(chat_history)} 条记录)", expanded=False):
            if chat_history:
                for msg in chat_history[-6:]:
                    r = msg.get("role", "user")
                    c = msg.get("content", "")
                    st.markdown(f"**{'👤 您' if r == 'user' else '🎨 视觉总监'}**: {c}")
            else:
                st.caption("暂无对话，可在下方提出关于商品视觉定位或镜头指导的疑问。")

            user_q = st.text_input(
                "咨询顾问",
                placeholder="例如：如何强化数显杯盖的科技质感？",
                key=f"sidebar_chat_in_{current_session['session_id']}",
            )
            if st.button("发送咨询", key=f"sidebar_chat_send_{current_session['session_id']}", use_container_width=True):
                if user_q.strip():
                    add_chat_message(current_session["session_id"], "user", user_q.strip())
                    current_session = get_session(current_session["session_id"])
                    with st.spinner("顾问梳理中..."):
                        try:
                            ans = chat_with_agent(
                                session_data=current_session,
                                user_message=user_q.strip(),
                                config=st.session_state.config,
                            )
                            add_chat_message(current_session["session_id"], "assistant", ans)
                            st.rerun()
                        except Exception as ex:
                            st.error(f"顾问回复受阻: {ex}")

    # ----------------- 顶部主工作台 Header -----------------
    sess_name = current_session.get("name", "未命名商业策划方案")
    sess_prod = current_session.get("product_info", {}).get("name", "未命名商品")
    sess_created = time.strftime(
        "%Y-%m-%d %H:%M",
        time.localtime(current_session.get("created_at", time.time())),
    )

    top_h_col1, top_h_col2 = st.columns([3.2, 1.8])
    with top_h_col1:
        st.title("📸 Commercial Studio 商业摄影与视觉工坊")
        st.caption("专为品牌主理人与视觉总监打造的商业级视觉策划与 3x3 摄影渲染系统")

    with top_h_col2:
        # 顾问浮层 Popover 与专案更名
        with st.popover("💬 首席视觉创意顾问 (全景唤起)", use_container_width=True):
            st.markdown("#### 🎨 首席商业视觉顾问")
            st.caption("随时基于当前商品方案与 9 大布景指导提供专业诊断。")
            copilot_box = st.container(height=260)
            with copilot_box:
                if not chat_history:
                    st.info("您好！我是您的品牌视觉创意总监。请随时向我咨询构图布景、卖点破局或详情页排版思路！")
                else:
                    for msg in chat_history:
                        role_label = "👤 用户" if msg.get("role") == "user" else "🎨 视觉总监"
                        st.markdown(f"**{role_label}**: {msg.get('content', '')}")

            copilot_query = st.chat_input("向首席视觉总监请教（如：首图怎样更具奢华感？）", key="drawer_copilot_input")
            if copilot_query:
                add_chat_message(current_session["session_id"], "user", copilot_query)
                current_session = get_session(current_session["session_id"])
                try:
                    rep = chat_with_agent(
                        session_data=current_session,
                        user_message=copilot_query,
                        config=st.session_state.config,
                    )
                    add_chat_message(current_session["session_id"], "assistant", rep)
                    st.rerun()
                except Exception as ex:
                    st.error(f"咨询失败: {ex}")

        # 方案重命名
        new_name_val = st.text_input(
            "专案方案命名",
            value=sess_name,
            key=f"sess_name_input_{current_session['session_id']}",
            help="失焦或回车即可保存专案名称",
        )
        if new_name_val.strip() and new_name_val.strip() != sess_name:
            current_session["name"] = new_name_val.strip()
            save_session(current_session)
            st.toast("✅ 专案名称已更新！", icon="📝")

    # ----------------- 4 步向导式沉浸流导轨 (Guided Stepper) -----------------
    st.markdown("<div class='stepper-header-box'>", unsafe_allow_html=True)
    step_col1, step_col2, step_col3, step_col4 = st.columns(4)

    gen_images_count = sum(
        1 for img in current_session.get("generated_images", []) if img.get("image_path")
    )
    has_matrix = bool(current_session.get("prompts_matrix"))

    step_items = [
        (1, "Step 1: 📦 商品资产录入", True),
        (2, "Step 2: 📐 9大视觉策划", has_matrix),
        (3, f"Step 3: 🎨 商业出图工坊 ({gen_images_count}/9)", has_matrix),
        (4, "Step 4: 📦 全套物料交付", gen_images_count > 0),
    ]

    for col, (s_num, s_title, s_ready) in zip([step_col1, step_col2, step_col3, step_col4], step_items):
        with col:
            is_active = current_step == s_num
            btn_type = "primary" if is_active else "secondary"
            btn_label = f"{'● ' if is_active else '○ '}{s_title}"
            if st.button(
                btn_label,
                key=f"btn_stepper_nav_{s_num}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state[step_key] = s_num
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 步骤一：📦 商品资产与特征录入 (Asset Onboarding)
    # -------------------------------------------------------------
    if current_step == 1:
        st.markdown("### 📦 步骤一：商品核心资产与多模态实物特征录入")
        st.caption("录入商品工业设计、核心材质与目标客群，上传实拍照让系统精准感知微距质感与光影细节。")

        saved_prod = current_session.get("product_info", {})
        c_p_left, c_p_right = st.columns([1.2, 1], gap="large")

        with c_p_left:
            with st.container(border=True):
                st.markdown("#### 🏷️ 商业资产档案")
                p_name = st.text_input(
                    "商品名称 *",
                    value=saved_prod.get("name", "极简智能真空气密随行保温杯"),
                    placeholder="例如：极简智能随行保温杯",
                    key=f"input_p_name_{current_session['session_id']}",
                )
                p_cat = st.text_area(
                    "材质工艺与工业外观特征",
                    value=saved_prod.get(
                        "category",
                        "316L医用不锈钢内胆 / 哑光亲肤磨砂黑涂层 / LED触控镜面水温数显盖",
                    ),
                    height=80,
                    placeholder="例如：316L不锈钢内胆、磨砂黑亲肤涂层、金属倒角边缘",
                    key=f"input_p_cat_{current_session['session_id']}",
                )
                p_aud = st.text_input(
                    "目标客群画像与生活场景",
                    value=saved_prod.get(
                        "target_audience",
                        "25-38岁都市通勤白领、精品咖啡爱好者、注重生活质感的商务出行人士",
                    ),
                    placeholder="例如：都市职场人、健身运动达人",
                    key=f"input_p_aud_{current_session['session_id']}",
                )
                p_pain = st.text_area(
                    "消费心理抗拒点与竞品短板 (痛点破局)",
                    value=saved_prod.get(
                        "pain_points",
                        "传统保温杯密封圈易漏水异味、杯盖易烫嘴、外壳磨损掉漆、缺乏高质感设计",
                    ),
                    height=80,
                    placeholder="例如：市面竞品容易渗水漏水、保温时长不足",
                    key=f"input_p_pain_{current_session['session_id']}",
                )

        with c_p_right:
            with st.container(border=True):
                st.markdown("#### 📸 实物参考资产与特征理解")
                uploaded_files = st.file_uploader(
                    "拖拽上传商品实物照片 (1~5 张)",
                    type=["jpg", "jpeg", "png", "webp"],
                    accept_multiple_files=True,
                    help="实物细节图可帮助多模态引擎精确提炼光影材质、倒角倒影与比例关系",
                    key=f"uploader_{current_session['session_id']}",
                )

                pil_images: List[Image.Image] = []
                if uploaded_files:
                    st.caption(f"已加载 {len(uploaded_files)} 张实拍资产：")
                    u_cols = st.columns(min(len(uploaded_files), 4))
                    for idx, f in enumerate(uploaded_files):
                        try:
                            img = Image.open(f).convert("RGB")
                            pil_images.append(img)
                            with u_cols[idx % 4]:
                                st.image(img, use_container_width=True)
                        except Exception as e:
                            st.warning(f"无法读取图片 {f.name}: {e}")

                # 实物特征预解析徽章展示
                st.markdown(
                    """
                    <div style="margin-top: 10px;">
                        <span class="studio-pill studio-pill-active">#316L医用级内胆</span>
                        <span class="studio-pill studio-pill-neutral">#哑光亲肤磨砂黑</span>
                        <span class="studio-pill studio-pill-success">#LED触控水温数显</span>
                        <span class="studio-pill studio-pill-neutral">#北欧极简工业设计</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("系统已挂载多模态感知通道，将自动融合实物材质特征生成专业布景指导。")

        st.divider()

        # Step 1 底部推进栏
        col_act1, col_act2, col_act3 = st.columns([2.5, 1.2, 1.2])
        with col_act1:
            start_plan_btn = st.button(
                "🚀 启动商业摄影全案推演 (生成 9 大视觉布景矩阵)",
                type="primary",
                use_container_width=True,
            )
        with col_act2:
            if st.button("🧹 重置当前方案", use_container_width=True):
                current_session["analysis_result"] = ""
                current_session["prompts_matrix"] = []
                current_session["generated_images"] = []
                save_session(current_session)
                st.toast("方案已完全重置！", icon="🔄")
                st.rerun()
        with col_act3:
            if has_matrix:
                if st.button("下一步：审阅视觉矩阵 →", use_container_width=True):
                    st.session_state[step_key] = 2
                    st.rerun()

        if start_plan_btn:
            if not p_name.strip():
                st.error("请输入商品名称后再启动策划！")
            else:
                p_info = {
                    "name": p_name.strip(),
                    "category": p_cat.strip(),
                    "target_audience": p_aud.strip(),
                    "pain_points": p_pain.strip(),
                }
                current_session["product_info"] = p_info
                save_session(current_session)

                status_box = st.empty()

                def _log(msg: str):
                    status_box.info(f"⚡ {msg}")

                try:
                    with st.spinner("🤖 商业视觉总监与策划智囊正在审读特征并构建 9 大镜头布景指令..."):
                        analysis_text, prompts_matrix = run_phase_one(
                            product_info=p_info,
                            pil_images=pil_images,
                            config=st.session_state.config,
                            status_callback=_log,
                        )
                        current_session["analysis_result"] = analysis_text
                        current_session["prompts_matrix"] = prompts_matrix

                        # 初始化 9 大图结构
                        new_gen_list = []
                        for item in prompts_matrix:
                            new_gen_list.append({
                                "id": item["id"],
                                "name": item["name"],
                                "desc": item.get("desc", ""),
                                "prompt": item["prompt"],
                                "image_path": None,
                                "status": "pending",
                                "error": None,
                                "versions": [],
                                "active_version": None,
                                "active_version_id": None,
                            })
                        current_session["generated_images"] = new_gen_list
                        current_session["schema_version"] = "2.0"
                        save_session(current_session)

                        st.toast("🎉 商业摄影策划案推演完成！自动进入视觉矩阵审阅！", icon="✨")
                        st.session_state[step_key] = 2
                        st.rerun()
                except Exception as e:
                    status_box.empty()
                    st.error(f"❌ 策划推演受阻: {str(e)}")

    # -------------------------------------------------------------
    # 步骤二：📐 9大视觉矩阵策划与审阅 (Creative Direction)
    # -------------------------------------------------------------
    elif current_step == 2:
        st.markdown("### 📐 步骤二：9 大商业视角摄影策划与镜头语言审阅")
        st.caption("商业视觉总监已针对电商全链路提炼 9 大视角镜头指导。在此审查与就地微调中文布景指令，为人机回路赋予 100% 掌控力。")

        prompts_matrix = current_session.get("prompts_matrix", [])
        analysis_result = current_session.get("analysis_result", "")

        if not prompts_matrix:
            st.warning("⚠️ 暂无视觉策划方案，请先在【步骤一】录入特征并启动策划推演。")
            if st.button("← 返回步骤一进行策划", type="primary"):
                st.session_state[step_key] = 1
                st.rerun()
        else:
            # 顶部方案核心摘要看台
            with st.expander("📄 查看《商业摄影全案策划与消费者心理洞察报告》", expanded=False):
                st.markdown(analysis_result)
                export_md = save_plan_markdown(
                    product_info=current_session.get("product_info", {}),
                    analysis_text=analysis_result,
                    prompt_or_matrix=prompts_matrix,
                )
                if os.path.exists(export_md):
                    with open(export_md, "r", encoding="utf-8") as f_md:
                        st.download_button(
                            "📥 导出商业策划案 (.md)",
                            data=f_md.read(),
                            file_name=os.path.basename(export_md),
                            mime="text/markdown",
                            key="dl_plan_md_step2",
                        )

            # 9 大商业视角卡片网格 / Tabs
            tab_titles = [f"{idx+1}. {item.get('name', f'视角{idx+1}')}" for idx, item in enumerate(prompts_matrix)]
            matrix_tabs = st.tabs(tab_titles)

            matrix_has_changed = False
            for idx, tab in enumerate(matrix_tabs):
                item = prompts_matrix[idx]
                with tab:
                    c_tab_l, c_tab_r = st.columns([2.5, 1.2], gap="large")
                    with c_tab_l:
                        st.markdown(f"**🎯 商业转化定位**：{item.get('desc', '')}")
                        t_area_key = f"lens_prompt_area_{current_session['session_id']}_{item['id']}"
                        edited_p = st.text_area(
                            "镜头语言与布景指导 (包含景深、光影、材质与焦段)：",
                            value=item.get("prompt", ""),
                            height=140,
                            key=t_area_key,
                            help="直接编辑中文布景指导，支持添加如'北欧极简晨光'、'台面带细密冷凝水珠'等镜头语言",
                        )

                        if edited_p.strip() != item.get("prompt", ""):
                            item["prompt"] = edited_p.strip()
                            # 同步更新 generated_images
                            for g_item in current_session.get("generated_images", []):
                                if g_item.get("id") == item["id"]:
                                    g_item["prompt"] = edited_p.strip()
                            matrix_has_changed = True

                    with c_tab_r:
                        st.markdown("**🪄 专家镜头语言微调**")
                        user_refine_wish = st.text_input(
                            "微调意图",
                            placeholder="如：增加晨光侧逆光 / 强调金属拉丝边缘",
                            key=f"wish_input_{item['id']}",
                        )
                        if st.button(
                            "🪄 摄影语言 AI 智能润色",
                            key=f"btn_ai_polish_{item['id']}",
                            use_container_width=True,
                        ):
                            if not user_refine_wish.strip():
                                st.warning("请输入您想增强的光影或布景意图！")
                            else:
                                with st.spinner("视觉专家正在精修镜头指令..."):
                                    try:
                                        polished = refine_prompt_with_ai(
                                            original_prompt=item["prompt"],
                                            user_feedback=user_refine_wish.strip(),
                                            config=st.session_state.config,
                                            image_type_name=item["name"],
                                        )
                                        item["prompt"] = polished
                                        for g_item in current_session.get("generated_images", []):
                                            if g_item.get("id") == item["id"]:
                                                g_item["prompt"] = polished
                                        matrix_has_changed = True
                                        save_session(current_session)
                                        st.toast("✅ 镜头指导已润色就绪！", icon="✨")
                                        st.rerun()
                                    except Exception as ex:
                                        st.error(f"润色失败: {ex}")

                        # 单视角即时测试渲染
                        if st.button(
                            f"🎯 单独测试渲染本视角",
                            key=f"btn_test_render_{item['id']}",
                            use_container_width=True,
                            type="secondary",
                        ):
                            with st.spinner(f"正在对【{item['name']}】执行商业出图..."):
                                try:
                                    ratio_cfg = st.session_state.get(
                                        f"aspect_ratio_{current_session['session_id']}", "1:1"
                                    )
                                    test_img_path = run_phase_two(
                                        edited_prompt=item["prompt"],
                                        config=st.session_state.config,
                                        aspect_ratio=ratio_cfg,
                                        filename_prefix=item["id"],
                                    )
                                    add_image_version(
                                        session_data=current_session,
                                        item_id=item["id"],
                                        image_path=test_img_path,
                                        prompt=item["prompt"],
                                        note="单视角试探性渲染",
                                        aspect_ratio=ratio_cfg,
                                    )
                                    st.toast(f"✅ 【{item['name']}】商业渲染成功！已存入版本链！", icon="📸")
                                    st.rerun()
                                except Exception as ex:
                                    st.error(f"渲染受阻: {ex}")

            if matrix_has_changed:
                current_session["prompts_matrix"] = prompts_matrix
                save_session(current_session)

            st.divider()

            # Step 2 底部推进栏
            col_b2_1, col_b2_2, col_b2_3 = st.columns([1.5, 2, 1.5])
            with col_b2_1:
                if st.button("← 返回修改商品特征 (Step 1)", use_container_width=True):
                    st.session_state[step_key] = 1
                    st.rerun()
            with col_b2_2:
                if st.button(
                    "确认镜头指导，进入商业大片出图工坊 (Step 3) →",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[step_key] = 3
                    st.rerun()
            with col_b2_3:
                st.caption(f"全套 9 大视角镜头指导已就绪")

    # -------------------------------------------------------------
    # 步骤三：🎨 商业大片批量出图与九宫格工坊 (Studio Rendering Canvas)
    # -------------------------------------------------------------
    elif current_step == 3:
        st.markdown("### 🎨 步骤三：商业场景渲染与 3x3 九宫格摄影工坊")
        st.caption("核心商业工作台。支持画幅比例设定、无状态多线程并发渲染、胶卷版本回滚与后悔药机制。")

        prompts_matrix = current_session.get("prompts_matrix", [])
        if not prompts_matrix:
            st.warning("⚠️ 尚未完成视觉矩阵策划，请先前往【步骤二】。")
            if st.button("← 前往策划矩阵", type="primary"):
                st.session_state[step_key] = 2
                st.rerun()
        else:
            # 顶部操作中控台 (Studio Control Bar)
            with st.container(border=True):
                ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.4, 1.2, 2.4])
                with ctrl_col1:
                    aspect_ratio = st.selectbox(
                        "📐 商业画幅比例",
                        options=["1:1", "3:4", "4:3", "9:16", "16:9"],
                        index=0,
                        key=f"aspect_ratio_{current_session['session_id']}",
                        help="1:1 常用于电商搜索白底主图与九宫格方图；3:4 常用于手机详情页首焦图",
                    )
                with ctrl_col2:
                    concurrency = st.slider(
                        "⚡ 并发渲染线程数",
                        min_value=1,
                        max_value=5,
                        value=3,
                        key=f"concurrency_{current_session['session_id']}",
                        help="并发调用可大幅缩减 9 张商业大片出图总耗时",
                    )
                with ctrl_col3:
                    st.write("")
                    st.write("")
                    start_batch_btn = st.button(
                        "🎨 一键并发渲染全套 9 大商业大片",
                        type="primary",
                        use_container_width=True,
                    )

            # 批量并发渲染逻辑（彻底消除 Context 丢失 bug）
            if start_batch_btn:
                total_items = len(prompts_matrix)
                progress_bar = st.progress(0.0, text="🚀 正在启动商业摄影多线程渲染引擎...")
                status_alert = st.empty()

                # 主线程深度快照传参，绝不使子线程触碰 st.*
                config_snapshot = copy.deepcopy(st.session_state.config)
                ratio_val = str(aspect_ratio)

                completed_count = 0
                with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
                    future_map = {
                        executor.submit(_worker_single_image, i, item, config_snapshot, ratio_val): i
                        for i, item in enumerate(prompts_matrix)
                    }

                    for future in concurrent.futures.as_completed(future_map):
                        idx, res = future.result()
                        completed_count += 1
                        frac = completed_count / total_items

                        if res["status"] == "success" and res.get("image_path"):
                            add_image_version(
                                session_data=current_session,
                                item_id=res["id"],
                                image_path=res["image_path"],
                                prompt=res["prompt"],
                                note="首轮并发商业出图",
                                aspect_ratio=ratio_val,
                            )
                        else:
                            for g_item in current_session.get("generated_images", []):
                                if g_item.get("id") == res["id"]:
                                    g_item["status"] = "failed"
                                    g_item["error"] = res.get("error")
                                    break
                            save_session(current_session)

                        progress_bar.progress(
                            frac,
                            text=f"⚡ 进度 ({completed_count}/{total_items}): 【{res['name']}】商业渲染完成...",
                        )

                progress_bar.progress(1.0, text="🎉 全套 9 大商业大片批量渲染完毕！")
                status_alert.success("🎉 全套商业摄影大片已渲染就绪并在下方九宫格画廊呈现！")
                time.sleep(1)
                st.rerun()

            st.write("")

            # ----------------- 3x3 九宫格商业摄影画廊与胶卷版本控制器 -----------------
            generated_images = current_session.get("generated_images", [])
            # 保证 generated_images 与 prompts_matrix 映射对齐
            if not generated_images and prompts_matrix:
                migrate_session_to_v2(current_session)
                generated_images = current_session.get("generated_images", [])

            ready_count = sum(
                1 for img in generated_images if img.get("image_path") and os.path.exists(img.get("image_path"))
            )

            # 画廊顶部状态栏
            g_header_l, g_header_r = st.columns([3, 1])
            with g_header_l:
                st.markdown(f"#### 🖼️ 3x3 商业摄影九宫格设计台 `● 已就绪 {ready_count}/9 张`")
            with g_header_r:
                if ready_count > 0:
                    zip_data = create_images_zip(generated_images)
                    st.download_button(
                        f"📦 打包下载已就绪 {ready_count} 张原图 (ZIP)",
                        data=zip_data,
                        file_name=f"commercial_gallery_{current_session['session_id'][:8]}.zip",
                        mime="application/zip",
                        key=f"zip_dl_step3_{current_session['session_id']}",
                        use_container_width=True,
                    )

            # 循环渲染 3x3 布局
            for row in range(3):
                cols = st.columns(3, gap="medium")
                for col_idx in range(3):
                    item_idx = row * 3 + col_idx
                    if item_idx < len(prompts_matrix):
                        p_meta = prompts_matrix[item_idx]
                        # 查找对应生成的图片项
                        img_item = None
                        for g in generated_images:
                            if g.get("id") == p_meta["id"]:
                                img_item = g
                                break
                        if not img_item:
                            img_item = {
                                "id": p_meta["id"],
                                "name": p_meta["name"],
                                "desc": p_meta.get("desc", ""),
                                "prompt": p_meta["prompt"],
                                "image_path": None,
                                "status": "pending",
                                "versions": [],
                                "active_version": None,
                            }

                        with cols[col_idx]:
                            with st.container(border=True):
                                versions = img_item.get("versions", [])
                                active_v = img_item.get("active_version")

                                # 顶部视角标题与版本状态徽章
                                status_badge = (
                                    f"<span class='studio-pill studio-pill-success'>● v{active_v} (现用)</span>"
                                    if active_v
                                    else "<span class='studio-pill studio-pill-neutral'>⏳ 待渲染</span>"
                                )
                                st.markdown(
                                    f"""
                                    <div class='card-perspective-title'>
                                        <span>{item_idx+1}. {img_item['name']}</span>
                                        {status_badge}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )
                                st.caption(img_item.get("desc", ""))

                                # 胶卷版本切换栏 (Version Strip)
                                if len(versions) > 0:
                                    v_options = [v.get("version_num", 1) for v in versions]
                                    view_ver_key = f"view_v_{img_item['id']}_{current_session['session_id']}"
                                    if view_ver_key not in st.session_state or st.session_state[view_ver_key] not in v_options:
                                        st.session_state[view_ver_key] = active_v or v_options[-1]

                                    if len(versions) > 1:
                                        def _fmt_v_label(vn: int) -> str:
                                            v_obj = next((v for v in versions if v.get("version_num") == vn), {})
                                            tag = " (现用)" if vn == active_v else ""
                                            note_short = v_obj.get("note", "")[:8]
                                            return f"v{vn}{tag} · {note_short}"

                                        cur_select_idx = v_options.index(st.session_state[view_ver_key]) if st.session_state[view_ver_key] in v_options else 0
                                        selected_v_num = st.selectbox(
                                            "🎞️ 胶卷快照版本链",
                                            options=v_options,
                                            index=cur_select_idx,
                                            format_func=_fmt_v_label,
                                            key=f"select_strip_{img_item['id']}_{current_session['session_id']}",
                                            help="切换选择任意历史版本进行查看、对比或一键回滚",
                                        )
                                        st.session_state[view_ver_key] = selected_v_num

                                    # 当前查看的版本对象
                                    viewing_v_num = st.session_state[view_ver_key]
                                    viewing_v_obj = next(
                                        (v for v in versions if v.get("version_num") == viewing_v_num),
                                        versions[-1],
                                    )
                                    display_img_path = viewing_v_obj.get("image_path")
                                    display_prompt = viewing_v_obj.get("prompt", "")
                                else:
                                    display_img_path = img_item.get("image_path")
                                    display_prompt = img_item.get("prompt", "")
                                    viewing_v_num = None
                                    viewing_v_obj = None

                                # 图片渲染区
                                if display_img_path and os.path.exists(display_img_path):
                                    st.image(display_img_path, use_container_width=True)

                                    # 如果当前正在查看非现用的历史版本，展示一键回滚操作
                                    if viewing_v_num and viewing_v_num != active_v:
                                        st.info(f"👁️ 正在预览历史版本 v{viewing_v_num} · 批注: {viewing_v_obj.get('note', '')}")
                                        if st.button(
                                            f"⏪ 回退为此版本 (Rollback to v{viewing_v_num})",
                                            key=f"btn_rollback_{img_item['id']}_{viewing_v_num}",
                                            use_container_width=True,
                                            type="primary",
                                        ):
                                            rollback_to_version(current_session, img_item["id"], viewing_v_num)
                                            st.toast(f"✅ 【{img_item['name']}】已成功回退为 v{viewing_v_num}！", icon="⏪")
                                            st.rerun()

                                    # 单图下载
                                    with open(display_img_path, "rb") as f_img:
                                        img_bytes = f_img.read()
                                    st.download_button(
                                        label="📥 下载本版本原图",
                                        data=img_bytes,
                                        file_name=os.path.basename(display_img_path),
                                        mime="image/jpeg",
                                        key=f"dl_img_{img_item['id']}_{viewing_v_num}",
                                        use_container_width=True,
                                    )
                                else:
                                    if img_item.get("status") == "failed":
                                        st.error(f"⚠️ 渲染失败: {img_item.get('error', '未知错误')}")
                                    else:
                                        st.info("商业大片待出图。")

                                    # 单独生成本卡片
                                    if st.button(
                                        f"⚡ 渲染本视角大片",
                                        key=f"btn_gen_single_{img_item['id']}",
                                        use_container_width=True,
                                        type="primary",
                                    ):
                                        with st.spinner(f"正在渲染【{img_item['name']}】..."):
                                            try:
                                                ratio_cfg = st.session_state.get(
                                                    f"aspect_ratio_{current_session['session_id']}", "1:1"
                                                )
                                                single_p = run_phase_two(
                                                    edited_prompt=img_item["prompt"],
                                                    config=st.session_state.config,
                                                    aspect_ratio=ratio_cfg,
                                                    filename_prefix=img_item["id"],
                                                )
                                                add_image_version(
                                                    session_data=current_session,
                                                    item_id=img_item["id"],
                                                    image_path=single_p,
                                                    prompt=img_item["prompt"],
                                                    note="单图初次渲染",
                                                    aspect_ratio=ratio_cfg,
                                                )
                                                st.toast(f"✅ 【{img_item['name']}】渲染完成！", icon="📸")
                                                st.rerun()
                                            except Exception as ex:
                                                st.error(f"出图受阻: {ex}")

                                # 底部抽屉：🪄 商业摄影镜头二次微调（追加版本快照，不覆盖老图）
                                with st.expander("🪄 商业摄影镜头二次微调 (AI 重塑新版)", expanded=False):
                                    st.caption("输入自然语言修改意见，系统将重塑镜头指令并渲染全新版本追加到版本链末尾：")
                                    refine_input = st.text_input(
                                        "镜头调整意见",
                                        placeholder="例如：将台面换成深色大理石，增加清晨侧逆光与蒸汽水汽",
                                        key=f"refine_in_{img_item['id']}_{current_session['session_id']}",
                                    )
                                    if st.button(
                                        "✨ 渲染新版本快照 (追加到版本链)",
                                        key=f"btn_commit_refine_{img_item['id']}",
                                        use_container_width=True,
                                    ):
                                        if not refine_input.strip():
                                            st.warning("请输入调整意见！")
                                        else:
                                            with st.spinner(f"正在智能调整【{img_item['name']}】布景并渲染新版本..."):
                                                try:
                                                    refined_prompt = refine_prompt_with_ai(
                                                        original_prompt=display_prompt or img_item["prompt"],
                                                        user_feedback=refine_input.strip(),
                                                        config=st.session_state.config,
                                                        image_type_name=img_item["name"],
                                                    )
                                                    ratio_cfg = st.session_state.get(
                                                        f"aspect_ratio_{current_session['session_id']}", "1:1"
                                                    )
                                                    new_rendered_path = run_phase_two(
                                                        edited_prompt=refined_prompt,
                                                        config=st.session_state.config,
                                                        aspect_ratio=ratio_cfg,
                                                        filename_prefix=img_item["id"],
                                                    )
                                                    add_image_version(
                                                        session_data=current_session,
                                                        item_id=img_item["id"],
                                                        image_path=new_rendered_path,
                                                        prompt=refined_prompt,
                                                        note=f"微调: {refine_input.strip()[:10]}",
                                                        aspect_ratio=ratio_cfg,
                                                    )
                                                    st.toast(f"🎉 【{img_item['name']}】新版本快照已生成并入库！", icon="✨")
                                                    st.rerun()
                                                except Exception as ex:
                                                    st.error(f"微调渲染受阻: {ex}")

            st.divider()

            # Step 3 底部推进栏
            col_b3_1, col_b3_2, col_b3_3 = st.columns([1.5, 2, 1.5])
            with col_b3_1:
                if st.button("← 返回视觉矩阵策划 (Step 2)", use_container_width=True):
                    st.session_state[step_key] = 2
                    st.rerun()
            with col_b3_2:
                if st.button(
                    "前往全套物料交付与精修工坊 (Step 4) →",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state[step_key] = 4
                    st.rerun()
            with col_b3_3:
                st.caption(f"当前完成度：{ready_count} / {len(prompts_matrix)} 张已入库")

    # -------------------------------------------------------------
    # 步骤四：📦 全套物料交付与精修工坊 (Asset Packaging & Handoff)
    # -------------------------------------------------------------
    elif current_step == 4:
        st.markdown("### 📦 步骤四：全套商业物料交付与精修工坊")
        st.caption("一站式检视 9 大视角现用商业大片资产、一键打包全套商用原图、导出策划 Markdown 报告并开辟新方案。")

        generated_images = current_session.get("generated_images", [])
        prompts_matrix = current_session.get("prompts_matrix", [])
        active_ready_images = [
            img for img in generated_images if img.get("image_path") and os.path.exists(img.get("image_path"))
        ]

        # 交付工具箱 (Delivery Action Bar)
        with st.container(border=True):
            st.markdown("#### 🚀 一键交付工具中枢")
            deliv_c1, deliv_c2, deliv_c3 = st.columns(3)

            with deliv_c1:
                if active_ready_images:
                    full_zip_bytes = create_images_zip(active_ready_images)
                    st.download_button(
                        label=f"📦 一键打包下载全部 {len(active_ready_images)} 张商业原图 (ZIP)",
                        data=full_zip_bytes,
                        file_name=f"ecommerce_full_package_{current_session['session_id'][:8]}.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True,
                        key="btn_full_zip_step4",
                    )
                else:
                    st.button("📦 暂无可下载的商业原图", disabled=True, use_container_width=True)

            with deliv_c2:
                analysis_text = current_session.get("analysis_result", "")
                if analysis_text or prompts_matrix:
                    md_path = save_plan_markdown(
                        product_info=current_session.get("product_info", {}),
                        analysis_text=analysis_text,
                        prompt_or_matrix=prompts_matrix,
                    )
                    if os.path.exists(md_path):
                        with open(md_path, "r", encoding="utf-8") as f_md:
                            md_body = f_md.read()
                        st.download_button(
                            label="📄 导出完整商业策划案报告 (.md)",
                            data=md_body,
                            file_name=os.path.basename(md_path),
                            mime="text/markdown",
                            use_container_width=True,
                            key="btn_md_step4",
                        )
                else:
                    st.button("📄 导出完整商业策划案报告", disabled=True, use_container_width=True)

            with deliv_c3:
                # 复制全套 9 大图提示词文本
                matrix_prompts_txt = "\n\n".join(
                    [
                        f"### {idx+1}. {item.get('name', '')}\n【镜头布景指导】：{item.get('prompt', '')}"
                        for idx, item in enumerate(prompts_matrix)
                    ]
                )
                with st.popover("📋 检视全套镜头布景提示词清单", use_container_width=True):
                    st.text_area(
                        "全套布景指令清单（可直接复制于 ComfyUI 或 Midjourney 复用）：",
                        value=matrix_prompts_txt,
                        height=260,
                    )

        st.markdown("#### 🖼️ 全景商用大片资产总览 (Master Assets Grid)")

        if not active_ready_images:
            st.info("💡 尚未渲染商业大片，请返回【步骤三】批量出图！")
        else:
            # 渲染物料总览卡片
            m_cols = st.columns(3, gap="medium")
            for idx, img_item in enumerate(active_ready_images):
                with m_cols[idx % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{img_item.get('name', f'视角_{idx+1}')}** `v{img_item.get('active_version', 1)}`")
                        st.image(img_item["image_path"], use_container_width=True)
                        st.caption(f"批注: {img_item.get('versions', [{}])[-1].get('note', '商用交付图')}")

        st.divider()

        # Step 4 底部推进栏
        col_b4_1, col_b4_2 = st.columns([2, 2])
        with col_b4_1:
            if st.button("← 返回商业出图工坊进行精修 (Step 3)", use_container_width=True):
                st.session_state[step_key] = 3
                st.rerun()
        with col_b4_2:
            if st.button("➕ 保存当前方案并开辟新商品工坊", type="primary", use_container_width=True):
                new_s = create_session()
                st.session_state.current_session_id = new_s["session_id"]
                st.session_state[f"studio_step_{new_s['session_id']}"] = 1
                st.toast("🎉 新工坊方案已开辟！", icon="✨")
                st.rerun()


if __name__ == "__main__":
    main()
