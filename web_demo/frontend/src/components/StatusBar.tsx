import { useState } from 'react';
import type { DemoMetaResponse } from '../types/api';
import Icon from './Icon';

interface TopbarProps {
  health: boolean;
  healthChecked: boolean;
}

function Modal({ title, children, onClose }: { title: string; children: React.ReactNode; onClose: () => void }) {
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.5)', zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={onClose}>
      <div style={{ background: '#fff', borderRadius: 16, padding: 24, width: 400, maxWidth: '90vw', boxShadow: '0 24px 60px rgba(15,23,42,0.18)' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ fontSize: 16, fontWeight: 700 }}>{title}</div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', fontSize: 20, cursor: 'pointer', color: '#94a3b8' }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function Topbar({ health, healthChecked }: TopbarProps) {
  const [showSettings, setShowSettings] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  let dotCls = 'off';
  let text = '正在连接…';
  if (healthChecked) {
    dotCls = health ? '' : 'err';
    text = health ? '服务在线' : '服务离线';
  }

  const clearCache = () => {
    try {
      localStorage.removeItem('labsafe_chat_session');
      alert('本地对话缓存已清除，刷新页面生效。');
    } catch {
      alert('清除失败');
    }
  };

  return (
    <>
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><Icon name="flask" size={18} stroke={2.2} /></div>
          <div>
            <div className="brand-name">实验室安全小助手</div>
            <div className="brand-sub">LAB SAFETY ASSISTANT</div>
          </div>
        </div>
        <div className="top-actions">
          <div className="health-pill">
            <span className={`health-dot ${dotCls}`} />
            <span>{text}</span>
          </div>
          <button className="icon-btn" title="设置" onClick={() => setShowSettings(true)}><Icon name="settings" size={16} /></button>
          <button className="icon-btn" title="帮助" onClick={() => setShowHelp(true)}><Icon name="question" size={16} /></button>
        </div>
      </header>

      {showSettings && (
        <Modal title="设置" onClose={() => setShowSettings(false)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ fontSize: 13, color: '#475569' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>数据管理</div>
              <button onClick={clearCache} style={{ padding: '8px 14px', borderRadius: 8, border: '1px solid #e5e8ee', background: '#f1f5f9', cursor: 'pointer', fontSize: 13 }}>
                清除本地对话缓存
              </button>
            </div>
            <div style={{ fontSize: 13, color: '#475569' }}>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>版本信息</div>
              <div>前端版本：v0.9.3</div>
              <div>密码认证：已启用</div>
            </div>
          </div>
        </Modal>
      )}

      {showHelp && (
        <Modal title="使用帮助" onClose={() => setShowHelp(false)}>
          <div style={{ fontSize: 13, color: '#475569', lineHeight: 1.7 }}>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>快捷操作</div>
            <div><kbd style={{ background: '#f1f5f9', border: '1px solid #e5e8ee', padding: '1px 5px', borderRadius: 4, fontSize: 12 }}>↵</kbd> 发送问题</div>
            <div><kbd style={{ background: '#f1f5f9', border: '1px solid #e5e8ee', padding: '1px 5px', borderRadius: 4, fontSize: 12 }}>⇧ ↵</kbd> 换行</div>
            <div style={{ fontWeight: 600, margin: '12px 0 8px' }}>功能说明</div>
            <div>• 输入实验室安全问题，AI 将基于知识库作答</div>
            <div>• 点击「仅检索」可查看本地知识库命中结果</div>
            <div>• 左侧历史记录可点击重新提问</div>
            <div>• 知识库态势页面可查看 3009 条知识库调用覆盖情况</div>
            <div style={{ marginTop: 12, color: '#94a3b8', fontSize: 12 }}>本助手仅供参考，最终操作以本单位 SOP 与安全员意见为准。</div>
          </div>
        </Modal>
      )}
    </>
  );
}

interface FootbarProps {
  meta: DemoMetaResponse | null;
}

export function Footbar({ meta }: FootbarProps) {
  return (
    <footer className="footbar">
      <div className="left">
        <span>© 2026 安全管理处</span>
        <span className="sep" />
        <span>本助手仅供参考，最终操作以本单位 SOP 与安全员意见为准</span>
      </div>
      <div className="right">
        {meta && (
          <>
            <span>{meta.app_version}</span>
            <span className="sep" />
            <span>KB {meta.knowledge_base_rows.toLocaleString()}</span>
            <span className="sep" />
          </>
        )}
        <span>已加密 · 已脱敏</span>
      </div>
    </footer>
  );
}
