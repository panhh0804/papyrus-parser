"""Configuration manager for setting up Papyrus with AI tools."""

import hashlib
import json
import re
from pathlib import Path
from typing import Optional, List

from .utils import print_compat

_HASH_COMMENT_PATTERN = re.compile(r"<!--\s*papyrus-template-hash:\s*([a-f0-9]+)\s*-->")


def _compute_hash(content: str) -> str:
    """Compute short SHA256 hash of template content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:8]


def _inject_hash(content: str, h: str) -> str:
    """Inject or update hash comment at end of markdown content."""
    content = _HASH_COMMENT_PATTERN.sub("", content)
    return content.rstrip() + f"\n\n<!-- papyrus-template-hash: {h} -->"


def _extract_hash(content: str) -> Optional[str]:
    """Extract hash from existing file content."""
    m = _HASH_COMMENT_PATTERN.search(content)
    return m.group(1) if m else None


def _is_outdated(filepath: Path, current_content: str) -> bool:
    """Check if an existing config file is outdated compared to current template."""
    if not filepath.exists():
        return False
    existing = filepath.read_text(encoding="utf-8")
    existing_hash = _extract_hash(existing)
    if existing_hash is None:
        return True  # Old file without hash = definitely outdated
    return existing_hash != _compute_hash(current_content)

# Template for Codex/Kimi SKILL.md - shared between tools
CODEX_KIMI_SKILL_TEMPLATE = """---
name: papyrus
description: Use this skill to read or parse documents (PDF, PPTX, DOCX, XLSX, Word, HTML). Avoids slow on-the-fly library installation by using a pre-installed universal document parser.
keywords: ["pdf", "document", "parse", "pptx", "presentation", "parser"]
---

# Document Parsing with Papyrus

When you need to read, extract, or analyze a document, use **`papyrus`** — a fast, pre-installed universal document parser.

## Supported Formats

- **PDF** (text-based and scanned/OCR)
- **PPTX** (PowerPoint presentations)
- **DOCX** (Word documents)
- **XLSX** (Excel spreadsheets → Markdown tables)
- **HTML** (web pages)
- **Markdown** (`.md` files)
- **Plain text** (`.txt`)

## Basic Usage

```bash
papyrus <file_path>                     # To markdown (default)
papyrus <file_path> --format json       # JSON output
papyrus <file_path> -o output.md        # Save to file
papyrus <file_path> --use-heavy         # OCR for scanned documents
papyrus <file_path> --use-fast          # Quick parsing
papyrus <file_path> -v                  # Verbose mode
```

## Smart Routing

- **Fast Path** (default): Quick parsing with pymupdf4llm/markitdown (~100ms)
- **Heavy Path** (--use-heavy): OCR with marker (5-30s, for scanned documents)

Use `--use-heavy` when output is empty or garbled (indicates scanned PDF).
"""


class ConfigManager:
    """Manages Papyrus configuration for different AI tools."""

    def __init__(self):
        self.home = Path.home()

    def check_all_configs(self) -> List[str]:
        """Check which markdown config files are missing the template hash (outdated).

        Returns:
            List of human-readable descriptions of outdated configs.
        """
        outdated = []

        # Files that receive template content with hash injection
        checks = [
            ("Claude Code SKILL.md", self.home / ".claude" / "CLAUDE.md"),
            ("Codex SKILL.md", self.home / ".codex" / "skills" / "papyrus" / "SKILL.md"),
            ("Kimi SKILL.md", self.home / ".kimi-code" / "skills" / "papyrus" / "SKILL.md"),
            ("AGENTS.md", self.home / "AGENTS.md"),
        ]

        for name, filepath in checks:
            if filepath.exists():
                content = filepath.read_text(encoding="utf-8")
                if _extract_hash(content) is None:
                    outdated.append(name)

        return outdated

    def setup_claude_code(self, mcp_mode: bool = False) -> bool:
        """Set up Claude Code to use Papyrus.

        Args:
            mcp_mode: If True, configure for MCP server; if False, use SKILL.md

        Returns:
            True if successful, False otherwise
        """
        try:
            claude_dir = self.home / ".claude"
            claude_dir.mkdir(exist_ok=True)

            if mcp_mode:
                return self._setup_claude_code_mcp()
            else:
                return self._setup_claude_code_skill()
        except Exception as e:
            print_compat(f"❌ Error setting up Claude Code: {e}")
            return False

    def _setup_claude_code_skill(self) -> bool:
        """Set up Claude Code with SKILL.md approach."""
        claude_md = self.home / ".claude" / "CLAUDE.md"

        content = """# Document Parsing with Papyrus

