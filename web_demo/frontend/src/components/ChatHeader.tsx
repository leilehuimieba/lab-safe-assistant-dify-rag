interface Props {
  count: number;
}

export default function ChatHeader({ count }: Props) {
  return (
    <div className="chat-header">
      <div className="chat-title">
        <h2>
          实验室安全问答
          {count > 0 && (
            <span style={{ fontSize: 12, color: 'var(--text-3)', fontWeight: 400 }}>
              {' '}· 已进行 {count} 轮对话
            </span>
          )}
        </h2>
        <span className="lane">Dify + RAG 智能问答链路</span>
      </div>
    </div>
  );
}
