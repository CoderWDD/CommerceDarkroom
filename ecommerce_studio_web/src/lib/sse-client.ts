import { fetchEventSource } from '@microsoft/fetch-event-source';

export interface SSECallbacks<T = Record<string, unknown>> {
  onMessage: (event: string, data: T) => void;
  onError?: (err: unknown) => void;
  onClose?: () => void;
}

export function subscribeSSE<T = Record<string, unknown>>(
  url: string,
  payload: Record<string, unknown>,
  callbacks: SSECallbacks<T>,
  abortSignal?: AbortSignal
) {
  return fetchEventSource(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(payload),
    signal: abortSignal,
    async onopen(response) {
      if (response.ok && response.headers.get('content-type')?.includes('text/event-stream')) {
        return;
      }
      throw new Error(`SSE Connection failed with HTTP ${response.status}`);
    },
    onmessage(msg) {
      if (msg.data) {
        try {
          const parsed = JSON.parse(msg.data);
          callbacks.onMessage(msg.event || 'message', parsed);
        } catch {
          callbacks.onMessage(msg.event || 'message', msg.data as unknown as T);
        }
      }
    },
    onerror(err) {
      if (callbacks.onError) {
        callbacks.onError(err);
      }
      throw err;
    },
    onclose() {
      if (callbacks.onClose) {
        callbacks.onClose();
      }
    },
  });
}

