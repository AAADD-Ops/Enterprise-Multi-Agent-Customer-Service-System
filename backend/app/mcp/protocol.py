"""MCP 协议定义 - 基于 Anthropic 官方 MCP SDK

本项目采用官方 mcp 包 (FastMCP + SSE 传输) 实现工具服务化。
工具定义通过 @mcp.tool() 装饰器声明在 server.py 中。
Client 通过 ClientSession + sse_client 进行工具发现和调用。
"""

# 保留以下类型用于内部状态传递（LangGraph AgentState）
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MCPToolCall:
    """工具调用请求（内部状态用）"""
    tool_name: str
    arguments: dict[str, Any]
    call_id: str = ""


@dataclass
class MCPToolResult:
    """工具调用结果（内部状态用）"""
    call_id: str
    tool_name: str
    content: Any
    error: str | None = None
