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
}
export type Msg = UserMsg | AiMsg;

interface Props {
  msg: Msg;
}

export default function ChatMessage({ msg }: Props) {
  const [openCites, setOpenCites] = useState(false);

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
            <DecisionBadge decision={dec} />
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
                {r.model}
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
        </div>
      </div>
    </div>
  );
}
