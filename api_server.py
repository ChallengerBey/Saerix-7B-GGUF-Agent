#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Saerix - FastAPI Web Server
WebSocket tabanlı agent chat API
"""
import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from agent.graph import app
from agent.state import AgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from config import WORKSPACE


# Session storage (in-memory, production'da Redis kullan)
sessions: Dict[str, AgentState] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: List[Dict[str, Any]] = []


def create_new_session() -> str:
    """Yeni agent session oluştur"""
    session_id = str(uuid.uuid4())[:8]
    sessions[session_id] = {"messages": []}
    return session_id


def get_session(session_id: str) -> AgentState:
    """Session al veya oluştur"""
    if session_id not in sessions:
        sessions[session_id] = {"messages": []}
    return sessions[session_id]


def run_agent_sync(session_id: str, user_message: str) -> tuple[str, List[Dict]]:
    """Agent'ı senkron çalıştır, cevap ve tool calls döndür"""
    state = get_session(session_id)
    state["messages"].append(HumanMessage(content=user_message))
    
    tool_calls = []
    final_response = ""
    
    for chunk in app.stream(state, stream_mode="values"):
        last_msg = chunk["messages"][-1]
        
        if last_msg.__class__.__name__ == "AIMessage":
            if last_msg.content:
                final_response = last_msg.content
            if getattr(last_msg, "tool_calls", None):
                for tc in last_msg.tool_calls:
                    tool_calls.append({
                        "name": tc["name"],
                        "arguments": tc["args"]
                    })
        elif last_msg.__class__.__name__ == "ToolMessage":
            # Tool sonucu - final response'a ekleme, sadece tool_calls'a kaydet
            pass
    
    # State'i güncelle
    sessions[session_id] = chunk
    
    return final_response, tool_calls


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"[+] Server başlatıldı. Workspace: {os.path.abspath(WORKSPACE)}")
    yield
    # Shutdown
    print("[+] Server kapatılıyor...")


api = FastAPI(title="Saerix Agent API", lifespan=lifespan)

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
api.mount("/static", StaticFiles(directory=static_dir), name="static")


@api.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))


@api.get("/api/health")
async def health():
    return {"status": "ok", "model": "saerix", "workspace": WORKSPACE}


@api.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id or create_new_session()
    response, tool_calls = run_agent_sync(session_id, req.message)
    return ChatResponse(
        response=response,
        session_id=session_id,
        tool_calls=tool_calls
    )


@api.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    state = get_session(session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg["type"] == "message":
                user_message = msg["content"]
                state["messages"].append(HumanMessage(content=user_message))
                
                # Streaming response
                tool_calls = []
                final_response = ""
                
                for chunk in app.stream(state, stream_mode="values"):
                    last_msg = chunk["messages"][-1]
                    
                    if last_msg.__class__.__name__ == "AIMessage":
                        if last_msg.content:
                            final_response = last_msg.content
                            await websocket.send_json({
                                "type": "token",
                                "content": last_msg.content
                            })
                        if getattr(last_msg, "tool_calls", None):
                            for tc in last_msg.tool_calls:
                                tool_calls.append({
                                    "name": tc["name"],
                                    "arguments": tc["args"]
                                })
                                await websocket.send_json({
                                    "type": "tool_call",
                                    "tool": tc["name"],
                                    "args": tc["args"]
                                })
                    elif last_msg.__class__.__name__ == "ToolMessage":
                        await websocket.send_json({
                            "type": "tool_result",
                            "tool": last_msg.name,
                            "content": last_msg.content[:1000]
                        })
                
                sessions[session_id] = chunk
                
                await websocket.send_json({
                    "type": "done",
                    "response": final_response,
                    "tool_calls": tool_calls
                })
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


@api.get("/api/sessions/{session_id}")
async def get_session_history(session_id: str):
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    messages = []
    for m in sessions[session_id]["messages"]:
        messages.append({
            "type": m.__class__.__name__,
            "content": getattr(m, "content", "")[:500]
        })
    return {"session_id": session_id, "messages": messages}


@api.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "deleted"}


@api.get("/api/workspace/tree")
async def workspace_tree(path: str = "."):
    """Dosya ağacı döndür"""
    from pathlib import Path
    import os
    
    workspace = Path(WORKSPACE).resolve()
    target = (workspace / path).resolve()
    
    if not str(target).startswith(str(workspace)):
        raise HTTPException(403, "Workspace dışı erişim")
    
    def build_tree(p: Path, max_depth: int = 3, current_depth: int = 0):
        if current_depth > max_depth:
            return None
        try:
            if p.is_file():
                return {"name": p.name, "type": "file", "path": str(p.relative_to(workspace))}
            
            children = []
            for child in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                # __pycache__ ve .git atla
                if child.name in ("__pycache__", ".git", ".venv", "venv", "node_modules"):
                    continue
                node = build_tree(child, max_depth, current_depth + 1)
                if node:
                    children.append(node)
            
            return {"name": p.name or ".", "type": "dir", "path": str(p.relative_to(workspace)), "children": children}
        except PermissionError:
            return None
    
    tree = build_tree(target)
    return tree or {"name": ".", "type": "dir", "path": ".", "children": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)