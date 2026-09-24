#!/usr/bin/env python3
"""Evalvacija kandidatov na drevesu + vhodi za TREE (out/odlocitev.json, out/tree_inputs.tsv).

Za vsako izvoženo formulo R (vozlišče nXX) in kandidata:
  K  = konjunkcija znanih literalov (črke z vrednostjo T -> X, F -> ¬X; U se izpusti)
  D-test:  (K)⋀¬(R)  protislovje   => K ⇒ R je veljavno  => vozlišče DOKAZANO (T)
  O-test:  (K)⋀(R)   protislovje   => K in R nezdružljiva => vozlišče OVRŽENO (F)
  (Obe preverjanji sta preverjanji PROTISLOVJA, ker pot za tavtologije v pregledovalniku propMinimization
   pade z ClassCastException – neujemanje nizov 'tautologija;)!)' / 'tautology;)!)'.)
  sicer                              => NI ODLOČENO (U); ostanek = minimalna DNF od K⋀R brez K
Vrednost vozlišča, ki je črka v višji formuli, je rezultat nižje formule (veriga dokazov).
"""
import itertools, json
from pathlib import Path

from export_tree import AND, OR
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
NEG, IMP = "¬", "⇒"
SL = json.loads((BASE / "cues_sl.json").read_text(encoding="utf-8"))


def kleene(op, vals):
    if op == "AND":
        return "F" if "F" in vals else ("T" if all(v == "T" for v in vals) else "U")
    return "T" if "T" in vals else ("F" if all(v == "F" for v in vals) else "U")  # OR, SCORE


def eval_tree(n, av, out):
    if n["op"] == "ATOM":
        return av[n["id"]]["v"]
    vals = [eval_tree(c, av, out) for c in n["otroci"]]
    v = kleene(n["op"], vals)
    out[n["id"]] = {"v": v, "T": vals.count("T"), "F": vals.count("F"), "U": vals.count("U"), "od": len(vals)}
    return v


def atoms_of(n):
    if n["op"] == "ATOM":
        yield n
    else:
        for c in n["otroci"]:
            yield from atoms_of(c)


def items_of(n):
    """Obvezne postavke (vozlišča s poljem 'postavka' ali atomi na ravni postavke)."""
    if n.get("postavka"):
        yield n
    elif n["op"] != "ATOM":
        for c in n["otroci"]:
            yield from items_of(c)


def truth_table_tests(R, K_lits, letters):
    """Referenčni izračun (Python) za primerjavo s pogonom TREE."""
    def ev(expr, env):
        py = expr.replace(NEG, " not ").replace(AND, " and ").replace(OR, " or ")
        return eval(py, {}, env)
    taut, sat = True, False
    for bits in itertools.product([False, True], repeat=len(letters)):
        env = dict(zip(letters, bits))
        k_ok = all(env[l] == val for l, val in K_lits)
        r = ev(R, env)
        if k_ok and not r:
            taut = False
        if k_ok and r:
            sat = True
    return taut, sat


