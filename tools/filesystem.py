import os
import re
from pathlib import Path
from langchain_core.tools import tool

WORKSPACE = Path(os.getenv("WORKSPACE", ".")).resolve()

def _safe_path(path: str) -> Path:
    p = (WORKSPACE / path).resolve()
    if not str(p).startswith(str(WORKSPACE)):
        raise PermissionError(f"Workspace dışı erişim engellendi: {path}")
    return p

@tool
def read_file(path: str) -> str:
    """Belirtilen dosyayı okur. Yol workspace köküne görelidir."""
    p = _safe_path(path)
    if not p.exists():
        return f"HATA: Dosya yok: {path}"
    if p.stat().st_size > 1_000_000:
        return f"HATA: Dosya çok büyük (>1MB): {path}"
    return p.read_text(encoding="utf-8", errors="replace")

@tool
def write_file(path: str, content: str) -> str:
    """Dosya yazar (klasörleri oluşturur). Var olanı ezer."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"OK: {path} yazıldı ({len(content)} bayt)."

@tool
def list_dir(path: str = ".") -> str:
    """Dizin listesi (ağaç formatında)."""
    p = _safe_path(path)
    if not p.is_dir():
        return f"HATA: Dizin değil: {path}"
    lines = []
    for root, dirs, files in os.walk(p):
        level = len(Path(root).relative_to(p).parts)
        indent = "  " * level
        lines.append(f"{indent}[DIR] {Path(root).name}/")
        for f in files:
            lines.append(f"{indent}  [FILE] {f}")
    return "\n".join(lines) if lines else "Boş."

@tool
def grep(pattern: str, path: str = ".", file_pattern: str = "*") -> str:
    """Dosya içinde regex arar (ilk 50 eşleşme)."""
    p = _safe_path(path)
    results = []
    regex = re.compile(pattern)
    for f in p.rglob(file_pattern):
        if f.is_file() and f.stat().st_size < 500_000:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(text.splitlines(), 1):
                    if regex.search(line):
                        rel = f.relative_to(WORKSPACE)
                        results.append(f"{rel}:{i}: {line.strip()}")
            except:
                pass
    return "\n".join(results[:50]) if results else "Eşleşme yok."