When you need to **read or parse any document** (PDF, PPTX, DOCX, Word, HTML, Markdown, text), you **must** use the `papyrus` CLI tool. Do NOT install pymupdf, PyPDF2, pdfplumber, python-pptx, or other parsing libraries on-the-fly.

## Supported Formats

- **PDF** — both text-based and scanned/image-based
- **PPTX** — PowerPoint presentations (2007+)
- **DOCX** — Microsoft Word documents
- **XLSX** — Excel spreadsheets (converts to Markdown tables)
- **HTML** — web pages and HTML files
- **Markdown** — `.md`, `.markdown` files
- **Plain text** — `.txt` files

## How to Use

```bash
# Basic: parse to markdown (auto-detects best strategy)
papyrus <file_path>

# Output as JSON (with metadata)
papyrus <file_path> --format json

# Save to file
papyrus <file_path> -o result.md

# Force OCR for scanned documents
papyrus <file_path> --use-heavy

# Force quick parsing (no OCR)
papyrus <file_path> --use-fast

# Verbose output (shows routing decision)
papyrus <file_path> -v
```

## When to Use --use-heavy

The heavy path (OCR with marker) is slower but better for:
- Scanned PDFs (when output is empty or garbled)
- Complex tables and multi-column layouts
- Mathematical formulas
- Documents with handwriting or annotations

Default (fast path) is fine for:
- Modern PDFs with selectable text
- Simple documents
- Quick previews
"""

        try:
            content = _inject_hash(content, _compute_hash(content))
            claude_md.write_text(content, encoding="utf-8")
            print_compat(f"✓ Created {claude_md}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {claude_md}: {e}")
            return False

    def _setup_claude_code_mcp(self) -> bool:
        """Set up Claude Code with MCP approach."""
        claude_json = self.home / ".claude" / "claude.json"

        # Try to load existing config
        config = {}
        if claude_json.exists():
            try:
                config = json.loads(claude_json.read_text())
            except Exception:
                pass

        # Add MCP server config
        if "mcpServers" not in config:
            config["mcpServers"] = {}

        papyrus_path = Path.home() / "papyrus"
        config["mcpServers"]["papyrus"] = {
            "command": "python",
            "args": ["-m", "papyrus.mcp_server"],
            "cwd": str(papyrus_path),
        }

        try:
            claude_json.write_text(json.dumps(config, indent=2), encoding="utf-8")
            print_compat(f"✓ Updated {claude_json}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {claude_json}: {e}")
            return False

    def setup_codex(self, mcp_mode: bool = False) -> bool:
        """Set up Codex to use Papyrus.

        Args:
            mcp_mode: If True, configure for MCP server; if False, use SKILL.md

        Returns:
            True if successful, False otherwise
        """
        try:
            if mcp_mode:
                return self._setup_codex_mcp()
            else:
                return self._setup_codex_skill()
        except Exception as e:
            print_compat(f"❌ Error setting up Codex: {e}")
            return False

    def _setup_codex_skill(self) -> bool:
        """Set up Codex with SKILL.md approach."""
        skills_dir = self.home / ".codex" / "skills" / "papyrus"
        skills_dir.mkdir(parents=True, exist_ok=True)

        skill_md = skills_dir / "SKILL.md"

        content = """---
name: papyrus
description: Use this skill to read or parse documents (PDF, PPTX, DOCX, XLSX, Word, HTML). Avoids slow on-the-fly library installation by using a pre-installed universal document parser.
keywords: ["pdf", "document", "parse", "pptx", "presentation", "parser"]
---

