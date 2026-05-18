from __future__ import annotations
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    mode: str = Field(default="lab", description="当前独立项目固定使用 lab / Dify RAG 链路")
    question: str = Field(min_length=1, max_length=4000)

class Citation(BaseModel):
    kb_id: str
    title: str
    source_title: str = ""
    source_org: str = ""
    source_url: str = ""
    risk_level: str = ""
    snippet: str = ""
    score: float = 0.0

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
    citations: list[Citation] = Field(default_factory=list)

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
