#!/usr/bin/env python3
"""4. korak: hierarhija -> formule za pregledovalnik TreeOfKnowledge (out/formule.json, out/formule.md).

Omejitve pregledovalnika (mapa Tree):
  propMinimization : spremenljivke A B C D (≤4)  -> glavni izvoz
  propositional    : spremenljivke P Q R   (≤3)  -> dodatni izvoz, kadar formula ustreza
Vezniki: ¬ ⋀ ⋁ ⇒ ⇔. Parser NIMA prednosti operatorjev (bere levo->desno),
zato je vsak vgnezden podizraz vedno v oklepaju.
Podvozlišče se vstavi v formulo starša, če skupno število črk ostane ≤ 4; sicer postane
lastna črka z lastno formulo (drevo drevesc).
"""
import itertools, json
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
AND, OR = "⋀", "⋁"
SYM = {"AND": AND, "OR": OR, "SCORE": OR}
LET_MIN, LET_PROP = "ABCD", "PQR"
LIMIT = 4


# ---------- načrt: katere podvozlišča vstavimo ----------

def plan(n):
    """Vrne (slots, cost). slot = ('ref', otrok) | ('in', otrok, podnačrt)."""
    slots = [["ref", c] for c in n["otroci"]]
    cost = len(slots)
    subplans = {id(c): plan(c) for c in n["otroci"] if c["op"] != "ATOM"}
    for s in sorted([s for s in slots if s[1]["op"] != "ATOM"], key=lambda s: subplans[id(s[1])][1]):
        sub_slots, sub_cost = subplans[id(s[1])]
        if cost - 1 + sub_cost <= LIMIT:
            s[0], cost = "in", cost - 1 + sub_cost
            s.append(sub_slots)
    return slots, cost


def render(n, slots, refs):
    parts = []
    for s in slots:
        if s[0] == "ref":
            refs.append(s[1])
            parts.append(f"#{len(refs) - 1}")
        else:
            inner = render(s[1], s[2], refs)
            # isti operator je asociativen -> brez oklepaja (parser bere levo->desno)
            parts.append(inner if SYM[s[1]["op"]] == SYM[n["op"]] else "(" + inner + ")")
    return SYM[n["op"]].join(parts)


def letters(expr, alphabet):
    import re
    return re.sub(r"#(\d)", lambda m: alphabet[int(m.group(1))], expr)


# ---------- minimizacija (Quine–McCluskey, ≤4 spremenljivke) ----------

def evaluate(expr, vals):
    py = expr.replace(AND, " and ").replace(OR, " or ")
    return eval(py, {}, vals)


def minimal_dnf(expr, vars_):
    minterms = [bits for bits in itertools.product([0, 1], repeat=len(vars_))
                if evaluate(expr, dict(zip(vars_, map(bool, bits))))]
    if not minterms:
        return [], 0
    # primarni implikanti
    terms = {tuple(m) for m in minterms}
    primes = set()
    while terms:
        used, nxt = set(), set()
        tl = list(terms)
        for a, b in itertools.combinations(tl, 2):
            diff = [i for i in range(len(a)) if a[i] != b[i]]
            if len(diff) == 1 and "-" not in (a[diff[0]], b[diff[0]]):
                t = list(a); t[diff[0]] = "-"
                nxt.add(tuple(t)); used |= {a, b}
        primes |= terms - used
        terms = nxt

    def covers(p, m):
        return all(pc == "-" or pc == mc for pc, mc in zip(p, m))
    primes = sorted(primes, key=lambda p: (-p.count("-"), [str(x) for x in p]))
    for k in range(1, len(primes) + 1):  # najmanjše pokritje (majhno, izčrpno)
        for combo in itertools.combinations(primes, k):
            if all(any(covers(p, m) for p in combo) for m in minterms):
                return sorted([[vars_[i] if b == 1 else "¬" + vars_[i] for i, b in enumerate(p) if b != "-"]
                        for p in combo], key=lambda t: [x.lstrip("\u00AC") for x in t]), len(minterms)
    return [], len(minterms)


