import { useCallback, useEffect, useState } from 'react';
import type {
  ChatRequest,
  ChatResponse,
  DemoMetaResponse,
  FeedbackRequest,
  HealthResponse,
  SearchResponse,
  StatsResponse,
} from '../types/api';

/** 通用 fetch 包装。所有路径必须是相对路径（如 /api/chat），由 Vite proxy / 后端托管转发。 */
async function jsonFetch<T>(input: RequestInfo, init?: RequestInit, timeoutMs = 60_000): Promise<T> {
  const password = localStorage.getItem('labsafe_password') || '';
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const r = await fetch(input, {
      ...init,
      signal: ctl.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(password ? { 'x-password': password } : {}),
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

export function useStats() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await jsonFetch<StatsResponse>('/api/stats');
        if (!cancelled) {
          setStats(data);
          setError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : '统计加载失败');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void load();
    const timer = window.setInterval(() => {
      void load();
    }, 15_000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return { stats, loading, error };
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

export function useFeedback() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submitFeedback = useCallback(async (payload: FeedbackRequest): Promise<void> => {
    setBusy(true);
    setError(null);
    try {
      await jsonFetch<{ status: string }>('/api/feedback', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : '反馈提交失败';
      setError(msg);
      throw e;
    } finally {
      setBusy(false);
    }
  }, []);

  return { submitFeedback, busy, error };
}
