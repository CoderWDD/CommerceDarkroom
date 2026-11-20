"use client";

import React from 'react';
import { RotateCcw, Columns, Download, CheckCircle2 } from 'lucide-react';
import { PerspectiveVersion } from '@/types/session';
import { Button } from '@/components/ui/button';

export interface VersionFilmstripProps {
  perspectiveId: string;
  versions: PerspectiveVersion[];
  activeVersionId: string | null;
  selectedVersionId: string;
  onSelectVersion: (versionId: string) => void;
  onRollback: (versionId: string) => void;
  onOpenDiff: () => void;
  currentImageUrl?: string | null;
}

export const VersionFilmstrip: React.FC<VersionFilmstripProps> = ({
  perspectiveId,
  versions,
  activeVersionId,
  selectedVersionId,
  onSelectVersion,
  onRollback,
  onOpenDiff,
  currentImageUrl,
}) => {
  // If no versions exist yet, show subtle empty indicator
  if (!versions || versions.length === 0) {
    return (
      <div className="py-1 px-2 rounded bg-zinc-950/40 border border-white/5 text-[11px] text-zinc-500 text-center">
        暂无版本快照，点击下方微调或一键出图生成
      </div>
    );
  }

  const isViewingHistory = activeVersionId && String(selectedVersionId) !== String(activeVersionId);

  const handleDownload = () => {
    if (!currentImageUrl) return;
    const link = document.createElement('a');
    link.href = currentImageUrl;
    link.download = `${perspectiveId}_${selectedVersionId}.jpg`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-2 pt-1 border-t border-white/5">
      {/* Horizontal Capsules Strip */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        <span className="text-[10px] text-zinc-500 font-medium shrink-0">
          胶卷:
        </span>
        {versions.map((ver) => {
          const isActive = String(ver.version_id) === String(activeVersionId) || String(ver.version_num) === String(activeVersionId);
          const isSelected = String(ver.version_id) === String(selectedVersionId) || String(ver.version_num) === String(selectedVersionId);
          const label = ver.version_id.startsWith('v') ? ver.version_id : `v${ver.version_id}`;
          const reason = ver.change_reason ? `: ${ver.change_reason.substring(0, 6)}` : '';

          return (
            <button
              key={ver.version_id}
              type="button"
              onClick={() => onSelectVersion(ver.version_id)}
              className={`flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono shrink-0 transition-all ${
                isSelected
                  ? 'bg-sky-500/20 border border-sky-400 text-sky-300 font-semibold shadow-sm'
                  : 'bg-zinc-950/60 border border-white/10 text-zinc-400 hover:text-zinc-200 hover:border-white/20'
              }`}
            >
              {isActive && (
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shrink-0" title="当前定稿版本" />
              )}
              <span>
                {label}
                {reason}
              </span>
            </button>
          );
        })}
      </div>

      {/* Action Row: Rollback, Diff, Download */}
      <div className="flex items-center justify-between gap-1 pt-1">
        {isViewingHistory ? (
          <Button
            variant="default"
            size="xs"
            onClick={() => onRollback(selectedVersionId)}
            className="gap-1 text-[11px] bg-emerald-600 hover:bg-emerald-500 text-white font-medium shadow-sm transition-all"
          >
            <RotateCcw className="h-3 w-3" />
            <span>⏪ 回滚为此版本</span>
          </Button>
        ) : (
          <div className="flex items-center gap-1 text-[11px] text-zinc-500 px-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
            <span>已是现用版本</span>
          </div>
        )}

        <div className="flex items-center gap-1">
          {versions.length >= 2 && (
            <Button
              variant="outline"
              size="xs"
              onClick={onOpenDiff}
              className="text-[11px] gap-1 text-zinc-400 hover:text-zinc-200 h-6 px-1.5"
              title="双版本对比"
            >
              <Columns className="h-3 w-3" />
              <span>对比</span>
            </Button>
          )}

          {currentImageUrl && (
            <Button
              variant="ghost"
              size="xs"
              onClick={handleDownload}
              className="text-[11px] gap-1 text-zinc-400 hover:text-zinc-200 h-6 px-1.5"
              title="下载原图"
            >
              <Download className="h-3 w-3" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
