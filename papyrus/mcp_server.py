"""MCP (Model Context Protocol) server for Papyrus document parser."""

import json
import sys
from typing import Any, Optional


class MCPServer:
    """Simple MCP server implementation for Papyrus."""

    def __init__(self):
        self.version = "1.0.0"

    def handle_request(self, request: dict) -> dict:
        """Handle MCP JSON-RPC 2.0 request."""
        request_id = request.get("id")

        try:
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                result = self.initialize(params)
            elif method == "tools/list":
                result = self.list_tools()
            elif method == "tools/call":
                result = self.call_tool(params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}",
                    },
                }
                if request_id is not None:
                    response["id"] = request_id
                return response

            response = {
                "jsonrpc": "2.0",
                "result": result,
            }
            if request_id is not None:
                response["id"] = request_id
            return response

        except Exception as e:
            response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": str(e),
                },
            }
            if request_id is not None:
                response["id"] = request_id
            return response

    def initialize(self, params: dict) -> dict:
        """Handle initialization."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {
                    "listChanged": False,
                },
            },
            "serverInfo": {
                "name": "papyrus",
                "version": "0.1.0",
            },
        }

    def list_tools(self) -> dict:
        """List available tools."""
        return {
            "tools": [
                {
                    "name": "parse_document",
                    "description": "Parse and extract content from various document formats (PDF, PPTX, DOCX, XLSX, HTML, Markdown, plain text)",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the document file to parse",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["markdown", "json"],
                                "description": "Output format (default: markdown)",
                                "default": "markdown",
                            },
                            "use_heavy": {
                                "type": "boolean",
                                "description": "Use heavy path with OCR for scanned documents (slower but better for complex/scanned PDFs)",
                                "default": False,
                            },
                            "use_fast": {
                                "type": "boolean",
                                "description": "Force fast path without OCR (faster but may fail on scanned documents)",
                                "default": False,
                            },
                        },
                        "required": ["file_path"],
                    },
                }
            ]
        }

    def call_tool(self, params: dict) -> dict:
        """Call a tool."""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})

        if tool_name == "parse_document":
            return self.parse_document_tool(tool_params)
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def parse_document_tool(self, params: dict) -> dict:
        """Parse a document using Papyrus."""
        from .cli import parse_document

        file_path = params.get("file_path")
        if not file_path:
            raise ValueError("file_path is required")

        output_format = params.get("format", "markdown")
        use_heavy = params.get("use_heavy", False)
        use_fast = params.get("use_fast", False)

        try:
            # Call the actual parsing function
            result = parse_document(
                file_path,
                output_format=output_format,
                force_heavy=use_heavy,
                force_fast=use_fast,
                verbose=False,
            )

            return result
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")
        except Exception as e:
            raise ValueError(f"Failed to parse document: {str(e)}")


def run_mcp_server():
    """Run the MCP server in stdio mode."""
    server = MCPServer()

    # Read from stdin, write to stdout
    while True:
        try:
            line = input()
            if not line.strip():
                continue

            request = json.loads(line)
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()

        except EOFError:
            break
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}",
                },
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
        except KeyboardInterrupt:
            break
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                },
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
