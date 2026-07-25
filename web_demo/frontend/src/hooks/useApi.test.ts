import { beforeEach, describe, expect, it, vi } from 'vitest';
import { jsonFetch } from './useApi';

describe('jsonFetch', () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    vi.restoreAllMocks();
  });

  it('sends the tab-scoped demo password after auth storage migration', async () => {
    sessionStorage.setItem('labsafe_password', 'session-secret');
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await jsonFetch<{ ok: boolean }>('/api/meta');

    const requestInit = fetchMock.mock.calls[0][1];
    expect(requestInit?.headers).toMatchObject({ 'x-password': 'session-secret' });
  });
});
