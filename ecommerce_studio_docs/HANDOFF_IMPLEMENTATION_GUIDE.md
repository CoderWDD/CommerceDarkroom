# 电商智能策划与生图工作台 (Ecommerce AI Studio) - 落地实施交接文档

> **致接手本项目的 AI / 开发者：**  
> 本文档旨在为您提供最清晰、可立即执行的落地指导。用户需要一个**带 Web 前端**的电商策划与生图工作台，拒绝纯命令行，支持**上传多张实拍商品图**、支持**在线修改提示词与模型配置**、支持**人在回路（Human-in-the-Loop）二次人工修改文案与Prompt**，最后**生成高清电商主图并可预览**。请根据本指南逐步完成代码实现。

---

## 1. 推荐技术选型

| 模块 | 选型 | 理由 |
| :--- | :--- | :--- |
| **前端交互** | **Streamlit** | Python 纯原生生态，支持多图拖拽上传、侧边栏设置抽屉、可编辑文本域、大图预览画廊、会话状态保持（Session State），开发效率最高。 |
| **智能体编排** | **CrewAI** | 用户已拉取 CrewAI 项目，利用其 Agent、Task 角色分工体系处理商业痛点挖掘与场景创意。 |
| **多模态与大脑**| **Google Gemini 2.0 Flash/Pro** 或 **GPT-4o** | 具备顶级的图文理解能力，能同时审视用户上传的多张商品图并提炼工业材质特征。 |
| **底层生图引擎**| **Google Imagen 3** (`imagen-3.0-generate-002`) 或 **OpenAI DALL-E 3** | 首选 Imagen 3，商业产品光影、材质真实度与英文文字排版极强。 |

---

## 2. 目标工程目录结构

建议在工程根目录下建立如下清晰的独立模块目录（例如 `ecommerce_studio/`）：

```text
ecommerce_studio/
├── app.py                      # Streamlit 界面主入口 (UI组件、交互逻辑、SessionState维护)
├── config_manager.py           # 负责读取/保存前端配置（API Key, Model, 各Agent提示词）到本地 JSON
├── default_config.json         # 默认提示词与模型配置模板
├── studio_crew.py              # 核心大脑：负责串联多模态读图、痛点挖掘、场景策划 Agent
├── tools/
│   ├── __init__.py
│   └── image_tool.py           # 生图工具：调用 Imagen 3 / DALL-E 3 并自动存盘到 output/
├── output/                     # 自动存放生成的策划案 Markdown 与生成的商业主图 JPG
└── requirements.txt            # 项目依赖
```

---

## 3. 核心机制与关键代码原型

### 3.1 人在回路（Human-in-the-Loop）两段式流程设计
在 `app.py` 中利用 `st.session_state` 实现分阶段执行与二次人工修改：

```python
import streamlit as st

# 状态初始化
if "stage" not in st.session_state:
    st.session_state.stage = "input" # input -> reviewed -> generated
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "final_prompt" not in st.session_state:
    st.session_state.final_prompt = ""

# 阶段 1：触发痛点分析与场景构思
if st.button("🚀 阶段一：AI 深度分析与视觉策划"):
    with st.spinner("AI 专家团队正在审视商品图、分析买家痛点并推演场景..."):
        # 调用 studio_crew 执行第一阶段
        analysis_text, prompt = run_phase_one(product_info, uploaded_images)
        st.session_state.analysis_result = analysis_text
        st.session_state.final_prompt = prompt
        st.session_state.stage = "reviewed"

# 阶段 2：人工审查与二次微调（仅在第一阶段完成后展示）
if st.session_state.stage in ["reviewed", "generated"]:
    st.subheader("✏️ 策划案与生图 Prompt 二次调整")
    st.info("您可以在下方直接编辑修改文案或场景 Prompt，确认后点击生成：")
    
    edited_prompt = st.text_area(
        "最终英文生图 Prompt（可直接微调）：", 
        value=st.session_state.final_prompt, 
        height=120
    )
    
    if st.button("🎨 阶段二：确认方案，开始生成电商图"):
        with st.spinner("生图引擎渲染中..."):
            image_path = run_phase_two(edited_prompt)
            st.session_state.image_path = image_path
            st.session_state.stage = "generated"

# 阶段 3：成果展示
if st.session_state.stage == "generated":
    st.subheader("🖼️ 最终电商主图预览")
    st.image(st.session_state.image_path, caption="AI 生成商业主图", use_container_width=True)
    with open(st.session_state.image_path, "rb") as file:
        st.download_button("📥 下载高清电商图", data=file, file_name="ecommerce_main.jpg")
```

