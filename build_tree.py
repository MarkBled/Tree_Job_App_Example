#!/usr/bin/env python3
"""3. korak: klasificirane postavke -> hierarhija (out/tree.json).

Tri drevesa:
  T_M  Obvezne zahteve   AND   (vrata: vse mora držati)
  T_N  Dodatno           SCORE (točkovanje, ne vrata; v pregledovalniku kot ⋁ = "vsaj en plus")
  T_P  Naloge            SCORE (pričakovane naloge iz razdelka Key Responsibilities)
Vozlišče z več kot MAX_OTROK otroki se razdeli na enakovredne dele (asociativnost ⋀/⋁).
"""
import json, math
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
MAX_OTROK = 4


class Ids:
    n = 0

    @classmethod
    def next(cls):
        cls.n += 1
        return f"n{cls.n:02d}"


def flatten(n):
    """Združi zaporedne enake operatorje (A⋀(B⋀C) = A⋀B⋀C), razen vozlišč z lastnim pomenom (postavke)."""
    if n["op"] == "ATOM":
        return n
    kids = []
    for c in (flatten(c) for c in n["otroci"]):
        if c["op"] == n["op"] and not c.get("postavka") and not c.get("raven"):
            kids += c["otroci"]
        else:
            kids.append(c)
    n["otroci"] = kids
    return n


def rebalance(n):
    if n["op"] == "ATOM":
        return n
    n["otroci"] = [rebalance(c) for c in n["otroci"]]
    while len(n["otroci"]) > MAX_OTROK:
        kids = n["otroci"]
        g = math.ceil(len(kids) / MAX_OTROK)
        size = math.ceil(len(kids) / g)
        chunks = [kids[i:i + size] for i in range(0, len(kids), size)]
        n["otroci"] = [c[0] if len(c) == 1 else
                       {"op": n["op"], "oznaka": f"{n['oznaka']} – del {i + 1}/{len(chunks)}",
                        "sinteticno": True, "otroci": c}
                       for i, c in enumerate(chunks)]
    return n


def assign_ids(n):
    if n["op"] != "ATOM":
        n["id"] = Ids.next()
        for c in n["otroci"]:
            assign_ids(c)
    return n


def item_node(item, obveznost):
    kids = [k["vozlisce"] for k in item["klavzule"] if k["obveznost"] == obveznost]
    if not kids:
        return None
    if len(kids) == 1:
        if kids[0]["op"] == "ATOM":
            return kids[0]
        k = dict(kids[0], besedilo=kids[0]["oznaka"], oznaka=item["oznaka"], postavka=item["id"])
        return k
    return {"op": "AND", "oznaka": item["oznaka"], "postavka": item["id"], "otroci": kids}


def main():
    cl = json.loads((BASE / "out" / "classified.json").read_text(encoding="utf-8"))
    items = cl["postavke"]
    M = [x for x in (item_node(i, "M") for i in items) if x]
    N = [k["vozlisce"] for i in items for k in i["klavzule"] if k["obveznost"] == "N"]
    P = [k["vozlisce"] for i in items for k in i["klavzule"] if k["obveznost"] == "P"]
    trees = [
        {"op": "AND", "oznaka": "Obvezne zahteve", "koren": "T_M", "vloga": "vrata", "otroci": M},
        {"op": "SCORE", "oznaka": "Dodatno (nice to have)", "koren": "T_N", "vloga": "točkovanje", "otroci": N},
        {"op": "SCORE", "oznaka": "Naloge (pričakovano)", "koren": "T_P", "vloga": "točkovanje", "otroci": P},
    ]
    trees = [assign_ids(rebalance(flatten(t))) for t in trees if t["otroci"]]
    atoms = {}

    def collect(n):
        if n["op"] == "ATOM":
            atoms[n["id"]] = n
        else:
            for c in n["otroci"]:
                collect(c)
    for t in trees:
        collect(t)
    dv = [{"postavka": i["id"], "klavzula": k["tekst"], **d}
          for i in items for k in i["klavzule"] for d in k["dvoumnosti"]]
    out = {"vir": cl["vir"], "lestvica": cl["lestvica"], "drevesa": trees,
           "st_atomov": len(atoms), "dvoumnosti": dv}
    (BASE / "out" / "tree.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(trees)} drevesa, {len(atoms)} atomov, {Ids.n} notranjih vozlišč -> out/tree.json")


if __name__ == "__main__":
    main()
