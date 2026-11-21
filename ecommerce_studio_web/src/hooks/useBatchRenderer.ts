"use client";

import { useRef, useCallback } from 'react';
import { useStudioStore } from '@/stores/useStudioStore';
import { subscribeSSE } from '@/lib/sse-client';
import { SSEBatchEvent } from '@/types/api';

const INACTIVITY_TIMEOUT_MS = 120000; // 120s 动态活动超时保镖（每当收到任意卡片进度或完成事件时自动刷新）
const MAX_TOTAL_TIMEOUT_MS = 900000; // 15 分钟全局安全熔断兜底

export function useBatchRenderer() {
  const {
    currentSession,
    aspectRatio,
    isBatchRendering,
    batchProgress,
    setBatchRenderingState,
    setSingleCardStatus,
    addNewVersionSnapshot,
    markAllRenderingAsError,
  } = useStudioStore();

  const abortControllerRef = useRef<AbortController | null>(null);
  const inactivityTimerRef = useRef<NodeJS.Timeout | null>(null);
  const globalTimerRef = useRef<NodeJS.Timeout | null>(null);
  const cardStartTimesRef = useRef<Record<string, number>>({});

  const clearAllTimers = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
      inactivityTimerRef.current = null;
    }
    if (globalTimerRef.current) {
      clearTimeout(globalTimerRef.current);
      globalTimerRef.current = null;
    }
  }, []);

  const resetInactivityTimer = useCallback(() => {
    if (inactivityTimerRef.current) {
      clearTimeout(inactivityTimerRef.current);
    }
    inactivityTimerRef.current = setTimeout(() => {
      console.warn('Batch render reached inactivity timeout (120s with no response from server). Force terminating...');
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setBatchRenderingState(false);
      if (markAllRenderingAsError) {
        markAllRenderingAsError('批量生图达到 120s 响应超时（服务端无活动推送），请检查代理服务商网络');
      }
    }, INACTIVITY_TIMEOUT_MS);
  }, [setBatchRenderingState, markAllRenderingAsError]);

  const stopBatchRender = useCallback(() => {
    clearAllTimers();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setBatchRenderingState(false);
    if (markAllRenderingAsError) {
      markAllRenderingAsError('批量渲染已由用户手动中止');
    }
  }, [clearAllTimers, setBatchRenderingState, markAllRenderingAsError]);

  const startBatchRender = useCallback(async () => {
    if (!currentSession?.session_id || isBatchRendering) return;

    // 清理旧资源
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    clearAllTimers();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const totalCards = currentSession.perspectives?.length || 9;
    cardStartTimesRef.current = {};
    const batchStartTime = Date.now();
    console.log(`🚀 [Batch Render Start] Session: ${currentSession.session_id}, total: ${totalCards}, serial concurrency: 1`);

    setBatchRenderingState(true, {
      total: totalCards,
      completed: 0,
      etaSeconds: Math.ceil(totalCards * 15),
      currentRunningIds: currentSession.perspectives.map((p) => p.id),
    });

    // 串行保活策略：首机位进入布光渲染，其余机位进入明确排队等待状态
    currentSession.perspectives.forEach((p, idx) => {
      if (idx === 0) {
        setSingleCardStatus(p.id, 'rendering', 10);
      } else {
        setSingleCardStatus(p.id, 'pending', 0);
      }
    });

    // 启动滑动动态心跳超时检测
    resetInactivityTimer();

    // 启动全局 15 分钟最大安全熔断保镖
    globalTimerRef.current = setTimeout(() => {
      console.warn('Batch render reached maximum total duration (15m). Force terminating...');
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setBatchRenderingState(false);
      if (markAllRenderingAsError) {
        markAllRenderingAsError('批量生图达到 15 分钟全局安全上限，已自动终止');
      }
    }, MAX_TOTAL_TIMEOUT_MS);

    try {
      subscribeSSE<SSEBatchEvent>(
        '/api/v1/studio/render-batch',
        {
          session_id: currentSession.session_id,
          aspect_ratio: aspectRatio,
          concurrency: 1, // 强制并发为 1
        },
        {
          onMessage: (event, data) => {
            // 每次接收到服务端事件，立即刷新动态无活动保镖定时器
            resetInactivityTimer();

            const rawEvent = (data?.event || event || '').toLowerCase();

            // 1. 单机位开始
            if (rawEvent === 'perspective_start') {
              const pid = data.perspective_id;
              if (pid) {
                cardStartTimesRef.current[pid] = Date.now();
                console.log(`🎬 [Batch Render] Perspective started: ${pid} (${data.name || ''})`);
                setSingleCardStatus(pid, 'rendering', 40);
              }
            }
            // 2. 单机位成功
            else if (rawEvent === 'perspective_done' || rawEvent === 'perspective_success') {
              const pid = data.perspective_id;
              if (pid) {
                const start = cardStartTimesRef.current[pid];
                const elapsed = start ? ((Date.now() - start) / 1000).toFixed(1) : '?';
                console.log(`✅ [Batch Render] Perspective finished in ${elapsed}s: ${pid} (${data.name || ''}) [${data.completed}/${data.total}]`);
                if (data.version) {
                  addNewVersionSnapshot(pid, data.version);
                }
                setSingleCardStatus(pid, 'success', 100);
              }
            }
            // 3. 单机位失败 / 异常报错（精准熔断单卡片，绝不卡在骨架屏）
            else if (rawEvent === 'perspective_error') {
              const pid = data.perspective_id;
              const errorMsg = data.error || data.message || '当前中继代理生图失败或接口不可用';
              if (pid) {
                const start = cardStartTimesRef.current[pid];
                const elapsed = start ? ((Date.now() - start) / 1000).toFixed(1) : '?';
                console.error(`❌ [Batch Render] Perspective error after ${elapsed}s: ${pid}: ${errorMsg}`);
                setSingleCardStatus(pid, 'error', 0, errorMsg);
              }
            }
            // 4. 进度同步
            else if (rawEvent === 'progress') {
              setBatchRenderingState(true, {
                completed: data.completed || 0,
                total: data.total || totalCards,
                etaSeconds: data.eta_seconds || 15,
              });
            }
            // 5. 批次全量完结
            else if (rawEvent === 'batch_complete' || rawEvent === 'complete') {
              const totalElapsed = ((Date.now() - batchStartTime) / 1000).toFixed(1);
              console.log(`🏁 [Batch Render Complete] Total elapsed: ${totalElapsed}s, completed: ${data.completed}/${data.total}`);
              clearAllTimers();
              setBatchRenderingState(false);
              // 同步权威 session 数据至前端状态库，确保 9 大图全量即时刷出
              if (data.session) {
                useStudioStore.getState().setSession(data.session);
              }
              // 兜底安全：将任何遗留的 rendering/pending 卡片置为完成或关闭
              const storeSession = useStudioStore.getState().currentSession;
              if (storeSession) {
                storeSession.perspectives.forEach((p) => {
                  if (p.render_status === 'rendering' || p.render_status === 'pending') {
                    setSingleCardStatus(p.id, p.image_url ? 'success' : 'error', 0, '渲染流已完结');
                  }
                });
              }
            }
          },
          onError: (err) => {
            console.warn('Batch render SSE interrupted or closed unexpectedly:', err);
            clearAllTimers();
            setBatchRenderingState(false);
            if (markAllRenderingAsError) {
              markAllRenderingAsError('SSE 网络连接中断，中继端点可能未开通生图服务或连接超时');
            }
          },
          onClose: () => {
            clearAllTimers();
            setBatchRenderingState(false);
          },
        },
        controller.signal
      );
    } catch (e) {
      console.error('Batch render initiation failed:', e);
      clearAllTimers();
      setBatchRenderingState(false);
      if (markAllRenderingAsError) {
        markAllRenderingAsError(e instanceof Error ? e.message : '启动批量生图请求失败');
      }
    }
  }, [
    currentSession,
    isBatchRendering,
    aspectRatio,
    setBatchRenderingState,
    setSingleCardStatus,
    addNewVersionSnapshot,
    markAllRenderingAsError,
    clearAllTimers,
    resetInactivityTimer,
  ]);

  return {
    isBatchRendering,
    batchProgress,
    startBatchRender,
    stopBatchRender,
  };
}
