"use client";

import React, { useState, useRef, useEffect } from 'react';
import {
  Sparkles,
  Send,
  Wand2,
  Check,
  Bot,
  User,
} from 'lucide-react';
import { useCopilotStore } from '@/stores/useCopilotStore';
import { useStudioStore } from '@/stores/useStudioStore';
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from '@/components/ui/sheet';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';

export const CopilotDrawer: React.FC = () => {
  const { isOpen, setOpen, isThinking, messages, sendMessage, applyActionChip } =
    useCopilotStore();
  const { currentStep, activePerspectiveId, currentSession } = useStudioStore();

  const [inputVal, setInputVal] = useState('');
  const [appliedId, setAppliedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeP = currentSession?.perspectives.find((p) => p.id === activePerspectiveId);
  const stepLabels: Record<number, string> = {
    1: 'Step 1: 资产录入',
    2: 'Step 2: 矩阵策划',
    3: 'Step 3: 出图工坊',
    4: 'Step 4: 物料交付',
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  const handleSend = async () => {
    if (!inputVal.trim() || isThinking) return;
    const txt = inputVal;
    setInputVal('');
    await sendMessage(txt);
  };

  const handleApplyChip = (targetPerspectiveId: string, prompt: string, chipId: string) => {
    applyActionChip(targetPerspectiveId, prompt);
    setAppliedId(chipId);
    setTimeout(() => setAppliedId(null), 2500);
  };

  const QUICK_QUESTIONS = [
    '帮我优化全案色系与光影调性',
    '怎么提升 01 白底主图的商业点击率？',
    '检查 9 张图的视觉故事线与连贯性',
  ];

  return (
    <Sheet open={isOpen} onOpenChange={setOpen}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-md p-0 flex flex-col justify-between bg-white border-l border-slate-200 text-slate-900 shadow-popover"
      >
        {/* Header */}
        <div className="p-4 border-b border-slate-100 space-y-2 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-blue-600 text-white shadow-xs">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <SheetTitle className="text-sm font-semibold text-slate-900">
                首席视觉顾问 (Creative Copilot)
              </SheetTitle>
              <p className="text-[11px] text-slate-500">
                商业摄影棚光影布景顾问与消费心理学专家
              </p>
            </div>
          </div>

          {/* Context Badge */}
          <div className="flex items-center gap-1.5 text-[11px] bg-white p-2 rounded-lg border border-slate-200 shadow-xs">
            <span className="text-slate-500 font-medium">当前情境:</span>
            <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-blue-700 border-blue-200 bg-blue-50 font-medium">
              {stepLabels[currentStep] || `Step ${currentStep}`}
            </Badge>
            {activeP && (
              <Badge variant="outline" className="text-[10px] py-0 px-1.5 text-indigo-700 border-indigo-200 bg-indigo-50 truncate max-w-[150px] font-medium">
                {activeP.name}
              </Badge>
            )}
          </div>
        </div>

        {/* Message History List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div
                key={msg.id}
                className={`flex gap-2.5 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="h-6 w-6 rounded-full bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 shrink-0 mt-0.5">
                    <Bot className="h-3.5 w-3.5" />
                  </div>
                )}

                <div
                  className={`space-y-2 max-w-[85%] rounded-2xl p-3 text-xs leading-relaxed ${
                    isUser
                      ? 'bg-blue-600 text-white rounded-tr-sm shadow-xs'
                      : 'bg-slate-50 text-slate-800 border border-slate-200 rounded-tl-sm shadow-xs'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Action Chip (Direct Injection) */}
                  {msg.action_chip && (
                    <div className="pt-2">
                      <Button
                        variant="outline"
                        size="xs"
                        onClick={() =>
                          handleApplyChip(
                            msg.action_chip!.target_perspective_id,
                            msg.action_chip!.suggested_prompt,
                            msg.id
                          )
                        }
                        className="w-full justify-between gap-1.5 text-[11px] bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100 hover:text-indigo-900"
                      >
                        <span className="truncate flex items-center gap-1 font-medium">
                          <Wand2 className="h-3 w-3 text-indigo-600" />
                          <span>{msg.action_chip.label}</span>
                        </span>
                        {appliedId === msg.id ? (
                          <Check className="h-3.5 w-3.5 text-emerald-600" />
                        ) : (
                          <span className="text-[10px] text-indigo-600 font-semibold">一键注入</span>
                        )}
                      </Button>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="h-6 w-6 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 shrink-0 mt-0.5">
                    <User className="h-3.5 w-3.5" />
                  </div>
                )}
              </div>
            );
          })}

          {isThinking && (
            <div className="flex gap-2.5 items-center text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200 w-fit">
              <Wand2 className="h-3.5 w-3.5 animate-spin text-indigo-600" />
              <span>顾问正在研判镜头调性与消费心理学...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Questions & Input Box */}
        <div className="p-4 border-t border-slate-100 space-y-3 bg-slate-50/50">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {QUICK_QUESTIONS.map((q, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => sendMessage(q)}
                className="text-[11px] whitespace-nowrap px-2.5 py-1 rounded-full bg-white border border-slate-200 text-slate-700 hover:text-blue-700 hover:border-blue-300 hover:bg-blue-50 transition-colors shrink-0 shadow-xs"
              >
                {q}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Input
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="向视觉顾问提问，或提出镜头光影微调要求..."
              className="text-xs h-9 bg-white border-slate-200 text-slate-900 focus:border-blue-500 shadow-xs"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <Button
              variant="studio-accent"
              size="icon"
              onClick={handleSend}
              disabled={isThinking || !inputVal.trim()}
              className="h-9 w-9 shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};
