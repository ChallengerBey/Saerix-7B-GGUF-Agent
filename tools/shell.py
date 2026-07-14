import subprocess
import shlex
import os
from langchain_core.tools import tool

ALLOWED_CMDS = {
    "ls", "cat", "head", "tail", "grep", "rg", "find", "stat",
    "python3", "python", "pip", "dotnet", "cargo", "go", "npm", "node",
    "git", "docker", "kubectl", "nmap", "dig", "whois", "curl", "wget",
    "ping", "netstat", "ss", "lsof", "ps", "top", "htop",
    "make", "cmake", "gcc", "clang", "rustc",
}

@tool
def run_shell(command: str, timeout: int = 120) -> str:
    """
    Güvenli shell komutu çalıştırır.
    İzin verilen komutlar: ls, cat, grep, find, python, git, nmap, docker, kubectl, dotnet, cargo, go, npm, make, cmake, ping, dig, whois, curl, wget, netstat, ss, lsof, ps.
    Komut en başta bu kelimelerden biriyle başlamalıdır.
    """
    parts = shlex.split(command)
    if not parts:
        return "HATA: Boş komut."
    base = parts[0].split("/")[-1]
    if base not in ALLOWED_CMDS:
        return f"HATA: Bu komut izinsiz: '{base}'. İzinli: {', '.join(sorted(ALLOWED_CMDS))}"

    try:
        res = subprocess.run(
            parts, capture_output=True, text=True, timeout=timeout, cwd=os.getenv("WORKSPACE", ".")
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        if res.returncode != 0:
            return f"EXIT {res.returncode}\nSTDOUT:\n{out}\nSTDERR:\n{err}"
        return out if out else "(çıktı yok)"
    except subprocess.TimeoutExpired:
        return f"HATA: Timeout ({timeout}s)."
    except Exception as e:
        return f"HATA: {e}"