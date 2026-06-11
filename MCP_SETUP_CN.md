# Papyrus MCP 服务器设置指南

Papyrus 可以作为 **MCP (Model Context Protocol) 服务器**运行，允许任何支持 MCP 的工具自动使用它进行文档解析。

## 什么是 MCP？

MCP 是一个标准化的协议，允许 AI 模型与外部工具交互。优势：
- ✅ **单一配置** - 所有工具共享一个配置（Claude、Codex、Kimi 等）
- ✅ **无需重复 SKILL.md 文件**
- ✅ **自动工具发现** - 工具无需手动设置即可找到 Papyrus
- ✅ **标准化接口** - 兼容任何支持 MCP 的工具

## 运行 Papyrus 作为 MCP 服务器

### 方式 1：交互模式（用于测试）

```bash
python -m papyrus.mcp_server
```

这会启动 MCP 服务器在 stdio 模式（从 stdin 读取，向 stdout 写入）。

### 方式 2：后台服务（用于生产）

```bash
# 在后台持续运行 MCP 服务器
nohup python -m papyrus.mcp_server > ~/.papyrus_mcp.log 2>&1 &
```

## 配置工具使用 Papyrus MCP

### Claude Code

编辑或创建 `~/.claude/claude.json`：

```json
{
  "mcpServers": {
    "papyrus": {
      "command": "/path/to/python",
      "args": ["-m", "papyrus.mcp_server"]
    }
  }
}
```

然后在 `~/.claude/CLAUDE.md` 添加 MCP 服务器信息：

```markdown
# 使用 Papyrus MCP 服务器

当你需要读取或分析文档时，使用来自 Papyrus MCP 服务器的 `parse_document` 工具。

## 支持的格式
- PDF（文字版和扫描版含 OCR）
- PPTX（PowerPoint 演示文稿）
- DOCX（Word 文档）
- XLSX（Excel 电子表格）
- HTML（网页）
- Markdown
- 纯文本

## 工具参数
- `file_path`: 文档路径（必需）
- `format`: 输出格式 - "markdown"（默认）或 "json"
- `use_heavy`: 布尔值 - 强制对扫描件使用 OCR
- `use_fast`: 布尔值 - 跳过 OCR 以提高速度

## 示例
解析 PDF 为 markdown：
```
使用 parse_document 工具，参数 file_path="homework.pdf"
```

解析演示文稿为 JSON：
```
使用 parse_document 工具，参数 file_path="slides.pptx", format="json"
```

用 OCR 解析扫描件：
```
使用 parse_document 工具，参数 file_path="scanned_doc.pdf", use_heavy=true
```
```

### Codex

编辑或创建 `~/.codex/config.toml`：

```toml
[mcp_servers]
papyrus = {command = "/path/to/python", args = ["-m", "papyrus.mcp_server"]}
```

或使用 Codex 的 UI 添加 MCP 服务器：
```bash
codex config add-mcp-server papyrus python -m papyrus.mcp_server
```

### Kimi Code

类似于 Codex。编辑 `~/.kimi-code/config.toml`：

```toml
[mcp_servers]
papyrus = {command = "/path/to/python", args = ["-m", "papyrus.mcp_server"]}
```

## 测试 MCP 设置

### 1. 直接测试服务器

```bash
# 通过 stdio 发送 JSON-RPC 请求
cat << 'EOF' | python -m papyrus.mcp_server
{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}
EOF
```

### 2. 用你的工具测试

- **Claude Code**：请求它读一个 PDF 文件，它应该自动使用 parse_document
- **Codex**：同样 - 请求解析文档
- **Kimi**：同样 - 请求文档解析

### 3. 检查日志

如果使用后台服务：
```bash
tail -f ~/.papyrus_mcp.log
```

## 高级：自定义 MCP 配置

### 环境变量

你可以向 MCP 服务器传递环境变量：

```json
{
  "mcpServers": {
    "papyrus": {
      "command": "/path/to/python",
      "args": ["-m", "papyrus.mcp_server"],
      "env": {
        "PAPYRUS_TESSERACT_CMD": "/custom/path/to/tesseract"
      }
    }
  }
}
```

### 自定义路径

如果 Papyrus 安装在非标准位置：

```json
{
  "mcpServers": {
    "papyrus": {
      "command": "/path/to/python",
      "args": ["-m", "papyrus.mcp_server"]
    }
  }
}
```

## MCP vs SKILL.md：何时使用哪个？

| 功能 | MCP | SKILL.md |
|------|-----|----------|
| 配置 | 每个工具一个文件 | 每个工具一个文件 |
| 标准化 | MCP 标准 | 工具特定 |
| 自动发现 | 是 | 否 |
| 最适合 | 长期维护、多工具 | 快速设置 |

**建议**：
- 使用 **MCP** 如果你想要最标准化、易维护的设置
- 使用 **SKILL.md** 如果你想要简单或不需要所有工具共享配置

## 故障排除

### "找不到命令：python"

确保 Python 在 PATH 中：
```bash
which python3
# 如果需要，使用完整路径：/usr/bin/python3
```

### MCP 服务器无法启动

检查日志：
```bash
tail -n 50 ~/.papyrus_mcp.log
```

### 工具无法找到 Papyrus

1. 验证 MCP 服务器正在运行：`ps aux | grep papyrus`
2. 手动测试：`echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python -m papyrus.mcp_server`
3. 检查配置文件格式（JSON 必须有效）
4. 配置更改后重启工具

### "initialize" 方法失败

这通常意味着 Python 环境有问题。验证：
```bash
python -c "from papyrus.cli import parse_document; print('OK')"
```

## 参考

- [主 README](README.md) - 通用文档
- [安装指南](README.md#安装) - 平台特定设置
- [MCP 协议](https://modelcontextprotocol.io/) - 官方 MCP 文档
