from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

SESSION_TTL_SECONDS = 30 * 60  # 30 min
CLEANUP_INTERVAL = 300  # clean every 5 min

@dataclass
class Session:
    session_id: str
    conversation_id: str = ""
    history: list[dict[str, str]] = field(default_factory=list)
    created_at: float = 0.0
    last_active: float = 0.0

_store: dict[str, Session] = {}
_lock = threading.Lock()
_last_cleanup = time.monotonic()


def _maybe_cleanup() -> None:
    global _last_cleanup
    now = time.monotonic()
    if now - _last_cleanup < CLEANUP_INTERVAL:
        return
    _last_cleanup = now
    expired = [
        sid for sid, s in _store.items()
        if time.time() - s.last_active > SESSION_TTL_SECONDS
    ]
    for sid in expired:
        _store.pop(sid, None)


def get_or_create(session_id: str = "") -> Session:
    with _lock:
        _maybe_cleanup()
        now = time.time()
        if session_id and session_id in _store:
            s = _store[session_id]
            s.last_active = now
            return s
        new_id = f"sess_{uuid.uuid4().hex[:12]}"
        s = Session(session_id=new_id, created_at=now, last_active=now)
        _store[new_id] = s
        return s


def set_conversation_id(session_id: str, conversation_id: str) -> None:
    with _lock:
        if session_id in _store:
            _store[session_id].conversation_id = conversation_id
            _store[session_id].last_active = time.time()


def add_history(session_id: str, question: str, answer: str) -> None:
    with _lock:
        if session_id in _store:
            s = _store[session_id]
            s.history.append({"question": question, "answer": answer})
            if len(s.history) > 20:
                s.history = s.history[-20:]
            s.last_active = time.time()
