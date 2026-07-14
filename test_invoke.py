#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from agent.graph import app
from langchain_core.messages import HumanMessage

result = app.invoke({'messages': [HumanMessage(content='projeyi listele')]}, config={'recursion_limit': 10})
for msg in result['messages']:
    cls = msg.__class__.__name__
    content = getattr(msg, 'content', '')
    print(f"{cls}: {str(content)[:300]}")