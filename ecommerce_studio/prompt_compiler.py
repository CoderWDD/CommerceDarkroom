"""
高内聚 9 视角商业提示词编译引擎 (Prompt Matrix Compiler)
双层装配与防漂移护栏编译机制
"""

from typing import Any, Dict, List, Optional
from ecommerce_studio.style_presets import STYLE_PRESET_REGISTRY, DEFAULT_STYLE_PRESET_ID, get_style_preset

# 9 大黄金商业视角元数据规范
PERSPECTIVE_DEFINITIONS: List[Dict[str, str]] = [
    {
        "id": "01_white_bg",
        "alt_id": "main_white_bg",
        "name": "商业纯净白底首图",
        "tag": "CTR点击率收割机",
        "category": "主图转化",
        "desc": "纯白无影摄影棚顶光与双侧柔光箱、商品主体居中微俯视15°、通透镜面微倒影、高动态范围HDR",
    },
    {
        "id": "02_scene",
        "alt_id": "lifestyle_scene",
        "name": "真实生活使用场景图",
        "tag": "生活代入与身份认同",
        "category": "场景共情",
        "desc": "融入真实目标场域，柔和侧逆自然光，搭配生活化道具与舒适采光氛围",
    },
    {
        "id": "03_detail",
        "alt_id": "material_detail",
        "name": "材质工艺与微距细节图",
        "tag": "精工品质与消除廉价感",
        "category": "品质背书",
        "desc": "85mm~100mm微距特写，超浅景深虚化背景，硬光侧打凸显精密纹理、精工倒角与高阶做工细节",
    },
    {
        "id": "04_structure",
        "alt_id": "structure_cutaway",
        "name": "黑科技解构与爆炸透视图",
        "tag": "技术壁垒与内部硬核",
        "category": "科技信任",
        "desc": "核心组件悬浮爆炸视图(Exploded View)、轴向线性排布、冷色科技轮廓光、半透明材质透光感与技术标线感",
    },
    {
        "id": "05_pain_killer",
        "alt_id": "pain_point_solution",
        "name": "痛点直击与抗拒点攻破图",
        "tag": "消灭退货与打消顾虑",
        "category": "决策攻坚",
        "desc": "直击买家最大抗拒痛点，高速快门多机位动感定格硬核实测瞬间，无可辩驳的视觉证据打消顾虑",
    },
    {
        "id": "06_size",
        "alt_id": "portable_commute",
        "name": "人体工学与真实比例图",
        "tag": "尺码锚定与真实参照",
        "category": "实用认知",
        "desc": "与真实生活参照物或人体自然交互同框，建立直观体量认知与空间比例感知",
    },
    {
        "id": "07_emotional",
        "alt_id": "core_feature",
        "name": "品牌情绪与故事氛围图",
        "tag": "品牌溢价与高级格调",
        "category": "品牌溢价",
        "desc": "电影感宽画幅光影（丁达尔光束、深色暖影调、蓝调黄昏），弱化商品棱角，强化环境意境渲染",
    },
    {
        "id": "08_color",
        "alt_id": "unboxing_gift",
        "name": "全系配色与陈列矩阵图",
        "tag": "多色激发与家族感",
        "category": "矩阵陈列",
        "desc": "现代艺术展台陈列，高低错落几何台阶，全系经典配色一字排开，统一侧光保证色彩精准无色差",
    },
    {
        "id": "09_buyer_show",
        "alt_id": "model_interaction",
        "name": "真实买家秀与社交种草图",
        "tag": "真实口碑与生活种草",
        "category": "社交种草",
        "desc": "真实生活环境自然随手抓拍、自然非影棚光、生活化真实环境背景、轻微胶片颗粒感与随性自然构图",
    },
]


