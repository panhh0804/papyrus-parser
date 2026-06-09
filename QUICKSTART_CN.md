# 快速开始指南

## 1. 安装

```bash
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## 2. 测试

```bash
# 显示帮助
papyrus --help

# 解析 markdown 文件
papyrus README.md

# 解析并保存到文件
papyrus test_sample.md -o output.md

# 解析为 JSON
papyrus test_sample.md --format json
```

## 3. 在 AI Agent 中使用

### Claude Code
```javascript
const { execSync } = require('child_process');

// 使用完整路径到 venv
const result = execSync('$HOME/papyrus/venv/bin/papyrus homework.pdf').toString();
console.log(result);
```

### Codex / Kimi (Python)
```python
import subprocess

result = subprocess.run(
    ['$HOME/papyrus/venv/bin/papyrus', 'homework.pdf'],
    capture_output=True,
    text=True
)
print(result.stdout)
```

## 4. 全局配置（可选）

在你的 shell 配置文件添加（`~/.zshrc` 或 `~/.bashrc`）：

```bash
export PATH="$HOME/papyrus/venv/bin:$PATH"
```

然后你可以直接使用：
```bash
papyrus homework.pdf
```

## 5. 高级：对扫描件使用重路径解析器

```bash
# 自动检测复杂 PDF 并使用 marker
papyrus scanned_document.pdf

# 强制使用重路径
papyrus document.pdf --use-heavy

# 详细输出（查看使用了哪个解析器）
papyrus document.pdf -v
```

## 支持的文件类型

- **PDF**（文字版和扫描版） ✅
- **DOCX** ✅
- **Markdown** ✅
- **纯文本** ✅
- **HTML** ✅

## 输出格式

- **Markdown**（默认）：清晰、易读
- **JSON**：结构化数据含元数据

```bash
# Markdown 输出
papyrus file.pdf

# JSON 输出
papyrus file.pdf --format json
```

---

**就这样！** 现在你有了一个跨平台的 AI Agent 文档解析器。

更多详情，请查看：
- [README.md](README.md) - 完整文档
- [USAGE_WITH_AGENTS.md](USAGE_WITH_AGENTS.md) - 集成指南
