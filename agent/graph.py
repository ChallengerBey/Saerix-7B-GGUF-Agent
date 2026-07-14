import json
import re
import sys
from typing import Dict, Any, List

from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, ToolMessage

from .state import AgentState
from .prompts import SYSTEM_PROMPT
from tools import ALL_TOOLS
from config import OLLAMA_BASE_URL, MODEL_NAME, TEMPERATURE, NUM_CTX

TOOL_MAP = {tool.name: tool for tool in ALL_TOOLS}

llm = ChatOllama(
    base_url=OLLAMA_BASE_URL,
    model=MODEL_NAME,
    temperature=TEMPERATURE,
    num_ctx=NUM_CTX,
)

TOOL_CALL_PATTERN = re.compile(
    r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}',
    re.DOTALL
)

def parse_tool_calls(content: str) -> List[Dict[str, Any]]:
    calls = []
    for match in TOOL_CALL_PATTERN.finditer(content):
        name = match.group(1)
        args_str = match.group(2)
        try:
            args = json.loads(args_str)
            calls.append({"name": name, "arguments": args})
        except json.JSONDecodeError:
            continue
    return calls

def execute_tool(name: str, args: dict) -> str:
    tool = TOOL_MAP.get(name)
    if not tool:
        return f"HATA: Tool bulunamadi: {name}"
    try:
        result = tool.invoke(args)
        return str(result)
    except Exception as e:
        return f"HATA ({name}): {e}"

def safe_print(msg: str):
    """Windows konsolunda emoji/safe print."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('ascii', 'replace').decode('ascii'))

def call_model(state: AgentState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(state["messages"])
    response = llm.invoke(messages)
    return {"messages": [response]}

def tool_executor(state: AgentState):
    last_msg = state["messages"][-1]
    content = getattr(last_msg, "content", "")
    tool_calls = parse_tool_calls(content)
    
    if not tool_calls:
        return {"messages": []}
    
    tool_messages = []
    for tc in tool_calls:
        name = tc["name"]
        args = tc["arguments"]
        safe_print(f"[TOOL] {name}({args})")
        result = execute_tool(name, args)
        safe_print(f"[RESULT] {str(result)[:200]}")
        tool_messages.append(
            ToolMessage(content=result, tool_call_id=f"call_{name}", name=name)
        )
    
    return {"messages": tool_messages}

def should_continue(state: AgentState):
    last = state["messages"][-1]
    content = getattr(last, "content", "")
    if parse_tool_calls(content):
        return "tools"
    if isinstance(last, ToolMessage):
        return "agent"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_executor)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_conditional_edges("tools", should_continue, {"agent": "agent", END: END})

app = workflow.compile()