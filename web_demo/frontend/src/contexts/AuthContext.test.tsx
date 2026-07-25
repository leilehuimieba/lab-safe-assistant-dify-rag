import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it } from 'vitest';
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
    localStorage.clear();
    sessionStorage.clear();
    window.location.hash = '';
  });

  it('migrates the legacy persistent password into session storage', async () => {
    localStorage.setItem('labsafe_password', 'demo-secret');

    render(<AuthProvider><Probe /></AuthProvider>);

    expect(screen.getByText('logged-in')).toBeInTheDocument();
    expect(localStorage.getItem('labsafe_password')).toBeNull();
    expect(sessionStorage.getItem('labsafe_password')).toBe('demo-secret');

    await userEvent.click(screen.getByRole('button', { name: 'logout' }));
    expect(sessionStorage.getItem('labsafe_password')).toBeNull();
  });
});
