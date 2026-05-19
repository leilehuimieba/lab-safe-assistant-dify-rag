import { useCallback, useEffect, useState } from 'react';
import type {
  ChatRequest,
  ChatResponse,
  DemoMetaResponse,
  HealthResponse,
  SearchResponse,
} from '../types/api';

/** 通用 fetch 包装。所有路径必须是相对路径（如 /api/chat），由 Vite proxy / 后端托管转发。 */
async function jsonFetch<T>(input: RequestInfo, init?: RequestInit, timeoutMs = 60_000): Promise<T> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const r = await fetch(input, {
      ...init,
      signal: ctl.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(init?.headers || {}),
      },
    });
    if (!r.ok) {
      const body = await r.text().catch(() => '');
      throw new Error(`HTTP ${r.status} ${r.statusText}${body ? ` — ${body}` : ''}`);
    }
    return (await r.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export function useMetaAndHealth() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<DemoMetaResponse | null>(null);
  const [health, setHealth] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [m, h] = await Promise.all([
          jsonFetch<DemoMetaResponse>('/api/meta'),
          jsonFetch<HealthResponse>('/health'),
        ]);
        if (cancelled) return;
        setMeta(m);
        setHealth(!!h.ok || h.status === 'ok');
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : '加载失败');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return { loading, error, meta, health };
}

export function useChat() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(async (req: ChatRequest): Promise<ChatResponse> => {
    setBusy(true);
    setError(null);
    try {
      return await jsonFetch<ChatResponse>('/api/chat', {
        method: 'POST',
        body: JSON.stringify(req),
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : '请求失败';
      setError(msg);
      throw e;
    } finally {
      setBusy(false);
    }
  }, []);

  return { send, busy, error, setError };
}

export function useSearch() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (q: string, topK = 5): Promise<SearchResponse> => {
    setBusy(true);
    setError(null);
    try {
      const params = new URLSearchParams({ q, top_k: String(topK) });
      return await jsonFetch<SearchResponse>(`/api/search?${params.toString()}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : '检索失败';
      setError(msg);
      throw e;
    } finally {
      setBusy(false);
    }
  }, []);

  return { search, busy, error, setError };
}
