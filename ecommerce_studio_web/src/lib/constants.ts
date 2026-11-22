import { Perspective, StylePreset } from '@/types/session';

export const STANDARD_PERSPECTIVES_META: Array<Omit<Perspective, 'prompt_zh' | 'active_version_id' | 'versions'>> = [
  {
    id: '01_white_bg',
    name: '商业纯净白底首图',
    tag: 'CTR点击率收割机',
    desc: '纯白无影棚拍摄，高光比洁净质感，正面略微俯视，让轮廓与质地第一眼吸睛',
    category: '主图转化',
    psychology_target: '搜索列表曝光第一眼抓取，建立品质信任度，拉升点击转化率',
  },
  {
    id: '02_scene',
    name: '真实生活使用场景图',
    tag: '生活方式与身份认同',
    desc: '清晨工作台自然窗光漫射，咖啡/日程本生活道具衬托，自然展现日常使用瞬间',
    category: '场景生活',
    psychology_target: '唤醒消费者对美好居家/办公品质生活的向往，建立情感共鸣',
  },
  {
    id: '03_detail',
    name: '材质工艺与微距细节图',
    tag: '超浅景深精工细节',
    desc: '85mm微距大光圈特写，细腻哑光漫反射与金属拉丝交界，极致工业质感',
    category: '材质工艺',
    psychology_target: '消除廉价塑料感，通过精工级细节特写支撑品牌高端溢价',
  },
  {
    id: '04_structure',
    name: '结构拆解与核心技术图',
    tag: '核心黑科技可视化',
    desc: '悬浮微距爆炸透视，多层密封结构、温控数显芯片与医用级内胆层层呈现',
    category: '原理透视',
    psychology_target: '硬核可视化黑科技，直观展现精密工艺，满足理性参数党',
  },
  {
    id: '05_pain_killer',
    name: '痛点场景攻坚图',
    tag: '打消渗水/烫嘴退货疑虑',
    desc: '背包收纳或倒置严密防护情境，精准展现严密气密防漏与安全阻热承诺',
    category: '痛点消灭',
    psychology_target: '正面攻克历史差评与决策抗拒点，给买家绝对下单安全感',
  },
  {
    id: '06_size',
    name: '便携携带与比例参照图',
    tag: '真实体感无尺码偏差',
    desc: '都市青年自然手持随行或放入标准车载杯架，真实人手比例，直观呈现量感',
    category: '尺码参照',
    psychology_target: '真实呈现便携握持手感与空间占用，避免到手尺寸心理落差',
  },
  {
    id: '07_emotional',
    name: '品牌情绪与质感氛围图',
    tag: '高端品牌溢价塑造',
    desc: '极简深色暗调布景，狭长轮廓冷金边光勾勒，杂志封面级视觉张力',
    category: '品牌格调',
    psychology_target: '营造高端精致的格调美学，加深品牌轻奢印记，促进高客单转化',
  },
  {
    id: '08_color',
    name: '全系配色与规格陈列图',
    tag: '丰富选择促进连单',
    desc: '曜石黑、深空钛、皓月白经典色系矩阵平齐陈列，统一光影质感',
    category: '多色矩阵',
    psychology_target: '提供丰富选款体验，满足个性化审美偏好，促进情侣/送礼连带购买',
  },
  {
    id: '09_buyer_show',
    name: '真实买家秀种草图',
    tag: '社交真实感与口碑背书',
    desc: '自然采光下的桌面一角，无刻意摆拍的真实生活抓拍，小红书生活美学感',
    category: '买家社交',
    psychology_target: '消除过度商业精修的距离感，提供真实买家体验背书，助推种草决策',
  },
];

