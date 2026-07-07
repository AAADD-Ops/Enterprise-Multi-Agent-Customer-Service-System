import asyncio, json
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.state import AgentState
from app.agents.router_agent import router_agent
from app.agents.retrieval_agent import retrieval_agent
from app.agents.answer_agent import answer_agent
from app.agents.human_handoff_agent import human_handoff_agent

TEST_CASES = [
    {
        'name': '1. 知识库检索 - 技术支持',
        'query': '我上个月买的路由器连不上网了怎么办',
    },
    {
        'name': '2. 知识库+工具 - 订单+退款',
        'query': '订单 ORD-001 还没到，退款政策是什么',
    },
    {
        'name': '3. 转人工 - 投诉',
        'query': '我要投诉，你们服务太差了',
    },
    {
        'name': '4. 知识库检索 - 操作指南',
        'query': '如何重置密码',
    },
]

def make_state(query):
    return {
        'messages': [HumanMessage(content=query)],
        'session_id': 'test', 'user_id': 'test',
        'routes': ['knowledge'], 'retrieved_docs': [],
        'tool_calls': [], 'tool_results': [],
        'need_human': False, 'summary': '', 'error': '',
    }

async def run():
    for tc in TEST_CASES:
        print('=' * 60)
        print(tc['name'])
        print(f"用户: {tc['query']}")
        print('-' * 60)
        
        state = make_state(tc['query'])
        
        # Router
        result = await router_agent(state)
        state.update(result)
        print(f"路由: {state['routes']}")
        
        # Branch
        if 'human' in state['routes']:
            result = await human_handoff_agent(state)
            content = result['messages'][0].content
            print(f"AI客服: {content[:200]}...")
        else:
            if 'knowledge' in state['routes']:
                result = await retrieval_agent(state)
                state.update(result)
                print(f"检索到: {len(state['retrieved_docs'])} 个文档")
            
            result = await answer_agent(state)
            content = result['messages'][0].content
            print(f"AI客服: {content[:300]}...")
        print()

asyncio.run(run())
