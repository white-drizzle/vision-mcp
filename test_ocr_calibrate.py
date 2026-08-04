import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import ocr_extract


def test_engine_singleton_reused():
    e1 = ocr_extract._get_engine()
    e2 = ocr_extract._get_engine()
    assert e1 is e2


def test_guess_mime():
    assert ocr_extract._guess_mime("x.png", b"\x89PNG\r\n") == "image/png"
    assert ocr_extract._guess_mime("x.jpg", b"\xff\xd8\xff\xe0") == "image/jpeg"


def _load_benchmark_png():
    """从会话日志提取基准图（P2 宽谱热源对比页）。"""
    import base64
    log_dir = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(log_dir):
        raise FileNotFoundError("no claude projects dir")
    logs = []
    for root, _dirs, files in os.walk(log_dir):
        for fn in files:
            if fn.endswith(".jsonl"):
                p = os.path.join(root, fn)
                try:
                    if os.path.getmtime(p) > 0:
                        logs.append((os.path.getmtime(p), p))
                except OSError:
                    pass
    logs.sort(reverse=True)
    for _t, p in logs:
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"image"' not in line or '"base64"' not in line:
                    continue
                import re
                m = re.search(r'"data":"(iVBOR[^"]+)"', line)
                if not m:
                    continue
                try:
                    return base64.b64decode(m.group(1))
                except Exception:
                    continue
    raise FileNotFoundError("no pasted image found")


def test_benchmark_ocr_extracts_truth():
    png = _load_benchmark_png()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png)
        tmp = f.name
    try:
        items = ocr_extract.ocr_extract(tmp, min_score=0.7)
        assert items, "OCR should find text"
        joined = "\n".join(it["text"] for it in items)
        # 色标关键数字必须出现（视觉模型之前读错的 262.31 / 266.15）
        assert "262.31" in joined, "colorbar value 262.31 must be OCR'd"
        assert "266.15" in joined, "colorbar value 266.15 must be OCR'd"
        # 表格数值
        assert "0.7-1.5" in joined, "table wavelength value"
        assert "20-22" in joined, "table heating rate"
        # JSON 构建可运行
        import json
        j = ocr_extract.ocr_to_json(items)
        assert isinstance(j, dict)
        json.dumps(j)  # must be serializable
    finally:
        os.remove(tmp)


def test_benchmark_scale_columns():
    png = _load_benchmark_png()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png)
        tmp = f.name
    try:
        items = ocr_extract.ocr_extract(tmp, min_score=0.9)
        scales = ocr_extract._build_colorbar_scales(items or [])
        # 应识别出至少一列竖直数字（色标）
        assert any(scales.values()), f"expected colorbar columns, got {scales}"
    finally:
        os.remove(tmp)

