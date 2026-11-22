"use client";

import React, { useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Sparkles,
  Wand2,
  CheckCircle2,
  RefreshCw,
  Layers,
  Palette,
  Tag,
  Info,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { StrategySummaryCard } from './StrategySummaryCard';
import { PerspectiveScriptGrid } from './PerspectiveScriptGrid';
import { Button } from '@/components/ui/button';
import { studioApi } from '@/lib/api-client';

export const Step2Container: React.FC = () => {
  const { currentSession, selectedStylePreset, setSession, setCurrentStep } = useStudioStore();
  const [isGeneratingAI, setIsGeneratingAI] = useState(false);
  const [hasTriggeredAI, setHasTriggeredAI] = useState(false);

  const productName = currentSession?.product_info?.name || '商品';
  const category = currentSession?.product_info?.category;
  const materials = currentSession?.product_info?.material_features || '';
  const painPoints = currentSession?.product_info?.pain_points || '';
  const targetAudience = currentSession?.product_info?.target_audience;
  const currentStyle = selectedStylePreset || currentSession?.style_preset || 'minimalist_muji';

  // 检查是否已有 AI 生成的提示词矩阵
  const hasExistingAIPrompts = Boolean(
    currentSession?.prompts_matrix &&
      currentSession.prompts_matrix.length >= 9 &&
      currentSession.prompts_matrix.some(
        (p) => Boolean(p.scene_highlight) || (p.prompt && p.prompt.length > 50)
      )
  );

  const isMatrixReady = hasTriggeredAI || hasExistingAIPrompts;

  // 一键基于 Step 1 资产特征，调用 AI 根据 9 大图的作用与场景生成提示词与整理
  const handleTriggerAIGeneration = async () => {
    if (!currentSession) return;
    setIsGeneratingAI(true);

    try {
      const res = await studioApi.planMatrix({
        session_id: currentSession.session_id,
        product_info: currentSession.product_info,
        style_preset: currentStyle,
      });

      if (res) {
        setSession(res);
        setHasTriggeredAI(true);
      }
    } catch (err) {
      console.error('AI matrix generation failed:', err);
    } finally {
      setIsGeneratingAI(false);
    }
  };

  const handleProceedToStudio = () => {
    setCurrentStep(3);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 space-y-6 pb-24">
      {/* Step Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            <span>Step 2: 9 大商业矩阵视觉策划</span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              AI 视觉导演全案策划
            </span>
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            基于《{productName}》形态与材质，由大模型针对 9 张图各自的商业转化目的与物理场景要求，全自主推理生成并整理出具体的图片提示词与视觉方案。
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentStep(1)}
            className="text-xs text-slate-700 hover:text-slate-900 border-slate-200"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            返回修改资产特征
          </Button>

          <Button
            variant="studio-accent"
            size="sm"
            onClick={handleProceedToStudio}
            disabled={!isMatrixReady || isGeneratingAI}
            className="text-xs font-semibold gap-1.5 shadow-md shadow-blue-600/20"
          >
            <span>前往 3x3 商业出图工坊 (Step 3)</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* 核心工作台：Step 1 资产特征看板 + 一键调用 AI 生成按钮 */}
      <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-r from-blue-50/90 via-indigo-50/40 to-amber-50/60 border border-blue-200/90 shadow-card space-y-4">
        {/* Step 1 录入的资产特征概览标签 */}
        <div className="flex items-center justify-between flex-wrap gap-2 pb-3 border-b border-blue-200/60">
          <div className="flex items-center gap-1.5 text-xs text-slate-700 font-semibold">
            <Layers className="h-4 w-4 text-blue-600" />
            <span>已载入 Step 1 商业资产档案：</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap text-xs">
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-800 font-medium shadow-2xs">
              <Tag className="h-3 w-3 text-blue-600" />
              <span>商品：{productName}</span>
            </span>

            {/* 实拍图与对标图资产统计标签 */}
            {(() => {
              const refs = currentSession?.product_info?.reference_images || [];
              const actuals = refs.filter((r) => (r.asset_type || 'actual') === 'actual').length;
              const competitors = refs.filter((r) => r.asset_type === 'competitor').length;
              return (
                <>
                  {actuals > 0 && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-blue-100/80 border border-blue-300 text-blue-800 font-medium shadow-2xs">
                      <span>📸 实拍图 {actuals} 张 (锁模保真)</span>
                    </span>
                  )}
                  {competitors > 0 && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-amber-100/80 border border-amber-300 text-amber-800 font-medium shadow-2xs">
                      <span>🛒 对标商品图 {competitors} 张 (构图参考)</span>
                    </span>
                  )}
                </>
              );
            })()}

            {category && (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-800 font-medium shadow-2xs">
                <span>品类：{category}</span>
              </span>
            )}

            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-800 font-medium shadow-2xs">
              <Palette className="h-3 w-3 text-amber-600" />
              <span>流派：{currentStyle}</span>
            </span>

            {targetAudience && (
              <span className="hidden xl:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 text-[11px] max-w-[200px] truncate shadow-2xs">
                <span>客群：{targetAudience}</span>
              </span>
            )}

            {materials && (
              <span className="hidden md:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 text-[11px] max-w-[200px] truncate shadow-2xs">
                <span>材质：{materials}</span>
              </span>
            )}

            {painPoints && (
              <span className="hidden lg:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 text-[11px] max-w-[200px] truncate shadow-2xs">
                <span>痛点：{painPoints}</span>
              </span>
            )}
          </div>
        </div>

        {/* 核心触发横幅与主要按钮 */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1 max-w-3xl">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-blue-600" />
              <span>AI 商业视觉导演 · 9 大图具体提示词生成与整理</span>
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              根据 Step 1 录入的资产信息，系统将针对 9 张图各自的特征与场景要求（
              <strong className="text-slate-800 font-medium">
                01白底首图、02生活场景、03材质微距、04爆炸解构、05痛点实测、06人体工学、07品牌格调、08全系配色、09买家种草
              </strong>
              ），调用 AI 深度推理并生成整理出专属的具体生图提示词与策略卡片。
            </p>
          </div>

          <div className="shrink-0 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Button
              variant="studio-accent"
              size="lg"
              onClick={handleTriggerAIGeneration}
              disabled={isGeneratingAI}
              className="gap-2 text-xs sm:text-sm font-bold h-11 px-5 shadow-md shadow-blue-600/25 bg-blue-600 hover:bg-blue-700 text-white"
            >
              {isGeneratingAI ? (
                <>
                  <Wand2 className="h-4 w-4 animate-spin text-white" />
                  <span>AI 正在逐一规划 9 大图提示词与整理...</span>
                </>
              ) : isMatrixReady ? (
                <>
                  <RefreshCw className="h-4 w-4 text-white" />
                  <span>🔄 重新调用 AI 生成与整理 9 大图提示词</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 text-white" />
                  <span>✨ 一键调用 AI 生成 9 大图提示词与整理</span>
                </>
              )}
            </Button>
          </div>
        </div>

        {/* 状态反馈条 */}
        <div className="pt-1 flex items-center gap-2">
          {isGeneratingAI ? (
            <div className="flex items-center gap-2 text-xs text-blue-700 font-medium">
              <span className="flex h-2 w-2 rounded-full bg-blue-600 animate-pulse" />
              <span>AI 视觉总监正在深度解析商品物理特征，为 9 张图定制对应的构图、光影与生图提示词...</span>
            </div>
          ) : isMatrixReady ? (
            <div className="flex items-center gap-2 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full font-medium shadow-2xs">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
              <span>
                ✅ 9 大图的提示词与策略已由 AI 根据各自场景与功能要求全案整理完成！您可点击下方卡片胶囊快捷微调，或直接前往出图。
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1 rounded-full font-medium shadow-2xs">
              <Info className="h-3.5 w-3.5 text-amber-600 shrink-0" />
              <span>
                👉 请点击上方按钮，触发 AI 基于资产信息为 9 张图分别规划与生成具体的提示词。
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 策略概览卡片 */}
      <StrategySummaryCard />

      {/* 3x3 商业视角策略卡片矩阵 */}
      <PerspectiveScriptGrid />

      {/* 底部常驻通关操作区 */}
      <div className="mt-8 p-6 rounded-2xl bg-gradient-to-r from-blue-50/80 via-white to-amber-50/60 border border-blue-200/80 shadow-card flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="space-y-1 text-center sm:text-left">
          <div className="flex items-center justify-center sm:justify-start gap-2">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <h4 className="text-sm font-bold text-slate-900">
              {isMatrixReady ? '9 大商业视觉策划已锁定，随时可发起批量出图' : '等待 AI 生成 9 大图提示词'}
            </h4>
          </div>
          <p className="text-xs text-slate-600">
            {isMatrixReady
              ? '所有 9 大视角已匹配黄金电商转化动线，提示词已整理就绪，点击右侧按钮进入出图工坊。'
              : '点击上方「一键调用 AI 生成 9 大图提示词与整理」按钮完成策划。'}
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto shrink-0 justify-center">
          <Button
            variant="outline"
            size="default"
            onClick={() => setCurrentStep(1)}
            className="text-xs text-slate-700 hover:text-slate-900 border-slate-200 bg-white"
          >
            <ArrowLeft className="h-3.5 w-3.5 mr-1" />
            返回 Step 1
          </Button>

          <Button
            variant="studio-accent"
            size="lg"
            onClick={handleProceedToStudio}
            disabled={!isMatrixReady || isGeneratingAI}
            className="gap-2 text-sm font-bold px-6 h-12 shadow-md shadow-blue-600/20 bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Sparkles className="h-4 w-4 text-white" />
            <span>前往 3x3 商业出图工坊 (Step 3) →</span>
          </Button>
        </div>
      </div>
    </div>
  );
};
