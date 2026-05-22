from __future__ import annotations
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    mode: str = Field(default="lab", description="当前独立项目固定使用 lab / Dify RAG 链路")
    question: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="", description="多轮对话会话 ID，留空则每次新建会话")

class Citation(BaseModel):
    kb_id: str
    title: str
    source_title: str = ""
    source_org: str = ""
    source_url: str = ""
    risk_level: str = ""
    snippet: str = ""
    score: float = 0.0

class TimingBreakdown(BaseModel):
    total_ms: int = 0
    retrieve_ms: int = 0
    rule_ms: int = 0
    cache_lookup_ms: int = 0
    upstream_ms: int = 0
    cache_hit: bool = False

class ChatResponse(BaseModel):
    answer: str
    mode: str
    model: str
    decision: str
    risk_level: str = ""
    matched_rule_id: str = ""
    matched_rule_action: str = ""
    low_confidence: bool = False
    low_confidence_reason: str = ""
    followup_logged: bool = False
    elapsed_ms: int = 0
    session_id: str = ""
    citations: list[Citation] = Field(default_factory=list)
    timings: TimingBreakdown = Field(default_factory=TimingBreakdown)

class FeedbackRequest(BaseModel):
    session_id: str = ""
    question: str = ""
    answer: str = ""
    rating: str = Field(default="", description="useful / not_useful")
    comment: str = Field(default="", max_length=500)

class StatsResponse(BaseModel):
    recent_count: int
    recent_avg_ms: float
    recent_p50_ms: float
    recent_p95_ms: float
    recent_max_ms: float
    recent_avg_upstream_ms: float = 0
    recent_p95_upstream_ms: float = 0
    recent_cached_count: int = 0
    recent_cache_hit_rate: float = 0

class DemoMetaResponse(BaseModel):
    app_version: str
    chat_lane_lab: str
    acceptance_status: str
    formal_eval_score: str
    stability_status: str
    knowledge_base_rows: int
    knowledge_base_imported: int
    knowledge_base_chunked: int = 0
    knowledge_base_external: int = 0
    demo_port: str
    dify_base_url: str
    dify_app_key_configured: bool
