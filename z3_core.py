#!/usr/bin/env python3
"""Logično jedro Z3 (SMT) – nadomestek za TREE; isti vhodi, ista politika, primerljiv izhod.

Razlike glede na TREE:
  * propozicije so ŠTEVILSKE: raven L_aXX ∈ 0..4, leta Y_aXX ≥ 0, sicer Bool B_aXX
    (atom je npr. L_a09 ≥ 4; dejstvo "raven 3" je L_a09 ≥ 3 → spodnja meja je zapisana neposredno)
  * celo drevo je ena formula (ni omejitve 4 spremenljivk)
  * vsako dejstvo je sledljiva predpostavka d_Dxxx; dejstva vrste I so vklopljena le, če je
    vklopljeno njihovo pravilo (B1–B11) → način S / B / občutljivost so samo drugačni nabori predpostavk
  * dokaz T:  dejstva ∧ ¬φ  je UNSAT  → minimalno jedro = najmanjši nabor dejstev, ki φ dokaže
    ovržba F: dejstva ∧ φ   je UNSAT  → minimalno jedro = najmanjši razlog za zavrnitev
  * najmanj manjkajočih dokazil za T_M: MaxSAT (Optimize) nad monotono abstrakcijo drevesa
  * vsak problem se zapiše v SMT-LIB2 (out/z3/*.smt2) in se ponovno preveri iz datoteke

Izhod: out/z3_odlocitev.json, out/z3/*.smt2
"""
import json, sys
from pathlib import Path

import z3

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "out"
J = lambda p: json.loads((BASE / p).read_text(encoding="utf-8"))
SL = J("cues_sl.json")
RULES = list(SL["premostitvena_pravila"])

sys.dont_write_bytecode = True
from decide import rank, atoms_of, items_of  # ista politika P1–P3 kot pri TREE  # noqa: E402


# ---------------- kodiranje ----------------

def atom_var(a):
    if a.get("raven"):
        return z3.Int("L_" + a["id"]), "raven"
    if a.get("prag_let"):
        return z3.Int("Y_" + a["id"]), "leta"
    return z3.Bool("B_" + a["id"]), "bool"


def atom_prop(a, v, kind):
    if kind == "raven":
        return v >= a["raven"]
    if kind == "leta":
        return v >= a["prag_let"]
    return v


def domain(v, kind):
    if kind == "raven":
        return z3.And(v >= 0, v <= 4)
    if kind == "leta":
        return v >= 0
    return z3.BoolVal(True)


def fact_constraint(f, a, v, kind):
    """Dejstvo → omejitev nad spremenljivko atoma (spodnja meja, negacija, natančno število)."""
    if "vrednost" in f:
        p = atom_prop(a, v, kind)
        return p if f["vrednost"] else z3.Not(p)
    if f.get("leta") is not None:
        return v == f["leta"] if f["kvantifikator"] == "=" else v >= f["leta"]
    lvl = f.get("raven") or SL["ravni_signalov"].get(f.get("signal") or "")
    if kind == "raven":
        return v >= lvl
    return atom_prop(a, v, kind)  # signal pri atomu brez ravni = trditev


def node_expr(n, P):
    if n["op"] == "ATOM":
        return P[n["id"]]
    kids = [node_expr(c, P) for c in n["otroci"]]
    return z3.And(*kids) if n["op"] == "AND" else z3.Or(*kids)


