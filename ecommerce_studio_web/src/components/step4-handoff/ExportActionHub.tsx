"use client";

import React, { useState } from 'react';
import { Package, FileText, Copy, Check, Download } from 'lucide-react';
import { useStudioStore } from '@/stores/useStudioStore';
import { Button } from '@/components/ui/button';
import { studioApi } from '@/lib/api-client';

export const ExportActionHub: React.FC = () => {
  const { currentSession } = useStudioStore();
  const [copiedPrompts, setCopiedPrompts] = useState(false);

  const sessionId = currentSession?.session_id || '';

  const handleDownloadZip = () => {
    if (!sessionId) return;
    const url = studioApi.getZipExportUrl(sessionId);
    window.open(url, '_blank');
  };

  const handleDownloadMarkdown = () => {
    if (!sessionId) return;
    const url = studioApi.getMarkdownExportUrl(sessionId);
    window.open(url, '_blank');
  };

  const handleCopyPrompts = () => {
    if (!currentSession?.perspectives) return;

    let content = `# 商业级电商视觉全案镜头语言与提示词矩阵\n专案: ${currentSession.name}\n生成时间: ${new Date().toLocaleString()}\n\n`;

    currentSession.perspectives.forEach((p, idx) => {
      content += `### 0${idx + 1}. ${p.name} (${p.tag})\n`;
      content += `- 转化心理学目标: ${p.psychology_target}\n`;
      content += `- 镜头语言与布景指导: ${p.prompt_zh}\n\n`;
    });

    navigator.clipboard.writeText(content);
    setCopiedPrompts(true);
    setTimeout(() => setCopiedPrompts(false), 2000);
  };

  return (
    <div
      id="export-actions-hub"
      className="bg-white border border-slate-200 rounded-2xl p-6 shadow-card flex flex-col md:flex-row md:items-center md:justify-between gap-4"
    >
      <div className="space-y-1">
        <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
          <Package className="h-4 w-4 text-blue-600" />
          全套物料交付枢纽 (Master Handoff Actions)
        </h3>
        <p className="text-xs text-slate-500">
          导出符合电商工业标准的规范文件命名 ZIP 压缩包与 Markdown 策划全案，方便设计与运营团队归档落地。
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="sm"
          onClick={handleCopyPrompts}
          className="gap-1.5 text-xs text-slate-700 hover:text-slate-900 border-slate-200 bg-white hover:bg-slate-50"
        >
          {copiedPrompts ? (
            <>
              <Check className="h-3.5 w-3.5 text-emerald-600" />
              <span>已复制提示词</span>
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              <span>复制 9 套摄影指令</span>
            </>
          )}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleDownloadMarkdown}
          className="gap-1.5 text-xs text-slate-700 hover:text-slate-900 border-slate-200 bg-white hover:bg-slate-50"
        >
          <FileText className="h-3.5 w-3.5 text-blue-600" />
          <span>导出 Markdown 策划全案</span>
        </Button>

        <Button
          variant="studio-accent"
          size="sm"
          onClick={handleDownloadZip}
          className="gap-1.5 text-xs font-semibold px-4 h-9 shadow-md shadow-amber-500/20"
        >
          <Download className="h-4 w-4" />
          <span>一键打包全部大图 (ZIP) 📦</span>
        </Button>
      </div>
    </div>
  );
};
