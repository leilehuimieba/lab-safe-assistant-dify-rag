import { useState } from 'react';
import type { ChatResponse } from '../types/api';
import Icon from './Icon';
import DecisionBadge from './DecisionBadge';
import RiskBadge from './RiskBadge';
import CitationCard from './CitationCard';
import Markdown from './Markdown';

export interface UserMsg {
  role: 'user';
  text: string;
  time: string;
}
export interface AiMsg {
  role: 'ai';
  time: string;
  resp: ChatResponse;
  userQuestion?: string;
}
export type Msg = UserMsg | AiMsg;

interface Props {
  msg: Msg;
  onFeedback?: (resp: ChatResponse, rating: 'useful' | 'not_useful', userQuestion?: string) => Promise<void>;
}

function getModelLabel(model?: string): string {
  if (model === 'local-fast-path') return '本地快速通道';
  if (model === 'dify-workflow') return 'Dify 主链路';
  if (model === 'rule-engine') return '规则引擎';
  if (model === 'fallback-rule-engine') return '结构化兜底';
  return model || '';
}

function getSourceHint(resp: ChatResponse): string {
  if (resp.timings?.cache_hit) return '安全缓存复用';
  if (resp.model === 'local-fast-path') return '本地知识直出';
  if (resp.model === 'dify-workflow') return '正式知识库主链路';
  if (resp.model === 'rule-engine') return '规则库直接判定';
  if (resp.model === 'fallback-rule-engine') return '规则+检索兜底';
  return '回答来源已标注';
}

