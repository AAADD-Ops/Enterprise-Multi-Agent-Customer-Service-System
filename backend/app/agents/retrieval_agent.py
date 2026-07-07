from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agents.state import AgentState
from app.rag.hybrid_retriever import get_hybrid_retriever
import json

QUERY_ANALYSIS_PROMPT = """分析用户问题，提取检索所需的信息，返回 JSON：

{{
  "intent": "用户意图（如：退款咨询/操作指南/故障排查/政策查询）",
  "keywords": ["关键词1", "关键词2"],
  "entities": ["实体名"],
  "rewritten": "改写后的检索查询（去除口语，保留核心术语，≤30字）"
}}

只返回 JSON。

用户问题：{query}"""

SELF_EVAL_PROMPT = """你是一个检索质量评估助手。判断以下检索结果是否能回答用户问题。

用户问题：{query}

检索结果：
{docs_summary}

返回 JSON：
{{"sufficient": true/false, "score": 0-10, "missing": "缺少什么信息（sufficient为false时填写）"}}"""

REFORMULATE_PROMPT = """第一次检索结果不充分，请换一个角度改写查询。

原始问题：{query}
上次改写：{last_query}
缺失信息：{missing}

只输出改写后的检索查询（≤30字），不要解释。"""

FILTER_PROMPT = """判断以下文档块是否与用户问题相关，只输出 "相关" 或 "不相关"。

用户问题：{query}
文档内容：{content}"""

_llm_singleton = None
 

def _get_llm():
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0,
        )
    return _llm_singleton


async def _parse_json_response(llm, messages) -> dict:
    """安全解析 LLM 返回的 JSON。"""
    try:
        response = await llm.ainvoke(messages)
        content = response.content.strip()
        if "{" in content:
            json_start = content.index("{")
            json_end = content.rindex("}") + 1
            return json.loads(content[json_start:json_end])
    except Exception:
        pass
    return {}


async def retrieval_agent(state: AgentState) -> dict:
    """检索智能体：LLM 驱动查询分析 → 混合检索 → 自我评估 → 迭代精炼 → 智能过滤。"""
    retriever = get_hybrid_retriever()
    last_message = state["messages"][-1]
    user_query = last_message.content if hasattr(last_message, "content") else str(last_message)
    llm = _get_llm()

    # ========== 阶段 1：查询意图分析（LLM）==========
    analysis = await _parse_json_response(
        llm,
        [SystemMessage(content=QUERY_ANALYSIS_PROMPT.format(query=user_query))]
    )
    rewritten = analysis.get("rewritten", user_query)
    keywords = analysis.get("keywords", [])

    # ========== 阶段 2：混合检索 ==========
    docs = await retriever.retrieve(rewritten)

    # ========== 阶段 3：自我评估（LLM 判断结果质量）==========
    if docs:
        docs_summary = "\n".join([
            f"[{i+1}] {d['content'][:200]}..." for i, d in enumerate(docs[:5])
        ])
        evaluation = await _parse_json_response(
            llm,
            [SystemMessage(content=SELF_EVAL_PROMPT.format(
                query=user_query, docs_summary=docs_summary
            ))]
        )
    else:
        evaluation = {"sufficient": False, "score": 0, "missing": "未检索到任何结果"}

    # ========== 阶段 4：迭代精炼（最多 2 次补充检索）==========
    max_retries = 2
    tried_queries = {rewritten}
    for _ in range(max_retries):
        if evaluation.get("sufficient") or evaluation.get("score", 0) >= 6:
            break

        missing = evaluation.get("missing", "")
        try:
            resp = await llm.ainvoke([SystemMessage(content=REFORMULATE_PROMPT.format(
                query=user_query, last_query=rewritten, missing=missing
            ))])
            new_query = resp.content.strip()
        except Exception:
            break
        if not new_query or new_query in tried_queries:
            break

        tried_queries.add(new_query)
        additional_docs = await retriever.retrieve(new_query)
        if additional_docs:
            # 去重合并
            seen_contents = {d["content"] for d in docs}
            for ad in additional_docs:
                if ad["content"] not in seen_contents:
                    docs.append(ad)
                    seen_contents.add(ad["content"])

            # 重新评估
            docs_summary = "\n".join([
                f"[{i+1}] {d['content'][:200]}..." for i, d in enumerate(docs[:8])
            ])
            evaluation = await _parse_json_response(
                llm,
                [SystemMessage(content=SELF_EVAL_PROMPT.format(
                    query=user_query, docs_summary=docs_summary
                ))]
            )

    # ========== 阶段 5：智能过滤（LLM 剔除不相关文档）==========
    if docs:
        filtered_docs = []
        for doc in docs:
            try:
                response = await llm.ainvoke([
                    SystemMessage(content=FILTER_PROMPT.format(
                        query=user_query, content=doc["content"][:500]
                    ))
                ])
                if "相关" in response.content and "不相关" not in response.content:
                    filtered_docs.append(doc)
            except Exception:
                filtered_docs.append(doc)  # 出错时保留
        if filtered_docs:
            docs = filtered_docs

    return {"retrieved_docs": docs, "error": ""}
