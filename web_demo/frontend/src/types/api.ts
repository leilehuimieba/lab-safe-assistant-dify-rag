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
  citations: Citation[];
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
  [k: string]: unknown;
}