BASE_PERSPECTIVE_STRATEGIES: Dict[str, Dict[str, Any]] = {
    "01_white_bg": {
        "scene_highlight": "30°纯白无影展台微俯视，极浅镜面接触微倒影，凸显原装通透质地与边缘光泽",
        "commercial_strategy": "搜索列表第一眼视觉抢占，消除杂乱干扰，秒建高品质正品质感与点击冲动",
        "quick_tweaks": [
            {"id": "light_top", "label": "💡 调亮无影顶光", "tweakText": "调亮无影摄影棚顶光与双侧柔光箱，强化主体通透洁净感"},
            {"id": "mirror_reflection", "label": "🪞 加镜面通透倒影", "tweakText": "展台表层增加极浅镜面接触微倒影，凸显高级通透倒影质感"},
            {"id": "golden_edge", "label": "✨ 强化边缘轮廓光", "tweakText": "边缘轮廓增加精致微光勾边，拉开主体与纯白背景的反差"},
            {"id": "hero_angle", "label": "📐 正视微仰霸气角度", "tweakText": "机位调整为正面平视略微仰角5度，增强产品的视觉体量感与高级气场"},
        ],
    },
    "02_scene": {
        "scene_highlight": "清晨自然光穿透纱帘斜射，融入真实生活环境台面，自然展现日常相伴使用瞬间",
        "commercial_strategy": "唤醒消费者对美好居家/办公品质生活的向往，建立情感共鸣，增强代入感与购买渴望",
        "quick_tweaks": [
            {"id": "scene_props", "label": "☕ 搭配高质感生活道具", "tweakText": "台面搭配雅致生活道具与自然绿植，烘托惬意生活方式"},
            {"id": "tyndall_sunlight", "label": "☀️ 加晨光丁达尔斜射", "tweakText": "模拟清晨斜射45度自然窗光，带有柔和丁达尔光束漫射"},
            {"id": "modern_space", "label": "🏢 置于现代极简明亮空间", "tweakText": "置于现代化明亮整洁台面，背景轻微景深虚化显示高阶环境"},
            {"id": "natural_greenery", "label": "🌿 加原木自然绿植点缀", "tweakText": "边缘点缀极简日系盆栽或新鲜绿植，营造静谧自然生机"},
        ],
    },
    "03_detail": {
        "scene_highlight": "镜头贴近局部 5-10 厘米极限微距，侧逆光细腻勾勒材质纹理与微米级精工倒角，超浅景深虚化",
        "commercial_strategy": "消除廉价塑料感，通过精工级细节特写支撑品牌高端溢价，击穿品质顾虑",
        "quick_tweaks": [
            {"id": "texture_luster", "label": "✨ 强化表面材质光泽", "tweakText": "硬朗侧逆光高反差切入，极致强化表面精工材质光泽与倒角高光"},
            {"id": "water_droplets", "label": "💧 表层凝结细密水珠", "tweakText": "外表层自然凝结微米级晶莹细小水珠，表现极致水润清新质感"},
            {"id": "ultra_shallow_dof", "label": "🔍 极致超浅景深虚化", "tweakText": "85mm微距定焦镜头全开光圈，焦点极致锐利，背景奶油般散景虚化"},
            {"id": "craft_details", "label": "🔘 突出微米精工接缝", "tweakText": "侧向聚光精准投射在核心接缝与工艺交界处，凸显微米级精细做工"},
        ],
    },
    "04_structure": {
        "scene_highlight": "核心构造与内部元器件轴向悬浮微距爆炸透视，多层阻隔结构与核心科技元器件层层清晰呈现",
        "commercial_strategy": "硬核可视化黑科技，直观展现不可见的内部精密工艺与核心用料，瞬间征服理性参数党",
        "quick_tweaks": [
            {"id": "axial_exploded", "label": "🚀 核心组件轴向悬浮透视", "tweakText": "核心组件沿中心轴悬浮展开Exploded View，展现内部层叠结构"},
            {"id": "tech_blue_light", "label": "🔷 科技冷蓝结构光", "tweakText": "投射冷蓝科技激光结构线条与边缘轮廓冷光，增强科技工业感"},
            {"id": "translucent_xray", "label": "🧬 半透明透光分层解析", "tweakText": "部分截面采用半透明X光透光材质，清晰呈现内部精密分层"},
            {"id": "industrial_callouts", "label": "📐 加极简工业技术标线", "tweakText": "背景搭配精密极简工业装配工程辅助线与刻度标线感"},
        ],
    },
    "05_pain_killer": {
        "scene_highlight": "直击买家最大抗拒痛点，高速快门多机位动感抓拍硬核实测瞬间，无可辩驳的视觉证据打消顾虑",
        "commercial_strategy": "正面强攻核心痛点与买家最怕退货的抗拒点，用事实证言消除下单顾虑",
        "quick_tweaks": [
            {"id": "freeze_test", "label": "🛡️ 核心痛点硬核实测", "tweakText": "针对核心买家痛点进行严苛使用场景实测，定格无瑕表现，打消下单疑虑"},
            {"id": "water_splash", "label": "💧 水润纯净瞬间抓拍", "tweakText": "高速快门动感抓拍清爽水花或细腻水雾，呈现清爽不油腻吸收与密封保护"},
            {"id": "durability_drop", "label": "⚡ 坚固耐用可靠性测试", "tweakText": "展现高强度使用环境下的耐用质感，证明安全可靠与精湛用料"},
            {"id": "comparative_evidence", "label": "✨ 真实效果对比证言", "tweakText": "高反差专业布光定格前后差异化表现，形成强有力的说服力与信任状"},
        ],
    },
    "06_size": {
        "scene_highlight": "成年手掌自然轻握，或与日常经典随身物品同框并列，直观展现真实人体工学比例",
        "commercial_strategy": "真实呈现握持手感与空间占用，彻底消除买家对大小尺寸的认知模糊与落差退货",
        "quick_tweaks": [
            {"id": "hand_grip", "label": "🖐️ 成年手掌自然轻握", "tweakText": "真实成年人手部自然人体工学握持，呈现一手掌控的真实体感与尺寸参照"},
            {"id": "daily_items", "label": "📱 与日常经典物品同框", "tweakText": "与手机/口红/钥匙等日常随身物品并列同框，直观参照小巧体量"},
            {"id": "portable_storage", "label": "👜 随身包袋收纳体量", "tweakText": "随手收纳在日常随身包袋口袋中，清晰展现便携收纳体量"},
            {"id": "multi_angle_scale", "label": "📐 多视角标准规格比例", "tweakText": "端正呈现正面与侧面标准比例，直观呈现长宽厚度人体工学体量"},
        ],
    },
    "07_emotional": {
        "scene_highlight": "电影级暗调冷金光束，微醺烟雾漫射，极简几何大理石展台，营造杂志封面级张力",
        "commercial_strategy": "营造沉浸式轻奢格调，拔高产品定位与审美认知，大幅拉升品牌溢价与客单价",
        "quick_tweaks": [
            {"id": "cinematic_gold_light", "label": "🎬 电影级暗调冷金光", "tweakText": "电影级宽画幅暗调打光，一道狭长冷金光束精准勾勒轮廓"},
            {"id": "smoke_diffusion", "label": "🌫️ 微醺高级烟雾漫射", "tweakText": "背景带有微醺缭绕的高级柔和冷雾与丁达尔光束漫射"},
            {"id": "marble_steps", "label": "🏛️ 极简几何大理石台阶", "tweakText": "置于高低错落的卡拉拉白与深灰大理石几何台阶展台上"},
            {"id": "sunset_blue_hour", "label": "🌅 蓝调落日余晖色彩", "tweakText": "背景透出黄昏Magic Hour深邃蓝调与落日天际线微光，格调深沉"},
        ],
    },
    "08_color": {
        "scene_highlight": "高低错落极简展台，全系规格与经典配色矩阵全景平齐陈列，统一摄影色温精准无偏色",
        "commercial_strategy": "提供全景丰富选款体验，满足个性化审美偏好，刺激套装与多规格连带下单",
        "quick_tweaks": [
            {"id": "staggered_pedestals", "label": "🧱 高低错落展台陈列", "tweakText": "采用高低层次分明的极简几何展台，多款经典规格主次分明错落陈列"},
            {"id": "accurate_color_temp", "label": "🎨 统一色温精准无偏色", "tweakText": "5500K专业商业标准色温高显色指数主光，确保各配色真实还原无色差"},
            {"id": "gift_box_set", "label": "🎁 礼盒送礼全套陈列", "tweakText": "背景伴随质感送礼定制烫金硬壳礼盒与礼袋，提升送礼档次感"},
            {"id": "individual_highlights", "label": "✨ 各款轮廓精致高光", "tweakText": "每一款配色轮廓均有一条精致侧逆轮廓高光，互相呼应立体感强烈"},
        ],
    },
    "09_buyer_show": {
        "scene_highlight": "小红书风格第一人称真实手持，窗边随手抓拍感，轻微生活感自然漫射，消除摆拍感",
        "commercial_strategy": "消除过度商业精修的生硬距离感，提供极具亲和力的买家口碑背书，促进最终付款决策",
        "quick_tweaks": [
            {"id": "redbook_first_person", "label": "📱 小红书第一人称手持", "tweakText": "第一人称视角随手拿起使用，背景有生活桌面或梳妆台温馨一角"},
            {"id": "window_snap", "label": "🌇 窗边随手抓拍感", "tweakText": "自然窗边随手抓拍，柔和漫射采光，构图自然随性无棚拍痕迹"},
            {"id": "film_grain", "label": "🎞️ 轻微生活胶片颗粒", "tweakText": "画面融入微量生活胶片暖调颗粒感，呈现温暖惬意的生活格调"},
            {"id": "candid_natural", "label": "💬 消除棚拍刻意摆拍痕迹", "tweakText": "消除过于完美的商业打光与道具摆弄，展现真实买家开箱爱不释手的瞬间"},
        ],
    },
}


