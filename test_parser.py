#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json

TOOL_CALL_PATTERN = re.compile(
    r'\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"arguments"\s*:\s*(\{.*?\})\s*\}',
    re.DOTALL
)

content = """DÜŞÜN: Kullanıcı proje yapısını istiyor. list_dir aracını kullanmalıyım.
EYLEM: {"name": "list_dir", "arguments": {"path": "."}}
GÖZLEM: (araç sonucu)
DEVAM ET: Sonucu kullanıcıya özetle."""

def parse_tool_calls(content: str):
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

result = parse_tool_calls(content)
print("Parsed:", result)