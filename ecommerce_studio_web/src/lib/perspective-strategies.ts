export interface QuickTweakItem {
  id: string;
  label: string; // e.g. "💡 调亮无影顶光"
  tweakText: string; // instruction injected into prompt
}

export interface PerspectiveStrategyDef {
  id: string;
  orderNumber: string;
  name: string;
  psychologyBadge: string;
  category: string;
  sceneHighlight: string;
  commercialStrategy: string;
  quickTweaks: QuickTweakItem[];
}

export interface ProductInfoContext {
  name?: string;
  category?: string;
  pain_points?: string;
  material_features?: string;
  target_audience?: string;
}

export const BASE_PERSPECTIVE_STRATEGIES: PerspectiveStrategyDef[] = [
  {
    id: '01_white_bg',
    orderNumber: '01',
    name: '商业纯净白底首图',
    psychologyBadge: 'CTR点击收割机',
    category: '主图转化',
    sceneHighlight: '30°纯白无影展台微俯视，极浅镜面接触微倒影，凸显原装通透质地与边缘光泽',
    commercialStrategy: '搜索列表第一眼视觉抢占，消除杂乱干扰，秒建高品质正品质感与点击冲动',
    quickTweaks: [
      { id: 'light_top', label: '💡 调亮无影顶光', tweakText: '调亮无影摄影棚顶光与双侧柔光箱，强化主体通透洁净感' },
      { id: 'mirror_reflection', label: '🪞 加镜面通透倒影', tweakText: '展台表层增加极浅镜面接触微倒影，凸显高级通透倒影质感' },
      { id: 'golden_edge', label: '✨ 强化边缘轮廓光', tweakText: '边缘轮廓增加精致微光勾边，拉开主体与纯白背景的反差' },
      { id: 'hero_angle', label: '📐 正视微仰霸气角度', tweakText: '机位调整为正面平视略微仰角5度，增强产品的视觉体量感与高级气场' },
    ],
  },
  {
    id: '02_scene',
    orderNumber: '02',
    name: '真实生活使用场景图',
    psychologyBadge: '生活方式与身份认同',
    category: '场景生活',
    sceneHighlight: '清晨自然光穿透纱帘斜射，融入真实生活环境台面，自然展现日常相伴使用瞬间',
    commercialStrategy: '唤醒消费者对美好居家/办公品质生活的向往，建立情感共鸣，增强代入感与购买渴望',
    quickTweaks: [
      { id: 'scene_props', label: '☕ 搭配高质感生活道具', tweakText: '台面搭配雅致生活道具与自然绿植，烘托惬意生活方式' },
      { id: 'tyndall_sunlight', label: '☀️ 加晨光丁达尔斜射', tweakText: '模拟清晨斜射45度自然窗光，带有柔和丁达尔光束漫射' },
      { id: 'modern_space', label: '🏢 置于现代极简明亮空间', tweakText: '置于现代化明亮整洁台面，背景轻微景深虚化显示高阶环境' },
      { id: 'natural_greenery', label: '🌿 加原木自然绿植点缀', tweakText: '边缘点缀极简日系盆栽或新鲜绿植，营造静谧自然生机' },
    ],
  },
  {
    id: '03_detail',
    orderNumber: '03',
    name: '材质工艺与微距细节图',
    psychologyBadge: '精工品质与消除廉价感',
    category: '材质工艺',
    sceneHighlight: '镜头贴近局部 5-10 厘米极限微距，侧逆光细腻勾勒材质纹理与微米级精工倒角，超浅景深虚化',
    commercialStrategy: '消除廉价塑料感，通过精工级细节特写支撑品牌高端溢价，击穿品质顾虑',
    quickTweaks: [
      { id: 'texture_luster', label: '✨ 强化表面材质光泽', tweakText: '硬朗侧逆光高反差切入，极致强化表面精工材质光泽与倒角高光' },
      { id: 'water_droplets', label: '💧 表层凝结细密水珠', tweakText: '外表层自然凝结微米级晶莹细小水珠，表现极致水润清新质感' },
      { id: 'ultra_shallow_dof', label: '🔍 极致超浅景深虚化', tweakText: '85mm微距定焦镜头全开光圈，焦点极致锐利，背景奶油般散景虚化' },
      { id: 'craft_details', label: '🔘 突出微米精工接缝', tweakText: '侧向聚光精准投射在核心接缝与工艺交界处，凸显微米级精细做工' },
    ],
  },
  {
    id: '04_structure',
    orderNumber: '04',
    name: '黑科技解构与爆炸透视图',
    psychologyBadge: '硬核黑科技与内部信任',
    category: '原理透视',
    sceneHighlight: '核心构造或分子成分轴向悬浮微距爆炸透视，多层阻隔结构与核心科技元器件层层清晰呈现',
    commercialStrategy: '硬核可视化黑科技，直观展现不可见的内部精密工艺与核心成分，瞬间征服理性参数党',
    quickTweaks: [
      { id: 'axial_exploded', label: '🚀 核心组件轴向悬浮透视', tweakText: '核心组件沿中心轴悬浮展开Exploded View，展现内部层叠结构' },
      { id: 'tech_blue_light', label: '🔷 科技冷蓝结构光', tweakText: '投射冷蓝科技激光结构线条与边缘轮廓冷光，增强科技工业感' },
      { id: 'translucent_xray', label: '🧬 半透明透光分层解析', tweakText: '部分截面采用半透明X光透光材质，清晰呈现内部精密分层' },
      { id: 'industrial_callouts', label: '📐 加极简工业技术标线', tweakText: '背景搭配精密极简工业装配工程辅助线与刻度标线感' },
    ],
  },
  {
    id: '05_pain_killer',
    orderNumber: '05',
    name: '痛点场景攻坚图',
    psychologyBadge: '打消下单疑虑',
    category: '痛点消灭',
    sceneHighlight: '直击买家最大抗拒痛点，高速快门多机位动感抓拍硬核实测瞬间，无瑕表现给买家绝对安全感',
    commercialStrategy: '正面强攻核心痛点与买家最怕退货的抗拒点，用事实证言消除下单顾虑',
    quickTweaks: [
      { id: 'freeze_test', label: '🛡️ 核心痛点硬核实测', tweakText: '针对核心买家痛点进行严苛使用场景实测，定格无瑕表现，打消下单疑虑' },
      { id: 'water_splash', label: '💧 水润纯净瞬间抓拍', tweakText: '高速快门动感抓拍清爽水花或细腻水雾，呈现清爽不油腻吸收与密封保护' },
      { id: 'durability_drop', label: '⚡ 坚固耐用可靠性测试', tweakText: '展现高强度使用环境下的耐用质感，证明安全可靠与精湛用料' },
      { id: 'comparative_evidence', label: '✨ 真实效果对比证言', tweakText: '高反差专业布光定格前后差异化表现，形成强有力的说服力与信任状' },
    ],
  },
  {
    id: '06_size',
    orderNumber: '06',
    name: '便携携带与比例参照图',
    psychologyBadge: '真实体感无尺码偏差',
    category: '尺码参照',
    sceneHighlight: '成年手掌自然轻握，或与日常经典随身物品同框并列，直观展现真实人体工学比例',
    commercialStrategy: '真实呈现握持手感与空间占用，彻底消除买家对大小尺寸的认知模糊与落差退货',
    quickTweaks: [
      { id: 'hand_grip', label: '🖐️ 成年手掌自然轻握', tweakText: '真实成年人手部自然人体工学握持，呈现一手掌控的真实体感与尺寸参照' },
      { id: 'daily_items', label: '📱 与日常经典物品同框', tweakText: '与手机/口红/钥匙等日常随身物品并列同框，直观参照小巧体量' },
      { id: 'portable_storage', label: '👜 随身包袋收纳体量', tweakText: '随手收纳在日常随身包袋口袋中，清晰展现便携收纳体量' },
      { id: 'multi_angle_scale', label: '📐 多视角标准规格比例', tweakText: '端正呈现正面与侧面标准比例，直观呈现长宽厚度人体工学体量' },
    ],
  },
  {
    id: '07_emotional',
    orderNumber: '07',
    name: '品牌情绪与质感氛围图',
    psychologyBadge: '高端品牌溢价塑造',
    category: '品牌格调',
    sceneHighlight: '电影级暗调冷金光束，微醺烟雾漫射，极简几何大理石展台，营造杂志封面级张力',
    commercialStrategy: '营造沉浸式轻奢格调，拔高产品定位与审美认知，大幅拉升品牌溢价与客单价',
    quickTweaks: [
      { id: 'cinematic_gold_light', label: '🎬 电影级暗调冷金光', tweakText: '电影级宽画幅暗调打光，一道狭长冷金光束精准勾勒轮廓' },
      { id: 'smoke_diffusion', label: '🌫️ 微醺高级烟雾漫射', tweakText: '背景带有微醺缭绕的高级柔和冷雾与丁达尔光束漫射' },
      { id: 'marble_steps', label: '🏛️ 极简几何大理石台阶', tweakText: '置于高低错落的卡拉拉白与深灰大理石几何台阶展台上' },
      { id: 'sunset_blue_hour', label: '🌅 蓝调落日余晖色彩', tweakText: '背景透出黄昏Magic Hour深邃蓝调与落日天际线微光，格调深沉' },
    ],
  },
  {
    id: '08_color',
    orderNumber: '08',
    name: '全系配色与规格陈列图',
    psychologyBadge: '丰富选择促进连单',
    category: '多色矩阵',
    sceneHighlight: '高低错落极简展台，全系规格与经典配色矩阵全景平齐陈列，统一摄影色温精准无偏色',
    commercialStrategy: '提供全景丰富选款体验，满足个性化审美偏好，刺激套装与多规格连带下单',
    quickTweaks: [
      { id: 'staggered_pedestals', label: '🧱 高低错落展台陈列', tweakText: '采用高低层次分明的极简几何展台，多款经典规格主次分明错落陈列' },
      { id: 'accurate_color_temp', label: '🎨 统一色温精准无偏色', tweakText: '5500K专业商业标准色温高显色指数主光，确保各配色真实还原无色差' },
      { id: 'gift_box_set', label: '🎁 礼盒送礼全套陈列', tweakText: '背景伴随质感送礼定制烫金硬壳礼盒与礼袋，提升送礼档次感' },
      { id: 'individual_highlights', label: '✨ 各款轮廓精致高光', tweakText: '每一款配色轮廓均有一条精致侧逆轮廓高光，互相呼应立体感强烈' },
    ],
  },
  {
    id: '09_buyer_show',
    orderNumber: '09',
    name: '真实买家秀种草图',
    psychologyBadge: '社交真实感与口碑背书',
    category: '买家社交',
    sceneHighlight: '小红书风格第一人称真实手持，窗边随手抓拍感，轻微生活感自然漫射，消除摆拍感',
    commercialStrategy: '消除过度商业精修的生硬距离感，提供极具亲和力的买家口碑背书，促进最终付款决策',
    quickTweaks: [
      { id: 'redbook_first_person', label: '📱 小红书第一人称手持', tweakText: '第一人称视角随手拿起使用，背景有生活桌面或梳妆台温馨一角' },
      { id: 'window_snap', label: '🌇 窗边随手抓拍感', tweakText: '自然窗边随手抓拍，柔和漫射采光，构图自然随性无棚拍痕迹' },
      { id: 'film_grain', label: '🎞️ 轻微生活胶片颗粒', tweakText: '画面融入微量生活胶片暖调颗粒感，呈现温暖惬意的生活格调' },
      { id: 'candid_natural', label: '💬 消除棚拍刻意摆拍痕迹', tweakText: '消除过于完美的商业打光与道具摆弄，展现真实买家开箱爱不释手的瞬间' },
    ],
  },
];

