"use client";

import React, { useRef, useState } from 'react';
import { UploadCloud, Trash2, ShieldCheck } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { studioApi } from '@/lib/api-client';

export const AssetUploadDropzone: React.FC = () => {
  const { currentSession, updateProductInfo } = useStudioStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const referenceImages = currentSession?.product_info?.reference_images || [];

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0 || !currentSession?.session_id) return;

    setIsUploading(true);
    const newAssets = [...referenceImages];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        const res = await studioApi.uploadAsset(
          currentSession.session_id,
          file,
          newAssets.length === 0
        );

        newAssets.push({
          id: res.id || `asset_${Date.now()}_${i}`,
          url: res.url,
          is_primary: newAssets.length === 0,
          vision_tags: res.vision_tags || ['#商业实物', '#材质基准'],
        });
      } catch (e) {
        console.error('Asset upload error:', e);
        // Fallback for local mock preview if API is warming up
        const localUrl = URL.createObjectURL(file);
        newAssets.push({
          id: `local_${Date.now()}_${i}`,
          url: localUrl,
          is_primary: newAssets.length === 0,
          vision_tags: ['#实物参考', '#几何基准', '#光影反光'],
        });
      }
    }

    updateProductInfo({ reference_images: newAssets });
    setIsUploading(false);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleDeleteAsset = (id: string) => {
    const updated = referenceImages.filter((img) => img.id !== id);
    if (updated.length > 0 && !updated.some((img) => img.is_primary)) {
      updated[0].is_primary = true;
    }
    updateProductInfo({ reference_images: updated });
  };

  const handleSetPrimary = (id: string) => {
    const updated = referenceImages.map((img) => ({
      ...img,
      is_primary: img.id === id,
    }));
    updateProductInfo({ reference_images: updated });
  };

  return (
    <div className="space-y-4 bg-zinc-900/60 backdrop-blur-md border border-white/[0.08] rounded-2xl p-6 shadow-2xl h-full flex flex-col justify-between">
      <div className="space-y-3">
        <div>
          <h3 className="text-base font-semibold text-zinc-100 flex items-center gap-2">
            <UploadCloud className="h-4 w-4 text-sky-400" />
            实物参考资产网格 (Physical Ingestion)
          </h3>
          <p className="text-xs text-zinc-400 mt-0.5">
            拖拽上传高清实物多机位照片，AI 将精准锁定外形几何特征与材质反光，避免出图变形失真。
          </p>
        </div>

        {/* Dropzone Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
            dragActive
              ? 'border-sky-400 bg-sky-500/10'
              : 'border-white/10 hover:border-sky-500/40 hover:bg-white/[0.02] bg-zinc-950/40'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept="image/*"
            className="hidden"
            onChange={(e) => handleFiles(e.target.files)}
          />

          <div className="flex flex-col items-center justify-center gap-2 text-zinc-400">
            <div className="h-10 w-10 rounded-full bg-zinc-800/80 flex items-center justify-center text-zinc-300">
              <UploadCloud className="h-5 w-5 text-sky-400" />
            </div>
            <div>
              <p className="text-xs font-medium text-zinc-200">
                {isUploading ? '正在上传并多模态解析中...' : '拖拽实物照片到此处，或点击浏览上传'}
              </p>
              <p className="text-[11px] text-zinc-500 mt-0.5">
                支持 JPG / PNG / WebP，可上传 1-5 张多角度细节图
              </p>
            </div>
          </div>
        </div>

        {/* Uploaded Reference Assets List */}
        {referenceImages.length > 0 && (
          <div className="space-y-2 pt-2">
            <p className="text-[11px] font-semibold text-zinc-400 uppercase tracking-wider">
              已就绪实物资产 ({referenceImages.length})
            </p>

            <div className="grid grid-cols-1 gap-2 max-h-[220px] overflow-y-auto pr-1">
              {referenceImages.map((asset) => (
                <div
                  key={asset.id}
                  className="flex items-center gap-3 p-2 rounded-lg bg-zinc-950/60 border border-white/5 hover:border-white/15 transition-all group"
                >
                  <div className="h-12 w-12 rounded-md overflow-hidden bg-zinc-800 shrink-0 border border-white/10 relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={asset.url}
                      alt="Ref Asset"
                      className="h-full w-full object-cover"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-medium text-zinc-200 truncate">
                        {asset.is_primary ? '主视觉基准参考' : '结构细节参考'}
                      </span>
                      {asset.is_primary && (
                        <Badge variant="success" className="text-[10px] py-0 px-1.5 h-4">
                          核心基准
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-1 flex-wrap mt-1">
                      {asset.vision_tags?.map((t, idx) => (
                        <span key={idx} className="text-[10px] text-zinc-500">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    {!asset.is_primary && (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSetPrimary(asset.id);
                        }}
                        className="text-[10px] text-zinc-400 hover:text-sky-300"
                      >
                        设为主基准
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteAsset(asset.id);
                      }}
                      className="h-7 w-7 text-zinc-500 hover:text-rose-400"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Safety & Grounding Tip Box */}
      <div className="mt-4 p-3 rounded-xl bg-zinc-950/40 border border-white/5 flex items-start gap-2.5 text-zinc-400 text-xs leading-relaxed">
        <ShieldCheck className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-medium text-zinc-300">工业级保真锁模机制: </span>
          基于实物参考图提取几何轮廓与反射率参数，出图时杜绝虚构未经验证的按钮、接口或违规宣传，商业落地安全合规。
        </div>
      </div>
    </div>
  );
};