export default function ChatMessage({ msg, onFeedback }: Props) {
  const [openCites, setOpenCites] = useState(false);
  const [feedbackState, setFeedbackState] = useState<'idle' | 'sending' | 'useful' | 'not_useful'>('idle');
  const [toast, setToast] = useState('');

  const showToast = (text: string) => {
    setToast(text);
    window.setTimeout(() => setToast(''), 2000);
  };

  if (msg.role === 'user') {
    return (
      <div className="msg user">
        <div className="avatar">我</div>
        <div className="bubble-wrap">
          <div className="who">
            我 <time>{msg.time}</time>
          </div>
          <div className="bubble">{msg.text}</div>
        </div>
      </div>
    );
  }

  const r = msg.resp;
  const dec = r.decision;
  const isEmergency = dec === 'emergency_redirect';
  const isBlocked = dec === 'rule_blocked';

  return (
    <div className="msg ai">
      <div className="avatar">
        <Icon name="sparkles" size={14} stroke={2} />
      </div>
      <div className="bubble-wrap">
        <div className="who">
          实验室安全小助手 <time>{msg.time}</time>
        </div>
        <div className={`bubble dec-${dec}`}>
          <div className="dec-row">
            <DecisionBadge decision={dec} model={r.model} />
            {r.risk_level ? <RiskBadge level={r.risk_level} /> : null}
            {r.matched_rule_id ? (
              <span
                className="badge"
                style={{
                  background: 'var(--surface-2)',
                  borderColor: 'var(--border)',
                  color: 'var(--text-2)',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                {r.matched_rule_id}
              </span>
            ) : null}
            <span style={{ flex: 1 }} />
            {r.model ? (
              <span className="badge model">
                <span className="b-dot" />
                {getModelLabel(r.model)}
              </span>
            ) : null}
            <span className="badge source">
              <span className="b-dot" />
              {getSourceHint(r)}
            </span>
            {r.model && r.model !== 'rule-engine' && r.model !== 'fallback-rule-engine' ? (
              <span className="badge source">
                首条依据 {r.citations?.[0]?.kb_id || 'N/A'}
              </span>
            ) : null}
          </div>

          {isEmergency && (
            <div className="emerg-cta">
              <div className="num">119</div>
              <div>
                <div className="label">这是紧急情况</div>
                <div className="sub">先撤离、再呼救，再回头阅读处置步骤</div>
              </div>
            </div>
          )}

          <Markdown source={r.answer} />

          {isBlocked && r.matched_rule_action && (
            <div className="block-callout">
              <Icon name="ban" size={14} />
              <div>
                此操作被规则引擎拦截：<code>{r.matched_rule_action}</code>
                {r.matched_rule_id ? (
                  <>
                    {' '}· 规则 <code>{r.matched_rule_id}</code>
                  </>
                ) : null}
              </div>
            </div>
          )}

          {r.low_confidence && r.low_confidence_reason && (
            <div className="lc-note">
              <Icon name="info" size={14} />
              <div>
                <strong>低置信度提示：</strong>
                {r.low_confidence_reason}。本回答仅供参考，请结合本单位 SOP 与安全员确认。
              </div>
            </div>
          )}

          <div
            style={{
              marginTop: 12,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: 12,
              flexWrap: 'wrap',
            }}
          >
            <div style={{ fontSize: 12, color: 'var(--text-3)' }}>
              响应耗时：<strong>{r.elapsed_ms || 0}ms</strong>
              {r.session_id ? (
                <>
                  {' '}· 会话 <code>{r.session_id.slice(0, 12)}</code>
                </>
              ) : null}
              {r.timings?.cache_hit ? (
                <>
                  {' '}· <strong style={{ color: 'var(--ok-600, #0a7f44)' }}>缓存命中</strong>
                </>
              ) : null}
              <div style={{ marginTop: 4 }}>
                检索 {r.timings?.retrieve_ms ?? 0}ms
                {' '}· 规则 {r.timings?.rule_ms ?? 0}ms
                {' '}· 缓存查询 {r.timings?.cache_lookup_ms ?? 0}ms
                {' '}· 上游 {r.timings?.upstream_ms ?? 0}ms
              </div>
            </div>
            {onFeedback ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, color: 'var(--text-3)' }}>这条回答有帮助吗？</span>
                <button
                  className="retry"
                  disabled={feedbackState === 'sending' || feedbackState === 'useful'}
                  onClick={async () => {
                    try {
                      setFeedbackState('sending');
                      await onFeedback(r, 'useful', msg.role === 'ai' ? msg.userQuestion : '');
                      setFeedbackState('useful');
                      showToast('反馈已提交，感谢！👍');
                    } catch {
                      setFeedbackState('idle');
                      showToast('提交失败，请重试');
                    }
                  }}
                >
                  {feedbackState === 'useful' ? '已记录 👍' : '有帮助'}
                </button>
                <button
                  className="retry"
                  disabled={feedbackState === 'sending' || feedbackState === 'not_useful'}
                  onClick={async () => {
                    try {
                      setFeedbackState('sending');
                      await onFeedback(r, 'not_useful', msg.role === 'ai' ? msg.userQuestion : '');
                      setFeedbackState('not_useful');
                      showToast('反馈已提交，感谢！👀');
                    } catch {
                      setFeedbackState('idle');
                      showToast('提交失败，请重试');
                    }
                  }}
                >
                  {feedbackState === 'not_useful' ? '已记录 👀' : '待改进'}
                </button>
              </div>
            ) : null}
          </div>

          {r.citations && r.citations.length > 0 && (
            <div className="cites">
              <button
                className={`cites-toggle ${openCites ? 'open' : ''}`}
                onClick={() => setOpenCites((v) => !v)}
              >
                <span className="chev">
                  <Icon name="chevron" size={12} />
                </span>
                {openCites ? '收起引用' : `展开引用 (${r.citations.length})`}
                <Icon name="book" size={12} />
              </button>
              {openCites && (
                <div className="cites-grid">
                  {r.citations.map((c, i) => (
                    <CitationCard key={i} citation={c} />
                  ))}
                </div>
              )}
            </div>
          )}
          {toast && (
            <div style={{
              position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
              background: '#0f172a', color: '#fff', padding: '10px 20px', borderRadius: 10,
              fontSize: 13, zIndex: 3000, boxShadow: '0 8px 30px rgba(0,0,0,0.2)',
              animation: 'msg-in 0.3s ease-out',
            }}>
              {toast}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
