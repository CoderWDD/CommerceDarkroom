"use client";

import { useRef, useCallback } from 'react';
import { useStudioStore } from '@/stores/useStudioStore';
import { subscribeSSE } from '@/lib/sse-client';
import { SSEBatchEvent } from '@/types/api';

const BATCH_TIMEOUT_MS = 180000; // 180s 客户端整体超时熔断安全保护

export function useBatchRenderer() {
  const {
    currentSession,
    aspectRatio,
    concurrency,
    isBatchRendering,
    batchProgress,
    setBatchRenderingState,
    setSingleCardStatus,
    addNewVersionSnapshot,
    markAllRenderingAsError,
  } = useStudioStore();

  const abortControllerRef = useRef<AbortController | null>(null);
  const timeoutTimerRef = useRef<NodeJS.Timeout | null>(null);

  const clearTimer = useCallback(() => {
    if (timeoutTimerRef.current) {
      clearTimeout(timeoutTimerRef.current);
      timeoutTimerRef.current = null;
    }
  }, []);

  const stopBatchRender = useCallback(() => {
    clearTimer();
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setBatchRenderingState(false);
    if (markAllRenderingAsError) {
      markAllRenderingAsError('批量渲染已由用户手动中止');
    }
  }, [clearTimer, setBatchRenderingState, markAllRenderingAsError]);

  const startBatchRender = useCallback(async () => {
    if (!currentSession?.session_id || isBatchRendering) return;

    // 清理旧资源
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    clearTimer();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const totalCards = currentSession.perspectives?.length || 9;
    setBatchRenderingState(true, {
      total: totalCards,
      completed: 0,
      etaSeconds: Math.ceil(totalCards * 15 / (concurrency || 3)),
      currentRunningIds: currentSession.perspectives.map((p) => p.id),
    });

    // 将所有卡片标记为开始渲染
    currentSession.perspectives.forEach((p) => {
      setSingleCardStatus(p.id, 'rendering', 10);
    });

    // 启动全局超时熔断保镖
    timeoutTimerRef.current = setTimeout(() => {
      console.warn('Batch render reached client timeout fuse (180s). Force terminating...');
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
      setBatchRenderingState(false);
      if (markAllRenderingAsError) {
        markAllRenderingAsError('批量生图达到 180s 超时熔断保护，请检查代理服务商网络与生图接口响应速度');
      }
    }, BATCH_TIMEOUT_MS);

    try {
      subscribeSSE<SSEBatchEvent>(
        '/api/v1/studio/render-batch',
        {
          session_id: currentSession.session_id,
          aspect_ratio: aspectRatio,
          concurrency: concurrency,
        },
        {
          onMessage: (event, data) => {
            const rawEvent = (data?.event || event || '').toLowerCase();

            // 1. 单机位开始
            if (rawEvent === 'perspective_start') {
              const pid = data.perspective_id;
              if (pid) {
                setSingleCardStatus(pid, 'rendering', 40);
              }
            }
            // 2. 单机位成功
            else if (rawEvent === 'perspective_done' || rawEvent === 'perspective_success') {
              const pid = data.perspective_id;
              if (pid) {
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
              clearTimer();
              setBatchRenderingState(false);
              // 同步权威 session 数据至前端状态库，确保 9 大图全量即时刷出
              if (data.session) {
                useStudioStore.getState().setSession(data.session);
              }
              // 兜底安全：将任何遗留的 rendering 卡片置为完成或关闭
              const storeSession = useStudioStore.getState().currentSession;
              if (storeSession) {
                storeSession.perspectives.forEach((p) => {
                  if (p.render_status === 'rendering') {
                    setSingleCardStatus(p.id, p.image_url ? 'success' : 'error', 0, '渲染流已完结');
                  }
                });
              }
            }
          },
          onError: (err) => {
            console.warn('Batch render SSE interrupted or closed unexpectedly:', err);
            clearTimer();
            setBatchRenderingState(false);
            if (markAllRenderingAsError) {
              markAllRenderingAsError('SSE 网络连接中断，中继端点可能未开通生图服务或连接超时');
            }
          },
          onClose: () => {
            clearTimer();
            setBatchRenderingState(false);
          },
        },
        controller.signal
      );
    } catch (e) {
      console.error('Batch render initiation failed:', e);
      clearTimer();
      setBatchRenderingState(false);
      if (markAllRenderingAsError) {
        markAllRenderingAsError(e instanceof Error ? e.message : '启动批量生图请求失败');
      }
    }
  }, [
    currentSession,
    isBatchRendering,
    aspectRatio,
    concurrency,
    setBatchRenderingState,
    setSingleCardStatus,
    addNewVersionSnapshot,
    markAllRenderingAsError,
    clearTimer,
  ]);

  return {
    isBatchRendering,
    batchProgress,
    startBatchRender,
    stopBatchRender,
  };
}
