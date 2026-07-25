import { useEffect } from 'react';
import Icon from './Icon';

interface MobileNavigationProps {
  open: boolean;
  onClose: () => void;
  onNew: () => void;
  history: string[];
  onHistoryClick: (question: string) => void;
  onLogout: () => void;
}

export default function MobileNavigation({
  open,
  onClose,
  onNew,
  history,
  onHistoryClick,
  onLogout,
}: MobileNavigationProps) {
  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className="mobile-nav-backdrop" onMouseDown={onClose}>
      <aside
        className="mobile-nav"
        role="dialog"
        aria-label="移动端导航"
        aria-modal="true"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <div className="mobile-nav-head">
          <div>
            <strong>导航与最近会话</strong>
            <span>实验室安全小助手</span>
          </div>
          <button className="icon-btn" aria-label="关闭导航" onClick={onClose}>×</button>
        </div>

        <div className="mobile-nav-actions">
          <button
            className="new-chat-btn"
            onClick={() => {
              onNew();
              onClose();
            }}
          >
            <Icon name="plus" size={15} stroke={2.4} /> 新建对话
          </button>
          <a href="#/kb" className="mobile-nav-link" onClick={onClose}>
            <Icon name="database" size={15} stroke={2.4} /> 知识库态势
          </a>
        </div>

        <div className="mobile-nav-history">
          <div className="sb-title">
            <span>最近会话</span>
            <span className="count">{history.length}</span>
          </div>
          {history.length === 0 ? (
            <div className="history-empty">尚无历史记录</div>
          ) : (
            history.map((question, index) => (
              <button
                key={`${question}-${index}`}
                className="mobile-history-item"
                onClick={() => {
                  onHistoryClick(question);
                  onClose();
                }}
              >
                <Icon name="history" size={14} />
                <span>{question}</span>
              </button>
            ))
          )}
        </div>

        <button className="mobile-logout-btn" onClick={onLogout}>
          <Icon name="ban" size={15} stroke={2.2} /> 退出登录
        </button>
      </aside>
    </div>
  );
}
