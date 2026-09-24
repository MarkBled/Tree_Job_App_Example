#!/usr/bin/env python3
"""Dejstva -> vrednosti atomov po kandidatih (out/dejstva_ocenjena.json).

Trivrednostna logika (Kleene): T dokazano, F ovrženo, U ni dokazano.
  - citat mora biti DOBESEDNO v besedilu kandidata, signal pa v citatu (sicer napaka)
  - raven iz signala je SPODNJA MEJA: raven < zahtevane -> U (ne F)
  - F samo iz izrecne negacije ali natančnega števila let pod pragom
  - način S: samo dejstva E; način B: E + I (premostitvena pravila)
  - T in F hkrati -> konflikt, obravnavano kot U in označeno
"""
import hashlib, json, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
SL = json.loads((BASE / "cues_sl.json").read_text(encoding="utf-8"))


def load_atoms():
    tree = json.loads((BASE / "out" / "tree.json").read_text(encoding="utf-8"))
    atoms = {}

    def walk(n):
        if n["op"] == "ATOM":
            atoms[n["id"]] = n
        else:
            for c in n["otroci"]:
                walk(c)
    for t in tree["drevesa"]:
        walk(t)
    return atoms


def atoms_fingerprint(atoms):
    """Prstni odtis propozicij: dejstva so vezana na id atomov, zato se mora drevo ujemati."""
    lines = "\n".join(f"{a}:{atoms[a]['oznaka']}" for a in sorted(atoms))
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def fact_value(f, atom):
    """Vrne (vrednost, razlaga)."""
    if "vrednost" in f:
        return ("T" if f["vrednost"] else "F"), ("izrecna trditev" if f["vrednost"] else "izrecna negacija")
    if "leta" in f:
        prag = atom.get("prag_let", 0)
        if f["leta"] >= prag:
            return "T", f"{f['kvantifikator']}{f['leta']} let ≥ prag {prag}"
        if f["kvantifikator"] == "=":
            return "F", f"natančno {f['leta']} let < prag {prag}"
        return "U", f"≥{f['leta']} let ne doseže praga {prag}"
    lvl = f.get("raven", SL["ravni_signalov"].get(f.get("signal", ""), None))
    if lvl is None:
        return "U", "ni signala ravni"
    req = atom.get("raven")
    if req is None or lvl >= req:
        return "T", f"raven {lvl} ≥ zahtevana {req}" if req else f"raven {lvl}"
    return "U", f"raven {lvl} < zahtevana {req} (spodnja meja, ne ovrže)"


def main():
    atoms = load_atoms()
    kand = json.loads((BASE / "out" / "kandidati.json").read_text(encoding="utf-8"))
    texts = {k["id"]: k["besedilo"] for k in kand["kandidati"]}
    data = json.loads((BASE / "data" / "dejstva.json").read_text(encoding="utf-8"))
    errors, facts = [], []
    fp = atoms_fingerprint(atoms)
    if data.get("propozicije_sha256") and data["propozicije_sha256"] != fp:
        print("NAPAKA: out/tree.json ima druge propozicije, kot so bila dejstva izluščena zanje "
              f"({fp[:12]} ≠ {data['propozicije_sha256'][:12]}). Ponovno poženi run_all.py ali ponovno izlušči dejstva.")
        sys.exit(2)
    for i, f in enumerate(data["dejstva"]):
        f = dict(f, idx=f"D{i + 1:03d}")
        if f["citat"] not in texts.get(f["k"], ""):
            errors.append(f"{f['idx']}: citat ni dobeseden v {f['k']}: {f['citat']!r}")
        if f.get("signal") and f["signal"].lower() not in f["citat"].lower():
            errors.append(f"{f['idx']}: signal {f['signal']!r} ni v citatu")
        if f["atom"] not in atoms:
            errors.append(f"{f['idx']}: neznan atom {f['atom']}")
            continue
        if f["vrsta"] == "I" and f.get("pravilo") not in SL["premostitvena_pravila"]:
            errors.append(f"{f['idx']}: vrsta I brez veljavnega pravila")
        f["vrednost_dejstva"], f["razlaga"] = fact_value(f, atoms[f["atom"]])
        facts.append(f)
    for u in data.get("neuporabljene_izjave", []):
        if u["citat"] not in texts.get(u["k"], ""):
            errors.append(f"neuporabljena izjava ni dobesedna v {u['k']}: {u['citat']!r}")
    if errors:
        print("NAPAKE:\n  " + "\n  ".join(errors))
        sys.exit(1)

    res = {}
    for k in texts:
        res[k] = {}
        for mode in ("S", "B"):
            vals = {}
            for aid in atoms:
                fs = [f for f in facts if f["k"] == k and f["atom"] == aid and (mode == "B" or f["vrsta"] == "E")]
                vs = {f["vrednost_dejstva"] for f in fs}
                if "T" in vs and "F" in vs:
                    v, note = "U", "KONFLIKT T/F"
                elif "T" in vs:
                    v, note = "T", ""
                elif "F" in vs:
                    v, note = "F", ""
                else:
                    v, note = "U", "" if fs else "ni podatka"
                vals[aid] = {"v": v, "dejstva": [f["idx"] for f in fs], "opomba": note}
            res[k][mode] = vals
    out = {"dejstva": facts, "neuporabljene_izjave": data.get("neuporabljene_izjave", []),
           "izluscil": data.get("izluscil"), "vrednosti": res}
    (BASE / "out" / "dejstva_ocenjena.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    for k in texts:
        s = {m: sum(1 for a in res[k][m].values() if a["v"] == "T") for m in "SB"}
        f = {m: [a for a, x in res[k][m].items() if x["v"] == "F"] for m in "SB"}
        print(f"{k}: T(S)={s['S']} T(B)={s['B']}  F(S)={f['S']} F(B)={f['B']}")
    print(f"{len(facts)} dejstev, vsi citati dobesedni -> out/dejstva_ocenjena.json")


if __name__ == "__main__":
    main()