class Candidate:
    """En kandidat: trdne omejitve (domene) + sledljiva dejstva."""

    def __init__(self, k, facts, atoms):
        self.k = k
        self.s = z3.Solver()
        self.s.set("core.minimize", True)
        self.V, self.P = {}, {}
        for aid, a in atoms.items():
            v, kind = atom_var(a)
            self.V[aid] = (v, kind)
            self.P[aid] = atom_prop(a, v, kind)
            self.s.add(domain(v, kind))
        self.ind = {}      # Dxxx -> Bool indikator
        self.meta = {}     # Dxxx -> dejstvo
        for f in facts:
            if f["k"] != k:
                continue
            a = atoms[f["atom"]]
            v, kind = self.V[f["atom"]]
            d = z3.Bool("d_" + f["idx"])
            self.s.add(z3.Implies(d, fact_constraint(f, a, v, kind)))
            self.ind[f["idx"]] = d
            self.meta[f["idx"]] = f

    def assumptions(self, rules_on):
        return [d for i, d in self.ind.items()
                if self.meta[i]["vrsta"] == "E" or self.meta[i].get("pravilo") in rules_on]

    def _unsat_with(self, extra, assum):
        self.s.push()
        self.s.add(extra)
        r = self.s.check(*assum)
        core = [str(c)[2:] for c in self.s.unsat_core()] if r == z3.unsat else None
        self.s.pop()
        return r, core

    def minimize(self, extra, core):
        """Brisanje po eno: zagotovljeno minimalno jedro (MUS)."""
        core = list(core)
        for c in list(core):
            trial = [self.ind[x] for x in core if x != c]
            r, _ = self._unsat_with(extra, trial)
            if r == z3.unsat:
                core.remove(c)
        return sorted(core)

    def value(self, phi, rules_on):
        assum = self.assumptions(rules_on)
        r, core = self._unsat_with(z3.Not(phi), assum)
        if r == z3.unsat:
            return "T", self.minimize(z3.Not(phi), core)
        r, core = self._unsat_with(phi, assum)
        if r == z3.unsat:
            return "F", self.minimize(phi, core)
        return "U", []

    def consistent(self, rules_on):
        r = self.s.check(*self.assumptions(rules_on))
        return r == z3.sat, ([str(c)[2:] for c in self.s.unsat_core()] if r == z3.unsat else [])

    def smt2(self, root, rules_on, label):
        assum = " ".join(str(d) for d in self.assumptions(rules_on))
        return (f"; {label}\n(set-option :produce-unsat-cores true)\n{self.s.sexpr()}"
                f"(push 1)\n(assert (not {root.sexpr()}))\n(check-sat-assuming ({assum}))\n(get-unsat-core)\n(pop 1)\n"
                f"(push 1)\n(assert {root.sexpr()})\n(check-sat-assuming ({assum}))\n(get-unsat-core)\n(pop 1)\n")


def min_missing(root, atom_vals, m_atoms):
    """Najmanj dodatnih dokazil (atomov U → T), da T_M postane T. MaxSAT nad monotono abstrakcijo."""
    o = z3.Optimize()
    t, pick = {}, {}
    for a in m_atoms:
        v = atom_vals[a]
        if v == "T":
            t[a] = z3.BoolVal(True)
        elif v == "F":
            t[a] = z3.BoolVal(False)
        else:
            pick[a] = z3.Bool("dodaj_" + a)
            t[a] = pick[a]
    o.add(node_expr(root, t))
    for p in pick.values():
        o.add_soft(z3.Not(p), 1)
    if o.check() != z3.sat:
        return None
    m = o.model()
    return sorted(a for a, p in pick.items() if z3.is_true(m.eval(p)))


# ---------------- glavni del ----------------

