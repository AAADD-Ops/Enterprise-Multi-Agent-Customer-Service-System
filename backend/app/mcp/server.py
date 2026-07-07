"""MCP Server - 基于 Anthropic 官方 MCP SDK (FastMCP + SSE 传输)"""

import asyncio
from mcp.server.fastmcp import FastMCP
from app.config import settings

mcp = FastMCP(
    name="enterprise-tools",
    host="0.0.0.0",
    port=settings.mcp_server_port,
    instructions="企业级多智能体客服系统 —— 提供 CRM 客户查询、工单查询、订单查询工具",
)


# ── CRM 客户查询 ──────────────────────────────────────

@mcp.tool(
    name="crm_query",
    description="查询 CRM 客户信息，返回客户姓名、等级、标签和历史备注。",
)
async def crm_query(customer_id: str) -> dict:
    import httpx
    if settings.crm_api_url is None:
        return {
            "customer_id": customer_id,
            "name": f"客户-{customer_id}",
            "level": "VIP",
            "tags": ["技术部门"],
            "notes": "（mock 数据 - 设置 CRM_API_URL 接入真实 CRM）",
        }
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.crm_api_url}/customers/{customer_id}")
        return resp.json()


# ── 工单查询 ──────────────────────────────────────────

@mcp.tool(
    name="ticket_query",
    description="查询工单状态，返回工单状态、优先级、负责人和摘要。",
)
async def ticket_query(ticket_id: str) -> dict:
    import httpx
    if settings.ticket_api_url is None:
        return {
            "ticket_id": ticket_id,
            "status": "处理中",
            "priority": "中",
            "assignee": "张三",
            "summary": "网络连接异常",
        }
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.ticket_api_url}/tickets/{ticket_id}")
        return resp.json()


# ── 订单查询 ──────────────────────────────────────────

@mcp.tool(
    name="order_query",
    description="查询订单信息，返回订单状态、金额、商品明细和创建时间。",
)
async def order_query(order_id: str) -> dict:
    import httpx
    if settings.order_api_url is None:
        return {
            "order_id": order_id,
            "status": "已发货",
            "amount": 299.00,
            "items": [{"name": "路由器", "qty": 1}],
            "created_at": "2026-06-15",
        }
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{settings.order_api_url}/orders/{order_id}")
        return resp.json()


# ── 启动入口 ──────────────────────────────────────────

async def run_mcp_server():
    """以 SSE 模式启动 MCP Server（独立进程，端口 9000）"""
    await mcp.run_sse_async()


def main():
    asyncio.run(run_mcp_server())


if __name__ == "__main__":
    main()