def get_perspective_strategy_data(
    pid: str,
    product_info: Dict[str, Any],
    vertical: str = "general",
    style_preset_id: Optional[str] = None,
) -> Dict[str, Any]:
    """生成兼具行业垂直属性与商品定制特性的策略高光与微调胶囊"""
    base = BASE_PERSPECTIVE_STRATEGIES.get(pid) or BASE_PERSPECTIVE_STRATEGIES["01_white_bg"]
    prod_name = product_info.get("name") or product_info.get("product_name") or "商品"
    pain_points = product_info.get("pain_points") or ""
    materials = product_info.get("material_features") or ""

    highlight = base["scene_highlight"]
    strategy = base["commercial_strategy"]
    tweaks = [dict(t) for t in base["quick_tweaks"]]

    # 深度动态插值（遵循 3W1H 物理场景具象法则）
    if pid == "01_white_bg":
        highlight = f"30°纯白无影展台微俯视，极浅镜面接触微倒影，完整呈现【{prod_name}】主体结构与质地，主体占比80%"
    elif pid == "02_scene":
        if vertical == "pet":
            highlight = f"置于现代简约客厅阳光落地窗边木地板上，猫咪在旁惬意玩耍，展现【{prod_name}】整洁无异味的品质养宠生活"
        elif vertical == "beauty":
            highlight = f"置于现代高定浴室大理石洗手台上，晨光透过百叶窗洒下斑驳光影与水光涟漪，展现【{prod_name}】清晨护肤仪式"
        elif vertical == "digital":
            highlight = f"置于现代极客极简实木工位，搭配机械键盘与显示器微光，展现【{prod_name}】先锋科技效率生活"
        elif vertical == "home_large":
            highlight = f"置于 40㎡ 挑高落地窗大平层客厅，黄昏温暖余晖洒在表面，展现【{prod_name}】宏阔舒适的居家质感"
        elif vertical == "food":
            highlight = f"置于原木餐桌中央，晨光微斜射，搭配精致餐盘与新鲜迷迭香点缀，呈现【{prod_name}】诱人垂涎的赏味时刻"
        elif vertical == "apparel":
            highlight = f"融入都市街头或自然山野微风环境，自然漫射光，模特动态穿搭展示【{prod_name}】挺阔版型与随性身姿"
        elif vertical == "outdoor":
            highlight = f"置于高山草甸或湖畔露营天幕下，晨曦丁达尔光束穿透林间，展现【{prod_name}】硬核山系户外生活"
        elif vertical == "baby":
            highlight = f"置于温馨明亮的奶油风儿童房原木地板，柔和自然漫射光，展现【{prod_name}】安全无毒的母婴呵护氛围"
        elif vertical == "industrial":
            highlight = f"置于专业工坊耐磨工作台或车库工具架旁，硬朗侧光打亮，展现【{prod_name}】硬核可靠的工业作业场景"
        else:
            highlight = f"清晨自然光穿透纱帘斜射，融入真实生活环境台面，自然展现【{prod_name}】高品质陪伴使用瞬间"
    elif pid == "03_detail":
        if vertical == "beauty":
            highlight = f"85mm微距特写瓶口与滴管处，高纯度精华水滴凝结欲滴，侧逆光折射微光，超浅景深背景完全散景"
        elif vertical == "pet":
            highlight = f"微距特写门洞踏板与边缘接缝 5 厘米处，硬光侧打凸显环保亲肤磨砂颗粒与双层密封抑菌硅胶圈"
        elif vertical == "home_large":
            highlight = f"85mm微距特写扶手转角精密双针车缝线，强侧光清晰勾勒天然纹理肌理与饱满回弹弧度，背景奶油般虚化"
        elif vertical == "food":
            highlight = f"100mm极限微距特写食材细腻纹理与微渗晶莹汁水，高显色光打出鲜亮色泽，超浅景深聚焦核心美味切面"
        else:
            highlight = f"镜头贴近局部 5-10 厘米极限微距，侧逆光细腻勾勒【{prod_name}】材质纹理与微米级精工倒角，超浅景深虚化"
    elif pid == "04_structure":
        if vertical == "beauty":
            highlight = f"分子级 3D 悬浮解构透视，核心活性成分与水网粒子层层悬浮展开，冷蓝光晕展现【{prod_name}】深层渗透科技"
        elif vertical == "pet":
            highlight = f"全机身模块化组件轴向悬浮爆炸视图(Exploded View)，分离顶盖、滤砂踏板与除臭滤芯组件有序排布"
        elif vertical == "home_large":
            highlight = f"半剖面悬浮透视解构，外层材质、高回弹内衬与承重龙骨底架自上而下轴向悬浮排开，展现【{prod_name}】硬核内部用料"
        elif vertical == "digital":
            highlight = f"精密内部元器件轴向悬浮爆炸视图，主控芯片、声学腔体与阻尼转轴层层排开，冷色科技蓝轮廓光"
        else:
            highlight = f"核心构造与内部元器件轴向悬浮微距爆炸透视，多层阻隔结构与核心科技层层清晰呈现"
    elif pid == "05_pain_killer":
        crush_target = pain_points if pain_points else "核心买家痛点与耐用顾虑"
        if vertical == "pet":
            highlight = f"直击猫砂外溅与闷臭痛点：高速快门抓拍猫咪出仓与落砂踏板高效回落滤净瞬间，密闭锁臭实测打消顾虑"
        elif vertical == "beauty":
            highlight = f"针对油腻搓泥顾虑：手背涂抹后 50 张吸油纸瞬间吹落无粘连，水润秒吸收对比形成无可辩驳的视觉证言"
        elif vertical == "apparel":
            highlight = f"针对渗水掉色顾虑：高压水枪强力喷淋表面水珠荷叶般滚落，强效暴风雨防风抗水实测瞬间"
        else:
            highlight = f"直击买家最大抗拒痛点（{crush_target}），高速快门多机位动感抓拍硬核实测瞬间，打消下单顾虑"
    elif pid == "06_size":
        if vertical in ["home_large", "pet"]:
            highlight = f"放置于现代客厅地面木地板上，与室内沙发、绿植或宠物并列同框，直观展现【{prod_name}】真实占地空间与宏阔体量"
        elif vertical in ["food", "beauty"]:
            highlight = f"成年女性手部自然托起轻握，或与手机口红并列平齐摆放，清晰认知【{prod_name}】真实容量与精致手感"
        else:
            highlight = f"成年人手部自然人体工学握持，或与日常经典随身物品同框并列，直观展现【{prod_name}】真实尺寸比例"
    elif pid == "07_emotional":
        highlight = f"电影级暗调冷金光束，微醺烟雾漫射，极简几何大理石展台，营造【{prod_name}】杂志封面级高端张力"
    elif pid == "08_color":
        highlight = f"高低错落极简展台，【{prod_name}】全系经典配色矩阵全景平齐陈列，统一 5500K 摄影色温精准无偏色"
    elif pid == "09_buyer_show":
        highlight = f"小红书风格第一人称真实随手抓拍【{prod_name}】，自然居家采光，轻微生活感自然漫射，消除任何摆拍痕迹"

    return {
        "scene_highlight": highlight,
        "commercial_strategy": strategy,
        "quick_tweaks": tweaks,
        "quick_tweak_pills": [t["label"] for t in tweaks],
    }


