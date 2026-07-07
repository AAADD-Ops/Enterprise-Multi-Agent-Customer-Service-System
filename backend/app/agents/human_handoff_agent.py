import json
import uuid
from langchain_core.messages import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState

HANDOFF_ANALYSIS_PROMPT = """分析以下用户对话，返回 JSON（不要其他内容）:

{
  "summary": "问题摘要（30字以内）",
  "category": "产品质量|服务态度|系统故障|物流配送|其他",
  "priority": "normal|urgent|critical"
}

对话:
{conversation}"""

REPLY_TEMPLATES = {
    "critical": "您的问题已触发紧急响应流程，工单 {ticket_id} 已创建并通知值班经理，请保持电话畅通，我们将在 5 分钟内与您联系。\n\n【问题摘要】{summary}\n【分类】{category}",
    "urgent": "您的问题已创建紧急工单 {ticket_id}，已优先派发给客服团队，预计 30 分钟内回复您。\n\n【问题摘要】{summary}\n【分类】{category}",
    "normal": "您的问题已转接至人工客服，工单 {ticket_id} 已创建，客服人员将在 24 小时内与您联系。在此期间您可以继续描述问题以便更快解决。\n\n【问题摘要】{summary}\n【分类】{category}",
}


async def human_handoff_agent(state: AgentState) -> dict:
    # 1. 提取对话历史
    messages = state.get("messages", [])
    conversation_lines = []
    for m in messages[-10:]:
        role = "用户" if (hasattr(m, "type") and m.type == "human") else "客服"
        content = m.content if hasattr(m, "content") else str(m)
        conversation_lines.append(f"{role}: {content}")
    conversation = "\n".join(conversation_lines)

    # 2. LLM 分析对话：生成摘要、分类、优先级
    ticket_id = uuid.uuid4().hex[:8].upper()
    info = {"summary": "用户请求人工处理", "category": "其他", "priority": "normal"}

    try:
        llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0,
        )
        prompt = HANDOFF_ANALYSIS_PROMPT.format(conversation=conversation)
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        content = response.content.strip()
        if "{" in content:
            start = content.index("{")
            end = content.rindex("}") + 1
            parsed = json.loads(content[start:end])
            info["summary"] = parsed.get("summary", info["summary"])
            info["category"] = parsed.get("category", info["category"])
            info["priority"] = parsed.get("priority", info["priority"])
    except (json.JSONDecodeError, ValueError, Exception):
        pass  # LLM 不可用时使用默认值

    # 3. 根据优先级生成差异化回复
    template = REPLY_TEMPLATES.get(info["priority"], REPLY_TEMPLATES["normal"])
    reply = template.format(
        ticket_id=ticket_id,
        summary=info["summary"],
        category=info["category"],
    )

    return {"messages": [AIMessage(content=reply)], "need_human": True, "error": ""}
