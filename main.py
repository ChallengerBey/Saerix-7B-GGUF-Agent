#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from agent.graph import app
from agent.state import AgentState
from langchain_core.messages import HumanMessage
from config import WORKSPACE

def main():
    print("[+] Saerix Agent baslatildi.")
    print(f"[+] Workspace: {os.path.abspath(WORKSPACE)}")
    print("[+] Araclar: read_file, write_file, list_dir, grep, run_shell, port_scan, osint_query, uav_telemetry")
    print("[+] Cikmak icin: 'exit' veya 'quit' yazin.\n")

    state = {"messages": []}

    while True:
        try:
            user = input("Sen: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[+] Gorusmek uzere.")
            break

        if not user:
            continue
        if user.lower() in ("exit", "quit", "cikis"):
            print("[+] Gorusmek uzere.")
            break

        state["messages"].append(HumanMessage(content=user))

        # Stream modunda calistir
        for chunk in app.stream(state, stream_mode="values"):
            last_msg = chunk["messages"][-1]
            if last_msg.__class__.__name__ == "AIMessage":
                if last_msg.content:
                    print(f"Agent: {last_msg.content}")
                if getattr(last_msg, "tool_calls", None):
                    for tc in last_msg.tool_calls:
                        print(f"[Tool Cagrisi] {tc['name']}({tc['args']})")
            elif last_msg.__class__.__name__ == "ToolMessage":
                content = last_msg.content
                if len(content) > 300:
                    content = content[:300] + "..."
                print(f"[Tool Sonucu] {content}")

        # Son state'i guncelle
        state = chunk

if __name__ == "__main__":
    main()