# ---------- izvoz ----------

def describe(x):
    if x["op"] == "ATOM":
        r = x.get("raven")
        lv = f"raven ≥{r}" if r else (f"prag ≥{x['prag_let']} let" if x.get("prag_let") else "izpolnjeno")
        return {"tip": "atom", "id": x["id"], "oznaka": x["oznaka"], "pogoj": lv,
                "obveznost": x["obveznost"], "signal": " ".join(x.get("signal", []))}
    return {"tip": "vozlišče", "id": x["id"], "oznaka": x["oznaka"], "pogoj": "glej formulo " + x["id"]}


def export(trees):
    formulas, queue = [], [(t, t["koren"]) for t in trees]
    seen = set()
    while queue:
        n, root = queue.pop(0)
        if n["id"] in seen:
            continue
        seen.add(n["id"])
        slots, _ = plan(n)
        refs = []
        expr = render(n, slots, refs)
        vars_ = list(LET_MIN[:len(refs)])
        f_min = letters(expr, LET_MIN)
        dnf, n_true = minimal_dnf(f_min, vars_)
        formulas.append({
            "id": n["id"], "drevo": root, "oznaka": n["oznaka"], "op": n["op"],
            "formula_propMinimization": f_min,
            "formula_propositional": letters(expr, LET_PROP) if len(refs) <= 3 else None,
            "legenda": {LET_MIN[i]: describe(r) for i, r in enumerate(refs)},
            "minimalna_DNF": [AND.join(t) for t in dnf],
            "resnicnih_vrstic": f"{n_true}/{2 ** len(refs)}",
            "opomba": "točkovanje: ⋁ = vsaj en izpolnjen; štej izpolnjene" if n["op"] == "SCORE" else None,
        })
        queue += [(r, root) for r in refs if r["op"] != "ATOM"]
    return formulas


def to_md(formulas, tree):
    L = [f"# Formule za pregledovalnik – {tree['vir']}", "",
         "Lestvica ravni: 1 poznavanje · 2 delovno · 3 praktično · 4 ekspert. "
         "Atom je resničen, ko ima kandidat vsaj zahtevano raven (oz. prag let).", "",
         "Vnos: **propMinimization** (A–D) ali **propositional** (P–R, kadar ≤3 spremenljivke). "
         "Črka, ki kaže na vozlišče `nXX`, je rezultat formule tega vozlišča.", ""]
    for f in formulas:
        L += [f"## {f['id']} · {f['oznaka']}  _(drevo {f['drevo']})_", "",
              f"- propMinimization: `{f['formula_propMinimization']}`"]
        if f["formula_propositional"]:
            L.append(f"- propositional: `{f['formula_propositional']}`")
        L.append(f"- minimalna DNF (najmanjše zadostne kombinacije): `{'  ⋁  '.join(f['minimalna_DNF'])}`"
                 f" · resničnih vrstic {f['resnicnih_vrstic']}")
        if f["opomba"]:
            L.append(f"- opomba: {f['opomba']}")
        L += ["", "| črka | pomen | pogoj | signal v besedilu |", "|---|---|---|---|"]
        for k, d in f["legenda"].items():
            L.append(f"| {k} | {d['oznaka']} (`{d['id']}`) | {d['pogoj']} | {d.get('signal', '')} |")
        L.append("")
    L += ["## Označene dvoumnosti", ""]
    for d in tree["dvoumnosti"]:
        L.append(f"- **{d['koda']}** ({d['postavka']}) „{d['klavzula']}“ – {d['razlaga']}")
    return "\n".join(L) + "\n"


def main():
    tree = json.loads((BASE / "out" / "tree.json").read_text(encoding="utf-8"))
    formulas = export(tree["drevesa"])
    (BASE / "out" / "formule.json").write_text(json.dumps(formulas, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "out" / "formule.md").write_text(to_md(formulas, tree), encoding="utf-8")
    print(f"{len(formulas)} formul -> out/formule.json, out/formule.md")


if __name__ == "__main__":
    main()
