"use client";

import React, { useState } from 'react';
import { Wand2, Check, Sparkles } from 'lucide-react';
import { Perspective } from '@/types/session';
import { useStudioStore } from '@/stores/useStudioStore';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { studioApi } from '@/lib/api-client';

export const ScriptCardItem: React.FC<{ perspective: Perspective; index: number }> = ({
  perspective,
  index,
}) => {
  const { currentSession, updatePerspectivePrompt, setActivePerspectiveId } = useStudioStore();
  const [isRefining, setIsRefining] = useState(false);
  const [justRefined, setJustRefined] = useState(false);

  const promptText = perspective.prompt_zh || '';

  const handleBlur = (e: React.FocusEvent<HTMLTextAreaElement>) => {
    updatePerspectivePrompt(perspective.id, e.target.value);
  };

  const handleMagicRefine = async () => {
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
    } catch (e) {
      console.error('Magic refine error:', e);
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
      className={`group flex flex-col justify-between bg-zinc-900/60 backdrop-blur-md border rounded-xl p-4 shadow-xl transition-all duration-200 ${
        justRefined
          ? 'border-emerald-500/60 ring-1 ring-emerald-500/40 bg-zinc-900/80'
          : 'border-white/[0.08] hover:border-sky-500/40'
      }`}
    >
      <div className="space-y-2.5">
        {/* Card Header: Slot Badge & Name */}
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] font-bold text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">
                0{index + 1}
              </span>
              <h4 className="text-xs font-semibold text-zinc-100 truncate">
                {perspective.name}
              </h4>
            </div>
            <p className="text-[11px] text-zinc-400">{perspective.tag}</p>
          </div>

          <Badge variant="outline" className="text-[10px] shrink-0 text-zinc-400">
            {perspective.category}
          </Badge>
        </div>

        {/* Psychology Target Note */}
        <div className="text-[11px] text-zinc-400 bg-zinc-950/50 p-2 rounded-lg border border-white/5 leading-relaxed line-clamp-2">
          <span className="text-zinc-500 font-medium">转化目标: </span>
          {perspective.psychology_target}
        </div>

        {/* Editable Chinese Direction Textarea */}
        <div className="space-y-1">
          <label className="text-[10px] font-medium text-zinc-400 uppercase tracking-wider flex items-center justify-between">
            <span>镜头与布景指导 (可就地编辑)</span>
            <span className="text-zinc-500 font-mono">{promptText.length} 字</span>
          </label>
          <Textarea
            rows={5}
            defaultValue={promptText}
            key={promptText} // Re-render when refined
            onBlur={handleBlur}
            placeholder="正在推演商业摄影镜头语言与布景指导..."
            className="text-xs bg-zinc-950/70 border-white/10 resize-none leading-relaxed text-zinc-200 focus:border-sky-500/50"
          />
        </div>
      </div>

      {/* Card Footer: Magic Refiner Button */}
      <div className="pt-3 flex items-center justify-between border-t border-white/5 mt-3">
        <span className="text-[10px] text-zinc-500">失焦自动存盘</span>

        <Button
          variant="outline"
          size="xs"
          onClick={handleMagicRefine}
          disabled={isRefining}
          className="gap-1.5 text-[11px] text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/10 hover:border-indigo-500/50"
        >
          {isRefining ? (
            <>
              <Wand2 className="h-3 w-3 animate-spin text-indigo-400" />
              <span>润色中...</span>
            </>
          ) : justRefined ? (
            <>
              <Check className="h-3 w-3 text-emerald-400" />
              <span>已优化</span>
            </>
          ) : (
            <>
              <Sparkles className="h-3 w-3 text-indigo-400" />
              <span>🪄 灵感润色</span>
            </>
          )}
        </Button>
      </div>
    </div>
  );
};
