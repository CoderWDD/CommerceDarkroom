"""
爆款风格流派引擎与注册中心 (Style Preset Registry)
定义 5 大官方爆款流派参数包：
- minimalist_muji: 极简原研哉 (日系留白)
- nordic_luxury: 北欧轻奢 (莫兰迪低饱和)
- german_deconstruct: 德系解构 (严谨精工工业)
- dopamine_energy: 多巴胺活力 (青年明快撞色)
- cyber_street: 赛博潮酷 (暗夜霓虹潮流)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StylePreset(BaseModel):
    id: str = Field(..., description="流派唯一ID")
    name: str = Field(..., description="中文名称")
    en_name: str = Field(..., description="英文名称")
    tagline: str = Field(..., description="一句话商业定位标语")
    description: str = Field(..., description="流派核心美学阐释")

    # 核心光学与环境 4 大维度
    lighting: str = Field(..., description="光影与布光方案 (主光/辅光/轮廓光)")
    environment: str = Field(..., description="布景道具、台面材质与空间留白基调")
    camera: str = Field(..., description="机位、镜头焦段、光圈与透视关系")
    color_tone: str = Field(..., description="主色调、副色调与色彩饱和度风格")

    # 防漂移参数
    anti_drift_rules: List[str] = Field(
        default_factory=list,
        description="绝对禁止出现的负面视觉特征",
    )
    perspective_enhancements: Dict[str, str] = Field(
        default_factory=dict,
        description="针对特定视角(如01_white_bg, 02_scene)的专用加权提示",
    )


STYLE_PRESET_REGISTRY: Dict[str, StylePreset] = {
    "minimalist_muji": StylePreset(
        id="minimalist_muji",
        name="极简原研哉 (日系留白)",
        en_name="Minimalist Zen & MUJI Aesthetic",
        tagline="大面积纯净留白，晨光漫射，静谧自然克制",
        description="源自日本大师原研哉的空之美学(Emptiness)，去除一切冗余修饰，让商品本身成为空间的视觉重心。",
        lighting="大面积顶光漫反射，微暖柔光箱无刺眼高光，晨光穿透纱帘形成的微弱柔和漫射光，几乎无强烈死黑阴影",
        environment="浅色原木肌理展台、米白高品质微水泥墙面、日式和纸质感、极其克制的微量禅意留白空间",
        camera="50mm 标准商业静物中焦段，正面微俯角15度，f/8 中等景深确保商品细节全清晰，透视自然无畸变",
        color_tone="温暖燕麦色、纯净米白、浅卡其、浅原木色，低饱和度、高明度，呈现天然温润的自然质感",
        anti_drift_rules=["严禁浓艳色彩", "严禁复杂霓虹与暗黑背景", "严禁炫目反光与凌乱道具"],
        perspective_enhancements={
            "01_white_bg": "绝对纯白哑光展台，自然微透极浅柔和接触影，消除任何炫光反冲",
            "02_scene": "伴随一杯清茶或一本极简手账，清晨初阳微抚桌面，营造归家宁静感",
        },
    ),
    "nordic_luxury": StylePreset(
        id="nordic_luxury",
        name="北欧轻奢 (莫兰迪低饱和)",
        en_name="Nordic Minimal Luxury",
        tagline="灰调高级质感，大理石与冷金点缀，中产格调溢价",
        description="斯堪的纳维亚现代家居与高端生活方式的结合，注重材质的高阶灰调与微量金属带来的轻奢冲击力。",
        lighting="侧逆45度自然窗光，伴随柔和丁达尔光束与双色温冷暖漫射，轮廓处有精致的高光细线",
        environment="卡拉拉白大理石台面、哑光黄铜细金属配件、低饱和度莫兰迪色系羊毛织物、几何水磨石",
        camera="85mm 商业人像与特写镜头，f/2.8 中浅景深，背景优雅散景虚化，焦内极致锐利",
        color_tone="莫兰迪灰调（灰绿/灰粉/燕麦灰）、高级冷灰、点缀10%以内的哑光香槟金或冷拉丝金属色",
        anti_drift_rules=["严禁暴发户式廉价大金大黄", "严禁粗糙塑料反光", "严禁刺眼霓虹光"],
        perspective_enhancements={
            "03_detail": "85mm极限微距，定焦于商品精工倒角与黄铜配件的交界处，散发出轻奢微光",
            "07_emotional": "电影级暖调黄昏光线与冷色大理石形成戏剧性冷暖对冲，拉满格调与溢价",
        },
    ),
    "german_deconstruct": StylePreset(
        id="german_deconstruct",
        name="德系解构 (严谨精工工业)",
        en_name="Bauhaus & German Precision Engineering",
        tagline="硬核机械美学，冷冽金属光泽，硬朗理性信任感",
        description="包豪斯现代主义与德国工业精密的极致融合，突出商品的精密机械装配、硬核功能与不可撼动的工业可靠度。",
        lighting="高反差硬朗侧逆光、数码级精准切割轮廓光、冷冽银白主光，硬核勾勒出几何边缘与锋利倒角",
        environment="阳极氧化深灰铝合金台面、炭黑工程塑料支架、精密毫米标尺、无尘实验室级别科技展台",
        camera="90mm 移轴微距摄影，全景深精细堆叠(Focus Stacking)，极致锐化边缘，无透视形变",
        color_tone="深空炭黑、冷钛灰、哑光银，极高反差，局部可带有0.5%科技幽蓝或指示冷白LED光效",
        anti_drift_rules=["严禁粉嫩色系", "严禁温馨家庭杂物", "严禁模糊朦胧镜头"],
        perspective_enhancements={
            "04_structure": "轴向精密悬浮解构爆炸图，各零件间带有冷蓝科技标线与微米级结构说明感",
            "05_pain_killer": "高强度暴力测试硬核环境，水滴飞溅瞬间在冷硬金属上粉碎定格，震撼信赖感",
        },
    ),
    "dopamine_energy": StylePreset(
        id="dopamine_energy",
        name="多巴胺活力 (青年明快撞色)",
        en_name="Dopamine Bright & Pop Energy",
        tagline="高饱和明快撞色，夏日阳光投影，激发冲动点击",
        description="拥抱Z世代年轻力与悦己情绪，通过鲜活高饱和的视觉冲击唤醒购买兴奋感，极大拉升CTR点击率。",
        lighting="模拟夏日正午清透直射阳光，带有清晰锐利的硬直投影，白色反光板高亮度立体补光",
        environment="纯色通透亚克力展台、波普艺术撞色背景板、水波纹光斑投影、明快极简几何方块堆叠",
        camera="35mm 人文广角与动感微俯视机位，充满活力的对角线构图，大景深明澈画质",
        color_tone="明亮柠檬黄、活力珊瑚橙、薄荷绿与克莱因蓝的大胆艺术碰撞，色彩通透浓郁，无压抑灰调",
        anti_drift_rules=["严禁昏暗暗调", "严禁死黑阴影", "严禁沉闷严肃的商务背景"],
        perspective_enhancements={
            "01_white_bg": "高调亮白底色，搭配鲜亮通透的色彩饱和度，通透立体倒影，第一眼吸睛夺目",
            "08_color": "全系高饱和配色在波普几何台阶上一字排开，如糖果般悦目丰富，激发收藏连单",
        },
    ),
    "cyber_street": StylePreset(
        id="cyber_street",
        name="赛博潮酷 (暗夜霓虹潮流)",
        en_name="Cyberpunk & Night Street Tech",
        tagline="暗夜深色基底，蓝紫电光流淌，未来主义科技潮牌",
        description="电影感赛博朋克与未来潮流街头的混合体，适合主打数码黑科技、电竞装备与先锋潮流的破圈单品。",
        lighting="双色冷暖高反差切光：45度电光青蓝主侧光 + 135度品红霓虹边缘轮廓反打，暗调深邃黑阶",
        environment="湿漉沥青反光地面、深黑碳纤维纹理板、全息渐变光晕、暗黑金属几何网格",
        camera="24mm 超广角低机位仰拍，大透视冲击力，配合暗部电影级细微胶片噪点与光晕漫射(Bloom)",
        color_tone="深邃极黑(#09090B)、电光青蓝(#00F0FF)、赛博品红(#FF003C)，高反差强视觉冲击",
        anti_drift_rules=["严禁田园乡村风", "严禁日式米白温馨感", "严禁大面积平庸白光"],
        perspective_enhancements={
            "04_structure": "发光的幽蓝半透明元器件在深黑背景中悬浮，电路导光条纹流转，极致科幻感",
            "09_buyer_show": "暗光街头潮流青年手持特写，背景是繁华夜市虚化的霓虹光斑，潮酷种草",
        },
    ),
}

DEFAULT_STYLE_PRESET_ID = "minimalist_muji"


def get_style_preset(preset_id: Optional[str] = None) -> StylePreset:
    """获取指定风格流派，若未指定或不存在则默认返回 minimalist_muji"""
    if not preset_id or preset_id not in STYLE_PRESET_REGISTRY:
        return STYLE_PRESET_REGISTRY[DEFAULT_STYLE_PRESET_ID]
    return STYLE_PRESET_REGISTRY[preset_id]


def list_style_presets() -> List[StylePreset]:
    """返回所有支持的官方风格流派对象列表"""
    return list(STYLE_PRESET_REGISTRY.values())


def get_all_style_presets() -> List[Dict[str, Any]]:
    """返回所有风格流派的字典形式列表（便于直接作为 JSON 响应）"""
    return [preset.model_dump() for preset in STYLE_PRESET_REGISTRY.values()]