# Document Parsing with Papyrus

When you need to read, extract, or analyze a document, use **`papyrus`** — a fast, pre-installed universal document parser. This avoids the overhead of discovering and installing parsing libraries on-the-fly.

## Supported Formats

- **PDF** (text-based and scanned/OCR)
- **PPTX** (PowerPoint presentations)
- **DOCX** (Word documents)
- **XLSX** (Excel spreadsheets → Markdown tables)
- **HTML** (web pages)
- **Markdown** (`.md` files)
- **Plain text** (`.txt`)

## Basic Usage

```bash
# Parse document to markdown (default, fast)
papyrus <file_path>

# Output as JSON (includes metadata)
papyrus <file_path> --format json

# Save to file
papyrus <file_path> -o output.md

# Use OCR for scanned documents
papyrus <file_path> --use-heavy

# Quick mode (no OCR analysis)
papyrus <file_path> --use-fast

# Verbose (shows which parser was chosen)
papyrus <file_path> -v
```

## Smart Routing

Papyrus automatically chooses the right parsing strategy:

- **Fast Path** (default): Uses `pymupdf4llm` and `markitdown`
  - Speed: ~100ms per document
  - Best for: Modern PDFs, DOCX, HTML, presentations
  - Requirements: Minimal dependencies

- **Heavy Path** (OCR): Uses `marker` with optical character recognition
  - Speed: 5-30 seconds depending on document size
  - Best for: Scanned PDFs, complex tables, formulas
  - Requirements: PyTorch, model download (~500MB on first use)

## Example Workflows

### Read a homework PDF
```bash
papyrus homework.pdf
```

### Extract presentation slides to JSON
```bash
papyrus presentation.pptx --format json
```

### Parse scanned document with OCR
```bash
# If normal parsing gives empty/garbled output:
papyrus scanned_exam.pdf --use-heavy
```

### Extract multiple pages from PDF
```bash
papyrus large_report.pdf | head -100  # First 100 lines
```

## When Output Looks Wrong

If you see empty output or garbled text:
1. Try `--use-heavy` flag for OCR processing
2. Check file format: `papyrus <file> -v` shows which parser was used
3. Make sure the file is readable and not corrupted

## Performance Tips

- First run with `--use-heavy` is slower due to model download (~500MB)
- Use `--use-fast` explicitly if you know the document doesn't need OCR
- Batch multiple documents to reuse cached models

---

**Papyrus** is pre-installed and available globally. Location: `$HOME/papyrus/venv/bin/papyrus`
"""

        try:
            content = _inject_hash(content, _compute_hash(content))
            skill_md.write_text(content, encoding="utf-8")
            print_compat(f"✓ Created {skill_md}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {skill_md}: {e}")
            return False

    def _setup_codex_mcp(self) -> bool:
        """Set up Codex with MCP approach."""
        codex_config = self.home / ".codex" / "config.toml"

        # Read existing config
        config_content = ""
        if codex_config.exists():
            config_content = codex_config.read_text()

        # Check if papyrus MCP is already configured
        if "papyrus" in config_content and "[mcp_servers]" in config_content:
            print_compat(f"✓ Papyrus MCP already configured in {codex_config}")
            return True

        # Add MCP server configuration
        papyrus_path = Path.home() / "papyrus"
        mcp_config = f"""
