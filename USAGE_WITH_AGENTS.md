# Using Papyrus with Claude Code, Codex, Kimi

This guide shows how to integrate `papyrus` into your AI assistant agent workflows.

## Quick Setup

```bash
# 1. Install papyrus
cd ~/papyrus
source venv/bin/activate  # or create your own venv
pip install -e .

# 2. Test it works
papyrus --help
```

## Claude Code

### Direct Command in Agent

```typescript
// In your Claude Code agent
import { execSync } from 'child_process';

const parseDocument = (filePath: string) => {
  try {
    const result = execSync(`papyrus "${filePath}" --format json`, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024, // 50MB for large documents
    });
    return JSON.parse(result);
  } catch (error) {
    console.error(`Failed to parse ${filePath}:`, error.message);
    throw error;
  }
};

// Usage
const doc = parseDocument('homework.pdf');
console.log(doc.content);
```

### As a Tool Function

```typescript
// Define as a reusable tool
const documentParser = {
  parse: async (filePath: string, options?: {format?: 'markdown' | 'json', useHeavy?: boolean}) => {
    const args = [
      'papyrus',
      filePath,
      `--format=${options?.format || 'markdown'}`,
    ];
    
    if (options?.useHeavy) {
      args.push('--use-heavy');
    }
    
    return execSync(args.join(' '), {encoding: 'utf-8'});
  },
};

// In your agent:
const result = await documentParser.parse('complex_paper.pdf', {useHeavy: true});
```

## Codex

Codex uses similar bash execution, but the exact integration depends on your setup:

```bash
# Direct command (if papyrus is in PATH)
papyrus document.pdf --format markdown

# Or with full path to venv
/path/to/venv/bin/papyrus document.pdf
```

### In Python Codex Scripts

```python
import subprocess
import json

def parse_doc(file_path: str, use_heavy: bool = False):
    cmd = ['papyrus', file_path]
    if use_heavy:
        cmd.append('--use-heavy')
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Parse failed: {result.stderr}")
    
    return result.stdout

# Usage
content = parse_doc('homework.pdf')
```

## Kimi

Similar to Codex, use subprocess calls:

```python
import os
import subprocess

# Ensure papyrus is available
def parse_with_doc_parse(file_path: str) -> str:
    result = subprocess.run(
        ['papyrus', file_path, '-v'],
        capture_output=True,
        text=True,
        timeout=120,
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    return result.stdout

# In your agent
document_content = parse_with_doc_parse('/path/to/homework.pdf')
```

## Environment Setup

### Make papyrus Available Globally

Option 1: Add to PATH (if using venv):

```bash
# Add to your shell config (.bashrc, .zshrc, etc.)
export PATH="$HOME/papyrus/venv/bin:$PATH"

# Test
papyrus --help
```

Option 2: Create a shell wrapper script:

```bash
#!/bin/bash
# Save as ~/bin/papyrus
$HOME/papyrus/venv/bin/python -m doc_parse "$@"
```

Then add `~/bin` to PATH:

```bash
export PATH="$HOME/bin:$PATH"
```

Option 3: System-wide install (not recommended, use venv instead):

```bash
pip install --user -e ~/papyrus
```

## Advanced Usage

### Handle Large Documents

```javascript
// Claude Code example - parse large PDFs with timeout
const parseLargeDoc = (filePath: string) => {
  const result = execSync(
    `papyrus "${filePath}" --use-fast --format json`,
    {
      encoding: 'utf-8',
      timeout: 180000, // 3 minutes
      maxBuffer: 100 * 1024 * 1024, // 100MB
    }
  );
  
  const data = JSON.parse(result);
  // Truncate if too large for context
  if (data.content.length > 100000) {
    data.content = data.content.substring(0, 100000) + '\n... [truncated]';
  }
  
  return data;
};
```

### Detect File Type and Route Manually

```python
from doc_parse import detect_file_type, should_use_heavy_path

file_path = 'document.pdf'
file_type = detect_file_type(file_path)

if file_type == 'pdf' and should_use_heavy_path(file_path):
    print("Complex PDF detected, using heavy parser...")
    cmd = ['papyrus', file_path, '--use-heavy']
else:
    print("Simple document, using fast parser...")
    cmd = ['papyrus', file_path]

result = subprocess.run(cmd, capture_output=True, text=True)
```

### Custom Processing Pipeline

```typescript
interface ParsedDoc {
  content: string;
  metadata: {
    file: string;
    parser: string;
  };
}

async function processDocument(filePath: string): Promise<ParsedDoc> {
  // Parse
  const result = execSync(`papyrus "${filePath}" --format json`, {
    encoding: 'utf-8',
  });
  
  const doc = JSON.parse(result) as ParsedDoc;
  
  // Post-process: clean up, extract sections, etc.
  doc.content = doc.content
    .split('\n')
    .filter(line => line.trim().length > 0)
    .join('\n');
  
  return doc;
}
```

## Troubleshooting

### Command not found: papyrus

Make sure the venv is active or path is set:

```bash
source $HOME/papyrus/venv/bin/activate
papyrus --help
```

Or use full path:

```bash
$HOME/papyrus/venv/bin/papyrus test.pdf
```

### Parse timeout or memory issues

Use fast path explicitly:

```bash
papyrus large_file.pdf --use-fast
```

Or increase timeout in your agent:

```typescript
execSync('papyrus file.pdf', {timeout: 300000}); // 5 minutes
```

### ImportError for heavy path

If you see "marker-pdf not installed":

```bash
source $HOME/papyrus/venv/bin/activate
pip install 'marker-pdf>=0.3.0'
```

Or use fast path only:

```bash
papyrus scanned.pdf --use-fast
```

## Performance Tips

1. **First run slower** - Models are downloaded on first use (~500MB for marker)
2. **Use fast path by default** - Explicitly opt into heavy path only when needed
3. **Batch processing** - Parse multiple files in sequence to reuse cached models
4. **CPU optimization** - For headless servers, disable GPU to save memory:

```bash
CUDA_VISIBLE_DEVICES=-1 papyrus file.pdf --use-heavy
```

---

Ready to parse documents in your AI agents! See main [README.md](README.md) for more details.
