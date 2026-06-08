English | [中文](#中文)

---

# Papyrus

**Stop installing parsing libraries every time your AI agent reads a document.**

Papyrus is a universal document parser designed for Claude Code, Codex, Kimi, and other AI assistants. It solves the most frustrating problem with document handling in agents: **every time an agent encounters a PDF or presentation, it searches for a library, discovers nothing is installed, runs `pip install`, and wastes 10+ seconds just to parse one file.**

With Papyrus, the tool is **already installed and globally available**. Your agents parse documents instantly.

## The Problem We Solve

Every time an AI agent tries to read a document:

❌ **Before Papyrus**:
1. Agent detects a `.pdf` file
2. Agent runs `pip install pymupdf` (or PyPDF2, or pdfplumber)
3. Waits 10-30 seconds for installation
4. Conflicts with other versions already installed
5. Finally parses the document

```
Total time: 10-30+ seconds for ONE document
```

✅ **With Papyrus**:
1. Agent runs: `papyrus document.pdf`
2. Document is parsed instantly
3. Done.

```
Total time: 100-500ms for most documents
```

## Features

- 🚀 **Zero Installation Overhead** — Pre-installed, globally available, just call `papyrus`
- ⚡ **Smart Routing** — Automatically chooses fast parsing (milliseconds) or OCR (for scanned documents)
- 📄 **Multi-Format Support** — PDF, PPTX, DOCX, Word, HTML, Markdown, plain text
- 🔬 **Optional OCR** — Heavy path with marker for scanned documents and complex tables
- 🌍 **Cross-Platform** — Works with Claude Code, Codex, Kimi, and any tool that runs shell commands
- 🧠 **AI-Agent Friendly** — Designed specifically for AI assistant workflows

## Quick Start

### Installation

Choose the guide for your operating system:

#### macOS

1. **Install Tesseract** (required for OCR support):
```bash
brew install tesseract
```

2. **Clone and install Papyrus**:
```bash
git clone https://github.com/yourusername/papyrus.git ~/papyrus
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

3. **Add to PATH** (optional, for system-wide access):
```bash
# Add this line to ~/.zshrc (or ~/.bash_profile for older systems)
export PATH="$HOME/papyrus/venv/bin:$PATH"

# Reload shell
source ~/.zshrc
```

4. **Verify installation**:
```bash
papyrus --help
```

#### Linux (Ubuntu/Debian)

1. **Install system dependencies**:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libmagic1 python3-venv
```

2. **Clone and install Papyrus**:
```bash
git clone https://github.com/yourusername/papyrus.git ~/papyrus
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

3. **Add to PATH** (optional, for system-wide access):
```bash
# Add this line to ~/.bashrc or ~/.zshrc
export PATH="$HOME/papyrus/venv/bin:$PATH"

# Reload shell
source ~/.bashrc  # or source ~/.zshrc
```

4. **Verify installation**:
```bash
papyrus --help
```

#### Windows

1. **Install Tesseract**:
   - Download the installer: https://github.com/UB-Mannheim/tesseract/wiki
   - Run `tesseract-ocr-w64-setup-v5.x.x.exe`
   - Note the installation path (e.g., `C:\Program Files\Tesseract-OCR`)

2. **Install Python dependencies**:
```cmd
# Open Command Prompt or PowerShell
git clone https://github.com/yourusername/papyrus.git %USERPROFILE%\papyrus
cd %USERPROFILE%\papyrus
python -m venv venv
venv\Scripts\activate
pip install -e .
```

3. **Configure Tesseract** (Windows only):
```python
# Create or edit: %USERPROFILE%\papyrus\papyrus\tesseract_config.py
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

4. **Add to PATH** (optional):
   - Press `Win + X` and select "System"
   - Click "Advanced system settings"
   - Click "Environment Variables"
   - Add `%USERPROFILE%\papyrus\venv\Scripts` to PATH
   - Restart your terminal

5. **Verify installation**:
```cmd
papyrus --help
```

### Troubleshooting Installation

| Issue | Solution |
|-------|----------|
| `command not found: papyrus` | Activate venv: `source venv/bin/activate` or reload PATH |
| `tesseract: command not found` | Install Tesseract for your OS (see above) |
| ImportError: No module named `pytesseract` | Reinstall: `pip install -e .` |
| (Windows) Tesseract not found | Update `tesseract_config.py` with correct path |
| ModuleNotFoundError: No module named 'magic' | Linux: `sudo apt-get install libmagic1` |

### Usage

```bash
# Parse PDF to markdown (auto-select strategy)
papyrus homework.pdf

# Output as JSON (with metadata)
papyrus document.pdf --format json

# Save to file
papyrus report.pdf -o result.md

# Force OCR for scanned documents
papyrus scanned_exam.pdf --use-heavy

# Verbose output (shows routing decision)
papyrus document.pdf -v
```

## Supported Formats

| Format | Support | Notes |
|--------|---------|-------|
| **PDF** | ✅ Full | Text-based and scanned (with OCR) |
| **PPTX** | ✅ Full | PowerPoint presentations |
| **DOCX** | ✅ Full | Microsoft Word documents |
| **XLSX** | ✅ Full | Excel spreadsheets (converted to Markdown tables) |
| **HTML** | ✅ Full | Web pages and HTML files |
| **Markdown** | ✅ Full | `.md`, `.markdown` files |
| **Plain Text** | ✅ Full | `.txt`, `.text` files |
| **PPT** | ⚠️ Unsupported | Use PPTX instead (convert with Office) |
| **XLS** | ⚠️ Limited | Old Excel format; use XLSX |

## How It Works

### Smart Routing

Papyrus analyzes your document and automatically chooses the right parser:

**Fast Path** (default for most documents):
- Uses `pymupdf4llm` (PDFs) and `markitdown` (other formats)
- Speed: ~100ms per document
- No ML models needed
- Minimal dependencies

**Heavy Path** (for complex/scanned documents):
- Uses `marker` with OCR
- Speed: 5-30 seconds depending on size
- Best for scanned PDFs, complex tables, formulas
- First run downloads models (~500MB)

```
Decision Logic:
- Simple PDF? → Fast path
- Scanned PDF? → Heavy path (OCR)
- Complex layout? → Heavy path
- PPTX/DOCX? → Always fast path
```

### Use Case: Claude Code Agent Reading Documents

**Without Papyrus**:
```typescript
// Agent starts reading a PDF...
const fs = require('fs');
const { execSync } = require('child_process');

// "I need to read this PDF"
execSync('pip install pymupdf', {encoding: 'utf-8'}); // ⏳ Wait 15s
// Finally parse...
```

**With Papyrus**:
```typescript
// Agent starts reading a PDF...
const fs = require('fs');
const { execSync } = require('child_process');

// "I need to read this PDF"
const content = execSync('papyrus document.pdf', {encoding: 'utf-8'}); // ⚡ Instant
// Already have the content
```

## Use in Your AI Agents

### Claude Code
```javascript
const { execSync } = require('child_process');

function parseDocument(filePath) {
  const result = execSync(`papyrus "${filePath}"`, {
    encoding: 'utf-8',
    maxBuffer: 50 * 1024 * 1024,
  });
  return result;
}
```

### Codex / Kimi (Python)
```python
import subprocess
import json

def parse_document(file_path: str):
    result = subprocess.run(
        ['papyrus', file_path, '--format', 'json'],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

### As a Bash One-Liner
```bash
papyrus homework.pdf | head -50
```

## Configuration

### Global System Instructions

Papyrus is automatically injected into:
- **Claude Code** — `~/.claude/CLAUDE.md`
- **Codex** — `~/.codex/skills/papyrus/SKILL.md`
- **Kimi Code** — `~/.kimi-code/skills/papyrus/SKILL.md`

Your agents will automatically know to use Papyrus when reading documents.

## Performance Characteristics

| Operation | Fast Path | Heavy Path |
|-----------|-----------|------------|
| Simple PDF | 50-100ms | 2-5s (model load) |
| PPTX | 100-200ms | N/A |
| DOCX | 50-100ms | N/A |
| Scanned PDF | ❌ Fails | 10-30s (OCR) |
| Complex tables | ⚠️ Ok | ✅ Better |

**First Run Note**: Heavy path downloads ~500MB of models on first use. Subsequent runs are much faster.

## Examples

### Example 1: Quick Document Preview
```bash
# Agent needs to check if a PDF is relevant
papyrus research_paper.pdf | head -100
```

### Example 2: Structured Data Extraction
```bash
# Extract presentation as JSON
papyrus slides.pptx --format json > slides_data.json
```

### Example 3: Scanned Document Processing
```bash
# First try (fast)
papyrus scanned_form.pdf

# If no text output, use OCR
papyrus scanned_form.pdf --use-heavy
```

### Example 4: Multi-Document Processing
```bash
# Process multiple files
for file in *.pdf; do
  papyrus "$file" -o "${file%.pdf}.md"
done
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty output | PDF is scanned (no text) | Use `papyrus <file> --use-heavy` |
| Garbled text | Wrong parser chosen | Check with `papyrus <file> -v` |
| Very slow | Heavy path running unnecessarily | Use `papyrus <file> --use-fast` |
| "Command not found" | Not in PATH | Source `~/.zshrc` or use full path |
| ImportError | Missing optional dependencies | `pip install 'papyrus[heavy]'` |

## Installation Options

### Basic (Fast Path Only)
```bash
pip install papyrus
```

### With Heavy Path Support (OCR)
```bash
pip install 'papyrus[heavy]'
# Or manually:
pip install papyrus marker-pdf
```

### From Source
```bash
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** — 5-minute setup guide
- **[USAGE_WITH_AGENTS.md](USAGE_WITH_AGENTS.md)** — Integration guide for specific tools
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** — Technical architecture

## License

MIT

**Dependencies**: This tool depends on several packages with different licenses. Most important:
- `pymupdf4llm` — AGPL-3.0
- `markitdown` — MIT
- `marker` (optional heavy path) — GPL-3.0 + RAIL-M (free for research and orgs < $2M revenue/funding)

If using heavy path in production, verify compliance with the marker licenses.

## Contributing

Issues, feature requests, and PRs welcome at https://github.com/yourusername/papyrus

---

<a name="中文"></a>

# Papyrus

**停止每次读文档都装库。**

Papyrus 是为 Claude Code、Codex、Kimi 等 AI 助手设计的通用文档解析器。它解决 AI Agent 文档处理中最痛苦的问题：**每当 Agent 遇到 PDF 或演示文稿，它都会搜索库、发现没装、运行 `pip install`、浪费 10+ 秒才能解析一个文件。**

用 Papyrus，工具**已经装好了，全局可用**。你的 Agent 秒速解析文档。

## 问题：Agent 读文件每次都装库

每次 AI Agent 尝试读取文档：

❌ **没有 Papyrus**:
1. Agent 检测到 `.pdf` 文件
2. Agent 运行 `pip install pymupdf`（或 PyPDF2、pdfplumber）
3. 等待 10-30 秒安装
4. 与其他已装版本冲突
5. 最后才开始解析

```
总耗时：10-30+ 秒（只是读一个文件）
```

✅ **有 Papyrus**:
1. Agent 运行：`papyrus document.pdf`
2. 文档秒速解析
3. 完毕

```
总耗时：100-500ms（大多数文档）
```

## 特性

- 🚀 **零安装开销** — 预装、全局可用、直接调用 `papyrus`
- ⚡ **智能路由** — 自动选择快速解析（毫秒）或 OCR（扫描件）
- 📄 **多格式支持** — PDF、PPTX、DOCX、Word、HTML、Markdown、纯文本
- 🔬 **可选 OCR** — 重路径用 marker 处理扫描件和复杂表格
- 🌍 **跨工具** — 支持 Claude Code、Codex、Kimi，任何能执行 shell 命令的工具
- 🧠 **Agent 友好** — 为 AI 助手工作流设计

## 快速开始

### 安装

根据你的操作系统选择对应的安装指南：

#### macOS

1. **安装 Tesseract**（OCR 支持必需）：
```bash
brew install tesseract
```

2. **克隆并安装 Papyrus**：
```bash
git clone https://github.com/yourusername/papyrus.git ~/papyrus
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

3. **添加到 PATH**（可选，全局可用）：
```bash
# 在 ~/.zshrc（或旧版系统的 ~/.bash_profile）末尾添加
export PATH="$HOME/papyrus/venv/bin:$PATH"

# 重新加载 shell
source ~/.zshrc
```

4. **验证安装**：
```bash
papyrus --help
```

#### Linux（Ubuntu/Debian）

1. **安装系统依赖**：
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libmagic1 python3-venv
```

2. **克隆并安装 Papyrus**：
```bash
git clone https://github.com/yourusername/papyrus.git ~/papyrus
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

3. **添加到 PATH**（可选，全局可用）：
```bash
# 在 ~/.bashrc 或 ~/.zshrc 末尾添加
export PATH="$HOME/papyrus/venv/bin:$PATH"

# 重新加载 shell
source ~/.bashrc  # 或 source ~/.zshrc
```

4. **验证安装**：
```bash
papyrus --help
```

#### Windows

1. **安装 Tesseract**：
   - 下载安装程序：https://github.com/UB-Mannheim/tesseract/wiki
   - 运行 `tesseract-ocr-w64-setup-v5.x.x.exe`
   - 记下安装路径（例如 `C:\Program Files\Tesseract-OCR`）

2. **安装 Python 依赖**：
```cmd
# 打开命令提示符或 PowerShell
git clone https://github.com/yourusername/papyrus.git %USERPROFILE%\papyrus
cd %USERPROFILE%\papyrus
python -m venv venv
venv\Scripts\activate
pip install -e .
```

3. **配置 Tesseract**（仅 Windows）：
```python
# 创建或编辑：%USERPROFILE%\papyrus\papyrus\tesseract_config.py
import pytesseract
pytesseract.pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

4. **添加到 PATH**（可选）：
   - 按 `Win + X` 选择"系统"
   - 点击"高级系统设置"
   - 点击"环境变量"
   - 将 `%USERPROFILE%\papyrus\venv\Scripts` 添加到 PATH
   - 重启终端

5. **验证安装**：
```cmd
papyrus --help
```

### 安装故障排除

| 问题 | 解决方案 |
|------|---------|
| `command not found: papyrus` | 激活虚拟环境：`source venv/bin/activate` 或重新加载 PATH |
| `tesseract: command not found` | 为你的系统安装 Tesseract（见上）|
| ImportError: No module named `pytesseract` | 重新安装：`pip install -e .` |
| (Windows) Tesseract 未找到 | 用正确路径更新 `tesseract_config.py` |
| ModuleNotFoundError: No module named 'magic' | Linux：`sudo apt-get install libmagic1` |

### 使用

```bash
# 解析 PDF 为 Markdown（自动选择策略）
papyrus homework.pdf

# 输出 JSON（含元数据）
papyrus document.pdf --format json

# 保存到文件
papyrus report.pdf -o result.md

# 对扫描件使用 OCR
papyrus scanned_exam.pdf --use-heavy

# 详细输出（显示路由决策）
papyrus document.pdf -v
```

## 支持的格式

| 格式 | 支持 | 备注 |
|------|------|------|
| **PDF** | ✅ 完全 | 文字版和扫描版（含 OCR） |
| **PPTX** | ✅ 完全 | PowerPoint 演示文稿 |
| **DOCX** | ✅ 完全 | Word 文档 |
| **XLSX** | ✅ 完全 | Excel 电子表格（转为 Markdown 表格） |
| **HTML** | ✅ 完全 | 网页和 HTML 文件 |
| **Markdown** | ✅ 完全 | `.md`、`.markdown` 文件 |
| **纯文本** | ✅ 完全 | `.txt`、`.text` 文件 |
| **PPT** | ⚠️ 不支持 | 用 PPTX（用 Office 转换） |
| **XLS** | ⚠️ 有限 | 旧版 Excel；建议用 XLSX |

## 工作原理

### 智能路由

Papyrus 分析你的文档，自动选择合适的解析器：

**快路径**（大多数文档）：
- 用 `pymupdf4llm`（PDF）和 `markitdown`（其他格式）
- 速度：~100ms 每个文档
- 无需 ML 模型
- 依赖最少

**重路径**（复杂/扫描文档）：
- 用 `marker` + OCR
- 速度：5-30 秒（取决于大小）
- 最适合扫描 PDF、复杂表格、数学公式
- 首次运行下载模型（~500MB）

```
决策逻辑：
- 简单 PDF？ → 快路径
- 扫描 PDF？ → 重路径（OCR）
- 复杂排版？ → 重路径
- PPTX/DOCX？ → 总是快路径
```

### 用例：Claude Code Agent 读文档

**没有 Papyrus**:
```typescript
// Agent 开始读 PDF...
const fs = require('fs');
const { execSync } = require('child_process');

// "我需要读这个 PDF"
execSync('pip install pymupdf', {encoding: 'utf-8'}); // ⏳ 等 15 秒
// 最后才开始解析...
```

**有 Papyrus**:
```typescript
// Agent 开始读 PDF...
const fs = require('fs');
const { execSync } = require('child_process');

// "我需要读这个 PDF"
const content = execSync('papyrus document.pdf', {encoding: 'utf-8'}); // ⚡ 秒速
// 已经有内容了
```

## 在 AI Agent 中使用

### Claude Code
```javascript
const { execSync } = require('child_process');

function parseDocument(filePath) {
  const result = execSync(`papyrus "${filePath}"`, {
    encoding: 'utf-8',
    maxBuffer: 50 * 1024 * 1024,
  });
  return result;
}
```

### Codex / Kimi（Python）
```python
import subprocess
import json

def parse_document(file_path: str):
    result = subprocess.run(
        ['papyrus', file_path, '--format', 'json'],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

### 命令行一行命令
```bash
papyrus homework.pdf | head -50
```

## 配置

### 全局系统指令

Papyrus 已自动注入到：
- **Claude Code** — `~/.claude/CLAUDE.md`
- **Codex** — `~/.codex/skills/papyrus/SKILL.md`
- **Kimi Code** — `~/.kimi-code/skills/papyrus/SKILL.md`

你的 Agent 会自动知道读文件时用 Papyrus。

## 性能指标

| 操作 | 快路径 | 重路径 |
|------|-------|-------|
| 简单 PDF | 50-100ms | 2-5s（模型加载） |
| PPTX | 100-200ms | N/A |
| DOCX | 50-100ms | N/A |
| 扫描 PDF | ❌ 失败 | 10-30s（OCR） |
| 复杂表格 | ⚠️ 一般 | ✅ 更好 |

**首次运行提示**：重路径首次运行下载 ~500MB 模型。后续运行快得多。

## 示例

### 示例 1：快速预览文档
```bash
# Agent 需要检查 PDF 是否相关
papyrus research_paper.pdf | head -100
```

### 示例 2：结构化数据提取
```bash
# 提取演示文稿为 JSON
papyrus slides.pptx --format json > slides_data.json
```

### 示例 3：扫描文档处理
```bash
# 先试试（快）
papyrus scanned_form.pdf

# 如果没有文本，用 OCR
papyrus scanned_form.pdf --use-heavy
```

### 示例 4：批量处理文档
```bash
# 处理多个文件
for file in *.pdf; do
  papyrus "$file" -o "${file%.pdf}.md"
done
```

## 故障排除

| 问题 | 原因 | 解决 |
|------|------|------|
| 空白输出 | PDF 是扫描件（无文本） | 用 `papyrus <file> --use-heavy` |
| 乱码文本 | 解析器选择错误 | 用 `papyrus <file> -v` 检查 |
| 非常慢 | 不必要地运行重路径 | 用 `papyrus <file> --use-fast` |
| "命令未找到" | 不在 PATH 中 | 重启 shell 或用完整路径 |
| ImportError | 缺少可选依赖 | `pip install 'papyrus[heavy]'` |

## 安装选项

### 基础版（仅快路径）
```bash
pip install papyrus
```

### 完全版（含 OCR）
```bash
pip install 'papyrus[heavy]'
# 或手动安装：
pip install papyrus marker-pdf
```

### 从源码
```bash
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## 文档

- **[QUICKSTART.md](QUICKSTART.md)** — 5 分钟快速开始
- **[USAGE_WITH_AGENTS.md](USAGE_WITH_AGENTS.md)** — 各工具集成指南
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** — 技术架构

## 许可

MIT

**依赖**：本工具依赖多个包，许可不同。最重要的：
- `pymupdf4llm` — AGPL-3.0
- `markitdown` — MIT
- `marker`（可选重路径）— GPL-3.0 + RAIL-M（研究和年营收 < $200 万的组织免费）

如在生产环境用重路径，请验证符合 marker 许可。

## 贡献

欢迎提 Issue、功能请求和 PR！https://github.com/yourusername/papyrus