[mcp_servers.papyrus]
command = "python"
args = ["-m", "papyrus.mcp_server"]
cwd = "{papyrus_path}"
"""

        if "[mcp_servers]" not in config_content:
            config_content += "\n[mcp_servers]\n"

        config_content += mcp_config

        try:
            codex_config.write_text(config_content, encoding="utf-8")
            print_compat(f"✓ Updated {codex_config}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {codex_config}: {e}")
            return False

    def setup_kimi(self, mcp_mode: bool = False) -> bool:
        """Set up Kimi Code to use Papyrus.

        Args:
            mcp_mode: If True, configure for MCP server; if False, use SKILL.md

        Returns:
            True if successful, False otherwise
        """
        try:
            if mcp_mode:
                return self._setup_kimi_mcp()
            else:
                return self._setup_kimi_skill()
        except Exception as e:
            print_compat(f"❌ Error setting up Kimi Code: {e}")
            return False

    def _setup_kimi_skill(self) -> bool:
        """Set up Kimi Code with SKILL.md approach (copy from Codex)."""
        kimi_skills_dir = self.home / ".kimi-code" / "skills" / "papyrus"
        kimi_skills_dir.mkdir(parents=True, exist_ok=True)

        # Copy from Codex SKILL.md
        codex_skill = self.home / ".codex" / "skills" / "papyrus" / "SKILL.md"

        if not codex_skill.exists():
            # If Codex not set up yet, create directly
            return self._setup_kimi_skill_direct()

        try:
            kimi_skill = kimi_skills_dir / "SKILL.md"
            kimi_skill.write_text(codex_skill.read_text())
            print_compat(f"✓ Created {kimi_skill}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to set up Kimi SKILL.md: {e}")
            return False

    def _setup_kimi_skill_direct(self) -> bool:
        """Set up Kimi Code SKILL.md directly."""
        kimi_skills_dir = self.home / ".kimi-code" / "skills" / "papyrus"
        kimi_skills_dir.mkdir(parents=True, exist_ok=True)

        # Use the same content as Codex
        return self._setup_codex_skill_content(
            kimi_skills_dir / "SKILL.md"
        )

    def _setup_codex_skill_content(self, filepath: Path) -> bool:
        """Helper to write Codex SKILL.md content to a file."""
        content = """---
name: papyrus
description: Use this skill to read or parse documents (PDF, PPTX, DOCX, XLSX, Word, HTML). Avoids slow on-the-fly library installation by using a pre-installed universal document parser.
keywords: ["pdf", "document", "parse", "pptx", "presentation", "parser"]
---

# Document Parsing with Papyrus

When you need to read, extract, or analyze a document, use **`papyrus`** — a fast, pre-installed universal document parser.

## Supported Formats

- **PDF** (text-based and scanned/OCR)
- **PPTX** (PowerPoint presentations)
- **DOCX** (Word documents)
- **XLSX** (Excel spreadsheets → Markdown tables)
- **HTML** (web pages)
- **Markdown** (`.md` files)
- **Plain text** (`.txt`)

## Basic Usage

```bash
papyrus <file_path>                     # To markdown (default)
papyrus <file_path> --format json       # JSON output
papyrus <file_path> -o output.md        # Save to file
papyrus <file_path> --use-heavy         # OCR for scanned documents
papyrus <file_path> --use-fast          # Quick parsing
papyrus <file_path> -v                  # Verbose mode
```

## Smart Routing

- **Fast Path** (default): Quick parsing with pymupdf4llm/markitdown (~100ms)
- **Heavy Path** (--use-heavy): OCR with marker (5-30s, for scanned documents)

Use `--use-heavy` when output is empty or garbled (indicates scanned PDF).
"""

        try:
            content = _inject_hash(content, _compute_hash(content))
            filepath.write_text(content, encoding="utf-8")
            print_compat(f"✓ Created {filepath}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {filepath}: {e}")
            return False

    def _setup_kimi_mcp(self) -> bool:
        """Set up Kimi Code with MCP approach."""
        kimi_config = self.home / ".kimi-code" / "config.toml"

        # Read existing config
        config_content = ""
        if kimi_config.exists():
            config_content = kimi_config.read_text()

        # Check if papyrus MCP is already configured
        if "papyrus" in config_content and "[mcp_servers]" in config_content:
            print_compat(f"✓ Papyrus MCP already configured in {kimi_config}")
            return True

        # Add MCP server configuration
        papyrus_path = Path.home() / "papyrus"
        mcp_config = f"""
[mcp_servers.papyrus]
command = "python"
args = ["-m", "papyrus.mcp_server"]
cwd = "{papyrus_path}"
"""

        if "[mcp_servers]" not in config_content:
            config_content += "\n[mcp_servers]\n"

        config_content += mcp_config

        try:
            kimi_config.write_text(config_content, encoding="utf-8")
            print_compat(f"✓ Updated {kimi_config}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {kimi_config}: {e}")
            return False

    def setup_agents_md(self) -> bool:
        """Create AGENTS.md in home directory for Codex."""
        try:
            agents_md = self.home / "AGENTS.md"

            content = """# Agent Guidelines for Document Processing

