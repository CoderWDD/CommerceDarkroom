"use client";

import React, { useState } from 'react';
import {
  Sparkles,
  Tag,
  Wand2,
  Sliders,
  Palette,
  Eye,
  FileEdit,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetTrigger,
} from '@/components/ui/sheet';
import { DEMO_PRESETS } from '@/lib/constants';

const QUICK_TAGS_MAP = {
  material: ['316L医用钢', '哑光喷砂', '阳极氧化铝', '食品级硅胶', '高透冰晶玻璃', '碳纤维纹理'],
  demographics: ['25-35岁高知通勤白领', '商务差旅精英', '精品咖啡重度爱好者', '开放工位专注创作者', 'Z世代潮流先锋'],
  painPoints: ['传统杯倒置易漏水弄湿背包', '开盖易烫伤舌头', '瓶身易刮花掉漆', '保温时长衰减快', '做工粗糙塑料感强'],
};

export const CommercialDossierForm: React.FC<{
  onStartPlanning: (directToStep3?: boolean) => void;
  isPlanning: boolean;
}> = ({ onStartPlanning, isPlanning }) => {
  const { currentSession, updateProductInfo, isExtractingDossier } = useStudioStore();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const productInfo = currentSession?.product_info || {
    name: '',
    category: '',
    target_audience: '',
    pain_points: '',
    material_features: '',
    visual_tags: [],
    color_palette: [],
  };

  const visualTags = productInfo.visual_tags || [];
  const colorPalette = productInfo.color_palette || [];

  const handleApplyPreset = (preset: (typeof DEMO_PRESETS)[0]) => {
    updateProductInfo(preset.data);
  };

  const handleInjectTag = (
    field: 'material_features' | 'target_audience' | 'pain_points',
    tagText: string
  ) => {
    const currentVal = productInfo[field] || '';
    const separator = currentVal.trim() ? '，' : '';
    updateProductInfo({
      [field]: `${currentVal}${separator}${tagText}`,
    });
  };

  // Helper to extract hex color from string like "#09090B 曜石黑"
  const extractHex = (str: string): string => {
    const match = str.match(/#([0-9A-Fa-f]{6}|[0-9A-Fa-f]{3})/);
    return match ? match[0] : '#2563EB';
  };

  return (
    <div className="space-y-5 bg-white border border-slate-200 rounded-2xl p-6 shadow-card h-full flex flex-col justify-between">
      <div className="space-y-4">
        {/* Header & Presets */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-blue-600" />
                商品商业档案 (Commercial Dossier)
              </h3>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                多模态就绪
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              实物物理材质与客群决策痛点，作为 9 大黄金商业视角推演与防漂移基石。
            </p>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-slate-500 font-medium">体验样例:</span>
            {DEMO_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className="text-[11px] px-2 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-slate-700 hover:text-blue-700 hover:border-blue-300 hover:bg-blue-50 transition-colors"
              >
                {preset.title.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Highlight Badges (Pills) Section: Visual Tags & Color Palette */}
        <div className="p-4 rounded-xl bg-slate-50/80 border border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800">
              <Eye className="h-3.5 w-3.5 text-blue-600" />
              <span>逆向提炼特征与视觉徽章 (Extracted Pills)</span>
            </div>

            {/* Progressive Disclosure Drawer Trigger */}
            <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="outline"
                  size="xs"
                  className="gap-1.5 text-xs text-slate-700 hover:text-slate-900 border-slate-200 bg-white hover:bg-slate-50"
                >
                  <Sliders className="h-3.5 w-3.5 text-amber-500" />
                  <span>高级参数微调</span>
                </Button>
              </SheetTrigger>

              <SheetContent side="right" className="overflow-y-auto max-w-lg w-full">
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2 text-slate-900">
                    <FileEdit className="h-4 w-4 text-blue-600" />
                    商业档案深度微调 (Dossier Fine-tuning)
                  </SheetTitle>
                  <SheetDescription>
                    您可以对多模态大脑逆向提炼的品名、材质、痛点与客群画像进行针对性手工精修。
                  </SheetDescription>
                </SheetHeader>

                <div className="space-y-5 pt-4">
                  {/* 1. 商品名称 */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-800">
                      商品全称 (Product Full Name)
                    </label>
                    <Input
                      value={productInfo.name || ''}
                      onChange={(e) => updateProductInfo({ name: e.target.value })}
                      placeholder="如：智能触控数显真空气密随行保温杯"
                      className="bg-white border-slate-200 text-xs text-slate-900"
                    />
                  </div>

                  {/* 2. 品类定位 */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-800">
                      精准品类属性 (Category)
                    </label>
                    <Input
                      value={productInfo.category || ''}
                      onChange={(e) => updateProductInfo({ category: e.target.value })}
                      placeholder="如：数码生活良品 / 户外便携水具"
                      className="bg-white border-slate-200 text-xs text-slate-900"
                    />
                  </div>

                  {/* 3. 材质工艺 */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-800">
                        工业材质与表面特征 (Material & Craft)
                      </label>
                      <span className="text-[10px] text-slate-500">点击标签快捷注入</span>
                    </div>
                    <Textarea
                      rows={3}
                      value={productInfo.material_features || ''}
                      onChange={(e) => updateProductInfo({ material_features: e.target.value })}
                      placeholder="描述工业材质与表面工艺"
                      className="bg-white border-slate-200 text-xs text-slate-900"
                    />
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      {QUICK_TAGS_MAP.material.map((tag) => (
                        <Badge
                          key={tag}
                          variant="tag"
                          onClick={() => handleInjectTag('material_features', tag)}
                          className="text-[10px] py-0 px-2"
                        >
                          + {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* 4. 目标客群 */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-800">
                        核心客群与生活方式 (Target Demographics)
                      </label>
                      <span className="text-[10px] text-slate-500">点击标签快捷注入</span>
                    </div>
                    <Textarea
                      rows={3}
                      value={productInfo.target_audience || ''}
                      onChange={(e) => updateProductInfo({ target_audience: e.target.value })}
                      placeholder="描述目标买家画像"
                      className="bg-white border-slate-200 text-xs text-slate-900"
                    />
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      {QUICK_TAGS_MAP.demographics.map((tag) => (
                        <Badge
                          key={tag}
                          variant="tag"
                          onClick={() => handleInjectTag('target_audience', tag)}
                          className="text-[10px] py-0 px-2"
                        >
                          + {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  {/* 5. 核心痛点 */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-800">
                        买家抗拒点与竞品短板 (Pain Points)
                      </label>
                      <span className="text-[10px] text-slate-500">点击标签快捷注入</span>
                    </div>
                    <Textarea
                      rows={3}
                      value={productInfo.pain_points || ''}
                      onChange={(e) => updateProductInfo({ pain_points: e.target.value })}
                      placeholder="描述买家在传统商品上遇到的痛点"
                      className="bg-white border-slate-200 text-xs text-slate-900"
                    />
                    <div className="flex items-center gap-1.5 flex-wrap pt-1">
                      {QUICK_TAGS_MAP.painPoints.map((tag) => (
                        <Badge
                          key={tag}
                          variant="tag"
                          onClick={() => handleInjectTag('pain_points', tag)}
                          className="text-[10px] py-0 px-2"
                        >
                          + {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2">
                    <Button
                      variant="studio-accent"
                      onClick={() => setDrawerOpen(false)}
                      className="w-full"
                    >
                      完成微调并关闭抽屉
                    </Button>
                  </div>
                </div>
              </SheetContent>
            </Sheet>
          </div>

          {/* Visual Tags Pills */}
          <div className="space-y-1.5">
            <span className="text-[11px] text-slate-600 font-medium flex items-center gap-1">
              <Tag className="h-3 w-3 text-blue-600" />
              <span>提取的视觉微标签 (Visual Tags):</span>
            </span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {visualTags.length > 0 ? (
                visualTags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1 text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 shadow-xs"
                  >
                    <span>{tag.startsWith('#') ? tag : `#${tag}`}</span>
                  </span>
                ))
              ) : (
                <span className="text-xs text-slate-400 italic">
                  上传实物图后将自动逆向分析并生成视觉微标签
                </span>
              )}
            </div>
          </div>

          {/* Color Palette Pills */}
          <div className="space-y-1.5 pt-1 border-t border-slate-200/80">
            <span className="text-[11px] text-slate-600 font-medium flex items-center gap-1">
              <Palette className="h-3 w-3 text-amber-500" />
              <span>主色调色板 (Color Palette):</span>
            </span>
            <div className="flex items-center gap-2 flex-wrap">
              {colorPalette.length > 0 ? (
                colorPalette.map((colorStr, idx) => {
                  const hex = extractHex(colorStr);
                  return (
                    <div
                      key={idx}
                      className="inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-700 shadow-xs"
                    >
                      <span
                        className="h-3 w-3 rounded-full border border-slate-300 shrink-0"
                        style={{ backgroundColor: hex }}
                      />
                      <span>{colorStr}</span>
                    </div>
                  );
                })
              ) : (
                <span className="text-xs text-slate-400 italic">
                  上传实物图后自动提取实物 Hex 色阶与配色
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Core Dossier Summary Preview Card */}
        <div className="space-y-3">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-800 flex items-center justify-between">
              <span>商品商业全称 (Product Commercial Name)</span>
              <span className="text-[10px] text-slate-500">主图与营销核心识别</span>
            </label>
            <Input
              value={productInfo.name || ''}
              onChange={(e) => updateProductInfo({ name: e.target.value })}
              placeholder="如：智能触控数显真空气密随行保温杯"
              className="bg-white border-slate-200 text-sm font-medium focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-800">
                材质工艺特征 (Material Features)
              </label>
              <Textarea
                rows={2}
                value={productInfo.material_features || productInfo.category || ''}
                onChange={(e) =>
                  updateProductInfo({
                    material_features: e.target.value,
                    category: e.target.value,
                  })
                }
                placeholder="316L不锈钢内胆、曜石黑微米级喷砂烤漆..."
                className="bg-white border-slate-200 text-xs min-h-[58px]"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-800">
                买家抗拒点 / 痛点攻坚 (Pain Points to Crush)
              </label>
              <Textarea
                rows={2}
                value={productInfo.pain_points || ''}
                onChange={(e) => updateProductInfo({ pain_points: e.target.value })}
                placeholder="传统保温杯倒置易渗水、保温衰减快、杯口易烫嘴..."
                className="bg-white border-slate-200 text-xs min-h-[58px]"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Proceed to Step 2 Navigation Action */}
      <div className="pt-2 space-y-2">
        <div className="flex flex-col sm:flex-row items-center gap-2.5">
          <Button
            variant="studio-accent"
            size="lg"
            onClick={() => onStartPlanning(false)}
            disabled={isExtractingDossier || !productInfo.name?.trim()}
            className="w-full sm:flex-1 gap-2 text-xs sm:text-sm h-11 shadow-md shadow-blue-600/20"
          >
            <Sparkles className="h-4 w-4 text-white" />
            <span>下一步：进入 9 大矩阵策划 (在 Step 2 触发 AI 生成提示词) →</span>
          </Button>

          <Button
            variant="outline"
            size="lg"
            onClick={() => onStartPlanning(true)}
            disabled={isPlanning || isExtractingDossier || !productInfo.name?.trim()}
            className="w-full sm:w-auto text-xs h-11 text-slate-700 hover:text-slate-900 border-slate-200 bg-white hover:bg-slate-50 gap-1.5"
          >
            {isPlanning ? (
              <>
                <Wand2 className="h-3.5 w-3.5 animate-spin text-slate-500" />
                <span>极速全案推演中...</span>
              </>
            ) : (
              <span>🚀 极速直通 Step 3 出图</span>
            )}
          </Button>
        </div>
        <p className="text-[11px] text-slate-500 text-center">
          💡 完成资产特征录入后进入 Step 2，点击专属按钮即可一键调用 AI 结合 9 大图各自的作用与场景进行深度生成和整理
        </p>
      </div>
    </div>
  );
};
