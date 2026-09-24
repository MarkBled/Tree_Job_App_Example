#!/usr/bin/env python3
"""Prošnje -> kandidati (out/kandidati.json).

Kandidat = glava "Kandidat N: Ime" + besedilo do naslednje glave.
Besedilo je normalizirano (presledki), da je dobesedne citate mogoče preveriti mehansko.
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
HEAD_RE = re.compile(r"(?:\U0001F464\s*)?Kandidat\s+(\d+)\s*:\s*([^\n\"]+)")


def norm(t: str) -> str:
    t = t.replace("“", '"').replace("”", '"').replace("’", "'").replace(" ", " ")
    return re.sub(r"\s+", " ", t).strip()


def pdf_pages(path: Path):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(path)], capture_output=True).stdout.decode("utf-8", "replace")).group(1))
    return [subprocess.run(["pdftotext", "-enc", "UTF-8", "-f", str(p), "-l", str(p), str(path), "-"],
                           capture_output=True, check=True).stdout.decode("utf-8") for p in range(1, n + 1)]


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else BASE / "data" / "Prosnje_kandidatov.pdf")
    pages = pdf_pages(src)
    full = "\n".join(pages)
    heads = list(HEAD_RE.finditer(full))
    out = []
    for k, m in enumerate(heads):
        end = heads[k + 1].start() if k + 1 < len(heads) else len(full)
        raw = full[m.start():end]
        start_page = next(i + 1 for i, p in enumerate(pages) if m.group(0).strip() in p)
        tail = norm(raw)[-40:]
        end_page = next((i + 1 for i, p in enumerate(pages) if tail in norm(p)), start_page)
        ime = m.group(2).strip()
        out.append({
            "id": f"K{m.group(1)}",
            "ime": ime,
            "naziv": "Dr." if ime.startswith("Dr.") else None,
            "strani": [start_page, end_page],
            "besedilo": norm(raw),
        })
    res = {"vir": src.name, "sha256": hashlib.sha256(src.read_bytes()).hexdigest(), "kandidati": out}
    (BASE / "out" / "kandidati.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(out)} kandidatov -> out/kandidati.json")


if __name__ == "__main__":
    main()