def detect_product_vertical(name: str, category: str = "", materials: str = "") -> str:
    """智能识别商品 10 大核心电商垂直行业，精准匹配对应的商业摄影构图动线"""
    text = f"{name} {category} {materials}".lower()
    if any(k in text for k in ["猫", "狗", "犬", "宠物", "猫砂", "砂棚", "猫爬架", "牵引绳", "水族", "宠"]):
        return "pet"
    if any(k in text for k in ["精华", "护肤", "美妆", "面霜", "口红", "原液", "水乳", "防晒", "粉底", "洗面奶", "唇膏", "面膜", "彩妆"]):
        return "beauty"
    if any(k in text for k in ["耳机", "键盘", "鼠标", "手机", "充电", "音箱", "数码", "智能手表", "电脑", "相机", "蓝牙", "数码"]):
        return "digital"
    if any(k in text for k in ["沙发", "椅子", "茶几", "床", "衣柜", "家具", "扫地机", "洗衣机", "冰箱", "空调", "净化器", "电视", "床垫", "餐桌"]):
        return "home_large"
    if any(k in text for k in ["牛排", "生鲜", "水果", "零食", "茶叶", "咖啡豆", "坚果", "烘焙", "粮油", "预制菜", "啤酒", "红酒", "海鲜", "肉类", "食品"]):
        return "food"
    if any(k in text for k in ["冲锋衣", "羽绒服", "t恤", "衬衫", "牛仔裤", "连衣裙", "内衣", "卫衣", "运动鞋", "女包", "男包", "服饰", "鞋包"]):
        return "apparel"
    if any(k in text for k in ["露营", "帐篷", "登山杖", "骑行", "睡袋", "钓鱼", "充气垫", "天幕", "冲浪", "户外", "运动"]):
        return "outdoor"
    if any(k in text for k in ["婴儿", "童装", "奶瓶", "纸尿裤", "婴儿推车", "儿童玩具", "辅食", "积木", "母婴"]):
        return "baby"
    if any(k in text for k in ["扳手", "电钻", "螺丝刀", "五金", "工具箱", "汽摩配件", "轮胎", "割草机", "机械"]):
        return "industrial"
    return "general"


