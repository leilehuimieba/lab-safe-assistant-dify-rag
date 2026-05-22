import type { Citation, DemoMetaResponse, StatsResponse } from '../types/api';
import CitationCard from './CitationCard';

interface Props {
  meta: DemoMetaResponse | null;
  health: boolean;
  loading: boolean;
  stats: StatsResponse | null;
  lastSearchCitations: Citation[];
}

function statusDot(s: string): string {
  if (/pass|stable|ok|ready/i.test(s)) return 'dot-ok';
  if (/warn|degrad|partial/i.test(s)) return 'dot-warn';
  if (/fail|down|error|miss/i.test(s)) return 'dot-err';
  return 'dot-ok';
}

export default function MetaPanel({ meta, health, loading, stats, lastSearchCitations }: Props) {
  if (loading || !meta) {
    return (
      <aside className="metabar">
        {[0, 1, 2].map((i) => (
          <div className="meta-card" key={i}>
            <div className="meta-card-head"><h3>系统信息</h3></div>
            <div className="meta-card-body">
              {[0, 1, 2, 3].map((j) => (
                <div className="meta-row" key={j}>
                  <span className="sk" style={{ width: 70, height: 12 }} />
                  <span className="sk" style={{ width: 90, height: 12 }} />
                </div>
              ))}
            </div>
          </div>
        ))}
      </aside>
    );
  }

  return (
    <aside className="metabar">
      <div className="meta-card">
        <div className="meta-card-head"><h3>系统状态</h3></div>
        <div className="meta-card-body">
          <div className="meta-row">
            <span className="meta-label">健康检查</span>
            <span className="meta-value">
              <span className={`status-dot ${health ? 'dot-ok' : 'dot-err'}`} />
              {health ? '在线' : '离线'}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">应用版本</span>
            <span className="meta-value">{meta.app_version}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">对话通道</span>
            <span className="meta-value">{meta.chat_lane_lab}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">验收状态</span>
            <span className="meta-value">
              <span className={`status-dot ${statusDot(meta.acceptance_status)}`} />
              {meta.acceptance_status}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">稳定性</span>
            <span className="meta-value">
              <span className={`status-dot ${statusDot(meta.stability_status)}`} />
              {meta.stability_status}
            </span>
          </div>
          <div className="meta-row">
            <span className="meta-label">评测分</span>
            <span className="meta-value">{meta.formal_eval_score}</span>
          </div>
        </div>
      </div>

      <div className="meta-card">
        <div className="meta-card-head">
          <h3>知识库</h3>
          <span style={{ fontSize: 11, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
            {meta.knowledge_base_rows} 条
          </span>
        </div>
        <div className="kb-grid">
          <div className="kb-stat"><div className="v">{meta.knowledge_base_imported.toLocaleString()}</div><div className="l">已导入</div></div>
          <div className="kb-stat"><div className="v">{meta.knowledge_base_chunked.toLocaleString()}</div><div className="l">已切分</div></div>
          <div className="kb-stat"><div className="v">{meta.knowledge_base_external}</div><div className="l">外部来源</div></div>
          <div className="kb-stat">
            <div className="v">
              {((meta.knowledge_base_imported / Math.max(1, meta.knowledge_base_rows)) * 100).toFixed(1)}%
            </div>
            <div className="l">导入率</div>
          </div>
        </div>
      </div>

      <div className="meta-card">
        <div className="meta-card-head"><h3>服务配置</h3></div>
        <div className="meta-card-body">
          <div className="meta-row">
            <span className="meta-label">Demo 端口</span>
            <span className="meta-value">:{meta.demo_port}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">Dify Base</span>
            <span className="meta-value muted" style={{ fontSize: 11 }}>{meta.dify_base_url}</span>
          </div>
          <div className="meta-row">
            <span className="meta-label">App Key</span>
            <span className="meta-value">
              <span className={`status-dot ${meta.dify_app_key_configured ? 'dot-ok' : 'dot-err'}`} />
              {meta.dify_app_key_configured ? '已配置' : '未配置'}
            </span>
          </div>
        </div>
      </div>

      <div className="meta-card">
        <div className="meta-card-head"><h3>最近性能</h3></div>
        <div className="kb-grid">
          <div className="kb-stat">
            <div className="v">{stats?.recent_count ?? 0}</div>
            <div className="l">样本数</div>
          </div>
          <div className="kb-stat">
            <div className="v">{Math.round(stats?.recent_avg_ms ?? 0)}</div>
            <div className="l">平均 ms</div>
          </div>
          <div className="kb-stat">
            <div className="v">{Math.round(stats?.recent_p95_ms ?? 0)}</div>
            <div className="l">P95 ms</div>
          </div>
          <div className="kb-stat">
            <div className="v">{Math.round(stats?.recent_max_ms ?? 0)}</div>
            <div className="l">最大 ms</div>
          </div>
        </div>
      </div>

      {lastSearchCitations.length > 0 && (
        <div className="meta-card">
          <div className="meta-card-head">
            <h3>最近检索结果</h3>
            <span style={{ fontSize: 11, color: 'var(--text-3)' }}>{lastSearchCitations.length} 条</span>
          </div>
          <div style={{ padding: 10 }}>
            {lastSearchCitations.map((c, i) => (
              <CitationCard key={i} citation={c} />
            ))}
          </div>
        </div>
      )}
    </aside>
  );
}
