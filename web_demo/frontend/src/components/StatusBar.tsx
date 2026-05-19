import type { DemoMetaResponse } from '../types/api';
import Icon from './Icon';

interface TopbarProps {
  health: boolean;
  healthChecked: boolean;
}

export function Topbar({ health, healthChecked }: TopbarProps) {
  let dotCls = 'off';
  let text = '正在连接…';
  if (healthChecked) {
    dotCls = health ? '' : 'err';
    text = health ? '服务在线' : '服务离线';
  }
  return (
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
        <button className="icon-btn" title="设置"><Icon name="settings" size={16} /></button>
        <button className="icon-btn" title="帮助"><Icon name="question" size={16} /></button>
      </div>
    </header>
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
