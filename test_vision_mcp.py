import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import vision_mcp


def test_chat_builds_thinking_payload_disabled():
    payload = vision_mcp._thinking_payload({}, True)
    assert payload["thinking"] == {"type": "enabled"}
    payload = vision_mcp._thinking_payload({}, False)
    assert payload["thinking"] == {"type": "disabled"}
    payload = vision_mcp._thinking_payload({}, None)
    assert "thinking" not in payload


def test_chat_default_thinking_preserved():
    payload = vision_mcp._thinking_payload({"model": "x"}, None)
    assert "thinking" not in payload


def test_resolve_thinking_scenarios():
    # detail 开思考，其余关
    assert vision_mcp._resolve_thinking(detail=True, thinking=None) is True
    assert vision_mcp._resolve_thinking(detail=False, thinking=None) is False
    # 显式覆盖优先
    assert vision_mcp._resolve_thinking(detail=True, thinking=False) is False
    assert vision_mcp._resolve_thinking(detail=False, thinking=True) is True
