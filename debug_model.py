#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from config import OLLAMA_BASE_URL, MODEL_NAME, TEMPERATURE, NUM_CTX
from agent.prompts import SYSTEM_PROMPT

llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    num_ctx=NUM_CTX,
)

messages = [
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content="projeyi listele")
]

response = llm.invoke(messages)
print("Content:")
print(response.content)
print("\nTool calls attr:", getattr(response, 'tool_calls', 'YOK'))