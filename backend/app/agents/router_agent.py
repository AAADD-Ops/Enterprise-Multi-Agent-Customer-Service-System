import json
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState

ROUTER_SYSTEM_PROMPT = """你是一个智能路由助手。根据用户消息判断需要哪些处理，返回 JSON：

{
  "routes": ["knowledge", "tool", "human"]
}

路由含义：
- knowledge: 产品使用问题、故障排查、FAQ、政策咨询、操作指南（优先走知识库检索）
- tool: 需要查询订单号/客户信息/工单号等具体数据时
- human: 仅限以下情况：
  1. 用户明确说"转人工""我要投诉""找真人""叫你们经理"
  2. 用户表达强烈不满或情绪激动（如辱骂、威胁升级）
  3. 用户明确拒绝机器人服务

关键判断规则：
- 问"怎么办""如何""怎么操作"是 knowledge，不是 human
- 问"好不好用""能不能""支不支持"是 knowledge，不是 human
- 问具体订单号（如 ORD-xxx）时同时加 knowledge 和 tool
- 只有用户主动要求人工时才加 human

只返回 JSON。示例：
- 问"路由器连不上网怎么办" → {"routes": ["knowledge"]}
- 问"订单 ORD-001 还没到，退款政策是什么" → {"routes": ["knowledge", "tool"]}
- 问"我要投诉，叫你们经理来" → {"routes": ["human"]}
- 问"如何重置密码" → {"routes": ["knowledge"]}
"""


async def router_agent(state: AgentState) -> dict:
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0,
    )

    messages = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + list(state["messages"][-5:])
    response = await llm.ainvoke(messages)
    content = response.content.strip()

    routes = ["knowledge"]
    need_human = False

    try:
        if "{" in content:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            parsed = json.loads(content[json_start:json_end])
            raw_routes = parsed.get("routes", ["knowledge"])
            valid = {"knowledge", "tool", "human"}
            routes = [r for r in raw_routes if r in valid] or ["knowledge"]
            need_human = "human" in routes
    except (json.JSONDecodeError, ValueError):
        pass

    return {"routes": routes, "need_human": need_human, "error": ""}
