import { forwardRef } from 'react';
import Icon from './Icon';

interface Props {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  onSearch: () => void;
  busy: boolean;
  searchBusy: boolean;
}

const ChatInput = forwardRef<HTMLTextAreaElement, Props>(function ChatInput(
  { value, onChange, onSubmit, onSearch, busy, searchBusy },
  ref,
) {
  const submit = () => {
    if (!value.trim() || busy || searchBusy) return;
    onSubmit();
  };

  const doSearch = () => {
    if (!value.trim() || busy || searchBusy) return;
    onSearch();
  };

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  const isBusy = busy || searchBusy;

  return (
    <div className="composer-wrap">
      <div className="composer">
        <textarea
          ref={ref}
          placeholder="输入你的实验室安全问题，例如：处理废试剂瓶有哪些注意事项？"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKey}
          rows={2}
        />
        <div className="composer-foot">
          <div className="hint">
            <kbd>↵</kbd> 发送 · <kbd>⇧ ↵</kbd> 换行
            <span style={{ color: 'var(--text-3)' }}>·</span>
            <span>实验室安全问答</span>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <button
              className="send-btn secondary"
              disabled={!value.trim() || isBusy}
              onClick={doSearch}
              title="仅检索本地知识库，不调用 AI"
            >
              {searchBusy ? '检索中…' : '仅检索'}
              {!searchBusy && <Icon name="book" size={13} stroke={2.2} />}
            </button>
            <button className="send-btn" disabled={!value.trim() || isBusy} onClick={submit}>
              {busy ? '等待响应…' : '发送'}
              {!busy && <Icon name="send" size={13} stroke={2.2} />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
});

export default ChatInput;