class PromptMatrixCompiler:
    """高内聚 9 视角商业提示词编译引擎"""

    @classmethod
    def compile_matrix(
        cls,
        product_info: Dict[str, Any],
        style_preset_id: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        style = get_style_preset(style_preset_id)
        prod_name = product_info.get("name") or product_info.get("product_name") or "高端商品"
        category = product_info.get("category", "")
        material = product_info.get("material_features", "高精密工业材质")
        pain_points = product_info.get("pain_points", "日常使用抗拒点")
        target_users = product_info.get("target_audience") or product_info.get("target_users", "追求品质生活的消费者")

        vertical = detect_product_vertical(prod_name, category, material)

        compiled_results = []
        for p_def in PERSPECTIVE_DEFINITIONS:
            pid = p_def["id"]
            p_name = p_def["name"]

            # 1. 行业自适应构图定位
            base_composition = p_def["desc"]
            if vertical == "pet":
                if pid == "02_scene":
                    base_composition = "融入真实温馨家居环境（现代极简客厅阳光处/落地窗阳台/猫爬架旁），柔和自然晨光斜射，猫咪在旁温馨陪伴，展现整洁无异味的品质养宠生活"
                elif pid == "03_detail":
                    base_composition = "85mm微距特写，浅景深虚化背景，侧逆光细腻勾勒抗菌哑光亲肤环保材质、圆润防磕碰大倒角与密闭防漏接缝"
                elif pid == "04_structure":
                    base_composition = "模块化分离结构悬浮爆炸视图(Exploded View)，分离式顶盖、抽屉式砂底盒、落砂过滤踏板与抑菌除臭滤芯组件轴向清晰排布，冷色科技轮廓光"
                elif pid == "05_pain_killer":
                    base_composition = f"针对养宠核心痛点（{pain_points or '防猫砂飞溅外带、全封闭强效锁臭隔绝异味、大空间进出顺畅'}），具象化视觉定格，呈现彻底隔臭不漏砂的硬核证言"
                elif pid == "06_size":
                    base_composition = "放置于室内家居地面，与成年猫咪或家居沙发并列同框，直观展现猫咪进出自由的宽敞内部体量与真实家居占地比例"
                elif pid == "07_emotional":
                    base_composition = "电影感宽画幅光影（丁达尔暖光漫射、温馨落日余晖），猫咪惬意陪伴在侧，弱化塑料感，传递人宠和谐共处的治愈高级格调"
                elif pid == "09_buyer_show":
                    base_composition = "小红书买家秀风格，真实居家客厅一角随手抓拍，柔和生活漫射光，猫咪好奇靠近或踩踏踏板，充满生活萌态与真实种草感"
            elif vertical == "beauty":
                if pid == "02_scene":
                    base_composition = "融入高定美学场域（现代极简晨光浴室大理石洗手台/梳妆台），柔和侧逆自然光，水润光泽倒影与水珠点缀"
                elif pid == "04_structure":
                    base_composition = "高阶分子水网或核心活性成分微距解析图，半透明折射光感与科技悬浮水光粒子，展现深层渗透科技"
                elif pid == "05_pain_killer":
                    base_composition = f"针对护肤核心抗拒点（{pain_points or '油腻厚重不吸收、搓泥卡粉、敏感泛红'}），手背清爽化水质地抓拍或哑光秒吸收对比，展现清爽透润"
                elif pid == "06_size":
                    base_composition = "成年女性手部自然轻握，或与日常经典护肤美妆物件并列同框，直观呈现一手掌控的精致体量"
                elif pid == "09_buyer_show":
                    base_composition = "小红书风格第一人称手持特写，自然窗边漫射光，质地晶莹剔透，亲切真实的社交开箱种草氛围"
            elif vertical == "digital":
                if pid == "02_scene":
                    base_composition = "融入现代极简极客工作台（电竞书房/现代商务办公桌面），柔和侧逆光，搭配现代数码配件与科技氛围"
                elif pid == "04_structure":
                    base_composition = "精密内部元器件悬浮爆炸透视图(Exploded View)，主控芯片、精密声学腔体或阻尼轴体轴向有序排布，冷色科技蓝轮廓光"
                elif pid == "05_pain_killer":
                    base_composition = f"针对数码硬核抗拒点（{pain_points or '发热降频、续航衰减、磕碰磨损'}），极客测试场景定格，视觉呈现卓越可靠性"
                elif pid == "06_size":
                    base_composition = "手部自然人体工学握持，或与超极本/手机并列平齐摆放，建立精准纤薄度与便携尺码感知"
                elif pid == "09_buyer_show":
                    base_composition = "极客桌面真实搭配开箱随手抓拍，桌面自然氛围光，真实数码博主种草推荐视角"
            elif vertical == "home_large":
                if pid == "02_scene":
                    base_composition = "融入宽敞明亮的现代品质家居环境（开放式现代客厅/生活阳台），柔和自然光，展现井然有序的整洁家居生活"
                elif pid == "04_structure":
                    base_composition = "工业精密结构分层解析，核心电机马达、动力模组或承重龙骨架构爆炸透视，科技工程感线条"
                elif pid == "05_pain_killer":
                    base_composition = f"针对家居生活核心痛点（{pain_points or '占地拥挤、运行噪音、清洁打理繁琐'}），严苛环境实测视觉证言，消除买家后顾之忧"
                elif pid == "06_size":
                    base_composition = "置于室内生活地面或柜体旁，与成人站姿或沙发餐桌并列同框，直观呈现真实占地空间与人体工学黄金高度"
                elif pid == "09_buyer_show":
                    base_composition = "真实住家生活空间开箱实景，自然生活光，整洁高级的无摆拍生活记录"

            # 2. 获取该视角下的流派强化参数
            style_enhancement = style.perspective_enhancements.get(pid, "")

            # 3. 动态拼装具有强约束力的中文提示词
            prompt = (
                f"【商业广告摄影】{p_name}。主体为一款高品质{prod_name}。"
                f"【工业与材质特征】：{material}。"
                f"【构图与视角】：{base_composition}，{style.camera}。"
                f"【商业布光与光影】：{style.lighting}。"
                f"【空间与道具布景】：{style.environment}。"
                f"【色彩与调性风格】：{style.color_tone}。"
            )

            if style_enhancement:
                prompt += f"【流派专属强化】：{style_enhancement}。"

            # 视角专属业务强化
            if pid == "05_pain_killer":
                prompt += f"【痛点攻坚场景】：具象化消除买家核心顾虑（{pain_points}），视觉呈现严密可靠。"
            elif pid in ("09_buyer_show", "02_scene"):
                prompt += f"【目标客群代入】：生动融入符合（{target_users}）生活品位的高阶氛围中。"

            # 防漂移质量锁
            negative_rules = "，".join(style.anti_drift_rules)
            prompt += f"【画质与防漂移规范】：8k超清分辨率，锐利对焦，真实质感，严禁出现：{negative_rules}。"

            strat = get_perspective_strategy_data(pid, product_info, vertical, style_preset_id)
            quick_tweaks = strat["quick_tweaks"]
            quick_pills = strat["quick_tweak_pills"]

            compiled_results.append({
                "id": pid,
                "alt_id": p_def.get("alt_id"),
                "name": p_name,
                "desc": p_def["desc"],
                "tag": p_def.get("tag", ""),
                "category": p_def.get("category", ""),
                "scene_highlight": strat["scene_highlight"],
                "commercial_strategy": strat["commercial_strategy"],
                "prompt": prompt,
                "prompt_zh": prompt,
                "quick_tweaks": quick_tweaks,
                "quick_tweak_pills": quick_pills,
            })

        return compiled_results
