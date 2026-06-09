# Papyrus MCP Server Setup Guide

Papyrus can be used as an **MCP (Model Context Protocol) server**, allowing any MCP-compatible tool to automatically use it for document parsing.

## What is MCP?

MCP is a standardized protocol that allows AI models to interact with external tools. Benefits:
- ✅ **Single configuration** for all tools (Claude, Codex, Kimi, etc.)
- ✅ **No redundant SKILL.md files** needed
- ✅ **Automatic tool discovery** - tools find Papyrus without manual setup
- ✅ **Standardized interface** compatible with any MCP-aware tool

## Running Papyrus as MCP Server

### Option 1: Interactive Mode (for testing)

```bash
cd ~/papyrus
source venv/bin/activate
python -m papyrus.mcp_server
```

This starts the MCP server in stdio mode (reads from stdin, writes to stdout).

### Option 2: Background Service (for production)

```bash
# Keep MCP server running in background
nohup python -m papyrus.mcp_server > ~/.papyrus_mcp.log 2>&1 &
```

## Configuring Tools to Use Papyrus MCP

### Claude Code

Edit or create `~/.claude/claude.json`:

```json
{
  "mcpServers": {
    "papyrus": {
      "command": "python",
      "args": ["-m", "papyrus.mcp_server"],
      "cwd": "$HOME/papyrus"
    }
  }
}
```

Then add the MCP server info to `~/.claude/CLAUDE.md`:

```markdown
# Using Papyrus MCP Server

When you need to read or analyze documents, use the `parse_document` tool from the Papyrus MCP server.

## Supported Formats
- PDF (text-based and scanned with OCR)
- PPTX (PowerPoint presentations)
- DOCX (Word documents)
- XLSX (Excel spreadsheets)
- HTML (web pages)
- Markdown
- Plain text

## Tool Parameters
- `file_path`: Path to the document (required)
- `format`: Output format - "markdown" (default) or "json"
- `use_heavy`: Boolean - force OCR for scanned documents
- `use_fast`: Boolean - skip OCR for faster parsing

## Examples
Parse a PDF to markdown:
```
Use the parse_document tool with file_path="homework.pdf"
```

Parse a presentation as JSON:
```
Use the parse_document tool with file_path="slides.pptx", format="json"
```

Parse a scanned document with OCR:
```
Use the parse_document tool with file_path="scanned_doc.pdf", use_heavy=true
```
```

### Codex

Edit or create `~/.codex/config.toml`:

```toml
[mcp_servers]
papyrus = {command = "python", args = ["-m", "papyrus.mcp_server"], cwd = "$HOME/papyrus"}
```

Or use Codex's UI to add MCP server:
```bash
codex config add-mcp-server papyrus python -m papyrus.mcp_server
```

### Kimi Code

Similar to Codex. Edit `~/.kimi-code/config.toml`:

```toml
[mcp_servers]
papyrus = {command = "python", args = ["-m", "papyrus.mcp_server"], cwd = "$HOME/papyrus"}
```

## Testing MCP Setup

### 1. Test Server Directly

```bash
# In one terminal, start the server
python -m papyrus.mcp_server

# In another terminal, send a test request
cat << 'EOF' | nc localhost 9000
{"jsonrpc": "2.0", "method": "initialize", "params": {}, "id": 1}
EOF
```

### 2. Test with Your Tool

- **Claude Code**: Ask it to read a PDF file, it should automatically use parse_document
- **Codex**: Same - ask it to parse a document
- **Kimi**: Same - request document parsing

### 3. Check Logs

If using background service:
```bash
tail -f ~/.papyrus_mcp.log
```

## Advanced: Custom MCP Configuration

### Environment Variables

You can pass environment variables to the MCP server:

```json
{
  "mcpServers": {
    "papyrus": {
      "command": "python",
      "args": ["-m", "papyrus.mcp_server"],
      "cwd": "$HOME/papyrus",
      "env": {
        "PAPYRUS_TESSERACT_CMD": "/custom/path/to/tesseract"
      }
    }
  }
}
```

### Custom Paths

If Papyrus is installed in a non-standard location:

```json
{
  "mcpServers": {
    "papyrus": {
      "command": "python",
      "args": ["-m", "papyrus.mcp_server"],
      "cwd": "/custom/papyrus/path"
    }
  }
}
```

## MCP vs SKILL.md: When to Use Which?

| Feature | MCP | SKILL.md |
|---------|-----|----------|
| Configuration | Single file per tool | One file per tool |
| Standardization | MCP standard | Tool-specific |
| Auto-discovery | Yes | Manual setup |
| Best for | Long-term, cross-tool | Quick setup |

**Recommendation**: 
- Use **MCP** if you want the most standardized, maintainable setup
- Use **SKILL.md** if you want simplicity or don't need all tools to share config

## Troubleshooting

### "Command not found: python"

Make sure Python is in PATH:
```bash
which python3
# Use full path if needed: /usr/bin/python3
```

### MCP Server Not Starting

Check the logs:
```bash
tail -n 50 ~/.papyrus_mcp.log
```

### Tool Not Finding Papyrus

1. Verify MCP server is running: `ps aux | grep papyrus`
2. Test manually: `python -m papyrus.mcp_server`
3. Check configuration file format (JSON must be valid)
4. Restart your tool after configuration changes

### "initialize" Method Failed

This usually means the Python environment is wrong. Verify:
```bash
python -c "from papyrus.cli import parse_document; print('OK')"
```

## See Also

- [Main README](README.md) - General documentation
- [Setup Guides](README.md#installation) - Platform-specific setup
- [MCP Protocol](https://modelcontextprotocol.io/) - Official MCP documentation
