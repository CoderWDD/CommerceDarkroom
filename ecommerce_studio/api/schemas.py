import time
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ProductDossier(BaseModel):
    product_name: Optional[str] = Field(default="", description="商品全称")
    name: Optional[str] = Field(default="", description="兼容名称字段")
    category: Optional[str] = Field(default="", description="品类属性")
    material_features: Optional[str] = Field(default="", description="材质工艺与工业特征")
    target_users: Optional[str] = Field(default="", description="目标客群画像")
    target_audience: Optional[str] = Field(default="", description="兼容目标客群字段")
    pain_points: Optional[str] = Field(default="", description="竞品短板与买家核心抗拒点")
    reference_images: Optional[List[str]] = Field(default_factory=list, description="实物参考图URL列表")


class StrategySummary(BaseModel):
    tone: str = Field(default="商业极简、顶级精工与生活格调", description="品牌视觉调性")
    usp: str = Field(default="直击痛点的极致视觉呈现", description="核心击穿卖点")
    color_palette: List[str] = Field(default_factory=list, description="推荐主色系与光影调色板")


class PerspectiveVersion(BaseModel):
    version_id: str = Field(..., description="版本ID，如 v1")
    version_num: int = Field(default=1, description="版本序列号")
    image_url: Optional[str] = Field(default=None, description="前端展示URL (/output/...)")
    image_path: Optional[str] = Field(default=None, description="后端物理磁盘绝对路径")
    prompt_zh: str = Field(default="", description="该版本确切中文生图镜头指导")
    timestamp: int = Field(default_factory=lambda: int(time.time()), description="创建时间戳")
    created_at_fmt: Optional[str] = Field(default="", description="格式化时间字符串")
    trigger_type: str = Field(default="manual_edit", description="触发类型: batch_initial / manual_edit / ai_refine")
    change_reason: str = Field(default="", description="修改动机或微调说明")
    aspect_ratio: str = Field(default="1:1", description="画幅比例: 1:1, 3:4, 16:9")
    status: str = Field(default="success", description="版本状态: success / error / pending")
    error: Optional[str] = Field(default=None, description="错误日志")


class Perspective(BaseModel):
    id: str = Field(..., description="视角标准唯一标识，如 01_white_bg 或 main_white_bg")
    alt_id: Optional[str] = Field(default=None, description="兼容别名")
    name: str = Field(..., description="视角专业中文名称")
    desc: Optional[str] = Field(default="", description="视角商业转化说明")
    tag: Optional[str] = Field(default="", description="转化心理学标签，如 CTR收割机")
    category: Optional[str] = Field(default="", description="商业分类")
    psychology_target: Optional[str] = Field(default="", description="消费心理学靶向目标")
    prompt_zh: str = Field(default="", description="当前镜头布景指导")
    active_version_id: Optional[str] = Field(default=None, description="当前激活展示的版本ID，如 v1")
    image_url: Optional[str] = Field(default=None, description="当前激活版本展示图URL (/output/...)")
    image_path: Optional[str] = Field(default=None, description="当前激活版本本地文件路径")
    render_status: Optional[str] = Field(default="idle", description="卡片状态: idle / rendering / pending / success / error")
    render_progress: Optional[int] = Field(default=0, description="卡片进度 0-100")
    versions: List[PerspectiveVersion] = Field(default_factory=list, description="历史版本快照链条")
    status: str = Field(default="idle", description="当前卡片状态: idle / rendering / success / error")
    error: Optional[str] = Field(default=None, description="渲染异常信息")


class ChatMessage(BaseModel):
    role: str = Field(..., description="角色: user / assistant / system")
    content: str = Field(..., description="对话消息正文")
    timestamp: int = Field(default_factory=lambda: int(time.time()), description="时间戳")


class StudioSession(BaseModel):
    session_id: str = Field(..., description="会话唯一ID")
    id: Optional[str] = Field(default=None, description="兼容前端会话ID")
    name: str = Field(default="", description="策划专案名称")
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))
    product_info: Dict[str, Any] = Field(default_factory=dict, description="商品档案")
    strategy_summary: Optional[StrategySummary] = Field(default=None, description="视觉总监策划全案摘要")
    perspectives: List[Perspective] = Field(default_factory=list, description="9大商业转化视角矩阵")
    prompts_matrix: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="兼容老矩阵结构")
    generated_images: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="兼容老生成图结构")
    chat_history: List[ChatMessage] = Field(default_factory=list, description="首席顾问对话历史")
    schema_version: str = Field(default="2.0", description="数据模式版本")


