import json
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState

ANSWER_SYSTEM_PROMPT = """你是一个专业的企业客服助手。请根据提供的参考信息回答用户问题。

规则：
1. 如果【工具查询结果】有数据，必须优先列出订单状态、商品、金额等精确信息，再结合知识库给出建议。
2. 如果【知识库内容】有相关政策，在工具数据之后补充说明。
3. 两者都没有则诚实告知。
4. 友好专业，分步骤时用编号列表。

参考信息：
{context}"""


async def answer_agent(state: AgentState) -> dict:
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.3,
    )

    context_parts = []

    # 1. 工具结果
    tool_results = state.get("tool_results", [])
    if tool_results:
        tool_context = "【工具查询结果 - 必须优先使用以下精确数据】\n"
        for tr in tool_results:
            tool_context += f"\n工具: {tr['tool_name']}\n"
            tool_context += f"参数: {json.dumps(tr['arguments'], ensure_ascii=False)}\n"
            tool_context += f"结果: {json.dumps(tr.get('result', tr.get('error', '')), ensure_ascii=False, indent=2)}\n"
        context_parts.append(tool_context)

    # 2. 知识库
    docs = state.get("retrieved_docs", [])
    if docs:
        doc_context = "\n\n---\n\n".join([d["content"] for d in docs])
        context_parts.append(f"【知识库内容 - 作为补充参考】\n{doc_context}")

    # === 改动3: 如果有历史摘要，插入到上下文最前面 ===
    summary = state.get("summary", "")
    if summary:
        context_parts.insert(0, f"【对话历史摘要】\n{summary}")
    context = "\n\n---\n\n".join(context_parts) if context_parts else "暂无相关参考信息"

    # 3. 过滤中间工具消息
    filtered = []
    for m in state["messages"]:
        if isinstance(m, ToolMessage):
            continue
        if isinstance(m, AIMessage) and hasattr(m, "tool_calls") and m.tool_calls:
            continue
        filtered.append(m)

    # 4. 生成回答
    system_prompt = ANSWER_SYSTEM_PROMPT.format(context=context)
    messages = [SystemMessage(content=system_prompt)] + filtered
    response = await llm.ainvoke(messages)

    return {"messages": [AIMessage(content=response.content)], "error": ""}
