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
      <DialogContent className="max-w-5xl w-[95vw] bg-white border border-slate-200 text-slate-900 p-6 shadow-popover">
        <DialogHeader className="flex flex-row items-center justify-between pb-3 border-b border-slate-200">
          <div>
            <DialogTitle className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Columns className="h-4 w-4 text-blue-600" />
              <span>商业大片双版本对决对比 ({perspective.name})</span>
            </DialogTitle>
          </div>

          {/* Mode Switcher */}
          <div className="flex items-center gap-2 pr-8">
            <div className="inline-flex rounded-lg bg-slate-100 p-0.5 border border-slate-200 text-xs">
              <button
                type="button"
                onClick={() => setMode('sideBySide')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-md transition-all ${
                  mode === 'sideBySide'
                    ? 'bg-white text-blue-700 shadow-xs font-medium'
                    : 'text-slate-600 hover:text-slate-900'
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
                    ? 'bg-white text-blue-700 shadow-xs font-medium'
                    : 'text-slate-600 hover:text-slate-900'
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
              <Badge variant="outline" className="text-blue-700 border-blue-200 bg-blue-50">
                版本 A
              </Badge>
              <select
                value={versionA.version_id}
                onChange={(e) => setVersionAId(e.target.value)}
                className="bg-white border border-slate-200 rounded-md text-xs px-2 py-1 text-slate-800 outline-none focus:border-blue-500"
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
              className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              采用 A 版本
            </Button>
          </div>

          {/* Version B Select */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-indigo-700 border-indigo-200 bg-indigo-50">
                版本 B
              </Badge>
              <select
                value={versionB.version_id}
                onChange={(e) => setVersionBId(e.target.value)}
                className="bg-white border border-slate-200 rounded-md text-xs px-2 py-1 text-slate-800 outline-none focus:border-blue-500"
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
              className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
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
                <div className="aspect-square w-full rounded-xl overflow-hidden bg-white border border-slate-200 studio-stage-matte relative">
                  {versionA.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={formatAssetUrl(versionA.image_url)}
                      alt="Version A"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
                      无图像
                    </div>
                  )}
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-700 max-h-24 overflow-y-auto leading-relaxed">
                  <span className="text-slate-500 font-medium">布景指导: </span>
                  {versionA.prompt_zh}
                </div>
              </div>

              {/* Image B */}
              <div className="flex flex-col gap-2">
                <div className="aspect-square w-full rounded-xl overflow-hidden bg-white border border-slate-200 studio-stage-matte relative">
                  {versionB.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={formatAssetUrl(versionB.image_url)}
                      alt="Version B"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-xs text-slate-400">
                      无图像
                    </div>
                  )}
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-[11px] text-slate-700 max-h-24 overflow-y-auto leading-relaxed">
                  <span className="text-slate-500 font-medium">布景指导: </span>
                  {versionB.prompt_zh}
                </div>
              </div>
            </div>
          ) : (
            /* Curtain Splitter Mode */
            <div className="relative aspect-square max-h-[500px] mx-auto rounded-xl overflow-hidden border border-slate-200 studio-stage-matte select-none">
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
                className="absolute top-0 bottom-0 w-0.5 bg-blue-600 shadow-md z-10 cursor-ew-resize flex items-center justify-center"
                style={{ left: `${sliderPos}%` }}
              >
                <div className="h-8 w-5 rounded-full bg-white border border-slate-300 text-slate-700 flex items-center justify-center text-[10px] font-bold shadow-md">
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

              <div className="absolute bottom-3 left-3 bg-white/90 backdrop-blur-md px-2.5 py-1 rounded text-[11px] text-slate-800 shadow-xs border border-slate-200 z-10">
                左侧: {versionA.version_id}
              </div>
              <div className="absolute bottom-3 right-3 bg-white/90 backdrop-blur-md px-2.5 py-1 rounded text-[11px] text-slate-800 shadow-xs border border-slate-200 z-10">
                右侧: {versionB.version_id}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};
