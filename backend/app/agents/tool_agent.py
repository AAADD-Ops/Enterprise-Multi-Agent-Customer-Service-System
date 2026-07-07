import json
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState
from app.mcp.registry import get_registry
from app.mcp.client import get_mcp_client

TOOL_AGENT_PROMPT = """你是企业客服工具调度助手。

规则：
1. 用户提到具体订单号（如 ORD-xxx）时，调用 order_query 查询
2. 用户提到具体工单号（如 TKT-xxx）时，调用 ticket_query 查询
3. 用户要查客户信息时，调用 crm_query 查询
4. 闲聊或一般问题直接文字回复，不要调用工具
5. 每次只调用一个工具"""


async def tool_agent(state: AgentState) -> dict:
    """工具调用Agent：LLM 原生 Function Calling 动态发现工具。"""
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0,
    )

    # 从 MCP Server 动态拉取工具列表，转 Function Calling 格式
    client = get_mcp_client()
    await client.list_tools()
    tool_defs = client.get_tool_definitions_for_llm()

    messages = [SystemMessage(content=TOOL_AGENT_PROMPT)] + list(state["messages"][-8:])
    response = await llm.ainvoke(messages, tools=tool_defs, tool_choice="auto" if tool_defs else "none")

    # LLM 原生返回 tool_calls，转换为内部格式
    if response.tool_calls:
        internal_calls = []
        for tc in response.tool_calls:
            internal_calls.append({
                "call_id": tc["id"],
                "tool_name": tc["name"],
                "arguments": tc["args"],
            })
        return {
            "tool_calls": internal_calls,
            "messages": [response],
            "error": "",
        }

    # 不需要调用工具
    return {"messages": [response], "error": ""}


async def tool_executor_agent(state: AgentState) -> dict:
    """工具执行Agent：遍历tool_calls列表，通过注册中心执行工具调用，生成ToolMessage。"""
    registry = get_registry()
    tool_results: list[dict] = []
    tool_messages: list[ToolMessage] = []

    for call in state.get("tool_calls", []):
        call_id = call.get("call_id", "unknown")
        try:
            # 通过注册中心执行工具（优先MCP，失败降级本地）
            result = await registry.execute(call["tool_name"], call["arguments"])
            tool_results.append({
                "tool_name": call["tool_name"],
                "arguments": call["arguments"],
                "result": result,
            })
            tool_messages.append(ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=call_id,
            ))
        except Exception as exc:
            err_msg = str(exc)
            tool_results.append({
                "tool_name": call["tool_name"],
                "arguments": call["arguments"],
                "error": err_msg,
            })
            tool_messages.append(ToolMessage(
                content=json.dumps({"error": err_msg}, ensure_ascii=False),
                tool_call_id=call_id,
            ))

    return {
        "tool_results": tool_results,
        "tool_calls": [],  # 清空标记执行完成
        "messages": tool_messages,
    }