## Document Parsing Policy

Whenever you need to **read, parse, or extract content from documents**, use **`papyrus`** — a universal document parser already installed and available globally.

### Why Papyrus?

- **Pre-installed** — No `pip install` delays
- **Universal** — Handles PDF, PPTX, DOCX, XLSX, HTML, Markdown, plain text
- **Intelligent** — Automatically chooses fast or OCR-based parsing
- **Consistent** — Same tool across Claude Code, Codex, Kimi, and other AI agents

### Command Syntax

```bash
# Basic: parse to markdown (auto-select strategy)
papyrus <file_path>

# Output as JSON (structured data + metadata)
papyrus <file_path> --format json

# Save to file
papyrus <file_path> -o output.md

# Force OCR for scanned documents
papyrus <file_path> --use-heavy

# Force quick parsing
papyrus <file_path> --use-fast

# Verbose output (shows which parser was chosen)
papyrus <file_path> -v
```

### Supported Document Types

- **PDF** — Both text-based and scanned/image-based PDFs
- **PPTX** — PowerPoint presentations (2007+)
- **DOCX** — Microsoft Word documents
- **XLSX** — Excel spreadsheets (converts to Markdown tables)
- **HTML** — Web pages and HTML files
- **Markdown** — `.md`, `.markdown` files
- **Plain Text** — `.txt`, `.text` files

### Smart Routing Rules

**Use Fast Path (default)** for:
- Modern PDFs with selectable text
- PPTX presentations
- DOCX / XLSX files
- HTML and Markdown
- Quick document previews

**Use Heavy Path (`--use-heavy`)** for:
- Scanned PDFs (when regular output is empty/garbled)
- Documents with complex table layouts
- PDFs with mathematical formulas
- Documents with handwriting or annotations

### Examples

#### 1. Read a homework PDF
```bash
papyrus homework.pdf
# Output goes to stdout as markdown
```

#### 2. Extract slides from PowerPoint
```bash
papyrus presentation.pptx --format json > slides.json
```

#### 3. Process scanned document with OCR
```bash
papyrus scanned_form.pdf --use-heavy
```

#### 4. Extract and save document
```bash
papyrus research_paper.pdf -o paper_content.md
```

### What NOT to Do

❌ **Never** run these commands:
```bash
pip install pymupdf
pip install PyPDF2
pip install pdfplumber
pip install python-pptx
pip install pdf2image
pip install python-docx
```

Papyrus already handles all of these — using it saves time and avoids version conflicts.

### Error Handling

| Problem | Solution |
|---------|----------|
| No text output | Try `papyrus <file> --use-heavy` for OCR |
| Slow performance | Use `papyrus <file> --use-fast` to skip OCR |
| Garbled output | Check file format: `papyrus <file> -v` |
| "Command not found" | Reload shell or verify PATH includes `$HOME/papyrus/venv/bin` |

### Performance Tips

- **First run slower** — Heavy path downloads models (~500MB) on first use
- **Batch documents** — Multiple files reuse cached models
- **Use `--use-fast`** — If you know the document doesn't need OCR
- **Disable GPU** — For headless environments: `CUDA_VISIBLE_DEVICES=-1 papyrus ...`

---

**Installation Path**: `$HOME/papyrus/venv/bin/papyrus`
**Available globally** — `papyrus` is in your PATH via `~/.zshrc` or `~/.bashrc`

For detailed documentation, see:
- `$HOME/papyrus/README.md` — Full feature reference
- `$HOME/papyrus/MCP_SETUP.md` — MCP server integration guide
"""

            content = _inject_hash(content, _compute_hash(content))
            agents_md.write_text(content, encoding="utf-8")
            print_compat(f"✓ Created {agents_md}")
            return True
        except Exception as e:
            print_compat(f"❌ Failed to write {agents_md}: {e}")
            return False
