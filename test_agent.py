from agent.graph import app
from agent.state import AgentState
from langchain_core.messages import HumanMessage

state = {'messages': [HumanMessage(content='Projeyi listele')]}
result = app.invoke(state)
print('Messages:', len(result['messages']))
for m in result['messages']:
    content = getattr(m, 'content', '')
    print(f'{m.__class__.__name__}: {content[:200]}')