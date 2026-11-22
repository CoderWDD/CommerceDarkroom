"use client";

import React, { useState } from 'react';
import { ZoomIn, Camera } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { formatAssetUrl } from '@/lib/constants';

export const MasterAssetGrid: React.FC = () => {
  const { currentSession, selectedPreviewVersions } = useStudioStore();
  const perspectives = currentSession?.perspectives || [];
  const [activeZoomUrl, setActiveZoomUrl] = useState<{ url: string; name: string } | null>(null);

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {perspectives.map((p, index) => {
          const selectedVersionId =
            selectedPreviewVersions[p.id] ||
            p.active_version_id ||
            (p.versions.length > 0 ? p.versions[p.versions.length - 1].version_id : 'v1');

          const activeVersion =
            p.versions.find((v) => String(v.version_id) === String(selectedVersionId)) ||
            p.versions.find((v) => String(v.version_id) === String(p.active_version_id));

          const imageUrl = formatAssetUrl(activeVersion?.image_url || p.image_url);

          return (
            <div
              key={p.id}
              className="group flex flex-col justify-between bg-white border border-slate-200 rounded-xl p-3.5 shadow-card hover:shadow-card-hover hover:border-blue-400 transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between pb-2">
                <div className="flex items-center gap-1.5 truncate">
                  <span className="font-mono text-[10px] font-bold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                    0{index + 1}
                  </span>
                  <span className="text-xs font-semibold text-slate-800 truncate">
                    {p.name}
                  </span>
                </div>
                <Badge variant="success" className="text-[10px] py-0 px-1.5 font-mono">
                  {selectedVersionId} 定稿
                </Badge>
              </div>

              {/* Image Preview Container (Pure White Stage) */}
              <div className="relative aspect-square w-full rounded-lg overflow-hidden bg-white border border-slate-200 studio-stage-matte flex items-center justify-center">
                {imageUrl ? (
                  <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={imageUrl}
                      alt={p.name}
                      className="w-full h-full object-cover select-none"
                    />
                    <div className="absolute inset-0 bg-slate-900/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      <Button
                        variant="studio"
                        size="xs"
                        onClick={() => setActiveZoomUrl({ url: imageUrl, name: p.name })}
                        className="text-xs bg-white/90 backdrop-blur-md text-slate-900 border-white/80 hover:bg-white shadow-sm"
                      >
                        <ZoomIn className="h-3.5 w-3.5 mr-1" />
                        高清放大
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center text-slate-400 gap-1">
                    <Camera className="h-6 w-6 text-slate-300" />
                    <span className="text-[11px] font-medium text-slate-500">未完成出图</span>
                  </div>
                )}
              </div>

              {/* Caption */}
              <div className="pt-2 text-[11px] text-slate-500 line-clamp-1 font-medium">
                {p.tag} · {p.psychology_target}
              </div>
            </div>
          );
        })}
      </div>

      {/* Lightbox Dialog */}
      <Dialog open={!!activeZoomUrl} onOpenChange={() => setActiveZoomUrl(null)}>
        <DialogContent className="max-w-4xl bg-white border-slate-200 p-2 flex flex-col items-center justify-center text-slate-900 shadow-popover">
          {activeZoomUrl && (
            <>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={activeZoomUrl.url}
                alt={activeZoomUrl.name}
                className="max-h-[80vh] w-auto object-contain rounded-lg shadow-md"
              />
              <div className="w-full px-4 py-2 text-xs text-slate-800 font-semibold">
                {activeZoomUrl.name}
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
};
