import Icon from './Icon';

export default function Thinking() {
  return (
    <div className="msg ai">
      <div className="avatar">
        <Icon name="sparkles" size={14} stroke={2} />
      </div>
      <div className="bubble-wrap">
        <div className="who">
          实验室安全小助手 <time>正在思考…</time>
        </div>
        <div className="bubble" style={{ borderLeftColor: 'var(--primary-500)' }}>
          <div className="thinking">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        </div>
      </div>
    </div>
  );
}
