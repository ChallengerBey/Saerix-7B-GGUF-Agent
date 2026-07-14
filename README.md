# SaerixAgent

LangGraph ReAct agent for Saerix LLM with 8 tools: filesystem, shell, network/OSINT, UAV telemetry, and RAG knowledge retrieval (OSW1 dataset).

## Features

- **ReAct Loop** — Thought → Action → Observation → Final Answer
- **8 Tools** — File ops, shell, port scan, OSINT, UAV, RAG
- **FastAPI Server** — REST API + Web UI
- **CLI Chat** — Interactive terminal loop

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # Set OLLAMA_URL if needed

# CLI chat
python chat.py

# API server (port 8000)
python api_server.py
# Web UI: http://localhost:8000
# API:    POST http://localhost:8000/chat {"message": "..."}
```

## Tools

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents |
| `write_file` | Write file |
| `list_dir` | List directory |
| `grep` | Search code/content |
| `run_shell` | Execute shell commands (allowlisted) |
| `port_scan` | Nmap port/service scan |
| `osint_query` | WHOIS, DNS, subdomain (crt.sh) |
| `knowledge_query` | RAG search on OSW1 dataset |

## Example Usage

```
User: Projeyi listele
→ Agent uses list_dir

User: src/main.py dosyasını oku
→ Agent uses read_file

User: Port 8080'de ne var?
→ Agent uses port_scan

User: example.com whois sorgula
→ Agent uses osint_query

User: Python async await nasıl çalışır?
→ Agent uses knowledge_query (RAG on OSW1)
```

## Architecture

```
SaerixAgent/
├── agent/
│   ├── graph.py          # LangGraph ReAct workflow
│   ├── prompts.py        # System prompt + ReAct examples
│   └── state.py          # AgentState definition
├── tools/
│   ├── filesystem.py     # read/write/list/grep
│   ├── shell.py          # run_shell (allowlisted)
│   ├── network.py        # port_scan, osint_query
│   ├── uav.py            # uav_telemetry (stub)
│   └── rag.py            # knowledge_query (ChromaDB)
├── static/               # Web UI (HTML/JS/CSS)
├── api_server.py         # FastAPI server
├── chat.py               # CLI chat loop
├── main.py               # Entry point
└── requirements.txt
```

## Requirements

- Python 3.10+
- Ollama running with Saerix model (`ollama run saerix`)
- ChromaDB vector store at `../rag_db` (OSW1 knowledge)

```bash
pip install langchain-core langgraph fastapi uvicorn python-dotenv chromadb requests
```

## Configuration

`.env` file:
```env
OLLAMA_URL=http://localhost:11434
MODEL_NAME=saerix:latest
WORKSPACE=./workspace
```

## License

Apache 2.0

## Developer

**Semih Ergili** — [@ChallengerBey](https://github.com/ChallengerBey)
