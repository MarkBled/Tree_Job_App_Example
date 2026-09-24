#!/usr/bin/env python3
"""5. korak (neobvezno): ovrednoti profil kandidata na drevesu.

  python3 evaluate.py --predloga            -> out/profil_predloga.json (vsi atomi, vrednosti null)
  python3 evaluate.py profil.json           -> izpis + out/ocena.json

Profil: {"a09": 4, "a41": 7, "a48": true, ...}
  atom z ravnijo  -> število 0–4   (resnično, če ≥ zahtevana raven)
  atom s pragom   -> leta          (resnično, če ≥ prag)
  ostalo          -> true/false
Manjkajoča vrednost = neresnično (in je izpisana kot manjkajoča).
"""
import json, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent


def atoms(n):
    if n["op"] == "ATOM":
        yield n
    else:
        for c in n["otroci"]:
            yield from atoms(c)


def truth(a, prof, missing):
    v = prof.get(a["id"])
    if v is None:
        missing.append(a["id"])
        return False
    if a.get("raven"):
        return float(v) >= a["raven"]
    if a.get("prag_let"):
        return float(v) >= a["prag_let"]
    return bool(v)


def ev(n, prof, missing, fails, trace):
    if n["op"] == "ATOM":
        t = truth(n, prof, missing)
        n["_t"] = t
        if not t:
            fails.append(n)
        return t
    vals = [ev(c, prof, missing, fails, trace) for c in n["otroci"]]
    if n["op"] == "AND":
        t = all(vals)
    elif n["op"] == "OR":
        t = any(vals)
    else:  # SCORE
        t = any(vals)
    n["_t"] = t
    trace[n["id"]] = {"oznaka": n["oznaka"], "vrednost": t, "izpolnjeno": sum(vals), "od": len(vals)}
    return t


def blocking(n):
    """Atomi, ki dejansko povzročijo neresničnost (neizpolnjena alternativa v ⋁, ki je izpolnjen, ne šteje)."""
    if n["_t"] or n["op"] == "SCORE" and n.get("koren"):
        return [] if n["op"] != "SCORE" else [a for a in atoms(n) if not a["_t"]]
    if n["op"] == "ATOM":
        return [n]
    return [a for c in n["otroci"] if not c["_t"] for a in blocking(c)]


def main():
    tree = json.loads((BASE / "out" / "tree.json").read_text(encoding="utf-8"))
    if len(sys.argv) > 1 and sys.argv[1] == "--predloga":
        tpl = {a["id"]: None for t in tree["drevesa"] for a in atoms(t)}
        tpl["_legenda"] = {a["id"]: f"{a['oznaka']} [{a['obveznost']}] " +
                           (f"raven≥{a['raven']}" if a.get("raven") else f"let≥{a['prag_let']}" if a.get("prag_let") else "da/ne")
                           for t in tree["drevesa"] for a in atoms(t)}
        (BASE / "out" / "profil_predloga.json").write_text(json.dumps(tpl, ensure_ascii=False, indent=2), encoding="utf-8")
        print("-> out/profil_predloga.json")
        return
    prof = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    res = {}
    for t in tree["drevesa"]:
        missing, fails, trace = [], [], {}
        val = ev(t, prof, missing, fails, trace)
        all_atoms = list(atoms(t))
        res[t["koren"]] = {"oznaka": t["oznaka"], "vloga": t["vloga"], "vrednost": val,
                           "izpolnjenih_atomov": f"{len(all_atoms) - len(fails)}/{len(all_atoms)}",
                           "neizpolnjeni": [{"id": a["id"], "oznaka": a["oznaka"]} for a in blocking(t) if a["id"] not in missing],
                           "manjkajoci": missing, "vozlisca": trace}
    (BASE / "out" / "ocena.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    for k, r in res.items():
        print(f"{k} {r['oznaka']} ({r['vloga']}): {'DA' if r['vrednost'] else 'NE'} · atomi {r['izpolnjenih_atomov']}")
        for a in r["neizpolnjeni"]:
            print(f"   ✗ {a['id']} {a['oznaka']}")
        if r["manjkajoci"]:
            print(f"   ? manjka podatek: {', '.join(r['manjkajoci'])}")


if __name__ == "__main__":
    main()