def main():
    tree = J("out/tree.json")
    fo = J("out/dejstva_ocenjena.json")
    kand = J("out/kandidati.json")
    names = {k["id"]: k["ime"] for k in kand["kandidati"]}
    roots = {t["koren"]: t for t in tree["drevesa"]}
    atoms = {a["id"]: a for t in tree["drevesa"] for a in atoms_of(t)}
    nodes = {}

    def walk(n):
        if n["op"] != "ATOM":
            nodes[n["id"]] = n
            for c in n["otroci"]:
                walk(c)
    for t in tree["drevesa"]:
        walk(t)
    m_atoms = [a["id"] for a in atoms_of(roots["T_M"])]
    m_items = list(items_of(roots["T_M"]))
    cands = {k: Candidate(k, fo["dejstva"], atoms) for k in names}
    (OUT / "z3").mkdir(exist_ok=True)

    def evaluate(rules_on, full=True):
        per = {}
        for k, c in cands.items():
            ok, conflict = c.consistent(rules_on)
            av, cores = {}, {}
            for aid in atoms:
                v, core = c.value(c.P[aid], rules_on) if full else (None, None)
                av[aid] = v
                if core:
                    cores[aid] = core
            nv = {}
            for nid, n in nodes.items():
                v, core = c.value(node_expr(n, c.P), rules_on)
                nv[nid] = v
                if core:
                    cores[nid] = core
            rv = {r: nv[t["id"]] for r, t in roots.items()}
            per[k] = {
                "ime": names[k], "konsistentna": ok, "konflikt": conflict,
                "T_M": rv["T_M"], "T_N": rv["T_N"], "T_P": rv["T_P"],
                "atomi": av, "vozlisca": nv, "jedra": cores,
                "postavke": {i["oznaka"]: nv[i["id"]] for i in m_items},
                "items": sum(1 for i in m_items if nv[i["id"]] == "T"),
                "aT": sum(1 for a in m_atoms if av[a] == "T"),
                "aF": sum(1 for a in m_atoms if av[a] == "F"),
                "P": sum(1 for a in atoms_of(roots["T_P"]) if av[a["id"]] == "T"),
                "N": sum(1 for a in atoms_of(roots["T_N"]) if av[a["id"]] == "T"),
                "manjka_najmanj": min_missing(roots["T_M"], av, m_atoms),
            }
        izl, order = rank(per)
        return per, izl, order

    res = {"z3": z3.get_version_string(), "nacini": {}, "obcutljivost": [], "smt2": [], "primerjava_tree": {}}
    for mode, rules_on in (("S", set()), ("B", set(RULES))):
        per, izl, order = evaluate(rules_on)
        ust = [k for k in per if per[k]["T_M"] == "T"]
        for i, k in enumerate(order):
            per[k]["rang"] = i + 1
        res["nacini"][mode] = {
            "pravila_vklopljena": sorted(rules_on), "kandidati": per, "izloceni": izl,
            "dokazano_ustrezni": ust, "vrstni_red": order, "izbrani": order[0] if order else None,
            "pravilo": "P2" if ust else "P3",
            "status": ("IZBRAN – dokazano izpolnjuje obvezne zahteve" if ust
                       else "PREDNOSTNI ZA PREVERJANJE – ni dokazano ustrezen"),
        }
        # SMT-LIB2 zapis + ponovno preverjanje iz besedila
        for k, c in cands.items():
            root = node_expr(roots["T_M"], c.P)
            txt = c.smt2(root, rules_on, f"{mode} {k} {names[k]} – T_M (dokaz: prvi check-sat unsat; ovržba: drugi unsat)")
            p = OUT / "z3" / f"{mode}_{k}.smt2"
            p.write_text(txt, encoding="utf-8")
            s2 = z3.Solver()
            s2.from_string(c.s.sexpr())
            assum = c.assumptions(rules_on)
            s2.push(); s2.add(z3.Not(root)); rd = s2.check(*assum); s2.pop()
            s2.push(); s2.add(root); ro = s2.check(*assum); s2.pop()
            v2 = "T" if rd == z3.unsat else ("F" if ro == z3.unsat else "U")
            res["smt2"].append({"datoteka": f"out/z3/{mode}_{k}.smt2", "nacin": mode, "k": k,
                                "T_M": per[k]["T_M"], "ponovitev_iz_smt2": v2, "ujemanje": v2 == per[k]["T_M"]})

    # občutljivost (enaka shema kot pri TREE)
    base = {m: {"izloceni": r["izloceni"], "vrstni_red": r["vrstni_red"], "izbrani": r["izbrani"]}
            for m, r in res["nacini"].items()}
    for r in RULES:
        rows = {}
        for lab, on in (("S_plus", {r}), ("B_minus", set(RULES) - {r})):
            per, izl, order = evaluate(on, full=True)
            rows[lab] = {"izloceni": izl, "vrstni_red": order, "izbrani": order[0] if order else None}
        res["obcutljivost"].append({
            "pravilo": r, "ime": SL["premostitvena_pravila"][r]["ime"], **rows,
            "spremeni_izbiro": rows["S_plus"]["izbrani"] != base["S"]["izbrani"] or rows["B_minus"]["izbrani"] != base["B"]["izbrani"],
            "spremeni_izlocene": rows["S_plus"]["izloceni"] != base["S"]["izloceni"] or rows["B_minus"]["izloceni"] != base["B"]["izloceni"],
            "spremeni_red": rows["S_plus"]["vrstni_red"] != base["S"]["vrstni_red"] or rows["B_minus"]["vrstni_red"] != base["B"]["vrstni_red"]})

    # primerjava s TREE (Kleene + propMinimization)
    dec = J("out/odlocitev.json")
    tot = ok = 0
    diffs = []
    for mode in ("S", "B"):
        for k in names:
            zt = res["nacini"][mode]["kandidati"][k]
            tv = fo["vrednosti"][k][mode]
            tn = dec["po_nacinu"][mode]["kandidati"][k]["vozlisca"]
            for aid in atoms:
                tot += 1
                if zt["atomi"][aid] == tv[aid]["v"]:
                    ok += 1
                else:
                    diffs.append({"nacin": mode, "k": k, "id": aid, "z3": zt["atomi"][aid], "tree": tv[aid]["v"]})
            for nid in nodes:
                tot += 1
                if zt["vozlisca"][nid] == tn[nid]["v"]:
                    ok += 1
                else:
                    diffs.append({"nacin": mode, "k": k, "id": nid, "z3": zt["vozlisca"][nid], "tree": tn[nid]["v"]})
        same_sel = res["nacini"][mode]["izbrani"] == dec["po_nacinu"][mode]["izbrani"]
        res["primerjava_tree"][mode] = {"izbrani_z3": res["nacini"][mode]["izbrani"],
                                        "izbrani_tree": dec["po_nacinu"][mode]["izbrani"], "enak_izbor": same_sel}
    res["primerjava_tree"]["vrednosti"] = {"primerjav": tot, "ujemanje": ok, "razlike": diffs}
    tree_sens = {s["pravilo"]: (s["S_plus"]["izbrani"], s["B_minus"]["izbrani"]) for s in dec["obcutljivost"]["pravila"]}
    res["primerjava_tree"]["obcutljivost_enaka"] = all(
        tree_sens[s["pravilo"]] == (s["S_plus"]["izbrani"], s["B_minus"]["izbrani"]) for s in res["obcutljivost"])

    (OUT / "z3_odlocitev.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    for mode, r in res["nacini"].items():
        print(f"[{mode}] izločeni={r['izloceni']} red={r['vrstni_red']} -> {r['izbrani']} ({names.get(r['izbrani'])})")
        for k, c in r["kandidati"].items():
            mm = c["manjka_najmanj"]
            print(f"   {k} {c['ime']:12} T_M={c['T_M']} atomi T/F={c['aT']}/{c['aF']} "
                  f"manjka≥{len(mm) if mm is not None else '∞'}  jedro T_M={c['jedra'].get(roots['T_M']['id'], [])}")
    pv = res["primerjava_tree"]["vrednosti"]
    print(f"Z3 ↔ TREE: {pv['ujemanje']}/{pv['primerjav']} vrednosti, izbor S/B enak: "
          f"{res['primerjava_tree']['S']['enak_izbor']}/{res['primerjava_tree']['B']['enak_izbor']}, "
          f"občutljivost enaka: {res['primerjava_tree']['obcutljivost_enaka']}")
    print(f"SMT-LIB2 ponovitev: {sum(x['ujemanje'] for x in res['smt2'])}/{len(res['smt2'])}")


if __name__ == "__main__":
    main()
