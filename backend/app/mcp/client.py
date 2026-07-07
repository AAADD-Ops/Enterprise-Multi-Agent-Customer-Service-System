"""MCP Client - 基于 Anthropic 官方 MCP SDK"""

from __future__ import annotations
from typing import Any
from contextlib import asynccontextmanager
import asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from app.config import settings


class MCPClient:
    """连接到 MCP Server，动态发现和调用工具。"""

    def __init__(self, server_url: str | None = None):
        self._server_url = (server_url or f"http://localhost:{settings.mcp_server_port}/sse").rstrip("/")
        self._tools_cache: list[dict[str, Any]] | None = None

    @asynccontextmanager
    async def _connect(self):
        """建立 SSE 连接并创建会话。"""
        async with sse_client(self._server_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    async def list_tools(self) -> list[dict[str, Any]]:
        """获取 MCP Server 上注册的所有工具。"""
        if self._tools_cache is not None:
            return self._tools_cache
        async with self._connect() as session:
            result = await session.list_tools()
            self._tools_cache = [
                {"name": t.name, "description": t.description, "parameters": t.inputSchema}
                for t in result.tools
            ]
            return self._tools_cache

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """调用工具，30s 超时兜底。"""
        async with self._connect() as session:
            result = await asyncio.wait_for(
                session.call_tool(tool_name, arguments),
                timeout=30.0,
            )
            if result.content:
                text = result.content[0].text
                if text:
                    import json
                    return json.loads(text) if text.startswith("{") else text
            return None

    def get_tool_definitions_for_llm(self) -> list[dict[str, Any]]:
        """将工具列表转为 OpenAI Function Calling 格式。"""
        raw = self._tools_cache or []
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t.get("parameters", {"type": "object", "properties": {}, "required": []}),
                },
            }
            for t in raw
        ]


_client: MCPClient | None = None


def get_mcp_client() -> MCPClient:
    global _client
    if _client is None:
        _client = MCPClient()
    return _client
