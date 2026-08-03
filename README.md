# vision-mcp

Give vision-less main models (like DeepSeek) the ability to **see images**, powered by Volcano Engine (Volcengine) Agent Plan's multimodal model through an OpenAI-compatible endpoint.

为无视觉主模型（如 DeepSeek）补上**读图能力**。后端视觉模型走火山引擎（Volcengine）Agent Plan 的多模态模型，OpenAI 兼容端点。

## Features / 功能

- **Image analysis** — local path / URL / base64 / data URL
  单张图分析 — 本地路径 / URL / base64 / data URL
- **HTML visual check** — render a webpage to a full-page screenshot (CDP, handles long pages), then analyze
  网页视觉检查 — 渲染整页截图（CDP，支持长页面）后分析
- **PPT analysis** — render slides to images via LibreOffice + pdftoppm, analyze layout
  PPT 分析 — 经 LibreOffice + pdftoppm 渲染成图后分析排版
- **PPT overlap detection** — double-checked: precise bounding-box coordinates (python-pptx) + visual cross-validation
  PPT 重叠检测 — 双保险：精确包围盒坐标（python-pptx）+ 视觉交叉验证

## Tools / 工具

| Tool 工具 | Input 输入 | Purpose 用途 |
|---|---|---|
| `analyze_image` | local path / URL / base64 / data URL | analyze a single image with a custom prompt |
| `describe_image` | same as above | quick generic description |
| `analyze_html` | URL / local HTML file / `data:` inline | webpage visual check (full-page CDP screenshot) |
| `analyze_ppt` | `.pptx` path + optional `page` | analyze one or all slide layouts |
| `check_ppt_overlap` | `.pptx` path | detect overlapping elements (coordinates + visual, double-checked) |

## Requirements / 依赖

### API
- **Volcengine Agent Plan** subscription with a valid `AUTH_TOKEN` (`ark-` prefix) from the Volcengine console.
- Endpoint (OpenAI-compatible): `https://ark.cn-beijing.volces.com/api/plan/v3`
- Default model: `doubao-seed-evolving` (override with `ARK_MODEL`; `kimi-k3` also works)

### Local tools
- **LibreOffice** — converts PPTX to PDF (`soffice --headless --convert-to pdf`). Windows path: `C:\Program Files\LibreOffice`. Install with `/qb`, not `/qn` (`/qn` triggers MSI transform failure 1603).
- **pdftoppm** (poppler) — converts PDF pages to PNG. Note output names are zero-padded (`page-01.png`); the code matches with glob.
- **python-pptx** — reads shape bounding boxes for overlap detection.

## Install / 安装

```bash
pip install "mcp>=1.2" curl_cffi python-pptx pillow
```

Set the API token via environment variable:

```bash
export ARK_AUTH_TOKEN="ark_xxxxxxxx"   # from Volcengine Agent Plan console
```

## Register with Claude Code / 注册到 Claude Code

Add to `~/.claude.json` → `mcpServers`:

```json
{
  "mcpServers": {
    "vision-mcp": {
      "type": "stdio",
      "command": "python",
      "args": ["/absolute/path/to/vision_mcp.py"],
      "env": {
        "ARK_AUTH_TOKEN": "ark_xxxxxxxx"
      }
    }
  }
}
```

> **Security / 安全**：the API token is passed only via the environment variable — no secrets are hardcoded in the code.
> API token 只经环境变量传入，代码中不硬编码任何密钥。

## Rate limiting / 限流

Continuous multi-page calls can trigger HTTP 429 `ServerOverloaded`. The all-pages mode already has a 4s inter-page delay plus automatic retry on 429/5xx (3 attempts, exponential backoff).

连续多页调用易触发 HTTP 429 ServerOverloaded。全部页模式已内置页间 4s 间隔 + 429/5xx 自动重试（3 次退避）。

## How overlap detection works / 重叠检测原理

1. **Coordinate check / 坐标检测**: python-pptx reads every shape's bounding box, computes pairwise rectangle intersections, reports overlapping pairs with exact area (pt²).
2. **Visual cross-validation / 视觉交叉验证**: overlapping pages are rendered and the vision model confirms whether the overlap is visually real or just bounding-box overlap with text padding.

Validated against a real 19-slide deck: 9 coordinate overlaps, of which 4 (slides 5/9/13/16) were real text overlaps and 5 were false positives — matching manual inspection.

## License

MIT
