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
  Camera,
  ShoppingBag,
  ArrowRightLeft,
} from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { AssetType } from '@/types/session';

const TICKER_STEPS = [
  '阶段 1/4: 正在上传原始物理/电商图像...',
  '阶段 2/4: 多模态视觉模型逆向审视中...',
  '阶段 3/4: 萃取材质特征/商业构图光影...',
  '阶段 4/4: 提炼防走样特征与买家决策标签...',
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
  const [activeUploadType, setActiveUploadType] = useState<AssetType>('actual');

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
            extractDossierFromPhoto(file, undefined, activeUploadType);
            break;
          }
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [extractDossierFromPhoto, activeUploadType]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const file = files[0];
    try {
      await extractDossierFromPhoto(file, undefined, activeUploadType);
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
    if (updated.length > 0 && !updated.some((img) => img.is_primary && (img.asset_type || 'actual') === 'actual')) {
      const firstActual = updated.find((img) => (img.asset_type || 'actual') === 'actual');
      if (firstActual) firstActual.is_primary = true;
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

  const handleToggleAssetType = (id: string) => {
    const updated = referenceImages.map((img) => {
      if (img.id === id) {
        const nextType: AssetType = (img.asset_type || 'actual') === 'actual' ? 'competitor' : 'actual';
        return {
          ...img,
          asset_type: nextType,
          is_primary: nextType === 'actual' ? img.is_primary : false,
        };
      }
      return img;
    });
    updateProductInfo({ reference_images: updated });
  };

  const actualImagesCount = referenceImages.filter((img) => (img.asset_type || 'actual') === 'actual').length;
  const competitorImagesCount = referenceImages.filter((img) => img.asset_type === 'competitor').length;

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
              随手拍与电商资产录入 (Dual-Asset Vision)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              区分上传【产品实拍图】与【对标商品图】，AI 结合实物形体保真与竞品视觉对标。
            </p>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-100 px-2 py-1 rounded-md border border-slate-200">
            <Clipboard className="h-3 w-3 text-blue-600" />
            <span>支持 Ctrl+V 粘贴</span>
          </div>
        </div>

        {/* Asset Type Toggle Switcher */}
        <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl border border-slate-200">
          <button
            type="button"
            onClick={() => setActiveUploadType('actual')}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
              activeUploadType === 'actual'
                ? 'bg-white text-blue-700 shadow-xs border border-blue-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Camera className="h-3.5 w-3.5 text-blue-600" />
            <span>产品实拍图 (实际图)</span>
            {actualImagesCount > 0 && (
              <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded-full font-bold">
                {actualImagesCount}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setActiveUploadType('competitor')}
            className={`flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold transition-all ${
              activeUploadType === 'competitor'
                ? 'bg-white text-amber-700 shadow-xs border border-amber-200'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <ShoppingBag className="h-3.5 w-3.5 text-amber-600" />
            <span>对标商品图 (电商图)</span>
            {competitorImagesCount > 0 && (
              <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.2 rounded-full font-bold">
                {competitorImagesCount}
              </span>
            )}
          </button>
        </div>

        {/* Upload Description Banner */}
        <div
          className={`text-xs px-3 py-2 rounded-lg border leading-relaxed flex items-center justify-between ${
            activeUploadType === 'actual'
              ? 'bg-blue-50/70 border-blue-200 text-blue-900'
              : 'bg-amber-50/70 border-amber-200 text-amber-900'
          }`}
        >
          <div>
            <span className="font-bold">
              {activeUploadType === 'actual' ? '📸 当前准备上传: 产品实拍图' : '🛒 当前准备上传: 对标商品图'}
            </span>
            <span className="ml-1 opacity-90">
              {activeUploadType === 'actual'
                ? '（您产品的实际原貌照片，Step 3 出图时强制保真锁模，杜绝产品变形与虚构）'
                : '（电商平台上其他品牌的优秀主图大片，Step 2 策划时参考其高级构图与光影）'}
            </span>
          </div>
        </div>

        {/* Laser Radar Scanning Dropzone */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => !isExtractingDossier && fileInputRef.current?.click()}
          className={`relative overflow-hidden border-2 border-dashed rounded-xl p-5 text-center transition-all min-h-[160px] flex flex-col items-center justify-center ${
            isExtractingDossier
              ? 'border-blue-500 bg-blue-50/40 shadow-sm cursor-wait'
              : dragActive
              ? 'border-blue-500 bg-blue-50/60 cursor-copy'
              : activeUploadType === 'actual'
              ? 'border-blue-300 hover:border-blue-500 hover:bg-blue-50/30 bg-slate-50/40 cursor-pointer'
              : 'border-amber-300 hover:border-amber-500 hover:bg-amber-50/30 bg-slate-50/40 cursor-pointer'
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
              <div
                className="absolute inset-0 opacity-15"
                style={{
                  backgroundImage:
                    'linear-gradient(rgba(37, 99, 235, 0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(37, 99, 235, 0.4) 1px, transparent 1px)',
                  backgroundSize: '24px 24px',
                }}
              />
              <div
                className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent shadow-[0_0_12px_#3b82f6]"
                style={{
                  animation: 'laserScan 2.4s ease-in-out infinite alternate',
                }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="h-32 w-32 rounded-full border border-blue-500/20 animate-ping opacity-25" />
              </div>
            </div>
          )}

          {/* Content Area */}
          <div className="relative z-20 flex flex-col items-center justify-center gap-2 text-slate-500">
            {isExtractingDossier ? (
              <div className="space-y-2.5 flex flex-col items-center">
                <div className="h-11 w-11 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 shadow-sm animate-pulse">
                  <Cpu className="h-5 w-5 animate-spin text-blue-600" style={{ animationDuration: '4s' }} />
                </div>

                <div className="space-y-1 text-center">
                  <p className="text-xs font-bold text-blue-700 tracking-wide flex items-center justify-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 animate-bounce" />
                    <span>多模态视觉大脑正在深度解析...</span>
                  </p>
                  <p className="text-[11px] text-slate-700 font-medium">
                    {extractionProgressText || TICKER_STEPS[tickerIndex]}
                  </p>
                </div>
              </div>
            ) : (
              <>
                <div
                  className={`h-10 w-10 rounded-full border flex items-center justify-center shadow-xs group-hover:scale-105 transition-transform ${
                    activeUploadType === 'actual'
                      ? 'bg-blue-50 border-blue-200 text-blue-600'
                      : 'bg-amber-50 border-amber-200 text-amber-600'
                  }`}
                >
                  <UploadCloud className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-800">
                    {activeUploadType === 'actual'
                      ? '拖拽【产品实拍图】到此处，或点击浏览上传'
                      : '拖拽【对标电商商品图】到此处，或点击浏览上传'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    支持 JPG / PNG / WebP，支持直接粘贴图片截图 (Ctrl+V)
                  </p>
                  <div
                    className={`inline-flex items-center gap-1 mt-1.5 text-[10px] font-medium px-2 py-0.5 rounded-full border ${
                      activeUploadType === 'actual'
                        ? 'text-blue-700 bg-blue-50 border-blue-200'
                        : 'text-amber-700 bg-amber-50 border-amber-200'
                    }`}
                  >
                    <Sparkles className="h-3 w-3" />
                    <span>
                      {activeUploadType === 'actual'
                        ? '自动提取实物特征，Step 3 出图保真防走样'
                        : '自动逆向商业光影与构图，Step 2 策划借鉴'}
                    </span>
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
                <span>
                  已就绪视觉资产 ({referenceImages.length}) · 实拍 {actualImagesCount} 张 / 对标 {competitorImagesCount} 张
                </span>
              </p>
              <span className="text-[10px] text-slate-500">
                实拍主图将作为 Step 3 锁模参考
              </span>
            </div>

            <div className="grid grid-cols-1 gap-2 max-h-[220px] overflow-y-auto pr-1">
              {referenceImages.map((asset) => {
                const isActual = (asset.asset_type || 'actual') === 'actual';
                return (
                  <div
                    key={asset.id}
                    className={`flex items-center gap-3 p-2 rounded-lg border transition-all group ${
                      asset.is_primary && isActual
                        ? 'bg-blue-50/50 border-blue-300 shadow-xs'
                        : !isActual
                        ? 'bg-amber-50/30 border-amber-200/80 hover:border-amber-300'
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
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {isActual ? (
                          <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 border-blue-300 bg-blue-50 text-blue-700">
                            实拍图
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-[10px] py-0 px-1.5 h-4 border-amber-300 bg-amber-50 text-amber-700">
                            对标电商图
                          </Badge>
                        )}

                        <span className="text-xs font-semibold text-slate-800 truncate">
                          {isActual
                            ? asset.is_primary
                              ? '主实拍保真锁模基准'
                              : '实拍工艺细节参考'
                            : '商业构图光影对标'}
                        </span>

                        {asset.is_primary && isActual && (
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
                              className={`text-[10px] px-1.5 py-0.2 rounded border ${
                                isActual
                                  ? 'text-slate-600 bg-slate-100 border-slate-200'
                                  : 'text-amber-800 bg-amber-100/60 border-amber-200'
                              }`}
                            >
                              {t}
                            </span>
                          ))
                        ) : (
                          <span className="text-[10px] text-slate-500">
                            {isActual ? '#实拍参考' : '#对标参考'}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          extractDossierFromExistingAsset(asset.url, undefined, asset.asset_type || 'actual');
                        }}
                        disabled={isExtractingDossier}
                        className="text-[10px] text-slate-500 hover:text-blue-600 hover:bg-slate-100"
                        title="重新对此资产进行多模态逆向解析"
                      >
                        重新逆向
                      </Button>

                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleToggleAssetType(asset.id);
                        }}
                        className="text-[10px] text-slate-500 hover:text-blue-600 hover:bg-slate-100 gap-0.5"
                        title="切换资产类型 (实拍图 / 对标图)"
                      >
                        <ArrowRightLeft className="h-2.5 w-2.5" />
                        <span>切为{isActual ? '对标' : '实拍'}</span>
                      </Button>

                      {isActual && !asset.is_primary && (
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
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Safety & Grounding Tip Box */}
      <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-start gap-2.5 text-slate-600 text-xs leading-relaxed">
        <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-slate-800">工业级双图协同体系: </span>
          基于【产品实拍图】提取真实轮廓与材质表面并在 Step 3 严格锁定，杜绝货不对板；同时基于【对标商品图】在 Step 2 汲取高转化商业布光与构图，实现爆款视觉全案。
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
