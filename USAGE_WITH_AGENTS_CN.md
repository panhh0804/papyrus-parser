# 在 Claude Code、Codex、Kimi 中使用 Papyrus

本指南展示如何将 `papyrus` 集成到你的 AI 助手 Agent 工作流中。

## 快速设置

```bash
# 1. 安装 papyrus
cd ~/papyrus
source venv/bin/activate  # 或创建你自己的 venv
pip install -e .

# 2. 测试是否可行
papyrus --help
```

## Claude Code

### 在 Agent 中直接使用命令

```typescript
// 在你的 Claude Code agent 中
import { execSync } from 'child_process';

const parseDocument = (filePath: string) => {
  try {
    const result = execSync(`papyrus "${filePath}" --format json`, {
      encoding: 'utf-8',
      maxBuffer: 50 * 1024 * 1024, // 50MB 用于大文档
    });
    return JSON.parse(result);
  } catch (error) {
    console.error(`Failed to parse ${filePath}:`, error.message);
    throw error;
  }
};

// 使用
const doc = parseDocument('homework.pdf');
console.log(doc.content);
```

### 作为工具函数

```typescript
// 定义为可复用工具
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

// 在你的 agent 中：
const result = await documentParser.parse('complex_paper.pdf', {useHeavy: true});
```

## Codex

Codex 使用类似的 bash 执行，但具体集成方式取决于你的设置：

```bash
# 直接命令（如果 papyrus 在 PATH 中）
papyrus document.pdf --format markdown

# 或使用完整 venv 路径
/path/to/venv/bin/papyrus document.pdf
```

### 在 Python Codex 脚本中

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

# 使用
content = parse_doc('homework.pdf')
```

## Kimi

类似于 Codex，使用 subprocess 调用：

```python
import os
import subprocess

# 确保 papyrus 可用
def parse_with_papyrus(file_path: str) -> str:
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

# 在你的 agent 中
document_content = parse_with_papyrus('/path/to/homework.pdf')
```

## 环境设置

### 全局使用 papyrus

选项 1：添加到 PATH（如果使用 venv）：

```bash
# 添加到你的 shell 配置文件（.bashrc、.zshrc 等）
export PATH="$HOME/papyrus/venv/bin:$PATH"

# 测试
papyrus --help
```

选项 2：创建 shell 包装脚本：

```bash
#!/bin/bash
# 保存为 ~/bin/papyrus
$HOME/papyrus/venv/bin/python -m papyrus "$@"
```

然后添加 `~/bin` 到 PATH：

```bash
export PATH="$HOME/bin:$PATH"
```

选项 3：系统范围安装（不推荐，使用 venv）：

```bash
pip install --user -e ~/papyrus
```

## 高级用法

### 处理大文档

```javascript
// Claude Code 示例 - 使用超时解析大型 PDF
const parseLargeDoc = (filePath: string) => {
  const result = execSync(
    `papyrus "${filePath}" --use-fast --format json`,
    {
      encoding: 'utf-8',
      timeout: 180000, // 3 分钟
      maxBuffer: 100 * 1024 * 1024, // 100MB
    }
  );
  
  const data = JSON.parse(result);
  // 如果太大则截断以适应上下文
  if (data.content.length > 100000) {
    data.content = data.content.substring(0, 100000) + '\n... [已截断]';
  }
  
  return data;
};
```

### 手动检测文件类型和路由

```python
from papyrus import detect_file_type, should_use_heavy_path

file_path = 'document.pdf'
file_type = detect_file_type(file_path)

if file_type == 'pdf' and should_use_heavy_path(file_path):
    print("检测到复杂 PDF，使用重路径...")
    cmd = ['papyrus', file_path, '--use-heavy']
else:
    print("简单文档，使用快路径...")
    cmd = ['papyrus', file_path]

result = subprocess.run(cmd, capture_output=True, text=True)
```

### 自定义处理管道

```typescript
interface ParsedDoc {
  content: string;
  metadata: {
    file: string;
    parser: string;
  };
}

async function processDocument(filePath: string): Promise<ParsedDoc> {
  // 解析
  const result = execSync(`papyrus "${filePath}" --format json`, {
    encoding: 'utf-8',
  });
  
  const doc = JSON.parse(result) as ParsedDoc;
  
  // 后处理：清理、提取段落等
  doc.content = doc.content
    .split('\n')
    .filter(line => line.trim().length > 0)
    .join('\n');
  
  return doc;
}
```

## 故障排除

### 命令未找到：papyrus

确保 venv 激活或路径已设置：

```bash
source $HOME/papyrus/venv/bin/activate
papyrus --help
```

或使用完整路径：

```bash
$HOME/papyrus/venv/bin/papyrus test.pdf
```

### 解析超时或内存问题

明确使用快路径：

```bash
papyrus large_file.pdf --use-fast
```

或在 agent 中增加超时：

```typescript
execSync('papyrus file.pdf', {timeout: 300000}); // 5 分钟
```

### 重路径的 ImportError

如果看到"marker-pdf 未安装"：

```bash
source $HOME/papyrus/venv/bin/activate
pip install 'marker-pdf>=0.3.0'
```

或仅使用快路径：

```bash
papyrus scanned.pdf --use-fast
```

## 性能技巧

1. **首次运行较慢** - 模型首次使用时下载（marker 约 500MB）
2. **默认使用快路径** - 仅在需要时明确选择重路径
3. **批处理** - 按顺序解析多个文件以复用缓存的模型
4. **CPU 优化** - 对于无头服务器，禁用 GPU 以节省内存：

```bash
CUDA_VISIBLE_DEVICES=-1 papyrus file.pdf --use-heavy
```

---

准备在你的 AI Agent 中解析文档了！更多详情见主 [README.md](README.md)。
