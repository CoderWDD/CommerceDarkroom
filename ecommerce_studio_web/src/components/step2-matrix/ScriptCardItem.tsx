"use client";

import React, { useState } from 'react';
import {
  Wand2,
  Check,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Target,
  Shield,
  SlidersHorizontal,
  Lock,
  RotateCw,
} from 'lucide-react';
import { Perspective, QuickTweakItem } from '@/types/session';
import { useStudioStore, matchPerspectiveId } from '@/stores/useStudioStore';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { studioApi } from '@/lib/api-client';
import {
  getPerspectiveStrategy,
  isTweakActive,
  toggleQuickTweak,
} from '@/lib/perspective-strategies';

interface ScriptCardItemProps {
  perspective: Perspective;
  index: number;
}

export const ScriptCardItem: React.FC<ScriptCardItemProps> = ({
  perspective,
  index,
}) => {
  const {
    currentSession,
    updatePerspectivePrompt,
    updatePerspectiveScript,
    activePerspectiveId,
    setActivePerspectiveId,
  } = useStudioStore();

  const [isRefining, setIsRefining] = useState(false);
  const [justRefined, setJustRefined] = useState(false);
  const [isReimagining, setIsReimagining] = useState(false);
  const [justReimagined, setJustReimagined] = useState(false);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [lastTweakToggled, setLastTweakToggled] = useState<string | null>(null);

  // 1. 本地策略兜底计算
  const fallbackStrategy = getPerspectiveStrategy(perspective.id, index, currentSession?.product_info);

  // 2. 匹配大模型全案推演生成的 prompts_matrix 条目
  const matrixItem = currentSession?.prompts_matrix?.find((item) =>
    matchPerspectiveId(item.id, perspective.id)
  );

  // 检查是否已有 AI 针对本视角生成的构想
  const isPlanned = Boolean(perspective.scene_highlight || matrixItem?.scene_highlight);

  // 3. 优先使用大模型动态输出的画面构想与商业策略，无则平稳降级
  const sceneHighlight =
    perspective.scene_highlight ||
    matrixItem?.scene_highlight ||
    fallbackStrategy.sceneHighlight;

  const commercialStrategy =
    perspective.commercial_strategy ||
    matrixItem?.commercial_strategy ||
    perspective.psychology_target ||
    fallbackStrategy.commercialStrategy;

  // 4. 优先使用大模型为该商品专属推导的定制微调胶囊，无则平稳降级
  const rawTweaks = perspective.quick_tweaks || matrixItem?.quick_tweaks;
  const rawPills = perspective.quick_tweak_pills || matrixItem?.quick_tweak_pills;

  let quickTweaks: QuickTweakItem[] = [];
  if (Array.isArray(rawTweaks) && rawTweaks.length > 0) {
    quickTweaks = rawTweaks;
  } else if (Array.isArray(rawPills) && rawPills.length > 0) {
    quickTweaks = rawPills.map((pill, idx) => ({
      id: `pill_${idx}`,
      label: pill,
      tweakText: pill,
    }));
  } else {
    quickTweaks = fallbackStrategy.quickTweaks;
  }

  const promptText = perspective.prompt_zh || '';
  const isSelected = activePerspectiveId === perspective.id;

  const handleBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
    updatePerspectivePrompt(perspective.id, e.target.value);
  };

  const handleTogglePill = (e: React.MouseEvent, tweak: QuickTweakItem) => {
    e.stopPropagation();
    const updated = toggleQuickTweak(promptText, tweak);
    updatePerspectivePrompt(perspective.id, updated);
    setLastTweakToggled(tweak.label);
    setTimeout(() => setLastTweakToggled(null), 1500);
  };

  // 单卡级 AI 全自主重新构思
  const handleReimagine = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!currentSession) return;
    setIsReimagining(true);

    try {
      const prodName = currentSession.product_info?.name || '商品';
      const res = await studioApi.regeneratePerspectiveScript({
        session_id: currentSession.session_id,
        perspective_id: perspective.id,
        instruction: `针对【${perspective.name}】进行全新的画面创意构思，结合《${prodName}》物理材质与买家决策心理，全自主重新规划机位视角、生活场域道具与光影层次。`,
        current_prompt: promptText,
      });

      if (res?.prompt_zh) {
        updatePerspectiveScript(perspective.id, {
          prompt_zh: res.prompt_zh,
          scene_highlight: res.scene_highlight,
          commercial_strategy: res.commercial_strategy,
          quick_tweaks: res.quick_tweaks,
          quick_tweak_pills: res.quick_tweak_pills,
        });
        setJustReimagined(true);
        setTimeout(() => setJustReimagined(false), 2200);
      }
    } catch (err) {
      console.error('Reimagine error, fallback to refinePrompt:', err);
      try {
        const res = await studioApi.refinePrompt({
          session_id: currentSession.session_id,
          perspective_id: perspective.id,
          instruction: `针对【${perspective.name}】全自主重新规划机位视角与光影层次。`,
          current_prompt: promptText,
        });
        if (res?.refined_prompt) {
          updatePerspectivePrompt(perspective.id, res.refined_prompt);
          setJustReimagined(true);
          setTimeout(() => setJustReimagined(false), 2200);
          return;
        }
      } catch {}
      // Fallback local dynamic enhancement
      const enhanced = `${promptText} 商业产品静物摄影，大师级控光，85mm微距景深，锐利反差细节，纯正商业棚拍质感。`.trim();
      updatePerspectivePrompt(perspective.id, enhanced);
      setJustReimagined(true);
      setTimeout(() => setJustReimagined(false), 2200);
    } finally {
      setIsReimagining(false);
    }
  };

  const handleMagicRefine = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!currentSession) return;
    setIsRefining(true);

    try {
      const res = await studioApi.refinePrompt({
        session_id: currentSession.session_id,
        perspective_id: perspective.id,
        instruction: '强化商业摄影棚顶级柔光箱打光、85mm定焦景深与真实工业反光质感',
        current_prompt: promptText,
      });

      if (res?.refined_prompt) {
        updatePerspectivePrompt(perspective.id, res.refined_prompt);
        setJustRefined(true);
        setTimeout(() => setJustRefined(false), 2000);
      }
    } catch (err) {
      console.error('Magic refine error:', err);
      // Fallback local enhancement
      const enhanced = `${promptText} 商业产品静物摄影，大师级控光，85mm微距景深，锐利反差细节，纯正商业棚拍质感。`.trim();
      updatePerspectivePrompt(perspective.id, enhanced);
      setJustRefined(true);
      setTimeout(() => setJustRefined(false), 2000);
    } finally {
      setIsRefining(false);
    }
  };

  return (
    <div
      onClick={() => setActivePerspectiveId(perspective.id)}
      className={`group flex flex-col justify-between rounded-2xl p-5 transition-all duration-200 border shadow-card bg-white relative cursor-pointer ${
        justReimagined || justRefined
          ? 'border-emerald-500 ring-1 ring-emerald-500/30 bg-emerald-50/20'
          : isSelected
          ? 'border-blue-500 ring-1 ring-blue-500/30 shadow-card-hover'
          : 'border-slate-200 hover:border-blue-400 hover:shadow-card-hover'
      }`}
    >
      <div className="space-y-4">
        {/* ① 机位角标与转化定位 (Perspective & Psychology Anchor) */}
        <div className="flex items-start justify-between gap-3 border-b border-slate-100 pb-3">
          <div className="space-y-1.5 flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-xs font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-200 shrink-0">
                {fallbackStrategy.orderNumber}
              </span>
              <h4 className="text-sm font-bold text-slate-900 truncate">
                {perspective.name || fallbackStrategy.name}
              </h4>
              <Badge
                variant="outline"
                className="text-[10px] px-2 py-0 font-medium text-slate-500 border-slate-200 bg-slate-50"
              >
                {perspective.category || fallbackStrategy.category}
              </Badge>
            </div>

            {/* Psychology Anchor Pill */}
            <div className="flex items-center gap-2 pt-0.5 flex-wrap">
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full shadow-xs">
                <Target className="h-3 w-3 text-emerald-600" />
                <span>{perspective.tag || fallbackStrategy.psychologyBadge}</span>
              </span>
              {lastTweakToggled && (
                <span className="text-[10px] text-blue-700 bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded animate-pulse">
                  已切换微调
                </span>
              )}
              {justReimagined && (
                <span className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-medium animate-pulse">
                  ✨ AI 已重新构想此场景
                </span>
              )}
            </div>
          </div>

          {/* Quick AI Reimagine Button in Header */}
          <Button
            variant="outline"
            size="xs"
            onClick={handleReimagine}
            disabled={isReimagining}
            className="shrink-0 gap-1 text-[11px] font-medium text-amber-800 bg-amber-50 hover:bg-amber-100/90 border-amber-300 hover:border-amber-400 shadow-xs"
            title="让 AI 视觉导演针对该机位重新推演全新的画面构思与镜头语言"
          >
            {isReimagining ? (
              <>
                <Wand2 className="h-3 w-3 animate-spin text-amber-600" />
                <span>构思中...</span>
              </>
            ) : (
              <>
                <Sparkles className="h-3 w-3 text-amber-600" />
                <span>✨ 重新构思</span>
              </>
            )}
          </Button>
        </div>

        {/* ② 电商大白话画面构想 (Plain-English Scene Highlight - 3W1H Dynamic AI First) */}
        <div className="rounded-xl p-3 bg-amber-50/60 border border-amber-200/70 space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-900">
              <Sparkles className="h-3.5 w-3.5 text-amber-600" />
              <span>画面构想亮点 (3W1H 大白话)</span>
            </div>
            {isPlanned ? (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-100/80 text-emerald-800 border border-emerald-300 flex items-center gap-1 shadow-2xs">
                <span>✨ AI 专属构思</span>
              </span>
            ) : (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-500 border border-slate-200">
                待触发规划
              </span>
            )}
          </div>

          {isReimagining ? (
            <div className="flex items-center gap-2 py-2 text-xs text-amber-800 font-medium">
              <Wand2 className="h-3.5 w-3.5 animate-spin text-amber-600" />
              <span>AI 视觉导演正在根据 3W1H 物理场景法则深度重新构思此画面...</span>
            </div>
          ) : isPlanned ? (
            <p className="text-xs text-slate-800 leading-relaxed font-normal">
              {sceneHighlight}
            </p>
          ) : (
            <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-amber-100/40 border border-dashed border-amber-300/80 text-xs text-amber-900/80">
              <span className="leading-snug">
                ⏳ 尚未构想。点击顶部「一键调用 AI 生成」或右侧按钮，AI 将量身构想具体画面
              </span>
              <Button
                variant="outline"
                size="xs"
                onClick={handleReimagine}
                className="shrink-0 text-[10px] h-6 px-2 text-amber-800 bg-white hover:bg-amber-50 border-amber-300"
              >
                ✨ 立即构想此图
              </Button>
            </div>
          )}
        </div>

        {/* ③ 商业攻坚与转化策略 (Commercial Strategy - Dynamic AI First) */}
        <div className="rounded-xl p-3 bg-blue-50/50 border border-blue-200/60 space-y-1.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-800">
              <Shield className="h-3.5 w-3.5 text-blue-600" />
              <span>商业攻坚策略</span>
            </div>
            {(perspective.commercial_strategy || matrixItem?.commercial_strategy) && (
              <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-blue-200/60 text-blue-900 border border-blue-300/60">
                心理靶向推演
              </span>
            )}
          </div>
          <p className="text-xs text-slate-700 leading-relaxed font-normal">
            {commercialStrategy}
          </p>
        </div>

        {/* ④ 免打字快捷风格微调胶囊 (One-Click Visual Tweaks - Dynamic AI First) */}
        <div className="space-y-2 pt-1">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-700 flex items-center gap-1.5">
              <SlidersHorizontal className="h-3.5 w-3.5 text-blue-600" />
              <span>一键微调胶囊 (免手写):</span>
            </span>
            <span className="text-[10px] text-slate-500">点击即生效</span>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {quickTweaks.map((tweak) => {
              const active = isTweakActive(promptText, tweak);
              return (
                <button
                  key={tweak.id}
                  type="button"
                  onClick={(e) => handleTogglePill(e, tweak)}
                  className={`text-[11px] px-2.5 py-1 rounded-full transition-all duration-150 flex items-center gap-1 select-none ${
                    active
                      ? 'bg-blue-50 text-blue-700 border border-blue-300 ring-1 ring-blue-500/20 font-semibold shadow-xs'
                      : 'bg-slate-100 text-slate-700 hover:text-slate-900 border border-slate-200 hover:border-slate-300 hover:bg-slate-200/70'
                  }`}
                  title={tweak.tweakText}
                >
                  <span>{tweak.label}</span>
                  {active && <Check className="h-3 w-3 text-blue-600" />}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ⑤ 底部卡片级操作栏与渐进式折叠底层摄影参数 */}
      <div className="pt-4 mt-4 border-t border-slate-100 space-y-2.5">
        <div className="flex items-center justify-between gap-2">
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setIsDrawerOpen(!isDrawerOpen);
            }}
            className="flex-1 flex items-center justify-between text-xs text-slate-500 hover:text-slate-800 py-1.5 px-2.5 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-colors"
          >
            <span className="flex items-center gap-1.5 text-[11px]">
              <span>⚙️ 展开查看底层摄影提示词与防漂移语法</span>
            </span>
            {isDrawerOpen ? (
              <ChevronUp className="h-3.5 w-3.5 text-slate-400" />
            ) : (
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            )}
          </button>

          <Button
            variant="ghost"
            size="xs"
            onClick={handleReimagine}
            disabled={isReimagining}
            className="text-[11px] text-amber-700 hover:text-amber-900 hover:bg-amber-50 h-8 px-2"
          >
            <RotateCw className={`h-3 w-3 mr-1 ${isReimagining ? 'animate-spin' : ''}`} />
            <span>换个构思</span>
          </Button>
        </div>

        {isDrawerOpen && (
          <div className="space-y-2.5 pt-2 animate-in fade-in slide-in-from-top-2 duration-200">
            {/* Locking hint */}
            <div className="flex items-start gap-1.5 text-[11px] text-amber-800 bg-amber-50 border border-amber-200 p-2 rounded-lg leading-relaxed">
              <Lock className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
              <span>
                已由 AI 视觉导演全自主推演并注入流派防漂移语法（4A总监级镜头参数，非专业人士无需修改）。
              </span>
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between text-[10px] text-slate-500">
                <span>底层镜头与打光指令 (失焦自动存盘)</span>
                <span className="font-mono text-slate-400">{promptText.length} 字</span>
              </div>
              <Textarea
                rows={4}
                defaultValue={promptText}
                key={promptText}
                onBlur={handleBlur}
                onClick={(e) => e.stopPropagation()}
                placeholder="正在由 AI 视觉导演装配镜头与光影参数..."
                className="font-mono text-[11px] bg-slate-50 border-slate-200 resize-none leading-relaxed text-slate-800 focus:border-blue-500 rounded-lg"
              />
            </div>

            <div className="flex items-center justify-between pt-1">
              <span className="text-[10px] text-slate-400">修改后将直接作用于出图</span>
              <Button
                variant="outline"
                size="xs"
                onClick={handleMagicRefine}
                disabled={isRefining}
                className="gap-1.5 text-[11px] text-indigo-600 border-indigo-200 hover:bg-indigo-50 hover:border-indigo-300"
              >
                {isRefining ? (
                  <>
                    <Wand2 className="h-3 w-3 animate-spin text-indigo-600" />
                    <span>润色中...</span>
                  </>
                ) : justRefined ? (
                  <>
                    <Check className="h-3 w-3 text-emerald-600" />
                    <span>已优化</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-3 w-3 text-indigo-600" />
                    <span>🪄 灵感润色</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
