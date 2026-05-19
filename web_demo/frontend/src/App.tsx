import { useEffect, useRef, useState } from 'react';
import { useChat, useMetaAndHealth, useSearch } from './hooks/useApi';
import type { ChatResponse, Citation } from './types/api';
import ChatMessage, { type Msg } from './components/ChatMessage';
import Sidebar from './components/Sidebar';
import MetaPanel from './components/MetaPanel';
import { Topbar, Footbar } from './components/StatusBar';
import ChatInput from './components/ChatInput';
import Thinking from './components/Thinking';
import EmptyHero from './components/EmptyHero';
import ChatHeader from './components/ChatHeader';
import Icon from './components/Icon';

function nowHHMM(): string {
  const d = new Date();
  return (
    d.getHours().toString().padStart(2, '0') +
    ':' +
    d.getMinutes().toString().padStart(2, '0')
  );
}

interface AppError {
  kind: 'backend' | 'network' | 'http';
  msg: string;
  lastQ?: string;
}

export default function App() {
  const { loading, error: metaError, meta, health } = useMetaAndHealth();
  const { send, busy } = useChat();
  const { search, busy: searchBusy } = useSearch();

  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [flashIdx, setFlashIdx] = useState(-1);
  const [error, setError] = useState<AppError | null>(null);
  const [lastSearchCitations, setLastSearchCitations] = useState<Citation[]>([]);

  const scrollRef = useRef<HTMLDivElement | null>(null);
  const composerRef = useRef<HTMLTextAreaElement | null>(null);

  // Lift backend connectivity failures into the inline alert.
  useEffect(() => {
    if (metaError) {
      setError({ kind: 'backend', msg: '后端服务未启动，请检查服务状态。' });
    }
  }, [metaError]);

  // Auto-scroll when messages or busy state changes.
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages.length, busy]);

  const focusComposer = () => {
    if (composerRef.current) {
      composerRef.current.focus();
      const v = composerRef.current.value;
      composerRef.current.setSelectionRange(v.length, v.length);
    }
  };

  const onPickQuick = (q: string, i: number) => {
    setInput(q);
    setFlashIdx(i);
    window.setTimeout(() => setFlashIdx(-1), 200);
    window.setTimeout(focusComposer, 0);
  };

  const submit = async () => {
    const q = input.trim();
    if (!q || busy || searchBusy) return;
    setError(null);
    setLastSearchCitations([]);
    const userMsg: Msg = { role: 'user', text: q, time: nowHHMM() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    try {
      const resp: ChatResponse = await send({ question: q, mode: 'lab' });
      setMessages((m) => [...m, { role: 'ai', time: nowHHMM(), resp }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : '网络请求失败';
      setError({ kind: 'network', msg: `请求失败：${msg}`, lastQ: q });
      setInput(q);
    }
  };

  const submitSearch = async () => {
    const q = input.trim();
    if (!q || busy || searchBusy) return;
    setError(null);
    const userMsg: Msg = { role: 'user', text: `【知识库检索】${q}`, time: nowHHMM() };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    try {
      const data = await search(q, 5);
      setLastSearchCitations(data.citations);
      // 构造一个伪 ChatResponse 用于显示检索结果
      const pseudoResp: ChatResponse = {
        answer: `本地知识库命中 **${data.count}** 条相关记录。`,
        mode: 'lab',
        model: 'kb-search',
        decision: 'dify_answer',
        risk_level: '',
        matched_rule_id: '',
        matched_rule_action: '',
        low_confidence: false,
        low_confidence_reason: '',
        followup_logged: false,
        citations: data.citations,
      };
      setMessages((m) => [...m, { role: 'ai', time: nowHHMM(), resp: pseudoResp }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : '检索失败';
      setError({ kind: 'network', msg: `检索失败：${msg}`, lastQ: q });
      setInput(q);
    }
  };

  const newChat = () => {
    setMessages([]);
    setInput('');
    setError(null);
    setLastSearchCitations([]);
  };

  const history = messages
    .filter((m): m is Extract<Msg, { role: 'user' }> => m.role === 'user')
    .slice(-5)
    .reverse()
    .map((m) => m.text);

  const userTurns = messages.filter((m) => m.role === 'user').length;

  return (
    <div className={`app ${loading ? 'loading-fade' : 'loaded'}`}>
      <Topbar health={health} healthChecked={!loading} />
      <Sidebar onPick={onPickQuick} onNew={newChat} history={history} flashIdx={flashIdx} />

      <main className="main">
        <ChatHeader count={userTurns} />

        <div className="chat-scroll" ref={scrollRef}>
          <div className="chat-stream">
            {error && (
              <div className={`alert ${error.kind === 'backend' ? 'err' : 'warn'}`}>
                <span className="a-icon"><Icon name="alert" size={16} /></span>
                <div>
                  <div className="a-title">
                    {error.kind === 'backend' ? '服务连接失败' : '网络请求异常'}
                  </div>
                  <div className="a-body">{error.msg}</div>
                </div>
                {error.kind !== 'backend' && (
                  <button
                    className="retry"
                    onClick={() => {
                      setError(null);
                      if (error.lastQ) setInput(error.lastQ);
                    }}
                  >
                    重试
                  </button>
                )}
              </div>
            )}

            {messages.length === 0 && !error && <EmptyHero onPick={onPickQuick} />}

            {messages.map((m, i) => (
              <ChatMessage key={i} msg={m} />
            ))}

            {busy && <Thinking />}
          </div>
        </div>

        <ChatInput
          ref={composerRef}
          value={input}
          onChange={setInput}
          onSubmit={submit}
          onSearch={submitSearch}
          busy={busy}
          searchBusy={searchBusy}
        />
      </main>

      <MetaPanel meta={meta} health={health} loading={loading} lastSearchCitations={lastSearchCitations} />
      <Footbar meta={meta} />
    </div>
  );
}
