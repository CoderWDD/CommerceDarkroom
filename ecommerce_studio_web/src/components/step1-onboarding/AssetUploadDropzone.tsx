"use client";

import React, { useEffect, useRef, useState } from 'react';
import {
  UploadCloud,
  Trash2,
  ShieldCheck,
  Scan,
  Sparkles,
  Clipboard,
  CheckCircle2,
  Cpu,
  Layers,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

const TICKER_STEPS = [
  '阶段 1/4: 正在上传随手拍原始物理图像...',
  '阶段 2/4: 多模态视觉模型逆向审视中...',
  '阶段 3/4: 萃取微米级材质特征与工业倒角...',
  '阶段 4/4: 提炼客群决策痛点与色彩调色板...',
];

export const AssetUploadDropzone: React.FC = () => {
  const {
    currentSession,
    updateProductInfo,
    isExtractingDossier,
    extractionProgressText,
    extractDossierFromPhoto,
    extractDossierFromExistingAsset,
  } = useStudioStore();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const dropzoneRef = useRef<HTMLDivElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [tickerIndex, setTickerIndex] = useState(0);

  const referenceImages = currentSession?.product_info?.reference_images || [];

  // Micro-copy step ticker rotation during extraction
  useEffect(() => {
    if (!isExtractingDossier) {
      setTickerIndex(0);
      return;
    }
    const interval = setInterval(() => {
      setTickerIndex((prev) => (prev + 1) % TICKER_STEPS.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [isExtractingDossier]);

  // Global & Container Paste Listener (Ctrl+V / Cmd+V)
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;

      for (let i = 0; i < items.length; i++) {
        if (items[i].type.indexOf('image') !== -1) {
          const file = items[i].getAsFile();
          if (file) {
            e.preventDefault();
            extractDossierFromPhoto(file);
            break;
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [extractDossierFromPhoto]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    try {
      await extractDossierFromPhoto(file);
    } catch (e) {
      console.error('Extraction error:', e);
    }
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
    <div
      ref={dropzoneRef}
      className="space-y-4 bg-white border border-slate-200 rounded-2xl p-6 shadow-card h-full flex flex-col justify-between"
    >
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Scan className="h-4 w-4 text-blue-600" />
              随手拍多模态逆向建档 (Vision-to-Dossier)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              拖拽、上传或直接剪贴板粘贴（Ctrl+V）实物随手拍，自动逆向萃取商业档案。
            </p>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
            <Clipboard className="h-3 w-3 text-blue-600" />
            <span>支持 Ctrl+V 粘贴</span>
          </div>
        </div>

        {/* Laser Radar Scanning Dropzone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !isExtractingDossier && fileInputRef.current?.click()}
          className={`relative overflow-hidden border-2 border-dashed rounded-xl p-6 text-center transition-all min-h-[170px] flex flex-col items-center justify-center ${
            isExtractingDossier
              ? 'border-blue-500 bg-blue-50/40 shadow-sm cursor-wait'
              : dragActive
              ? 'border-blue-500 bg-blue-50/60 cursor-copy'
              : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50/80 bg-slate-50/40 cursor-pointer'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            disabled={isExtractingDossier}
            onChange={(e) => handleFiles(e.target.files)}
          />

          {/* Laser Radar Scanning Animation Overlay */}
          {isExtractingDossier && (
            <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
              {/* Radar Grid Texture */}
              <div
                className="absolute inset-0 opacity-15"
                style={{
                  backgroundImage:
                    'linear-gradient(rgba(37, 99, 235, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 99, 235, 0.4) 1px, transparent 1px)',
                  backgroundSize: '24px 24px',
                }}
              />

              {/* Laser Scanning Beam Traversing Up and Down */}
              <div
                className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent shadow-[0_0_12px_#3b82f6]"
                style={{
                  animation: 'laserScan 2.4s ease-in-out infinite alternate',
                }}
              />

              {/* Radial Center Pulse */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-32 w-32 rounded-full border border-blue-500/20 animate-ping opacity-25" />
              </div>
            </div>
          )}

          {/* Content Area */}
          <div className="relative z-20 flex flex-col items-center justify-center gap-2.5 text-slate-500">
            {isExtractingDossier ? (
              <div className="space-y-3 flex flex-col items-center">
                <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 shadow-sm animate-pulse">
                  <Cpu className="h-6 w-6 animate-spin text-blue-600" style={{ animationDuration: '4s' }} />
                </div>

                <div className="space-y-1 text-center">
                  <p className="text-xs font-bold text-blue-700 tracking-wide flex items-center justify-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 animate-bounce" />
                    <span>多模态视觉大脑正在深度解析...</span>
                  </p>
                  <p className="text-[11px] text-slate-700 font-medium">
                    {extractionProgressText || TICKER_STEPS[tickerIndex]}
                  </p>
                  <p className="text-[10px] text-slate-500">
                    逆向萃取工业材质特征、客群画像、买家抗拒点与主色阶
                  </p>
                </div>
              </div>
            ) : (
              <>
                <div className="h-11 w-11 rounded-full bg-blue-50 border border-blue-200/60 flex items-center justify-center text-blue-600 shadow-xs group-hover:scale-105 transition-transform">
                  <UploadCloud className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-800">
                    拖拽实物照片到此处，或点击浏览上传
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    支持 JPG / PNG / WebP，支持直接粘贴图片截图 (Ctrl+V)
                  </p>
                  <div className="inline-flex items-center gap-1 mt-1.5 text-[10px] font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                    <Sparkles className="h-3 w-3" />
                    <span>上传后自动逆向解析填充商业档案</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Uploaded Reference Assets List */}
        {referenceImages.length > 0 && (
          <div className="space-y-2 pt-2">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold text-slate-600 uppercase tracking-wider flex items-center gap-1.5">
                <Layers className="h-3 w-3 text-blue-600" />
                <span>已就绪实物资产 ({referenceImages.length})</span>
              </p>
              <span className="text-[10px] text-slate-500">
                主基准图将直接作为光学锁模参考
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 max-h-[220px] overflow-y-auto pr-1">
              {referenceImages.map((asset) => (
                <div
                  key={asset.id}
                  className={`flex items-center gap-3 p-2 rounded-lg border transition-all group ${
                    asset.is_primary
                      ? 'bg-blue-50/50 border-blue-300 shadow-xs'
                      : 'bg-white border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <div className="h-12 w-12 rounded-md overflow-hidden bg-slate-100 shrink-0 border border-slate-200 relative">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={asset.url}
                      alt="Ref Asset"
                      className="h-full w-full object-cover"
                    />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold text-slate-800 truncate">
                        {asset.is_primary ? '主视觉基准参考' : '结构细节参考'}
                      </span>
                      {asset.is_primary && (
                        <Badge variant="success" className="text-[10px] py-0 px-1.5 h-4 gap-0.5">
                          <CheckCircle2 className="h-2.5 w-2.5" />
                          <span>主锁模基准</span>
                        </Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-1 flex-wrap mt-1">
                      {asset.vision_tags && asset.vision_tags.length > 0 ? (
                        asset.vision_tags.slice(0, 3).map((t, idx) => (
                          <span
                            key={idx}
                            className="text-[10px] text-slate-600 bg-slate-100 px-1.5 py-0.2 rounded border border-slate-200"
                          >
                            {t}
                          </span>
                        ))
                      ) : (
                        <span className="text-[10px] text-slate-500">#实物参考</span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        extractDossierFromExistingAsset(asset.url);
                      }}
                      disabled={isExtractingDossier}
                      className="text-[10px] text-slate-500 hover:text-blue-600 hover:bg-slate-100"
                    >
                      重新逆向
                    </Button>
                    {!asset.is_primary && (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSetPrimary(asset.id);
                        }}
                        className="text-[10px] text-slate-500 hover:text-blue-600 hover:bg-slate-100"
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
                      className="h-7 w-7 text-slate-400 hover:text-red-600 hover:bg-red-50"
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
      <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-2.5 text-slate-600 text-xs leading-relaxed">
        <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">工业级保真锁模机制: </span>
          基于随手拍实物提取真实外形轮廓、工业倒角与材质反光，9
          大视角严格防漂移，杜绝虚构未经验证的结构部件或失真功能。
        </div>
      </div>

      <style jsx>{`
        @keyframes laserScan {
          0% {
            top: 2%;
          }
          100% {
            top: 96%;
          }
        }
      `}</style>
    </div>
  );
};
