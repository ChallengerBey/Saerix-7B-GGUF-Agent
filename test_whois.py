#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from agent.graph import app
from langchain_core.messages import HumanMessage

# Test OSINT query
result = app.invoke({'messages': [HumanMessage(content='example.com whois sorgula')]})
for msg in result['messages']:
    cls = msg.__class__.__name__
    content = getattr(msg, 'content', '')
    print(f"{cls}: {str(content)[:300]}")
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        print(f"  TOOL CALLS: {msg.tool_calls}")