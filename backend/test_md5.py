import asyncio, hashlib, sys
sys.path.insert(0, r'D:\企业级多智能体客服系统\backend')
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from app.config import settings

QUERY_ANALYSIS_PROMPT = """分析用户问题，提取检索所需的信息，返回 JSON：
{
  "intent": "用户意图",
  "keywords": ["关键词1", "关键词2"],
  "entities": ["实体名"],
  "rewritten": "改写后的检索查询"
}
只返回 JSON。
用户问题：{query}"""

TEST_PAIRS = [
    ("路由器连不上网怎么办", "路由器上不了网咋整"),
    ("订单 ORD-001 还没到", "ORD-001 的物流状态"),
    ("如何重置密码", "密码忘了怎么办"),
]

async def test():
    llm = ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0,
    )
    for q1, q2 in TEST_PAIRS:
        print(f'原始1: {q1}')
        print(f'原始2: {q2}')
        r1 = await llm.ainvoke([SystemMessage(content=QUERY_ANALYSIS_PROMPT.format(query=q1))])
        r2 = await llm.ainvoke([SystemMessage(content=QUERY_ANALYSIS_PROMPT.format(query=q2))])
        import json
        try:
            c1 = r1.content.strip()
            c2 = r2.content.strip()
            if '{' in c1: c1 = c1[c1.index('{'):c1.rindex('}')+1]
            if '{' in c2: c2 = c2[c2.index('{'):c2.rindex('}')+1]
            j1 = json.loads(c1)
            j2 = json.loads(c2)
            rw1 = j1.get('rewritten', q1)
            rw2 = j2.get('rewritten', q2)
            md5_1 = hashlib.md5(rw1.encode()).hexdigest()
            md5_2 = hashlib.md5(rw2.encode()).hexdigest()
            print(f'  改写1: {rw1}')
            print(f'  改写2: {rw2}')
            print(f'  MD5相同: {md5_1 == md5_2}')
        except:
            print('  解析失败')
        print()

asyncio.run(test())
