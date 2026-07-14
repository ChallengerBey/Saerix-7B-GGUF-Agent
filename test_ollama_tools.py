#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ollama

# Test raw ollama tool calling
client = ollama.Client(host='http://localhost:11434')

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "Dizin listesi (ağaç formatında).",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "workspace'e göreli yol"}
                },
                "required": []
            }
        }
    }
]

messages = [
    {"role": "system", "content": "Sen bir dosya asistanısın. Araçları kullan."},
    {"role": "user", "content": "Projeyi listele."}
]

response = client.chat(model='qwen2.5-coder:7b', messages=messages, tools=tools)
print("Response:", response)
if 'message' in response:
    msg = response['message']
    print("Content:", msg.get('content'))
    print("Tool calls:", msg.get('tool_calls'))