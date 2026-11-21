"use client";

import React, { useState } from 'react';
import {
  ZoomIn,
  Camera,
  Wand2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  AlertCircle,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { Perspective } from '@/types/session';
import { useStudioStore } from '@/stores/useStudioStore';
import { VersionFilmstrip } from './VersionFilmstrip';
import { VersionDiffModal } from './VersionDiffModal';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { studioApi } from '@/lib/api-client';
import { Dialog, DialogContent } from '@/components/ui/dialog';

interface StudioPerspectiveCardProps {
  perspective: Perspective;
  aspectRatio: '1:1' | '3:4' | '16:9';
  index: number;
}

export const StudioPerspectiveCard: React.FC<StudioPerspectiveCardProps> = ({
  perspective,
  aspectRatio,
  index,
}) => {
  const {
    currentSession,
    selectedPreviewVersions,
    selectPreviewVersion,
    rollbackVersion,
    addNewVersionSnapshot,
    setSingleCardStatus,
    setActivePerspectiveId,
  } = useStudioStore();

  const [isRefineOpen, setIsRefineOpen] = useState(false);
  const [refineInstruction, setRefineInstruction] = useState('');
  const [isRefiningSlot, setIsRefiningSlot] = useState(false);
  const [isDiffOpen, setIsDiffOpen] = useState(false);
  const [isLightboxOpen, setIsLightboxOpen] = useState(false);

  // Active version vs selected preview version
  const activeVersionId = perspective.active_version_id;
  const selectedVersionId =
    selectedPreviewVersions[perspective.id] ||
    activeVersionId ||
    (perspective.versions.length > 0 ? perspective.versions[perspective.versions.length - 1].version_id : 'v1');

  const selectedVersion =
    perspective.versions.find(
      (v) => String(v.version_id) === String(selectedVersionId) || String(v.version_num) === String(selectedVersionId)
    ) ||
    perspective.versions.find(
      (v) => String(v.version_id) === String(activeVersionId) || String(v.version_num) === String(activeVersionId)
    );

  const displayImageUrl = selectedVersion?.image_url || perspective.image_url;
  const isRendering = perspective.render_status === 'rendering';
  const isError = perspective.render_status === 'error';

  const aspectRatioClass = {
    '1:1': 'aspect-square',
    '3:4': 'aspect-[3/4]',
    '16:9': 'aspect-video',
  }[aspectRatio];

  const handleRenderNewVersion = async () => {
    if (!currentSession?.session_id) return;
    setIsRefiningSlot(true);
    setSingleCardStatus(perspective.id, 'rendering', 30);

    const changeReason = refineInstruction.trim() || '二次商业布景微调渲染';

    try {
      const newVersion = await studioApi.renderSlot({
        session_id: currentSession.session_id,
        perspective_id: perspective.id,
        prompt_zh: perspective.prompt_zh,
        instruction: refineInstruction.trim() || undefined,
        change_reason: changeReason,
        trigger_type: 'manual_edit',
        aspect_ratio: aspectRatio,
      });

      if (newVersion) {
        addNewVersionSnapshot(perspective.id, newVersion);
        setRefineInstruction('');
        setIsRefineOpen(false);
      }
    } catch (e: unknown) {
      console.error('Slot rendering error:', e);
      const errMsg = e instanceof Error ? e.message : '渲染失败';
      setSingleCardStatus(perspective.id, 'error', 0, errMsg);
    } finally {
      setIsRefiningSlot(false);
    }
  };

  return (
    <>
      <div
        onClick={() => setActivePerspectiveId(perspective.id)}
        className="flex flex-col justify-between bg-zinc-900/60 backdrop-blur-md border border-white/[0.08] hover:border-sky-500/40 rounded-xl p-3.5 shadow-xl transition-all duration-200 group"
      >
        {/* Card Header: Slot No, Name, Status */}
        <div className="flex items-center justify-between pb-2">
          <div className="flex items-center gap-1.5 truncate pr-2">
            <span className="font-mono text-[10px] font-bold text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded border border-sky-500/20">
              0{index + 1}
            </span>
            <span className="text-xs font-semibold text-zinc-200 truncate">
              {perspective.name}
            </span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {isRendering ? (
              <Badge variant="warning" className="text-[10px] py-0 px-1.5 gap-1 animate-pulse">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                置景布光中
              </Badge>
            ) : isError ? (
              <Badge
                variant="destructive"
                className="text-[10px] py-0 px-1.5 gap-1 bg-rose-500/10 text-rose-400 border border-rose-500/20"
                title={perspective.error_message}
              >
                <AlertCircle className="h-3 w-3 text-rose-400" />
                出图失败
              </Badge>
            ) : displayImageUrl ? (
              <Badge variant="success" className="text-[10px] py-0 px-1.5 gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                就绪
              </Badge>
            ) : (
              <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-zinc-500">
                待拍摄
              </Badge>
            )}
          </div>
        </div>

        {/* Image Canvas Container */}
        <div
          className={`relative w-full ${aspectRatioClass} rounded-lg overflow-hidden bg-zinc-950 border border-white/5 flex items-center justify-center`}
        >
          {isRendering ? (
            /* Shimmer Skeleton */
            <div className="absolute inset-0 bg-gradient-to-r from-zinc-900 via-zinc-800 to-zinc-900 bg-[length:200%_100%] animate-shimmer flex flex-col items-center justify-center gap-2 text-zinc-400">
              <Camera className="h-7 w-7 text-sky-400/80 animate-pulse" />
              <span className="text-[11px] font-mono text-zinc-300">
                正在渲染商业大片...
              </span>
            </div>
          ) : isError ? (
            /* Error Fallback with Retry */
            <div className="absolute inset-0 bg-rose-950/20 border border-rose-500/20 p-3 flex flex-col items-center justify-center gap-1.5 text-center">
              <AlertTriangle className="h-6 w-6 text-rose-400" />
              <span className="text-xs font-semibold text-rose-300">生图失败 / 接口异常</span>
              <p className="text-[10px] text-zinc-400 line-clamp-2 px-2" title={perspective.error_message}>
                {perspective.error_message || '当前中继代理端点未开通生图接口或连接超时'}
              </p>
              <Button
                variant="outline"
                size="xs"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRenderNewVersion();
                }}
                disabled={isRefiningSlot}
                className="mt-1 h-6 text-[10px] gap-1 border-rose-500/40 text-rose-300 hover:bg-rose-500/10 hover:text-rose-200"
              >
                <RefreshCw className={`h-3 w-3 ${isRefiningSlot ? 'animate-spin' : ''}`} />
                <span>重试此机位</span>
              </Button>
            </div>
          ) : displayImageUrl ? (
            /* Image Preview */
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={displayImageUrl}
                alt={perspective.name}
                className="w-full h-full object-cover transition-opacity duration-300"
              />

              {/* Hover Overlay with Lightbox Trigger */}
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                <Button
                  variant="studio"
                  size="xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    setIsLightboxOpen(true);
                  }}
                  className="gap-1 text-xs text-white bg-black/60 backdrop-blur-md hover:bg-black/80"
                >
                  <ZoomIn className="h-3.5 w-3.5" />
                  <span>全屏查看</span>
                </Button>
              </div>
            </>
          ) : (
            /* Empty State Wireframe Placeholder */
            <div className="flex flex-col items-center justify-center gap-1.5 text-zinc-600 p-4 text-center">
              <Camera className="h-8 w-8 text-zinc-700" />
              <span className="text-[11px] text-zinc-500">商业暗房机位已锁定</span>
              <span className="text-[10px] text-zinc-600 line-clamp-1">
                {perspective.tag}
              </span>
            </div>
          )}
        </div>

        {/* Version Filmstrip Control */}
        <div className="pt-2">
          <VersionFilmstrip
            perspectiveId={perspective.id}
            versions={perspective.versions}
            activeVersionId={activeVersionId}
            selectedVersionId={selectedVersionId}
            onSelectVersion={(vId) => selectPreviewVersion(perspective.id, vId)}
            onRollback={(vId) => rollbackVersion(perspective.id, vId)}
            onOpenDiff={() => setIsDiffOpen(true)}
            currentImageUrl={displayImageUrl}
          />
        </div>

        {/* Collapsible Refine Panel */}
        <div className="pt-2 border-t border-white/5 mt-2">
          <button
            type="button"
            onClick={() => setIsRefineOpen(!isRefineOpen)}
            className="flex items-center justify-between w-full text-[11px] text-zinc-400 hover:text-zinc-200 transition-colors py-0.5"
          >
            <span className="flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-sky-400" />
              <span>摄影布景二次微调</span>
            </span>
            {isRefineOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>

          {isRefineOpen && (
            <div className="mt-2 space-y-2 pt-1 border-t border-white/5">
              <Input
                value={refineInstruction}
                onChange={(e) => setRefineInstruction(e.target.value)}
                placeholder="输入微调要求（如：增强杯口金属光泽与倒影）"
                className="text-xs h-7 bg-zinc-950/70 border-white/10"
                onKeyDown={(e) => e.key === 'Enter' && handleRenderNewVersion()}
              />

              <Button
                variant="studio-accent"
                size="xs"
                onClick={handleRenderNewVersion}
                disabled={isRefiningSlot}
                className="w-full text-xs h-7 gap-1"
              >
                {isRefiningSlot ? (
                  <>
                    <Wand2 className="h-3 w-3 animate-spin" />
                    <span>正在拍摄新版本...</span>
                  </>
                ) : (
                  <>
                    <Wand2 className="h-3 w-3" />
                    <span>🪄 渲染新版本快照 (生成 v{perspective.versions.length + 1})</span>
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Version Diff Modal */}
      <VersionDiffModal
        isOpen={isDiffOpen}
        onClose={() => setIsDiffOpen(false)}
        perspective={perspective}
        onRollback={(vId) => rollbackVersion(perspective.id, vId)}
      />

      {/* Lightbox Modal */}
      <Dialog open={isLightboxOpen} onOpenChange={setIsLightboxOpen}>
        <DialogContent className="max-w-4xl bg-black/95 border-white/10 p-2 flex flex-col items-center justify-center">
          {displayImageUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={displayImageUrl}
              alt={perspective.name}
              className="max-h-[80vh] w-auto object-contain rounded-lg shadow-2xl"
            />
          )}
          <div className="w-full px-4 py-2 flex items-center justify-between text-xs text-zinc-300">
            <span className="font-semibold text-zinc-100">{perspective.name}</span>
            <span className="font-mono text-zinc-400">版本: {selectedVersionId}</span>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};