---

### 3.2 多模态商品图特征提取（Vision LLM）
在 `studio_crew.py` 中，使用 Gemini SDK 同时输入文字和用户上传的 PIL Image：

```python
from google import genai
from google.genai import types
from PIL import Image

def analyze_product_multimodal(client, text_info: str, pil_images: list[Image.Image]):
    prompt = f"""
    你是一名顶级电商视觉总监与工业设计审图专家。
    以下是商品的文字信息：
    {text_info}
    
    请仔细审视上传的商品实物图，提取：
    1. 商品外观工业设计特征（主体颜色、材质是磨砂/镜面/金属/玻璃、线条形状）
    2. 核心细节（把手、按键、屏幕、LOGO位置等）
    3. 结合买家痛点，推演最能衬托商品质感的真实生活场景。
    """
    
    contents = [prompt] + pil_images
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=contents
    )
    return response.text
```

---

### 3.3 生图工具（Google Imagen 3 自动存盘）
位于 `tools/image_tool.py`：

```python
import os
import time
from google import genai
from google.genai import types

def generate_ecommerce_image(prompt: str, output_dir: str = "output") -> str:
    os.makedirs(output_dir, exist_ok=True)
    client = genai.Client()
    
    response = client.models.generate_images(
        model='imagen-3.0-generate-002',
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio="1:1",          # 1:1电商主图
            person_generation="allow_adult",
            output_mime_type="image/jpeg"
        )
    )
    
    file_name = f"product_{int(time.time())}.jpg"
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, "wb") as f:
        f.write(response.generated_images[0].image.image_bytes)
        
    return file_path
```

---

## 4. 实施执行步骤清单（Implementation Checklist）

接手实施的 AI / 开发者应按以下步骤依序落地：

- [ ] **Step 1: 安装必要环境依赖**
  ```bash
  pip install streamlit google-genai openai pillow pydantic python-dotenv
  ```
- [ ] **Step 2: 建立 `config_manager.py` 与 `default_config.json`**
  * 支持前端读写保存：`gemini_api_key`, `openai_api_key`, `active_provider`, 以及 3 个 Agent 的自定义提示词。
- [ ] **Step 3: 编写 `tools/image_tool.py`**
  * 封装 Imagen 3 与 DALL-E 3 生图接口，支持指定比例并自动存盘为本地 JPG。
- [ ] **Step 4: 编写 `studio_crew.py`**
  * 实现多模态图片 + 文字的痛点分析任务。
  * 实现输出结构化方案（痛点剖析、营销文案、英文生图 Prompt）。
- [ ] **Step 5: 编写 `app.py`（Streamlit 完整界面）**
  * 侧边栏：API Key 与 System Prompt 在线配置面板（支持点击保存）。
  * 中间区：商品信息表单 + `st.file_uploader(accept_multiple_files=True)` 多图上传与缩略图预览。
  * 工作流区：两段式执行按钮 + 人工富文本二次微调文本框。
  * 预览区：高清大图展示与下载按钮。
- [ ] **Step 6: 本地启动与端到端测试**
  ```bash
  streamlit run ecommerce_studio/app.py
  ```
  输入测试商品（如便携保温杯），上传 1 张图，验证“分析 $\rightarrow$ 手动修改 $\rightarrow$ 成功出图并下载”。
