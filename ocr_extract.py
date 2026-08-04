"""RapidOCR 封装：惰性单例 + 置信度过滤 + 结构化 JSON 构建。

供 vision-mcp 做数字校准（视觉描述 + OCR 精确数字）。
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        from rapidocr_onnxruntime import RapidOCR
        _engine = RapidOCR()
    return _engine


def _guess_mime(path: str, data: bytes) -> str:
    mime_by_ext = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif", ".avif": "image/avif",
        ".bmp": "image/bmp",
    }
    mime_by_sig = {
        b"\x89PNG": "image/png", b"\xff\xd8": "image/jpeg", b"RIFF": "image/webp",
        b"GIF8": "image/gif", b"ftyp": "image/avif",
    }
    ext = os.path.splitext(path)[1].lower()
    if ext in mime_by_ext:
        return mime_by_ext[ext]
    for sig, m in mime_by_sig.items():
        if data[:8].startswith(sig):
            return m
    return "image/jpeg"


def ocr_extract(image_path: str, min_score: float = 0.7) -> Optional[list[dict]]:
    """识别图片文字，返回 [{box:[x4,y4], text, score, y_center}] 按 y 排序。

    引擎初始化失败返回 None（调用方回退纯视觉）。min_score 过滤低置信项。
    """
    try:
        engine = _get_engine()
    except Exception:
        return None
    try:
        result, _elapse = engine(image_path)
    except Exception:
        return None
    if not result:
        return []
    items = []
    for box, text, score in result:
        if score < min_score:
            continue
        ys = [p[1] for p in box]
        items.append({"box": box, "text": str(text), "score": float(score),
                      "y_center": sum(ys) / len(ys)})
    items.sort(key=lambda it: it["y_center"])
    return items


def _build_table(items: list[dict]) -> list[list[str]]:
    """按 y 聚类成行、按 x 聚类成列，重建表格。"""
    if not items:
        return []
    rows: list[list[dict]] = []
    for it in items:
        y = it["y_center"]
        placed = False
        for r in rows:
            if abs(r[0]["y_center"] - y) <= 12:
                r.append(it)
                placed = True
                break
        if not placed:
            rows.append([it])
    table = []
    for r in rows:
        r.sort(key=lambda it: min(p[0] for p in it["box"]))
        table.append([it["text"] for it in r])
    return table


def _build_colorbar_scales(items: list[dict]) -> dict[str, list[str]]:
    """识别竖直分布的数字列（x 相近、y 递增），返回 {left/right: [数字]}。"""
    import re
    numeric = [it for it in items if re.fullmatch(r"[\d.]+", it["text"].strip())]
    numeric.sort(key=lambda it: min(p[0] for p in it["box"]))
    cols: list[list[dict]] = []
    col_xs: list[float] = []  # 与 cols 平行，记录每列的代表 x
    for it in numeric:
        x = min(p[0] for p in it["box"])
        placed = False
        for i, c in enumerate(cols):
            if abs(col_xs[i] - x) <= 8:
                c.append(it)
                col_xs[i] = min(col_xs[i], x)
                placed = True
                break
        if not placed:
            cols.append([it])
            col_xs.append(x)
    scales: dict[str, list[str]] = {}
    order = sorted(range(len(cols)), key=lambda i: col_xs[i])[:2]
    for rank, i in enumerate(order):
        c = sorted(cols[i], key=lambda it: it["y_center"])
        key = "left" if rank == 0 else "right"
        scales[key] = [it["text"] for it in c]
    return scales


def ocr_to_json(items: list[dict]) -> dict[str, Any]:
    """把 OCR 结果构造成结构化 JSON（title/table/colorbar_scales/captions）。"""
    if not items:
        return {}
    # 标题：y 最小（页面最上）的文字
    title = items[0]["text"]
    # 表格：取中间 y 区间的项按行重建
    table = _build_table(items)
    scales = _build_colorbar_scales(items)
    # 图注：含关键词的行
    captions = [it["text"] for it in items
                if any(k in it["text"] for k in ("图", "Fig", "Source", "来源", "("))]
    return {
        "title": title,
        "table": table,
        "colorbar_scales": scales,
        "captions": captions,
    }
