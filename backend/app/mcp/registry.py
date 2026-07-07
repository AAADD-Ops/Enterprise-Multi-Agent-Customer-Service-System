"""工具注册中心 - MCP Client 优先，失败降级本地"""

from __future__ import annotations
from typing import Optional, Any
import json
import httpx
from app.config import settings


async def _crm_query_local(customer_id: str) -> dict:
    if settings.crm_api_url is None:
        return {"customer_id": customer_id, "name": f"客户-{customer_id}", "level": "VIP", "tags": ["技术部门"]}
    async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
        resp = await client.get(f"{settings.crm_api_url}/customers/{customer_id}")
        return resp.json()


async def _ticket_query_local(ticket_id: str) -> dict:
    if settings.ticket_api_url is None:
        return {"ticket_id": ticket_id, "status": "处理中", "priority": "中", "assignee": "张三", "summary": "网络连接异常"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
        resp = await client.get(f"{settings.ticket_api_url}/tickets/{ticket_id}")
        return resp.json()


async def _order_query_local(order_id: str) -> dict:
    if settings.order_api_url is None:
        return {"order_id": order_id, "status": "已发货", "amount": 299.00, "items": [{"name": "路由器", "qty": 1}], "created_at": "2026-06-15"}
    async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
        resp = await client.get(f"{settings.order_api_url}/orders/{order_id}")
        return resp.json()


_LOCAL_TOOLS = {
    "crm_query": _crm_query_local,
    "ticket_query": _ticket_query_local,
    "order_query": _order_query_local,
}


class ToolRegistry:
    """MCP Client 优先，失败降级本地直调。"""

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        # 1. 优先 MCP Client
        try:
            from app.mcp.client import get_mcp_client
            client = get_mcp_client()
            result = await client.call_tool(tool_name, arguments)
            if result:
                return result
        except Exception:
            pass

        # 2. 降级本地
        handler = _LOCAL_TOOLS.get(tool_name)
        if handler is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return await handler(**arguments)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {"name": "crm_query", "description": "查询 CRM 客户信息", "parameters": {"type": "object", "properties": {"customer_id": {"type": "string"}}, "required": ["customer_id"]}},
            {"name": "ticket_query", "description": "查询工单状态", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}},
            {"name": "order_query", "description": "查询订单信息", "parameters": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}},
        ]


_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
