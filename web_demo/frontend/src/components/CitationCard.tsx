import type { Citation } from '../types/api';
import Icon from './Icon';
import ScoreBar from './ScoreBar';

interface Props {
  citation: Citation;
}

export default function CitationCard({ citation: c }: Props) {
  const inner = (
    <>
      <div className="cite-head">
        <div>
          <div className="cite-title">{c.title}</div>
          <div className="cite-meta">
            <span>{c.source_org}</span>
            {c.source_title ? (
              <>
                <span className="sep" />
                <span>{c.source_title}</span>
              </>
            ) : null}
            {c.risk_level ? (
              <>
                <span className="sep" />
                <span className={`badge risk-${c.risk_level}`} style={{ padding: '1px 7px', fontSize: 10 }}>
                  风险 {c.risk_level}
                </span>
              </>
            ) : null}
          </div>
        </div>
      </div>
      <div className="cite-snippet">{c.snippet}</div>
      <div className="cite-footer">
        <ScoreBar score={c.score} />
        {c.source_url ? (
          <span className="cite-link">
            打开来源 <Icon name="external" size={11} />
          </span>
        ) : (
          <span style={{ fontSize: 11, color: 'var(--text-3)' }}>无外链</span>
        )}
      </div>
    </>
  );

  if (c.source_url) {
    return (
      <a className="cite-card" href={c.source_url} target="_blank" rel="noopener noreferrer">
        {inner}
      </a>
    );
  }
  return <div className="cite-card">{inner}</div>;
}
