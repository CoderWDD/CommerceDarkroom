"use client";

import React from 'react';
import { Sparkles, Tag, ArrowRight, Wand2 } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { DEMO_PRESETS } from '@/lib/constants';

const QUICK_TAGS_MAP = {
  material: ['316L医用钢', '哑光喷砂', '阳极氧化铝', '食品级硅胶', '高透冰晶玻璃'],
  demographics: ['25-35岁高知通勤白领', '商务差旅精英', '精品咖啡重度爱好者', '开放工位专注创作者'],
  painPoints: ['传统杯倒置易漏水弄湿背包', '开盖易烫伤舌头', '瓶身易刮花掉漆', '保温时长衰减快'],
};

export const CommercialDossierForm: React.FC<{ onStartPlanning: () => void; isPlanning: boolean }> = ({
  onStartPlanning,
  isPlanning,
}) => {
  const { currentSession, updateProductInfo } = useStudioStore();
  const productInfo = currentSession?.product_info || {
    name: '',
    category: '',
    target_audience: '',
    pain_points: '',
    material_features: '',
  };

  const handleApplyPreset = (preset: (typeof DEMO_PRESETS)[0]) => {
    updateProductInfo(preset.data);
  };

  const handleInjectTag = (field: 'material_features' | 'target_audience' | 'pain_points', tagText: string) => {
    const currentVal = productInfo[field] || '';
    const separator = currentVal.trim() ? '，' : '';
    updateProductInfo({
      [field]: `${currentVal}${separator}${tagText}`,
    });
  };

  return (
    <div className="space-y-6 bg-zinc-900/60 backdrop-blur-md border border-white/[0.08] rounded-2xl p-6 shadow-2xl">
      {/* Header & Presets */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div>
            <h3 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-sky-400" />
              商品商业档案 (Commercial Dossier)
            </h3>
            <p className="text-xs text-zinc-400 mt-0.5">
              输入商品物理材质特征与客群决策痛点，作为 9 大镜头语言推演的基石。
            </p>
          </div>

          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] text-zinc-500 font-medium">快速体验样例:</span>
            {DEMO_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-800 border border-white/10 text-zinc-300 hover:text-sky-300 hover:border-sky-500/40 transition-colors"
              >
                {preset.title.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {/* 1. 商品名称与品类定位 */}
        <div className="space-y-1.5">
          <label className="text-xs font-medium text-zinc-300 flex items-center justify-between">
            <span>1. 商品名称与品类属性 (Product Name & Category)</span>
            <span className="text-[10px] text-zinc-500 font-normal">必填</span>
          </label>
          <Input
            value={productInfo.name || ''}
            onChange={(e) => updateProductInfo({ name: e.target.value })}
            placeholder="如：智能数显真空气密随行保温杯"
            className="bg-zinc-950/60 border-white/10 text-sm focus:border-sky-500/50"
          />
        </div>

        {/* 2. 材质工艺与工业特征 */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-zinc-300">
              2. 材质工艺与工业特征 (Material & Craft)
            </label>
            <div className="flex items-center gap-1 text-[11px] text-zinc-500">
              <Tag className="h-3 w-3" />
              <span>点击快捷注入:</span>
            </div>
          </div>
          <Textarea
            rows={2}
            value={productInfo.material_features || productInfo.category || ''}
            onChange={(e) => updateProductInfo({ material_features: e.target.value, category: e.target.value })}
            placeholder="描述商品外观质感，如：316L医用级不锈钢内胆，外壁曜石黑哑光亲肤喷砂，触控LED冷光数显杯盖"
            className="bg-zinc-950/60 border-white/10 text-xs min-h-[64px]"
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

        {/* 3. 核心目标客群画像 */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-zinc-300">
              3. 核心目标客群与使用场域 (Target Demographics)
            </label>
            <div className="flex items-center gap-1 text-[11px] text-zinc-500">
              <Tag className="h-3 w-3" />
              <span>点击快捷注入:</span>
            </div>
          </div>
          <Textarea
            rows={2}
            value={productInfo.target_audience || ''}
            onChange={(e) => updateProductInfo({ target_audience: e.target.value })}
            placeholder="如：25-38岁高知都市白领、商务差旅人士、注重办公桌仪式感的精品咖啡/茶饮爱好者"
            className="bg-zinc-950/60 border-white/10 text-xs min-h-[64px]"
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

        {/* 4. 竞品差评与核心抗拒点 */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-zinc-300">
              4. 竞品差评与买家核心决策抗拒点 (Pain Points to Crush)
            </label>
            <div className="flex items-center gap-1 text-[11px] text-zinc-500">
              <Tag className="h-3 w-3" />
              <span>点击快捷注入:</span>
            </div>
          </div>
          <Textarea
            rows={2}
            value={productInfo.pain_points || ''}
            onChange={(e) => updateProductInfo({ pain_points: e.target.value })}
            placeholder="如：市面竞品保温时长短、放在背包里容易渗水弄湿电脑、杯口易烫嘴、瓶身容易刮花掉漆"
            className="bg-zinc-950/60 border-white/10 text-xs min-h-[64px]"
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
      </div>

      {/* Start Planning CTA Button */}
      <div className="pt-2">
        <Button
          variant="studio-accent"
          size="lg"
          onClick={onStartPlanning}
          disabled={isPlanning || !productInfo.name?.trim()}
          className="w-full gap-2 text-sm h-11"
        >
          {isPlanning ? (
            <>
              <Wand2 className="h-4 w-4 animate-spin text-sky-200" />
              <span>正在基于商品特征解构 9 大商业视觉矩阵...</span>
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" />
              <span>启动商业摄影全案推演 (自动策划 9 大视觉方案)</span>
              <ArrowRight className="h-4 w-4 ml-1" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
};
