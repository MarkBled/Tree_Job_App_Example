#!/usr/bin/env python3
"""1. korak: PDF/besedilo -> postavke (out/items.json).

Postavka = oznaka "Naziv:" + besedilo do naslednje oznake.
Razdelek (K/P/M) določajo oznake razdelkov iz cues.json.
Uporaba: python3 segment.py data/JobReqId26984690.pdf
"""
import json, re, subprocess, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
CUES = json.loads((BASE / "cues.json").read_text(encoding="utf-8"))

NORMALIZE = {"​": "", "‑": "-", "’": "'", " ": " ", "‐": "-"}
LABEL_RE = re.compile(r"(?:(?<=^)|(?<=[\s.:]))([A-Z][A-Za-z&/\-]*(?: (?:[A-Za-z&/\-]+))*?):(?=\s|[A-Z])")
SMALL_WORDS = {"to", "and", "of", "&", "for", "in"}
SENT_RE = re.compile(r"(?<=\.)\s+(?=[A-Z0-9])")


def read_text(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        # izrecno UTF-8 (na Windows bi text=True dekodiral s cp1252 in pokvaril znake, npr. '‑' -> 'â€‘')
        t = subprocess.run(["pdftotext", "-enc", "UTF-8", str(path), "-"], capture_output=True, check=True).stdout.decode("utf-8")
    else:
        t = path.read_text(encoding="utf-8")
    for a, b in NORMALIZE.items():
        t = t.replace(a, b)
    return re.sub(r"\s+", " ", t).strip()


def is_label(s: str) -> bool:
    words = s.split()
    if not 1 <= len(words) <= 5:
        return False
    return all(w[0].isupper() or w in SMALL_WORDS for w in words)


def split_sentences(t: str):
    return [s.strip() for s in SENT_RE.split(t) if s.strip()]


def segment(text: str):
    razdelki = CUES["oznake_razdelkov"]
    labels = []
    for m in LABEL_RE.finditer(text):
        name, start = m.group(1), m.start()
        # "Job Overview Role Overview" -> "Role Overview" (naslov brez dvopičja pred oznako)
        for key in razdelki:
            if name != key and name.endswith(" " + key):
                start, name = m.end() - len(key) - 1, key
        if is_label(name):
            labels.append((name, start, m.end()))
    # meta = vse pred prvo oznako razdelka
    first = next((l for l in labels if l[0] in razdelki), None)
    meta = text[: first[1]].strip() if first else ""
    labels = [l for l in labels if first and l[1] >= first[1]]

    items, razdelek, n = [], None, 0
    for k, (name, _start, lend) in enumerate(labels):
        end = labels[k + 1][1] if k + 1 < len(labels) else len(text)
        body = text[lend:end].strip()
        if name in razdelki:
            razdelek = razdelki[name]
            if not body:
                continue  # čista oznaka razdelka (npr. "Qualifications:")
        n += 1
        items.append({
            "id": f"I{n:02d}",
            "oznaka": name,
            "razdelek": razdelek,
            "obveznost_oznake": CUES["prepis_obveznosti_oznake"].get(name, razdelek),
            "besedilo": body,
            "stavki": split_sentences(body),
        })
    return {"meta": meta, "postavke": items}


def main():
    src = Path(sys.argv[1] if len(sys.argv) > 1 else BASE / "data" / "JobReqId26984690.pdf")
    res = segment(read_text(src))
    res["vir"] = src.name
    out = BASE / "out" / "items.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(res['postavke'])} postavk -> {out}")


if __name__ == "__main__":
    main()
