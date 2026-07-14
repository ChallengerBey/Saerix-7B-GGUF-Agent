#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Saerix - İnteraktif Agent Chat
Ollama modeli + LangGraph agent + Tools (ReAct pattern)
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.graph import app
from agent.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from config import WORKSPACE

def main():
    print("=" * 60)
    print("  Saerix Agent - İnteraktif Chat")
    print("=" * 60)
    print(f"Workspace: {os.path.abspath(WORKSPACE)}")
    print("Araçlar: read_file, write_file, list_dir, grep,")
    print("         run_shell, port_scan, osint_query, uav_telemetry")
    print("Çıkış: 'exit', 'quit', 'çıkış'")
    print("=" * 60)
    print()

    state = {"messages": []}

    while True:
        try:
            user = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGörüşmek üzere!")
            break

        if not user:
            continue
        if user.lower() in ("exit", "quit", "çıkış", "cikis"):
            print("Görüşmek üzere!")
            break

        state["messages"].append(HumanMessage(content=user))

        # Stream modunda çalıştır
        for chunk in app.stream(state, stream_mode="values"):
            last_msg = chunk["messages"][-1]
            
            if last_msg.__class__.__name__ == "AIMessage":
                if last_msg.content:
                    print(f"Agent: {last_msg.content}")
                if getattr(last_msg, "tool_calls", None):
                    for tc in last_msg.tool_calls:
                        print(f"  [Tool Çağrısı] {tc['name']}({tc['args']})")
            elif last_msg.__class__.__name__ == "ToolMessage":
                content = last_msg.content
                if len(content) > 500:
                    content = content[:500] + "..."
                print(f"  [Tool Sonucu] {content}")

        # State'i güncelle
        state = chunk

        print()

if __name__ == "__main__":
    main()