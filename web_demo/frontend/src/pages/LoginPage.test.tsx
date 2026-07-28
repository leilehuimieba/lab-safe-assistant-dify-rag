import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '../contexts/AuthContext';
import LoginPage from './LoginPage';

describe('LoginPage', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('validates against the protected auth endpoint and rejects a wrong password', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false });
    vi.stubGlobal('fetch', fetchMock);

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>,
    );

    await userEvent.type(screen.getByPlaceholderText('密码'), 'wrong-password');
    await userEvent.click(screen.getByRole('button', { name: '进入系统' }));

    await waitFor(() => expect(screen.getByText('密码错误')).toBeInTheDocument());
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/check', {
      headers: { 'x-password': 'wrong-password' },
    });
    expect(sessionStorage.getItem('labsafe_password')).toBeNull();
  });
});