def main():
    tree = json.loads((BASE / "out" / "tree.json").read_text(encoding="utf-8"))
    formule = json.loads((BASE / "out" / "formule.json").read_text(encoding="utf-8"))
    fo = json.loads((BASE / "out" / "dejstva_ocenjena.json").read_text(encoding="utf-8"))
    kand = json.loads((BASE / "out" / "kandidati.json").read_text(encoding="utf-8"))
    names = {k["id"]: k["ime"] for k in kand["kandidati"]}
    roots = {t["koren"]: t for t in tree["drevesa"]}
    tsv, result = [], {"nacini": SL["nacini"], "politika": SL["politika_izbire"], "po_nacinu": {}}

    for mode in ("S", "B"):
        per = {}
        for k in names:
            av = fo["vrednosti"][k][mode]
            nodes = {}
            rv = {r: eval_tree(t, av, nodes) for r, t in roots.items()}
            # --- formule za TREE ---
            proofs = []
            for f in formule:
                letters = list(f["legenda"].keys())
                R = f["formula_propMinimization"]
                K_lits = []
                for L, d in f["legenda"].items():
                    v = av[d["id"]]["v"] if d["tip"] == "atom" else nodes[d["id"]]["v"]
                    if v in ("T", "F"):
                        K_lits.append((L, v == "T"))
                K = AND.join(L if val else NEG + L for L, val in K_lits)
                e_in = f"({K}){AND}{NEG}({R})" if K else f"{NEG}({R})"
                c_in = f"({K}){AND}({R})" if K else R
                taut, sat = truth_table_tests(R, K_lits, letters)
                verdict = "T" if taut else ("F" if not sat else "U")
                resid = []
                if verdict == "U":
                    kx = f"({K}){AND}({R})" if K else R
                    fixed = {L for L, _ in K_lits}
                    mins, _ = minimal_dnf_neg(kx, letters)
                    resid = [AND.join(l for l in term if l.lstrip(NEG) not in fixed) for term in mins]
                expect = nodes[f["id"]]["v"]
                proofs.append({"vozlisce": f["id"], "oznaka": f["oznaka"], "drevo": f["drevo"], "R": R, "K": K,
                               "D_vhod": e_in, "O_vhod": c_in, "python": verdict, "kleene": expect,
                               "ostanek": resid,
                               "crke": {L: {"id": d["id"], "oznaka": d["oznaka"],
                                            "v": av[d["id"]]["v"] if d["tip"] == "atom" else nodes[d["id"]]["v"]}
                                        for L, d in f["legenda"].items()}})
                assert verdict == expect, (mode, k, f["id"], verdict, expect)
                key = f"{mode}|{k}|{f['id']}"
                tsv.append(f"{key}|D\t{e_in}")
                tsv.append(f"{key}|O\t{c_in}")
            m_atoms = list(atoms_of(roots["T_M"]))
            m_items = list(items_of(roots["T_M"]))
            cnt = lambda v: sum(1 for a in m_atoms if av[a["id"]]["v"] == v)
            per[k] = {
                "ime": names[k], "T_M": rv["T_M"], "T_N": rv["T_N"], "T_P": rv["T_P"],
                "postavke_T": sum(1 for i in m_items if nodes.get(i["id"], {}).get("v") == "T"),
                "postavke": {i["oznaka"]: nodes[i["id"]]["v"] for i in m_items},
                "atomi_M": {"T": cnt("T"), "F": cnt("F"), "U": cnt("U"), "vseh": len(m_atoms)},
                "F_atomi": [a["id"] for a in m_atoms if av[a["id"]]["v"] == "F"],
                "T_P_st": sum(1 for a in atoms_of(roots["T_P"]) if av[a["id"]]["v"] == "T"),
                "T_N_st": sum(1 for a in atoms_of(roots["T_N"]) if av[a["id"]]["v"] == "T"),
                "vozlisca": nodes, "dokazi": proofs,
            }
        # --- politika P1–P3 ---
        izlocen = [k for k, r in per.items() if r["T_M"] == "F"]
        ustrezni = [k for k, r in per.items() if r["T_M"] == "T"]
        ostali = [k for k in per if k not in izlocen]
        if ustrezni:
            pravilo = "P2"
            order = sorted(ustrezni, key=lambda k: (-per[k]["T_N_st"], -per[k]["T_P_st"]))
        else:
            pravilo = "P3"
            order = sorted(ostali, key=lambda k: (-per[k]["postavke_T"], -per[k]["atomi_M"]["T"],
                                                  per[k]["atomi_M"]["F"], -per[k]["T_P_st"], -per[k]["T_N_st"]))
        for i, k in enumerate(order):
            per[k]["rang"] = i + 1
        for k in izlocen:
            per[k]["rang"] = None
        top = order[0] if order else None
        tie = len(order) > 1 and all(
            (per[order[0]][x] if x != "atomi_M" else per[order[0]][x]["T"]) ==
            (per[order[1]][x] if x != "atomi_M" else per[order[1]][x]["T"])
            for x in ("postavke_T", "atomi_M", "T_P_st", "T_N_st"))
        result["po_nacinu"][mode] = {
            "kandidati": per, "izloceni": izlocen, "dokazano_ustrezni": ustrezni,
            "pravilo": pravilo, "vrstni_red": order, "izbrani": top, "izenacenje": tie,
            "status": ("IZBRAN – dokazano izpolnjuje obvezne zahteve" if pravilo == "P2"
                       else "PREDNOSTNI ZA PREVERJANJE – ni dokazano ustrezen"),
        }
    result["obcutljivost"] = sensitivity(tree, fo, names)
    for mode in ("S", "B"):
        assert result["obcutljivost"][mode]["izbrani"] == result["po_nacinu"][mode]["izbrani"]
    (BASE / "out" / "odlocitev.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "out" / "tree_inputs.tsv").write_text("\n".join(tsv) + "\n", encoding="utf-8")
    for mode, r in result["po_nacinu"].items():
        print(f"[{mode}] izločeni={r['izloceni']} ustrezni={r['dokazano_ustrezni']} {r['pravilo']} red={r['vrstni_red']} "
              f"-> {r['izbrani']} ({names.get(r['izbrani'])}) izenačenje={r['izenacenje']}")
        for k, c in r["kandidati"].items():
            print(f"   {k} {c['ime']:12} T_M={c['T_M']} post_T={c['postavke_T']}/9 atomi={c['atomi_M']} P={c['T_P_st']} N={c['T_N_st']}")
    for row in result["obcutljivost"]["pravila"]:
        print(f"   {row['pravilo']:4} {row['ime']:9} S+ -> izb={row['S_plus']['izbrani']} izl={row['S_plus']['izloceni']}   "
              f"B- -> izb={row['B_minus']['izbrani']} izl={row['B_minus']['izloceni']}  {'IZBIRA ' if row['spremeni_izbiro'] else ''}{'IZLOČITEV ' if row['spremeni_izlocene'] else ''}{'RED' if row['spremeni_red'] else ''}")
    print(f"{len(tsv)} vhodov za TREE -> out/tree_inputs.tsv")


def atom_values(facts, k, atom_ids, allowed):
    """Vrednosti atomov za kandidata k ob dovoljenih pravilih (množica; 'E' = dejstva brez pravila)."""
    out = {}
    for aid in atom_ids:
        vs = {f["vrednost_dejstva"] for f in facts if f["k"] == k and f["atom"] == aid
              and (f["vrsta"] == "E" or f.get("pravilo") in allowed)}
        out[aid] = {"v": "U" if ("T" in vs and "F" in vs) else ("T" if "T" in vs else ("F" if "F" in vs else "U"))}
    return out


def rank(per):
    izl = sorted(k for k, r in per.items() if r["T_M"] == "F")
    ust = [k for k, r in per.items() if r["T_M"] == "T"]
    rest = [k for k in per if k not in izl]
    if ust:
        order = sorted(ust, key=lambda k: (-per[k]["N"], -per[k]["P"]))
    else:
        order = sorted(rest, key=lambda k: (-per[k]["items"], -per[k]["aT"], per[k]["aF"], -per[k]["P"], -per[k]["N"]))
    return izl, order


def sensitivity(tree, fo, names):
    roots = {t["koren"]: t for t in tree["drevesa"]}
    all_atoms = [a["id"] for t in tree["drevesa"] for a in atoms_of(t)]
    m_atoms = [a["id"] for a in atoms_of(roots["T_M"])]
    m_items = list(items_of(roots["T_M"]))
    rules = list(SL["premostitvena_pravila"])

    def run(allowed):
        per = {}
        for k in names:
            av = atom_values(fo["dejstva"], k, all_atoms, allowed)
            nodes = {}
            rv = {r: eval_tree(t, av, nodes) for r, t in roots.items()}
            per[k] = {"T_M": rv["T_M"], "items": sum(1 for i in m_items if nodes[i["id"]]["v"] == "T"),
                      "aT": sum(1 for a in m_atoms if av[a]["v"] == "T"), "aF": sum(1 for a in m_atoms if av[a]["v"] == "F"),
                      "P": sum(1 for a in atoms_of(roots["T_P"]) if av[a["id"]]["v"] == "T"),
                      "N": sum(1 for a in atoms_of(roots["T_N"]) if av[a["id"]]["v"] == "T")}
        izl, order = rank(per)
        return {"izloceni": izl, "vrstni_red": order, "izbrani": order[0] if order else None}

    base_S, base_B = run(set()), run(set(rules))
    rows = []
    for r in rules:
        s_plus, b_minus = run({r}), run(set(rules) - {r})
        rows.append({"pravilo": r, "ime": SL["premostitvena_pravila"][r]["ime"],
                     "S_plus": s_plus, "B_minus": b_minus,
                     "spremeni_izbiro": s_plus["izbrani"] != base_S["izbrani"] or b_minus["izbrani"] != base_B["izbrani"],
                     "spremeni_izlocene": s_plus["izloceni"] != base_S["izloceni"] or b_minus["izloceni"] != base_B["izloceni"],
                     "spremeni_red": s_plus["vrstni_red"] != base_S["vrstni_red"] or b_minus["vrstni_red"] != base_B["vrstni_red"]})
    return {"S": base_S, "B": base_B, "pravila": rows}


def minimal_dnf_neg(expr, letters):
    """minimal_dnf iz export_tree ne pozna ¬; tukaj ¬X -> (not X)."""
    import export_tree as et
    src = expr.replace(NEG, " not ")
    orig = et.evaluate
    et.evaluate = lambda e, vals: eval(e.replace(AND, " and ").replace(OR, " or "), {}, vals)
    try:
        return et.minimal_dnf(src, letters)
    finally:
        et.evaluate = orig


if __name__ == "__main__":
    main()
