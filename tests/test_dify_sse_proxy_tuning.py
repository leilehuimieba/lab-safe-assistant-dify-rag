from web_demo.routers.chat_routes import (
    _dify_sse_chunk_size,
    _dify_sse_response_headers,
)


def test_sse_proxy_uses_low_latency_chunk_size_by_default(monkeypatch):
    monkeypatch.delenv("DIFY_SSE_PROXY_CHUNK_SIZE", raising=False)
    assert _dify_sse_chunk_size() == 1


def test_sse_proxy_chunk_size_is_bounded(monkeypatch):
    monkeypatch.setenv("DIFY_SSE_PROXY_CHUNK_SIZE", "0")
    assert _dify_sse_chunk_size() == 1

    monkeypatch.setenv("DIFY_SSE_PROXY_CHUNK_SIZE", "999999")
    assert _dify_sse_chunk_size() == 4096

    monkeypatch.setenv("DIFY_SSE_PROXY_CHUNK_SIZE", "invalid")
    assert _dify_sse_chunk_size() == 1


def test_sse_proxy_disables_middleware_compression_and_buffering():
    headers = _dify_sse_response_headers()
    assert headers["Cache-Control"] == "no-cache, no-transform"
    assert headers["X-Accel-Buffering"] == "no"
    assert headers["Content-Encoding"] == "identity"
