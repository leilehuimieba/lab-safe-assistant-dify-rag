import Icon from './Icon';
import { QUICK_QUESTIONS } from './quickQuestions';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  onPick: (q: string, i: number) => void;
  onNew: () => void;
  history: string[];
  flashIdx: number;
  onHistoryClick?: (q: string) => void;
}

export default function Sidebar({ onPick, onNew, history, flashIdx, onHistoryClick }: SidebarProps) {
  const { logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="sb-section">
        <button className="new-chat-btn" onClick={onNew}>
          <Icon name="plus" size={14} stroke={2.4} /> 新建对话
        </button>
        <a href="#/kb" className="new-chat-btn" style={{ marginTop: 8, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Icon name="database" size={14} stroke={2.4} /> 知识库态势
        </a>
      </div>

      <div className="sb-section">
        <div className="sb-title">
          <span>快捷问题</span>
          <span className="count">{QUICK_QUESTIONS.length}</span>
        </div>
        <div className="quick-list">
          {QUICK_QUESTIONS.map((q, i) => (
            <button
              key={i}
              className={`quick-item ${flashIdx === i ? 'flash' : ''}`}
              onClick={() => onPick(q, i)}
            >
              <span className="quick-num">{i + 1}</span>
              <span>{q}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="sb-section">
        <div className="sb-title">
          <span>最近会话</span>
          <span className="count">{history.length}</span>
        </div>
        {history.length === 0 ? (
          <div className="history-empty">尚无历史记录</div>
        ) : (
          <div>
            {history.map((h, i) => (
              <div
                className="history-item"
                key={i}
                onClick={() => onHistoryClick?.(h)}
                title="点击重新提问"
              >
                <Icon name="history" size={12} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {h}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="sb-section" style={{ marginTop: 'auto' }}>
        <button
          className="new-chat-btn"
          onClick={logout}
          style={{ background: 'transparent', border: '1px solid rgba(239,68,68,0.4)', color: '#ef4444' }}
        >
          <Icon name="ban" size={14} stroke={2.4} /> 退出登录
        </button>
      </div>
    </aside>
  );
}
