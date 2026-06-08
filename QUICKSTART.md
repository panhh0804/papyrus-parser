# Quick Start

## 1. Install

```bash
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## 2. Test

```bash
# Show help
papyrus --help

# Parse a markdown file
papyrus README.md

# Parse and save to file
papyrus test_sample.md -o output.md

# Parse as JSON
papyrus test_sample.md --format json
```

## 3. Use in Your AI Agent

### Claude Code
```javascript
const { execSync } = require('child_process');

// With full path to venv
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

## 4. Make it Global (Optional)

Add to your shell config (`~/.zshrc` or `~/.bashrc`):

```bash
export PATH="$HOME/papyrus/venv/bin:$PATH"
```

Then you can just use:
```bash
papyrus homework.pdf
```

## 5. Advanced: Use Heavy Parser for Scanned PDFs

```bash
# Auto-detect complex PDFs and use marker
papyrus scanned_document.pdf

# Force heavy parser
papyrus document.pdf --use-heavy

# Verbose output (see which parser is used)
papyrus document.pdf -v
```

## Supported File Types

- **PDF** (text & scanned) ✅
- **DOCX** ✅
- **Markdown** ✅
- **Plain text** ✅
- **HTML** ✅

## Output Formats

- **Markdown** (default): Clean, human-readable
- **JSON**: Structured data with metadata

```bash
# Markdown output
papyrus file.pdf

# JSON output
papyrus file.pdf --format json
```

---

**That's it!** Now you have a cross-platform document parser for your AI agents.

For more details, see:
- [README.md](README.md) - Full documentation
- [USAGE_WITH_AGENTS.md](USAGE_WITH_AGENTS.md) - Integration guide
