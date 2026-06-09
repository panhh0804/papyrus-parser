# Papyrus：项目总结

## 什么是 Papyrus？

一个通用的 CLI 工具，用于解析文档（PDF、DOCX、Markdown、HTML 等）为 markdown 或 JSON 格式。**适用于 Claude Code、Codex、Kimi 以及任何能执行 shell 命令的工具。**

## 核心功能

### 1. **智能路由** 🔄
- 自动检测文档类型和复杂度
- 路由到快路径（快速、轻量）或重路径（最佳质量、较慢）
- 用户可以用标志强制选择任一路径

### 2. **快路径** ⚡
- 使用 `pymupdf4llm`（PDF）和 `markitdown`（其他格式）
- 典型文档解析时间 ~100ms
- 无需 ML 模型，依赖最少
- 简单文档的默认选择

### 3. **重路径** 🔬（可选）
- 使用 `marker` 及其 OCR 能力
- 对扫描 PDF、复杂表格、数学公式有优秀表现
- 需要 PyTorch 和模型下载（~500MB）
- 用户可选：`pip install 'papyrus[heavy]'`

### 4. **跨平台 CLI** 🌍
- 支持 Claude Code、Codex、Kimi 和其他 AI 工具
- 单一入口：`papyrus <file> [options]`
- 多种输出格式：markdown、JSON
- 可配置行为通过标志

## 项目结构

```
papyrus/
├── papyrus/
│   ├── __init__.py          # 公开 API
│   ├── cli.py               # 命令行接口（基于 Click）
│   ├── detector.py          # 文件类型和复杂度检测
│   ├── router.py            # 路由逻辑
│   ├── config_manager.py    # AI 工具配置管理
│   ├── mcp_server.py        # MCP 服务器实现
│   └── parsers/
│       ├── fast_path.py     # pymupdf4llm & markitdown
│       └── heavy_path.py    # marker 集成（可选）
├── README.md                # 完整文档
├── QUICKSTART.md            # 5 分钟快速开始
├── USAGE_WITH_AGENTS.md     # AI 助手集成指南
├── MCP_SETUP.md             # MCP 服务器设置
├── CODE_REVIEW.md           # 代码审查报告
├── setup-unix.sh            # Unix 自动化安装脚本
├── setup-windows.ps1        # Windows 自动化安装脚本
├── pyproject.toml           # 包配置
└── LICENSE                  # MIT + 依赖许可说明
```

## 安装

### 快速版（仅快路径）
```bash
cd ~/papyrus
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 包含重路径支持
```bash
pip install -e '.[heavy]'
```

## 使用示例

### 命令行
```bash
# 解析到标准输出
papyrus homework.pdf

# 保存到文件
papyrus report.pdf -o result.md

# JSON 输出
papyrus document.pdf --format json

# 对扫描件强制使用重路径
papyrus scan.pdf --use-heavy

# 详细输出（显示路由决策）
papyrus complex_paper.pdf -v
```

### 在代码中使用（Claude Code / Codex / Kimi）

**Claude Code (JavaScript):**
```javascript
const { execSync } = require('child_process');
const result = execSync('$HOME/papyrus/venv/bin/papyrus homework.pdf').toString();
```

**Codex / Kimi (Python):**
```python
import subprocess
result = subprocess.run(['$HOME/papyrus/venv/bin/papyrus', 'homework.pdf'],
                       capture_output=True, text=True)
print(result.stdout)
```

## 关键设计决策

### 1. **默认轻量级**
- 快路径（pymupdf4llm/markitdown）是默认选择
- 无强制 ML 依赖
- 重路径（marker）是可选且用户可安装的
- 保持安装快速和内存占用低

### 2. **智能检测**
- 分析文件内容，而不仅仅是扩展名
- 检测扫描 PDF（基于图像、无文本）
- 检测复杂布局（表格、图形、多列）
- 无需用户干预的智能路由

### 3. **跨工具兼容性**
- 不局限于单一 LLM 平台
- 可执行 CLI，适用于任何工具
- 基于子进程的集成，最大化可移植性
- 无需特殊 API 或协议

### 4. **清晰的许可证**
- papyrus 代码：MIT
- 依赖清晰文档化
- Marker（重路径）许可证警告明确注明
- 用户了解他们正在部署什么

## 有效之处

✅ **简单 PDF 和文档** - 毫秒级解析  
✅ **自动路由** - 检测复杂度并正确路由  
✅ **多格式支持** - PDF、DOCX、Markdown、HTML、图像  
✅ **清洁输出** - 格式良好的 markdown、结构化 JSON  
✅ **低开销** - 无服务器进程、无复杂设置  
✅ **跨平台** - 支持 Claude Code、Codex、Kimi 等  

## 已知限制

⚠️ **扫描 PDF（无重路径）** - 文本提取不佳  
⚠️ **大 PDF 使用重路径** - 可能较慢（根据大小 5-30 秒）  
⚠️ **模型首次下载** - 重路径首次需要 ~500MB 模型  
⚠️ **GPU 非必需但有帮助** - 重路径在 CPU 上运行但较慢  

## 下一步 / 未来工作

1. **添加进度报告** - 显示大文件的解析进度
2. **缓存层** - 缓存解析结果避免重复解析
3. **批处理** - 支持一次解析多个文件
4. **配置文件** - 允许用户自定义路由规则
5. **性能基准测试** - 在各种文档上比较快/重路径

## 为什么选择这种方法而不是 MCP？

- **MCP 很优秀**用于标准化工具发现，但比较重
- **CLI 更直接**对于 AI Agent - 更简单的集成，无额外进程
- **可以后来变成 MCP** - 核心逻辑独立于 CLI，容易包装
- **更低的入门门槛** - 用户只运行一条命令，无 MCP 服务器管理

## 许可证说明

**papyrus 包装器代码**：MIT - 随意使用  
**依赖**：
- pymupdf4llm：AGPL-3.0
- markitdown：MIT
- marker（可选重路径）：GPL-3.0 代码 + RAIL-M 模型（年收入 < $200 万的组织免费）

**用户应注意**：如果你重新分发带 marker 支持的 papyrus，你必须遵守：
- GPL-3.0 代码许可
- RAIL-M 模型许可（年收入 > $200 万不免费）

我们在 README 和 LICENSE 中明确文档化了这一点以防止意外。

---

## 如何贡献 / 扩展

1. **报告问题**：发现解析错误？在 GitHub 提交问题
2. **添加解析器**：容易添加新格式支持 - 只需在 `parsers/` 中创建新模块
3. **改进检测**：微调 `detector.py` 中的路由启发式
4. **性能**：分析和优化解析管道

---

**状态**：✅ **工作中的 MVP**  
**适用于**：Claude Code、Codex、Kimi Agent  
**下一阶段**：收集反馈，基于实际使用添加功能