class SessionSummary(BaseModel):
    session_id: str
    name: str
    created_at: int
    updated_at: int
    product_name: Optional[str] = ""
    image_count: int = 0
    images_count: int = 0
    chat_count: int = 0


# --- 请求模型 ---

class CreateSessionRequest(BaseModel):
    name: Optional[str] = Field(default="", description="专案名称")
    product_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="初始化商品信息")


class PlanRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="会话ID，若为空则自动创建")
    product_info: Dict[str, Any] = Field(..., description="商品商业档案信息")
    stream: Optional[bool] = Field(default=False, description="是否以SSE方式流式推演")


class UpdatePromptRequest(BaseModel):
    prompt_zh: str = Field(..., description="新中文镜头指导词")


class RefinePromptRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="会话ID")
    perspective_id: Optional[str] = Field(default=None, description="视角ID")
    instruction: Optional[str] = Field(default=None, description="微调润色意见")
    user_feedback: Optional[str] = Field(default=None, description="兼容参数名")


class RefineSlotRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="会话ID")
    perspective_id: Optional[str] = Field(default=None, description="视角ID")
    prompt_zh: Optional[str] = Field(default=None, description="指定的中文镜头指导词")
    instruction: Optional[str] = Field(default=None, description="微调指示")
    user_feedback: Optional[str] = Field(default=None, description="兼容参数")
    render_now: Optional[bool] = Field(default=False, description="润色后是否立即渲染新版本")
    change_reason: Optional[str] = Field(default="单视角调整重新出图", description="修改动机")
    trigger_type: Optional[str] = Field(default="manual_edit", description="触发源类型")
    aspect_ratio: Optional[str] = Field(default="1:1", description="画幅比例")


class RenderVersionRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="会话ID")
    perspective_id: Optional[str] = Field(default=None, description="视角ID")
    prompt_zh: Optional[str] = Field(default=None, description="指定的中文镜头指导词，为空则取当前视角词")
    instruction: Optional[str] = Field(default=None, description="微调指示")
    user_feedback: Optional[str] = Field(default=None, description="兼容参数")
    change_reason: Optional[str] = Field(default="单视角调整重新出图", description="修改动机")
    trigger_type: Optional[str] = Field(default="manual_edit", description="触发源类型")
    aspect_ratio: Optional[str] = Field(default="1:1", description="画幅比例")


class RollbackRequest(BaseModel):
    session_id: Optional[str] = Field(default=None, description="会话ID")
    perspective_id: Optional[str] = Field(default=None, description="视角ID")
    version_id: Union[str, int] = Field(..., description="目标版本ID (如 'v1' 或 1)")


class BatchRenderRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    aspect_ratio: Optional[str] = Field(default="1:1", description="画幅比例")
    concurrency: Optional[int] = Field(default=1, description="并发度 (默认锁定为1，优先保证长连接稳定性与防止触发网关限流)")
    perspective_ids: Optional[List[str]] = Field(default=None, description="选定渲染的视角ID列表，默认全部9个")
    prompts: Optional[Dict[str, str]] = Field(default=None, description="前端当前各视角镜头指导词映射字典")


class CopilotChatRequest(BaseModel):
    session_id: str = Field(..., description="会话ID")
    message: str = Field(..., description="主理人对话内容")
    context: Optional[Dict[str, Any]] = Field(default=None, description="当前上下文（步骤与聚焦视角ID）")
    stream: Optional[bool] = Field(default=True, description="是否SSE流式返回")


class UpdateConfigRequest(BaseModel):
    active_provider: Optional[str] = None
    gemini: Optional[Dict[str, Any]] = None
    openai: Optional[Dict[str, Any]] = None
    custom_openai: Optional[Dict[str, Any]] = None
    ollama: Optional[Dict[str, Any]] = None

    model_config = {"extra": "allow"}


class TestConnectionRequest(BaseModel):
    provider: str = Field(..., description="gemini / openai / custom_openai / ollama")
    api_key: Optional[str] = Field(default="", description="测试候选密钥")
    base_url: Optional[str] = Field(default="", description="测试候选 Base URL")
    model: Optional[str] = Field(default="", description="测试候选模型")
    image_model: Optional[str] = Field(default="", description="测试候选生图模型")
    check_image_model: Optional[bool] = Field(default=False, description="是否一并探测生图权限")


class TestConnectionResponse(BaseModel):
    success: bool
    provider: str
    latency_ms: int
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)

