import asyncio, json
import sys
sys.path.insert(0, r'D:\企业级多智能体客服系统\backend')

from langchain_core.messages import HumanMessage
from app.agents.tool_agent import tool_agent
from app.mcp.client import get_mcp_client

TEST_CASES = [
    {
        'name': '1. 订单查询 - 应触发 order_query',
        'query': '查询订单 ORD-001 的物流状态',
        'should_call_tool': True,
    },
    {
        'name': '2. 纯FAQ - 不应触发工具',
        'query': '退款政策是什么',
        'should_call_tool': False,
    },
    {
        'name': '3. 工单查询 - 应触发 ticket_query',
        'query': '工单 TKT-12345678 处理得怎么样了',
        'should_call_tool': True,
    },
    {
        'name': '4. 客户查询 - 应触发 crm_query',
        'query': '查一下客户 CUST-001 的信息',
        'should_call_tool': True,
    },
    {
        'name': '5. 闲聊 - 不应触发工具',
        'query': '你好，今天天气不错',
        'should_call_tool': False,
    },
]

def make_state(query):
    return {
        'messages': [HumanMessage(content=query)],
        'session_id': 'test', 'user_id': 'test',
        'routes': ['tool'], 'retrieved_docs': [],
        'tool_calls': [], 'tool_results': [],
        'need_human': False, 'summary': '', 'error': '',
    }

async def run():
    for tc in TEST_CASES:
        print('=' * 50)
        print(tc['name'])
        print(f'Query: {tc["query"]}')
        state = make_state(tc['query'])
        result = await tool_agent(state)
        calls = result.get('tool_calls', [])
        print(f'Tool calls: {len(calls)}')
        for c in calls:
            print(f'  -> {c["tool_name"]}({json.dumps(c["arguments"], ensure_ascii=False)})')
        passed = (len(calls) > 0) == tc['should_call_tool']
        print(f'Result: {"PASS" if passed else "FAIL"}')
        print()

asyncio.run(run())