export const STYLE_PRESETS: StylePreset[] = [
  {
    id: 'minimalist_muji',
    name: '极简原研哉 (日系留白)',
    en_name: 'Minimalist Zen & MUJI Aesthetic',
    badge: '日系留白',
    tagline: '大面积纯净留白，晨光漫射，静谧自然克制',
    description: '源自日本大师原研哉的空之美学(Emptiness)，去除一切冗余修饰，让商品本身成为空间的视觉重心。',
    lighting: '大面积顶光漫反射，微暖柔光箱无刺眼高光，晨光穿透纱帘形成的微弱柔和漫射光，几乎无强烈死黑阴影',
    environment: '浅色原木肌理展台、米白高品质微水泥墙面、日式和纸质感、极其克制的微量禅意留白空间',
    camera: '50mm 标准商业静物中焦段，正面微俯角15度，f/8 中等景深确保商品细节全清晰，透视自然无畸变',
    color_tone: '温暖燕麦色、纯净米白、浅卡其、浅原木色，低饱和度、高明度，呈现天然温润的自然质感',
    anti_drift_rules: ['严禁浓艳色彩', '严禁复杂霓虹与暗黑背景', '严禁炫目反光与凌乱道具'],
    accent_color: '#f59e0b',
  },
  {
    id: 'nordic_luxury',
    name: '北欧轻奢 (莫兰迪低饱和)',
    en_name: 'Nordic Minimal Luxury',
    badge: '莫兰迪轻奢',
    tagline: '灰调高级质感，大理石与冷金点缀，中产格调溢价',
    description: '斯堪的纳维亚现代家居与高端生活方式的结合，注重材质的高阶灰调与微量金属带来的轻奢冲击力。',
    lighting: '侧逆45度自然窗光，伴随柔和丁达尔光束与双色温冷暖漫射，轮廓处有精致的高光细线',
    environment: '卡拉拉白大理石台面、哑光黄铜细金属配件、低饱和度莫兰迪色系羊毛织物、几何水磨石',
    camera: '85mm 商业人像与特写镜头，f/2.8 中浅景深，背景优雅散景虚化，焦内极致锐利',
    color_tone: '莫兰迪灰调（灰绿/灰粉/燕麦灰）、高级冷灰、点缀10%以内的哑光香槟金或冷拉丝金属色',
    anti_drift_rules: ['严禁暴发户式廉价大金大黄', '严禁粗糙塑料反光', '严禁刺眼霓虹光'],
    accent_color: '#10b981',
  },
  {
    id: 'german_deconstruct',
    name: '德系解构 (严谨精工工业)',
    en_name: 'Bauhaus & German Precision Engineering',
    badge: '包豪斯精工',
    tagline: '硬核机械美学，冷冽金属光泽，硬朗理性信任感',
    description: '包豪斯现代主义与德国工业精密的极致融合，突出商品的精密机械装配、硬核功能与不可撼动的工业可靠度。',
    lighting: '高反差硬朗侧逆光、数码级精准切割轮廓光、冷冽银白主光，硬核勾勒出几何边缘与锋利倒角',
    environment: '阳极氧化深灰铝合金台面、炭黑工程塑料支架、精密毫米标尺、无尘实验室级别科技展台',
    camera: '90mm 移轴微距摄影，全景深精细堆叠(Focus Stacking)，极致锐化边缘，无透视形变',
    color_tone: '深空炭黑、冷钛灰、哑光银，极高反差，局部可带有0.5%科技幽蓝或指示冷白LED光效',
    anti_drift_rules: ['严禁粉嫩色系', '严禁温馨家庭杂物', '严禁模糊朦胧镜头'],
    accent_color: '#0ea5e9',
  },
  {
    id: 'dopamine_energy',
    name: '多巴胺活力 (青年明快撞色)',
    en_name: 'Dopamine Bright & Pop Energy',
    badge: 'Z世代高活',
    tagline: '高饱和明快撞色，夏日阳光投影，激发冲动点击',
    description: '拥抱Z世代年轻力与悦己情绪，通过鲜活高饱和的视觉冲击唤醒购买兴奋感，极大拉升CTR点击率。',
    lighting: '模拟夏日正午清透直射阳光，带有清晰锐利的硬直投影，白色反光板高亮度立体补光',
    environment: '纯色通透亚克力展台、波普艺术撞色背景板、水波纹光斑投影、明快极简几何方块堆叠',
    camera: '35mm 人文广角与动感微俯视机位，充满活力的对角线构图，大景深明澈画质',
    color_tone: '明亮柠檬黄、活力珊瑚橙、薄荷绿与克莱因蓝的大胆艺术碰撞，色彩通透浓郁，无压抑灰调',
    anti_drift_rules: ['严禁昏暗暗调', '严禁死黑阴影', '严禁沉闷严肃的商务背景'],
    accent_color: '#ec4899',
  },
  {
    id: 'cyber_street',
    name: '赛博潮酷 (暗夜霓虹潮流)',
    en_name: 'Cyberpunk & Night Street Tech',
    badge: '暗夜霓虹',
    tagline: '暗夜深色基底，蓝紫电光流淌，未来主义科技潮牌',
    description: '电影感赛博朋克与未来潮流街头的混合体，适合主打数码黑科技、电竞装备与先锋潮流的破圈单品。',
    lighting: '双色冷暖高反差切光：45度电光青蓝主侧光 + 135度品红霓虹边缘轮廓反打，暗调深邃黑阶',
    environment: '湿漉沥青反光地面、深黑碳纤维纹理板、全息渐变光晕、暗黑金属几何网格',
    camera: '24mm 超广角低机位仰拍，大透视冲击力，配合暗部电影级细微胶片噪点与光晕漫射(Bloom)',
    color_tone: '深邃极黑(#09090B)、电光青蓝(#00F0FF)、赛博品红(#FF003C)，高反差强视觉冲击',
    anti_drift_rules: ['严禁田园乡村风', '严禁日式米白温馨感', '严禁大面积平庸白光'],
    accent_color: '#8b5cf6',
  },
];

