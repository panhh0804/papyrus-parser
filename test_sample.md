# Test Document

This is a sample markdown document for testing the papyrus tool.

## Features

- Fast parsing with pymupdf4llm and markitdown
- Heavy parsing with marker for complex documents
- Smart routing based on document characteristics

## Code Example

```python
from papyrus import route_file, parse_with_fast_path

result = parse_with_fast_path("document.pdf")
print(result["content"])
```

## Summary

The papyrus tool provides a unified CLI for parsing documents across multiple AI assistant platforms.
