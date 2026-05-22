// 与后端 FastAPI/Pydantic 模型严格对齐
export interface Citation {
  kb_id: string;
  title: string;
  source_title: string;
  source_org: string;
  source_url: string;
  risk_level: string;
  snippet: string;
  score: number;
}

export interface ChatRequest {
  mode: string;
  question: string;
  session_id?: string;
}

export type DecisionKind =
  | 'dify_answer'
  | 'dify_answer_guarded'
  | 'dify_low_confidence'
  | 'rule_blocked'
  | 'emergency_redirect'
  | 'need_more_info'
  | 'structured_fallback'
  | string;

export interface ChatResponse {
  answer: string;
  mode: string;
  model: string;
  decision: DecisionKind;
  risk_level: string;
  matched_rule_id: string;
  matched_rule_action: string;
  low_confidence: boolean;
  low_confidence_reason: string;
  followup_logged: boolean;
  elapsed_ms: number;
  session_id: string;
  citations: Citation[];
  timings: {
    total_ms: number;
    retrieve_ms: number;
    rule_ms: number;
    cache_lookup_ms: number;
    upstream_ms: number;
    cache_hit: boolean;
  };
}

export interface SearchResponse {
  query: string;
  count: number;
  citations: Citation[];
}

export interface DemoMetaResponse {
  app_version: string;
  chat_lane_lab: string;
  acceptance_status: string;
  formal_eval_score: string;
  stability_status: string;
  knowledge_base_rows: number;
  knowledge_base_imported: number;
  knowledge_base_chunked: number;
  knowledge_base_external: number;
  demo_port: string;
  dify_base_url: string;
  dify_app_key_configured: boolean;
}

export interface HealthResponse {
  ok: boolean;
  status: string;
  service?: string;
  kb_loaded?: number;
  dify_base_url?: string;
  dify_app_key_configured?: boolean;
  dify_reachable?: boolean;
  dify_error?: string;
  [k: string]: unknown;
}

export interface StatsResponse {
  recent_count: number;
  recent_avg_ms: number;
  recent_p50_ms: number;
  recent_p95_ms: number;
  recent_max_ms: number;
  recent_avg_upstream_ms: number;
  recent_p95_upstream_ms: number;
  recent_cached_count: number;
  recent_cache_hit_rate: number;
}

export interface FeedbackRequest {
  session_id: string;
  question: string;
  answer: string;
  rating: 'useful' | 'not_useful';
  comment?: string;
}