export function getPerspectiveStrategy(
  id?: string,
  index: number = 0,
  productInfo?: ProductInfoContext | null
): PerspectiveStrategyDef {
  let base: PerspectiveStrategyDef;

  if (id) {
    const found = BASE_PERSPECTIVE_STRATEGIES.find((item) => {
      if (item.id === id) return true;
      if (id.length >= 2 && item.orderNumber === id.substring(0, 2)) return true;
      if (id.includes(item.id.replace(/^\d+_/, ''))) return true;
      return false;
    });
    base = found || BASE_PERSPECTIVE_STRATEGIES[Math.max(0, Math.min(index, BASE_PERSPECTIVE_STRATEGIES.length - 1))];
  } else {
    const safeIdx = Math.max(0, Math.min(index, BASE_PERSPECTIVE_STRATEGIES.length - 1));
    base = BASE_PERSPECTIVE_STRATEGIES[safeIdx];
  }

  // 若传入具体商品信息，深度动态插值，彻底消除硬编码痕迹
  if (productInfo?.name) {
    const prodName = productInfo.name;
    const painPoints = productInfo.pain_points;
    const materials = productInfo.material_features;

    let customizedHighlight = base.sceneHighlight;
    let customizedStrategy = base.commercialStrategy;
    let customizedTweaks = [...base.quickTweaks];

    const lowerInfo = `${prodName} ${productInfo.category || ''} ${materials || ''}`.toLowerCase();
    const isPet = /猫|狗|犬|宠物|猫砂|砂棚|爬架|牵引绳|水族/.test(lowerInfo);
    const isBeauty = /精华|护肤|美妆|面霜|口红|原液|水乳|防晒|粉底|洗面奶/.test(lowerInfo);
    const isLarge = /家具|沙发|茶几|床|柜|桌|椅|冰箱|洗衣机|扫地机|净化器/.test(lowerInfo);

    if (base.id === '01_white_bg') {
      customizedHighlight = `30°纯白无影展台微俯视，极浅镜面接触微倒影，凸显【${prodName}】原装质地与光泽`;
    } else if (base.id === '02_scene') {
      if (isPet) {
        customizedHighlight = `融入真实温馨家居环境（现代客厅阳光处/落地窗旁），柔和自然晨光斜射，猫咪在旁惬意陪伴`;
      } else if (isBeauty) {
        customizedHighlight = `融入现代高定浴室洗手台或精致梳妆台，晨光透射，水润光泽倒影与水光涟漪点缀`;
      } else {
        customizedHighlight = `清晨自然晨光穿透纱帘斜射，融入真实生活环境台面，自然展现【${prodName}】日常高品质陪伴场景`;
      }
    } else if (base.id === '03_detail' && materials) {
      customizedHighlight = `镜头贴近局部 5-10 厘米极限微距，高光细腻勾勒【${materials.slice(0, 30)}】，超浅景深虚化`;
    } else if (base.id === '04_structure') {
      if (isPet) {
        customizedHighlight = `模块化可拆卸顶盖、抽屉式砂底盒与抑菌除臭滤芯组件轴向悬浮爆炸透视(Exploded View)`;
      } else if (isBeauty) {
        customizedHighlight = `高阶活性分子水网解析与精工滴管泵头轴向微距悬浮解析，展现深层渗透科技`;
      }
    } else if (base.id === '05_pain_killer') {
      if (painPoints) {
        customizedHighlight = `针对买家核心痛点（${painPoints.slice(0, 32)}），高速快门多机位动感抓拍硬核实测瞬间，无瑕表现彻底打消退货疑虑`;
        customizedStrategy = `正面强攻买家最大抗拒点（${painPoints.slice(0, 24)}），用无可辩驳的视觉实证给买家绝对下单安全感`;
      } else if (isPet) {
        customizedHighlight = `针对猫砂外溅飞洒、异味扩散核心顾虑，高速快门抓拍严密隔臭防漏砂实测瞬间`;
      }
    } else if (base.id === '06_size') {
      if (isPet || isLarge) {
        customizedHighlight = `放置于室内家居地面，与成年猫咪或家居沙发并列同框，直观建立宽敞空间体量与占地比例认知`;
        customizedTweaks = [
          { id: 'pet_compare', label: '🐱 成年猫咪同框参照', tweakText: '与成年猫咪亲密同框，直观呈现猫咪轻松进出的宽敞内部空间' },
          { id: 'floor_scale', label: '🛋️ 客厅地面真实占地比例', tweakText: '放置于现代简约客厅木地板，与沙发茶几并列参照真实占地面积' },
          { id: 'door_dimension', label: '📐 宽大出入门洞特写', tweakText: '微距特写宽敞无阻门洞尺寸，凸显胖猫轻松出入不卡身' },
          { id: 'multi_angle_scale', label: '📐 多视角标准规格比例', tweakText: '端正呈现正面与侧面标准比例，直观呈现长宽高度体量' },
        ];
      } else {
        customizedHighlight = `成年手掌自然握持，或与日常随身物品并列摆放，清晰认知【${prodName}】真实人体工学比例`;
      }
    } else if (base.id === '09_buyer_show') {
      if (isPet) {
        customizedHighlight = `小红书真实买家秀风格，温馨客厅随手抓拍，猫咪好奇靠近或踩踏出入，生活感十足`;
        customizedTweaks = [
          { id: 'cat_candid', label: '🐾 猫咪好奇互动抓拍', tweakText: '自然随手抓拍猫咪好奇靠近或踩踏踏板的生动萌态，毫无摆拍痕迹' },
          { id: 'warm_livingroom', label: '🏡 真实客厅温馨一角', tweakText: '背景为真实整洁干净的居家客厅一角，自然温暖漫射窗光' },
          { id: 'film_grain', label: '🎞️ 轻微生活胶片颗粒', tweakText: '画面融入微量生活胶片暖调颗粒感，呈现温暖惬意的养宠生活' },
          { id: 'candid_natural', label: '💬 消除棚拍刻意摆拍痕迹', tweakText: '消除过于刻意的商业棚拍感，展现真实铲屎官开箱爱不释手的瞬间' },
        ];
      }
    }

    return {
      ...base,
      sceneHighlight: customizedHighlight,
      commercialStrategy: customizedStrategy,
      quickTweaks: customizedTweaks,
    };
  }

  return base;
}

export function isTweakActive(currentPrompt: string | undefined, tweak: QuickTweakItem): boolean {
  if (!currentPrompt) return false;
  return currentPrompt.includes(tweak.tweakText) || currentPrompt.includes(tweak.label);
}

export function toggleQuickTweak(currentPrompt: string | undefined, tweak: QuickTweakItem): string {
  const base = currentPrompt || '';
  if (isTweakActive(base, tweak)) {
    // Remove tweak
    const escaped = tweak.tweakText.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const escapedLabel = tweak.label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex1 = new RegExp(`[，、\\s]*【微调[：:]\\s*${escaped}】[。]?`, 'g');
    const regex2 = new RegExp(`[，、\\s]*【微调[：:]\\s*${escapedLabel}】[。]?`, 'g');
    const regex3 = new RegExp(`[，、\\s]*${escaped}[。]?`, 'g');
    return base.replace(regex1, '').replace(regex2, '').replace(regex3, '').trim();
  } else {
    // Append tweak non-destructively
    const addition = `【微调：${tweak.tweakText}】`;
    return base ? `${base.trim()} ${addition}` : addition;
  }
}
