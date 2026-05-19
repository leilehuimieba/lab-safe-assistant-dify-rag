import Icon from './Icon';
import { QUICK_QUESTIONS } from './quickQuestions';

interface SidebarProps {
  onPick: (q: string, i: number) => void;
  onNew: () => void;
  history: string[];
  flashIdx: number;
}

export default function Sidebar({ onPick, onNew, history, flashIdx }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sb-section">
        <button className="new-chat-btn" onClick={onNew}>
          <Icon name="plus" size={14} stroke={2.4} /> 新建对话
        </button>
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
              <div className="history-item" key={i}>
                <Icon name="history" size={12} />
                <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {h}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}
