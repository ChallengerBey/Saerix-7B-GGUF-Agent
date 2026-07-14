from langchain_core.tools import tool
from tools.filesystem import read_file, write_file, list_dir, grep
from tools.shell import run_shell
from tools.network import port_scan, osint_query
from tools.uav import uav_telemetry
from tools.rag import knowledge_query

ALL_TOOLS = [
    read_file,
    write_file,
    list_dir,
    grep,
    run_shell,
    port_scan,
    osint_query,
    uav_telemetry,
    knowledge_query,
]