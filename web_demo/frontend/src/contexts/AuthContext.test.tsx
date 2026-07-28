import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';

function Probe() {
  const { isLoggedIn, logout } = useAuth();
  return (
    <>
      <span>{isLoggedIn ? 'logged-in' : 'logged-out'}</span>
      <button onClick={logout}>logout</button>
    </>
  );
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    sessionStorage.clear();
    window.location.hash = '';
  });

  it('migrates and validates the legacy password before treating it as logged in', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', fetchMock);
    localStorage.setItem('labsafe_password', 'demo-secret');

    render(<AuthProvider><Probe /></AuthProvider>);

    await waitFor(() => expect(screen.getByText('logged-in')).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/check', {
      headers: { 'x-password': 'demo-secret' },
    });
    expect(localStorage.getItem('labsafe_password')).toBeNull();

    await userEvent.click(screen.getByRole('button', { name: 'logout' }));
    expect(sessionStorage.getItem('labsafe_password')).toBeNull();
  });

  it('clears an invalid password restored from session storage', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }));
    sessionStorage.setItem('labsafe_password', 'wrong-password');

    render(<AuthProvider><Probe /></AuthProvider>);

    await waitFor(() => expect(sessionStorage.getItem('labsafe_password')).toBeNull());
    expect(screen.getByText('logged-out')).toBeInTheDocument();
  });
});
