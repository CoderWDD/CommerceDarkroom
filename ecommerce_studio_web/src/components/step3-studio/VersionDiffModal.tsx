"use client";

import React, { useState } from 'react';
import { Columns, SplitSquareVertical, RotateCcw } from 'lucide-react';
import { Perspective } from '@/types/session';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { formatAssetUrl } from '@/lib/constants';

interface VersionDiffModalProps {
  isOpen: boolean;
  onClose: () => void;
  perspective: Perspective | null;
  onRollback: (versionId: string) => Promise<void>;
}

export const VersionDiffModal: React.FC<VersionDiffModalProps> = ({
  isOpen,
  onClose,
  perspective,
  onRollback,
}) => {
  const [mode, setMode] = useState<'sideBySide' | 'curtain'>('sideBySide');
  const [versionAId, setVersionAId] = useState<string>('');
  const [versionBId, setVersionBId] = useState<string>('');
  const [sliderPos, setSliderPos] = useState<number>(50); // 0% - 100% for curtain mode

  if (!perspective || !perspective.versions || perspective.versions.length < 2) {
    return null;
  }

  const versions = perspective.versions;
  const currentVAId = versionAId || versions[0].version_id;
  const currentVBId = versionBId || versions[versions.length - 1].version_id;

  const versionA = versions.find((v) => v.version_id === currentVAId) || versions[0];
  const versionB = versions.find((v) => v.version_id === currentVBId) || versions[versions.length - 1];

  const handleApplyA = async () => {
    await onRollback(versionA.version_id);
    onClose();
  };

  const handleApplyB = async () => {
    await onRollback(versionB.version_id);
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl w-[95vw] bg-zinc-950/95 border-white/10 p-6">
        <DialogHeader className="flex flex-row items-center justify-between pb-3 border-b border-white/10">
          <div>
            <DialogTitle className="text-base font-semibold text-zinc-100 flex items-center gap-2">
              <Columns className="h-4 w-4 text-sky-400" />
              <span>商业大片双版本对决对比 ({perspective.name})</span>
            </DialogTitle>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-2 pr-8">
            <div className="inline-flex rounded-lg bg-zinc-900 p-0.5 border border-white/10 text-xs">
              <button
                type="button"
                onClick={() => setMode('sideBySide')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                  mode === 'sideBySide'
                    ? 'bg-zinc-800 text-sky-400 font-medium'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <Columns className="h-3.5 w-3.5" />
                <span>左右分屏</span>
              </button>
              <button
                type="button"
                onClick={() => setMode('curtain')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                  mode === 'curtain'
                    ? 'bg-zinc-800 text-sky-400 font-medium'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                <SplitSquareVertical className="h-3.5 w-3.5" />
                <span>卷帘对比</span>
              </button>
            </div>
          </div>
        </DialogHeader>

        {/* Version Pickers Header */}
        <div className="grid grid-cols-2 gap-6 pt-2">
          {/* Version A Select */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-sky-400 border-sky-500/30">
                版本 A
              </Badge>
              <select
                value={versionA.version_id}
                onChange={(e) => setVersionAId(e.target.value)}
                className="bg-zinc-900 border border-white/10 rounded-md text-xs px-2 py-1 text-zinc-200 outline-none"
              >
                {versions.map((v) => (
                  <option key={v.version_id} value={v.version_id}>
                    {v.version_id}: {v.change_reason || '初始渲染'}
                  </option>
                ))}
              </select>
            </div>
            <Button
              variant="default"
              size="xs"
              onClick={handleApplyA}
              className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              采用 A 版本
            </Button>
          </div>

          {/* Version B Select */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-indigo-400 border-indigo-500/30">
                版本 B
              </Badge>
              <select
                value={versionB.version_id}
                onChange={(e) => setVersionBId(e.target.value)}
                className="bg-zinc-900 border border-white/10 rounded-md text-xs px-2 py-1 text-zinc-200 outline-none"
              >
                {versions.map((v) => (
                  <option key={v.version_id} value={v.version_id}>
                    {v.version_id}: {v.change_reason || '微调渲染'}
                  </option>
                ))}
              </select>
            </div>
            <Button
              variant="default"
              size="xs"
              onClick={handleApplyB}
              className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              采用 B 版本
            </Button>
          </div>
        </div>

        {/* Visual Display Comparison Area */}
        <div className="pt-2">
          {mode === 'sideBySide' ? (
            <div className="grid grid-cols-2 gap-6 items-stretch">
              {/* Image A */}
              <div className="flex flex-col gap-2">
                <div className="aspect-square w-full rounded-xl overflow-hidden bg-zinc-900 border border-white/10 relative">
                  {versionA.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={formatAssetUrl(versionA.image_url)}
                      alt="Version A"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-zinc-500">
                      无图像
                    </div>
                  )}
                </div>
                <div className="p-2.5 rounded-lg bg-zinc-900/60 border border-white/5 text-[11px] text-zinc-300 max-h-24 overflow-y-auto leading-relaxed">
                  <span className="text-zinc-500 font-medium">布景指导: </span>
                  {versionA.prompt_zh}
                </div>
              </div>

              {/* Image B */}
              <div className="flex flex-col gap-2">
                <div className="aspect-square w-full rounded-xl overflow-hidden bg-zinc-900 border border-white/10 relative">
                  {versionB.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={formatAssetUrl(versionB.image_url)}
                      alt="Version B"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-zinc-500">
                      无图像
                    </div>
                  )}
                </div>
                <div className="p-2.5 rounded-lg bg-zinc-900/60 border border-white/5 text-[11px] text-zinc-300 max-h-24 overflow-y-auto leading-relaxed">
                  <span className="text-zinc-500 font-medium">布景指导: </span>
                  {versionB.prompt_zh}
                </div>
              </div>
            </div>
          ) : (
            /* Curtain Splitter Mode */
            <div className="relative aspect-square max-h-[500px] mx-auto rounded-xl overflow-hidden border border-white/15 select-none">
              {/* Background: Version A */}
              {versionA.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={formatAssetUrl(versionA.image_url)}
                  alt="Version A"
                  className="absolute inset-0 w-full h-full object-cover"
                />
              )}

              {/* Foreground: Version B with clip-path */}
              {versionB.image_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={formatAssetUrl(versionB.image_url)}
                  alt="Version B"
                  className="absolute inset-0 w-full h-full object-cover"
                  style={{
                    clipPath: `inset(0 0 0 ${sliderPos}%)`,
                  }}
                />
              )}

              {/* Draggable Divider Line */}
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(255,255,255,0.8)] z-10 cursor-ew-resize flex items-center justify-center"
                style={{ left: `${sliderPos}%` }}
              >
                <div className="h-8 w-5 rounded-full bg-white text-zinc-950 flex items-center justify-center text-[10px] font-bold shadow-md">
                  ↔
                </div>
              </div>

              {/* Invisible touch/mouse slider input */}
              <input
                type="range"
                min="0"
                max="100"
                value={sliderPos}
                onChange={(e) => setSliderPos(Number(e.target.value))}
                className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-20"
              />

              <div className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[11px] text-white z-10">
                左侧: {versionA.version_id}
              </div>
              <div className="absolute bottom-3 right-3 bg-black/60 backdrop-blur-md px-2 py-1 rounded text-[11px] text-white z-10">
                右侧: {versionB.version_id}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
