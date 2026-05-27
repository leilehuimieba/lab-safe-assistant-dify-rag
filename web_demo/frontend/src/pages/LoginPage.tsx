import { useState, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';

const COLORS = {
  bg: '#0f172a',
  card: '#1e293b',
  text: '#f1f5f9',
  text2: '#94a3b8',
  cyan: '#06b6d4',
  red: '#ef4444',
  glow: 'rgba(6, 182, 212, 0.3)',
};

export default function LoginPage() {
  const { login } = useAuth();
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [checking, setChecking] = useState(false);

  const submit = useCallback(async () => {
    const pw = input.trim();
    if (!pw) {
      setError('请输入密码');
      return;
    }
    setChecking(true);
    setError('');
    try {
      // 验证密码：调用 /health 接口带密码头
      const r = await fetch('/health', {
        headers: { 'x-password': pw },
      });
      if (r.ok) {
        login(pw);
        window.location.hash = '/';
      } else {
        setError('密码错误');
      }
    } catch (e) {
      setError('网络错误，请重试');
    } finally {
      setChecking(false);
    }
  }, [input, login]);

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        background: COLORS.bg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          background: COLORS.card,
          border: `1px solid ${COLORS.glow}`,
          borderRadius: 16,
          padding: '40px 36px',
          width: 360,
          boxShadow: `0 0 40px ${COLORS.glow}`,
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{ fontSize: 22, fontWeight: 700, color: COLORS.text, marginBottom: 6 }}>
            实验室安全助手
          </div>
          <div style={{ fontSize: 13, color: COLORS.text2 }}>请输入访问密码</div>
        </div>

        <input
          type="password"
          value={input}
          onChange={(e) => { setInput(e.target.value); setError(''); }}
          onKeyDown={(e) => { if (e.key === 'Enter') submit(); }}
          placeholder="密码"
          style={{
            width: '100%',
            padding: '12px 14px',
            borderRadius: 8,
            border: `1px solid ${error ? COLORS.red : COLORS.glow}`,
            background: COLORS.bg,
            color: COLORS.text,
            fontSize: 14,
            outline: 'none',
            boxSizing: 'border-box',
            marginBottom: error ? 8 : 16,
          }}
        />

        {error && (
          <div style={{ color: COLORS.red, fontSize: 13, marginBottom: 12, textAlign: 'center' }}>{error}</div>
        )}

        <button
          onClick={submit}
          disabled={checking}
          style={{
            width: '100%',
            padding: '12px',
            borderRadius: 8,
            border: 'none',
            background: COLORS.cyan,
            color: COLORS.bg,
            fontSize: 14,
            fontWeight: 600,
            cursor: checking ? 'not-allowed' : 'pointer',
            opacity: checking ? 0.7 : 1,
          }}
        >
          {checking ? '验证中...' : '进入系统'}
        </button>
      </div>
    </div>
  );
}