export const DEMO_PRESETS = [
  {
    id: 'smart_cup',
    title: '智能数显真空气密保温杯',
    subtitle: '316L医用钢 / 触控数显 / 都市通勤',
    data: {
      name: '智能数显真空气密随行保温杯',
      category: '316L医用不锈钢 / 哑光亲肤磨砂黑 / 触控数显杯盖',
      target_audience: '25-38岁都市白领、商务通勤人士、注重生活质感的咖啡/茶饮爱好者',
      pain_points: '市面竞品保温时长短、放在背包里容易渗水、杯口易烫嘴、瓶身容易刮花掉漆',
      material_features: '316L医用级不锈钢内胆，外壁曜石黑亲肤喷砂烤漆，高精度LED数显触控屏',
    },
  },
  {
    id: 'face_serum',
    title: '时光极光修护焕亮精华露',
    subtitle: '高活性玻色因 / 极简冰晶瓶 / 敏感肌修复',
    data: {
      name: '时光极光臻萃修护焕亮精华露',
      category: '轻奢院线级护肤 / 渐变极光冰晶玻璃瓶 / 真空按压泵',
      target_audience: '22-35岁高知女性、经常熬夜需要屏障修护的年轻白领、成分党',
      pain_points: '传统精华易氧化失活、瓶口接触污染、质地厚重闷痘、见效慢容易假滑',
      material_features: '双层透光冰晶高硼硅玻璃，微晶流光质地，食品级电化铝冷冽泵头',
    },
  },
  {
    id: 'anc_headphones',
    title: '钛音境空间音频降噪耳机',
    subtitle: '48dB主动降噪 / 记忆海绵 / 高解析金标',
    data: {
      name: '钛音境空间音频头戴式无线降噪耳机',
      category: 'Hi-Fi无损无线音频 / 航空铝金属耳壳 / 蛋白皮透气耳罩',
      target_audience: '音乐发烧友、差旅飞行常客、开放工位需深度专注的极客创作者',
      pain_points: '夹头压耳耳屏疼、降噪耳压感太重、蓝牙延迟大断连、塑料感明显易折断',
      material_features: '航空级钛铝合金转轴，亲肤纳米蛋白皮耳罩，哑光雾面金属外壳',
    },
  },
];

export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    return `${process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '')}/api/v1/studio`;
  }
  return '/api/v1/studio';
};

export const formatAssetUrl = (url?: string | null): string => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    const base = process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, '');
    return `${base}${url.startsWith('/') ? '' : '/'}${url}`;
  }
  return url;
};
