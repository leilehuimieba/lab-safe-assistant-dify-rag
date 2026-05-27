import { Component, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          width: '100vw', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: '#f6f7f9', color: '#0f172a', fontFamily: 'system-ui, sans-serif'
        }}>
          <div style={{ textAlign: 'center', maxWidth: 480, padding: 24 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>⚠️</div>
            <div style={{ fontSize: 20, fontWeight: 700, marginBottom: 8 }}>页面出错了</div>
            <div style={{ fontSize: 14, color: '#475569', lineHeight: 1.6, marginBottom: 20 }}>
              某个组件发生了运行时错误。你可以尝试刷新页面恢复。
            </div>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '10px 20px', borderRadius: 10, border: 'none',
                background: '#0f766e', color: '#fff', fontSize: 14, fontWeight: 500,
                cursor: 'pointer'
              }}
            >
              刷新页面
            </button>
            {this.state.error && (
              <pre style={{
                marginTop: 20, textAlign: 'left', fontSize: 11, color: '#64748b',
                background: '#f1f5f9', padding: 12, borderRadius: 8, overflow: 'auto'
              }}>
                {this.state.error.message}
              </pre>
            )}
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
