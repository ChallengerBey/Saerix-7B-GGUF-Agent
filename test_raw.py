#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from agent.graph import app
from langchain_core.messages import HumanMessage

# Debug: raw model output
from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL, MODEL_NAME, TEMPERATURE, NUM_CTX

llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    num_ctx=NUM_CTX,
)

from agent.prompts import SYSTEM_PROMPT
from langchain_core.messages import SystemMessage

messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content="projeyi listele")]
response = llm.invoke(messages)
print("RAW RESPONSE:")
print(f"Type: {type(response)}")
print(f"Content: {repr(response.content)}")
print(f"Tool calls attr: {getattr(response, 'tool_calls', 'YOK')}")