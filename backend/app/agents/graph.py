from langgraph.graph import StateGraph, START, END

from app.agents.state import AgentState
from app.agents.router_agent import router_agent
from app.agents.retrieval_agent import retrieval_agent
from app.agents.answer_agent import answer_agent
from app.agents.tool_agent import tool_agent, tool_executor_agent
from app.agents.human_handoff_agent import human_handoff_agent


def fanout_after_router(state: AgentState) -> list[str]:
    routes = state.get("routes", ["knowledge"])
    if "human" in routes:
        return ["human_handoff"]
    dests = []
    if "knowledge" in routes:
        dests.append("retrieval_agent")
    if "tool" in routes:
        dests.append("tool_agent")
    return dests or ["answer_agent"]


def route_after_tool(state: AgentState) -> str:
    routes = state.get("routes", [])
    if "tool" not in routes:
        return "join"  # 跳过工具路径
    if state.get("tool_calls"):
        return "tool_executor"
    return "join"


def join_node(state: AgentState) -> dict:
    """汇合节点：不做任何处理，仅作为多条路径的统一汇合点。"""
    return {}


def build_graph(checkpointer=None):
    builder = StateGraph(AgentState)

    builder.add_node("router", router_agent)
    builder.add_node("retrieval_agent", retrieval_agent)
    builder.add_node("answer_agent", answer_agent)
    builder.add_node("tool_agent", tool_agent)
    builder.add_node("tool_executor", tool_executor_agent)
    builder.add_node("human_handoff", human_handoff_agent)
    builder.add_node("join", join_node)

    builder.add_edge(START, "router")

    # fork：router 根据 routes 并行派发
    builder.add_conditional_edges("router", fanout_after_router, {
        "retrieval_agent": "retrieval_agent",
        "tool_agent": "tool_agent",
        "human_handoff": "human_handoff",
        "answer_agent": "answer_agent",
    })

    # 所有路径 → join → answer_agent（保证只执行一次）
    builder.add_edge("retrieval_agent", "join")
    builder.add_edge("tool_executor", "join")
    builder.add_conditional_edges("tool_agent", route_after_tool, {
        "tool_executor": "tool_executor",
        "join": "join",
    })
    builder.add_edge("join", "answer_agent")

    builder.add_edge("answer_agent", END)
    builder.add_edge("human_handoff", END)

    if checkpointer is not None:
        return builder.compile(checkpointer=checkpointer)
    return builder.compile()


_graph = None


def get_graph(checkpointer=None):
    global _graph
    if checkpointer is not None:
        return build_graph(checkpointer=checkpointer)
    if _graph is None:
        _graph = build_graph(checkpointer=None)
    return _graph
