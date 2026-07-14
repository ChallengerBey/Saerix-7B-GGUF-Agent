import subprocess
import urllib.request
import json
from langchain_core.tools import tool

@tool
def port_scan(target: str, ports: str = "1-1024", args: str = "-sV -T4") -> str:
    """
    Nmap ile port tarama.
    target: IP veya domain (örn: 192.168.1.1, scanme.nmap.org)
    ports: port aralığı (örn: '80,443,8080' veya '1-65535')
    args: ek nmap argümanları (default: -sV -T4)
    """
    if not target or " " in target:
        return "HATA: Geçersiz target."
    cmd = ["nmap", "-p", ports] + args.split() + [target]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        return res.stdout + ("\n[STDERR]\n" + res.stderr if res.stderr else "")
    except FileNotFoundError:
        return "HATA: 'nmap' kurulu değil. (Windows: choco install nmap / Linux: sudo apt install nmap)"
    except Exception as e:
        return f"HATA: {e}"

@tool
def osint_query(query_type: str, target: str) -> str:
    """
    Basit OSINT sorguları.
    query_type: 'whois' | 'dig' | 'subdomain'
    target: domain veya IP
    """
    try:
        if query_type == "whois":
            cmd = ["whois", target]
        elif query_type == "dig":
            cmd = ["dig", "+short", "ANY", target]
        elif query_type == "subdomain":
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            url = f"https://crt.sh/?q=%.{target}&output=json"
            with urllib.request.urlopen(url, timeout=20, context=ctx) as r:
                data = json.load(r)
            subs = sorted({entry["name_value"].strip() for entry in data if "name_value" in entry})
            return "\n".join(subs[:100])
        else:
            return "HATA: query_type 'whois', 'dig' veya 'subdomain' olmalı."
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return res.stdout.strip() or res.stderr.strip()
    except FileNotFoundError:
        return f"HATA: '{cmd[0]}' kurulu değil."
    except Exception as e:
        return f"HATA: {e}"