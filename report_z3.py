#!/usr/bin/env python3
"""Offline poročilo za jedro Z3 (out/report_z3.html, EN privzeto + SL) + zapis (out/zapis_z3.json).

Enaka zgradba kot report.py (TREE) – razdelki 1–6 in kartice kandidatov – za neposredno primerjavo;
dodan je razdelek 7 (primerjava TREE ↔ Z3).
"""
import datetime, hashlib, html, json, re, sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "out"
J = lambda p: json.loads((BASE / p).read_text(encoding="utf-8"))
E = lambda s: html.escape(str(s if s is not None else ""))

HASHED = [
    "data/JobReqId26984690.pdf", "data/Prosnje_kandidatov.pdf", "cues.json", "cues_sl.json", "data/dejstva.json",
    "segment.py", "classify.py", "build_tree.py", "candidates.py", "facts.py", "decide.py",
    "z3_core.py", "report_z3.py", "i18n_en.json", "out/tree.json", "out/dejstva_ocenjena.json", "out/z3_odlocitev.json",
]

CSS = """
:root{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--acc:#2f5d8a;
--t:#1f7a4a;--tbg:#e3f3ea;--f:#a8322d;--fbg:#f8e4e2;--u:#8a6a12;--ubg:#f6eed6;--code:#f1f0ec}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--muted:#9d9c95;--line:#33332f;--acc:#8db4dc;
--t:#7fd3a3;--tbg:#17352a;--f:#f0948e;--fbg:#3d1f1d;--u:#e2c275;--ubg:#3a311a;--code:#2a2a27}}
:root[data-theme="dark"]{--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--muted:#9d9c95;--line:#33332f;--acc:#8db4dc;
--t:#7fd3a3;--tbg:#17352a;--f:#f0948e;--fbg:#3d1f1d;--u:#e2c275;--ubg:#3a311a;--code:#2a2a27}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1120px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px} h2{font-size:1.2rem;margin:36px 0 10px;padding-top:8px;border-top:1px solid var(--line)}
h3{margin:0;font-size:1.05rem} .card h3{margin:14px 0 4px}
.muted{color:var(--muted);font-size:.85em} .small{font-size:.88em}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}
.hero{border-left:5px solid var(--acc)}
.hero .big{font-size:1.25rem;font-weight:600;margin:4px 0 8px}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:10px 0}
.lbl{font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:3px}
.chip{display:inline-block;padding:1px 9px;border-radius:999px;font-size:.82em;font-weight:600;white-space:nowrap}
.chip.t{background:var(--tbg);color:var(--t)} .chip.f{background:var(--fbg);color:var(--f)} .chip.u{background:var(--ubg);color:var(--u)}
.pill{font-size:.8rem;border:1px solid var(--line);border-radius:999px;padding:2px 10px;color:var(--muted)}
.cand header{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}
table{border-collapse:collapse;width:100%;font-size:.88rem;margin:8px 0}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
th{font-weight:600;color:var(--muted);font-size:.8rem}
.scroll{overflow-x:auto} .q{font-style:italic}
.gloss{color:var(--muted);font-size:.85em;margin-top:2px}
code{background:var(--code);padding:1px 5px;border-radius:5px;font-size:.88em;word-break:break-word}
code.hash{font-size:.75em} td:first-child code{white-space:nowrap}
pre.smt{white-space:pre-wrap;font-size:.78em;background:var(--code);padding:10px;border-radius:8px;max-height:360px;overflow:auto}
details{margin:8px 0} summary{cursor:pointer;font-weight:600;color:var(--acc)}
ul,ol{padding-left:20px} li{margin:3px 0}
button{font:inherit;padding:7px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
.langsw{display:flex;gap:4px;justify-content:flex-end;margin-bottom:8px}
.langsw button{padding:3px 10px;font-size:.82rem} .langsw button[aria-pressed="true"]{background:var(--acc);color:var(--card);border-color:var(--acc)}
nav.toc a{color:var(--acc);text-decoration:none;margin-right:14px;font-size:.9rem;display:inline-block}
.lb[hidden]{display:none}
.engine{display:inline-block;font-size:.75rem;font-weight:700;letter-spacing:.05em;padding:2px 8px;border-radius:6px;background:var(--acc);color:var(--card);vertical-align:middle;margin-left:8px}
@media print{details{display:block} details>*{display:block} button,nav,.langsw{display:none}}
"""


def sha(p):
    return hashlib.sha256((BASE / p).read_bytes()).hexdigest()


def chip(v, label=None):
    cls = {"T": "t", "F": "f", "U": "u"}.get(v, "u")
    return f'<span class="chip {cls}">{E(label or v)}</span>'


def main():
    z = J("out/z3_odlocitev.json")
    dec = J("out/odlocitev.json")
    fo = J("out/dejstva_ocenjena.json")
    kand = J("out/kandidati.json")
    tree = J("out/tree.json")
    sl = J("cues_sl.json")
    tr = J("i18n_en.json")
    names = {k["id"]: k["ime"] for k in kand["kandidati"]}
    facts = {f["idx"]: f for f in fo["dejstva"]}
    atoms, nodes, parent = {}, {}, {}

    def walk(n, root):
        if n["op"] == "ATOM":
            atoms[n["id"]] = dict(n, drevo=root)
        else:
            nodes[n["id"]] = dict(n, drevo=root)
            for c in n["otroci"]:
                walk(c, root)
    for t in tree["drevesa"]:
        walk(t, t["koren"])
    roots = {t["koren"]: t for t in tree["drevesa"]}
    mode0 = sl["politika_izbire"].get("privzeti_nacin", "S")
    mode1 = "B" if mode0 == "S" else "S"
    R0, R1 = z["nacini"][mode0], z["nacini"][mode1]
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
    cmp = z["primerjava_tree"]
    smt_ok = sum(x["ujemanje"] for x in z["smt2"])
    decisive = [r for r in z["obcutljivost"] if r["spremeni_izbiro"] or r["spremeni_izlocene"]]
    unused_en = {u["citat"]: tr["unused_reasons"][i] for i, u in enumerate(fo["neuporabljene_izjave"])}

    # ---- zapis ----
    smt_files = sorted((OUT / "z3").glob("*.smt2"))
    record = {
        "zapis": "Minimalni pregledljivi zapis odločitve – jedro Z3",
        "razpis": "Citi Job Req 26984690 – Senior AI Engineer, Banking Technology",
        "ustvarjeno": now, "jedro": f"Z3 {z['z3']} (SMT)",
        "viri_in_programi": [{"pot": p, "sha256": sha(p)} for p in HASHED if (BASE / p).exists()]
                            + [{"pot": f"out/z3/{p.name}", "sha256": sha(f'out/z3/{p.name}')} for p in smt_files],
        "nacin_primarni": mode0, "nacini": sl["nacini"], "politika_izbire": sl["politika_izbire"],
        "premostitvena_pravila": sl["premostitvena_pravila"],
        "rezultat": {m: {"izloceni": r["izloceni"], "vrstni_red": r["vrstni_red"], "izbrani": r["izbrani"],
                         "status": r["status"], "T_M": {k: c["T_M"] for k, c in r["kandidati"].items()},
                         "jedra_T_M": {k: c["jedra"].get(roots["T_M"]["id"], []) for k, c in r["kandidati"].items()},
                         "manjka_najmanj": {k: c["manjka_najmanj"] for k, c in r["kandidati"].items()}}
                     for m, r in z["nacini"].items()},
        "obcutljivost": z["obcutljivost"],
        "primerjava_tree": {"vrednosti": f"{cmp['vrednosti']['ujemanje']}/{cmp['vrednosti']['primerjav']}",
                            "izbor_S": cmp["S"]["enak_izbor"], "izbor_B": cmp["B"]["enak_izbor"],
                            "obcutljivost_enaka": cmp["obcutljivost_enaka"]},
        "smt2_ponovitev": f"{smt_ok}/{len(z['smt2'])}",
        "meja_dopustnosti": {
            "dokazano_z_Z3": "Ob navedenih omejitvah (dejstva kot spodnje meje, negacije, natančna števila) je vsaka propozicija/vozlišče dokazano (dejstva ∧ ¬φ UNSAT), ovrženo (dejstva ∧ φ UNSAT) ali neodločeno; minimalno jedro navaja dejstva, ki to povzročijo.",
            "ni_dokazano": "Resničnost dejstev, pravilnost interpretacije citatov, primernost kandidata, pravičnost politike izbire, pravilnost samega reševalnika Z3.",
            "zahteva_cloveka": ["potrditev vsakega dejstva in njegove vrste (E/I)", "odobritev ali zavrnitev vsakega premostitvenega pravila",
                                "odobritev politike izbire P1–P3", "odločitev o zaposlitvi"]},
        "podpisi": {"pregledal_dejstva": None, "odobril_pravila": None, "odobril_politiko": None, "datum": None},
    }
    canon = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    record["pecat_sha256"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    record["_pecat"] = "SHA-256 kanonične JSON oblike zapisa brez polj 'pecat_sha256' in '_pecat'. Pečat zaznava spremembe, NI podpis."
    (OUT / "zapis_z3.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    embedded = json.dumps(record, ensure_ascii=False).replace("</", "<\\/")
    smt_texts = {p.stem: p.read_text(encoding="utf-8") for p in smt_files}

    def tr_label(s):
        if s in tr["labels"]:
            return tr["labels"][s]
        for pat, rep in tr["label_patterns"]:
            s = re.sub(pat, rep, s)
        for k, v in tr["labels"].items():
            s = s.replace(k, v)
        return s

    def body(lang):
        en = lang == "en"
        T = (lambda s, e: e) if en else (lambda s, e: s)
        lab = tr_label if en else (lambda s: s)
        P = "z" + lang + "-"

        def chipL(v):
            return chip(v, {"T": T("T · dokazano", "T · proven"), "F": T("F · ovrženo", "F · refuted"),
                            "U": T("U · ni dokazano", "U · not proven")}[v])

        def z3prop(aid):
            a = atoms[aid]
            if a.get("raven"):
                return f"L_{aid} ≥ {a['raven']}"
            if a.get("prag_let"):
                return f"Y_{aid} ≥ {a['prag_let']}"
            return f"B_{aid}"

        def z3fact(f):
            a = atoms[f["atom"]]
            aid = f["atom"]
            if "vrednost" in f:
                return z3prop(aid) if f["vrednost"] else "¬(" + z3prop(aid) + ")"
            if f.get("leta") is not None:
                return f"Y_{aid} {'=' if f['kvantifikator'] == '=' else '≥'} {f['leta']}"
            lvl = f.get("raven") or sl["ravni_signalov"].get(f.get("signal") or "")
            return f"L_{aid} ≥ {lvl}" if a.get("raven") else f"B_{aid}"

        def infix(n, depth=0):
            if n["op"] == "ATOM":
                return n["id"]
            op = " ∧ " if n["op"] == "AND" else " ∨ "
            s = op.join(infix(c, depth + 1) for c in n["otroci"])
            return f"({s})" if depth else s

        def quote(q):
            g = tr["quotes"].get(q) if en else None
            return f"<span class='q'>„{E(q)}“</span>" + (f"<div class='gloss'>EN: {E(g)}</div>" if g else "")

        def core_txt(core):
            if not core:
                return "—"
            return ", ".join(f"<code>{E(i)}</code> ({E(facts[i]['atom'])}{(' · ' + facts[i]['pravilo']) if facts[i].get('pravilo') else ''})" for i in core)

        def cand_card(k):
            c0, c1 = R0["kandidati"][k], R1["kandidati"][k]
            kt = next(x for x in kand["kandidati"] if x["id"] == k)
            rows = []
            for f in fo["dejstva"]:
                if f["k"] != k:
                    continue
                a = atoms[f["atom"]]
                v0 = c0["atomi"][f["atom"]]
                rows.append(
                    f"<tr><td><code>{E(f['idx'])}</code></td><td><code>{E(f['atom'])}</code> {E(lab(a['oznaka']))}"
                    f"<div class='muted'>{T('atom', 'atom')}: <code>{E(z3prop(f['atom']))}</code></div></td>"
                    f"<td>{quote(f['citat'])}</td><td><code>{E(z3fact(f))}</code></td>"
                    f"<td>{E(f['vrsta'])}{(' · ' + E(f['pravilo'])) if f.get('pravilo') else ''}</td>"
                    f"<td>{chip(v0)}<div class='muted'>{mode0}</div></td></tr>")
            items = "".join(
                f"<tr><td>{E(i)}</td><td>{chip(v)}</td><td>{chip(c1['postavke'][i])}</td>"
                f"<td class='small'>{core_txt(c0['jedra'].get(next(n['id'] for n in nodes.values() if n.get('postavka') and n['oznaka'] == i), []) if v in 'TF' else [])}</td></tr>"
                for i, v in c0["postavke"].items())
            why_f = "".join(f"<li><code>{E(a)}</code> {E(lab(atoms[a]['oznaka']))}: {core_txt(c0['jedra'].get(a, []))}</li>"
                            for a, v in c0["atomi"].items() if v == "F")
            why_f1 = "".join(f"<li><code>{E(a)}</code> {E(lab(atoms[a]['oznaka']))}: {core_txt(c1['jedra'].get(a, []))}</li>"
                             for a, v in c1["atomi"].items() if v == "F" and atoms[a]["drevo"] == "T_M")
            mm = c0["manjka_najmanj"]
            miss = (T("nemogoče – vsaj ena obvezna propozicija je ovržena", "impossible – at least one mandatory proposition is refuted")
                    if mm is None else f"<b>{len(mm)}</b>: " + ", ".join(f"<code>{a}</code> {E(lab(atoms[a]['oznaka']))}" for a in mm))
            unused = "".join(f"<li>{quote(u['citat'])} — {E(unused_en[u['citat']] if en else u['razlog'])}</li>"
                             for u in fo["neuporabljene_izjave"] if u["k"] == k)
            badge = (T("izločen", "excluded") if c0["T_M"] == "F" else T("rang ", "rank ") + str(c0.get("rang"))) + f" ({mode0})"
            letter = (f"<p class='q small'>{E(kt['besedilo'])}</p>" +
                      (f"<div class='gloss'><b>EN (unofficial translation, not evidence):</b> {E(tr['letters'][k])}</div>" if en else ""))
            smt = smt_texts.get(f"{mode0}_{k}", "")
            return f"""
<article class="card cand" id="{P}{k}">
  <header><h3>{E(k)} · {E(names[k])}</h3><span class="pill">{E(badge)}</span></header>
  <div class="grid3">
    <div><div class="lbl">{T('Obvezne', 'Mandatory')} T_M ({mode0})</div>{chipL(c0['T_M'])}</div>
    <div><div class="lbl">{T('Obvezne', 'Mandatory')} T_M ({mode1})</div>{chipL(c1['T_M'])}</div>
    <div><div class="lbl">{T('Atomi', 'Atoms')} T_M ({mode0}) T/F/U</div><b>{c0['aT']} / {c0['aF']} / {len([a for a in atoms if atoms[a]['drevo']=='T_M']) - c0['aT'] - c0['aF']}</b></div>
  </div>
  <p class="small"><b>{T('Najmanj manjkajočih dokazil za T_M = T', 'Fewest missing proofs for T_M = T')} (MaxSAT, {mode0}):</b> {miss}</p>
  {f'<p class="small"><b>{T("Razlog za izločitev (minimalno jedro)", "Reason for exclusion (minimal core)")}, {mode0}:</b></p><ul class="small">{why_f}</ul>' if why_f else ''}
  {f'<p class="small"><b>{T("Ovržene obvezne propozicije v načinu", "Refuted mandatory propositions in mode")} {mode1}:</b></p><ul class="small">{why_f1}</ul>' if why_f1 else ''}
  <details><summary>{T('Obvezne postavke z jedri', 'Mandatory items with cores')} ({mode0} / {mode1})</summary>
    <div class="scroll"><table><thead><tr><th>{T('postavka', 'item')}</th><th>{mode0}</th><th>{mode1}</th><th>{T('minimalno jedro', 'minimal core')} ({mode0})</th></tr></thead><tbody>{items}</tbody></table></div></details>
  <details><summary>{T('Dejstva kot omejitve Z3', 'Facts as Z3 constraints')} ({T('str.', 'p.')} {kt['strani'][0]}{('–' + str(kt['strani'][1])) if kt['strani'][1] != kt['strani'][0] else ''})</summary>
    <div class="scroll"><table><thead><tr><th>#</th><th>{T('propozicija', 'proposition')}</th><th>{T('citat', 'quote (original)')}</th><th>{T('omejitev', 'constraint')}</th><th>{T('vrsta', 'type')}</th><th>{T('atom', 'atom')}</th></tr></thead>
    <tbody>{''.join(rows)}</tbody></table></div></details>
  <details><summary>{T('Točen vhod SMT-LIB2', 'Exact SMT-LIB2 input')} (<code>out/z3/{mode0}_{k}.smt2</code>)</summary><pre class="smt">{E(smt)}</pre></details>
  {f"<details><summary>{T('Izjave, ki jih jedro ne upošteva', 'Statements the core does not use')}</summary><ul class='small'>{unused}</ul></details>" if unused else ''}
  <details><summary>{T('Izvirno besedilo prošnje', 'Original application text (Slovenian)')}</summary>{letter}</details>
</article>"""

        atom_rows = "".join(
            f"<tr><td><code>{a}</code></td><td>{E(lab(x['oznaka']))}</td><td>{E(x['drevo'])}</td><td>{E(x['obveznost'])}</td>"
            f"<td><code>{E(z3prop(a))}</code></td></tr>" for a, x in atoms.items())
        rule_rows = "".join(
            f"<tr><td><code>{E(t['koren'])}</code> {E(lab(t['oznaka']))}</td><td class='small'><code>{E(infix(t))}</code></td></tr>"
            for t in tree["drevesa"])
        node_rows = "".join(
            f"<tr><td><code>{nid}</code></td><td>{E(lab(n['oznaka']))}</td><td class='small'><code>{E(infix(n))}</code></td></tr>"
            for nid, n in nodes.items())
        brule_rows = "".join(
            f"<tr><td><b>{E(r)}</b> {E(x['ime'])}</td><td>{E(tr['rules'][r][0] if en else x['pravilo'])}</td>"
            f"<td class='muted'>{E(tr['rules'][r][1] if en else x['tveganje'])}</td>"
            f"<td>{('<b>' + T('odločilno', 'decisive') + '</b>') if any(d['pravilo'] == r for d in decisive) else (T('vpliva na vrstni red', 'changes the ranking') if any(s['pravilo'] == r and s['spremeni_red'] for s in z['obcutljivost']) else '—')}</td></tr>"
            for r, x in sl["premostitvena_pravila"].items())
        exc = T("izločeni", "excluded")
        sens_rows = "".join(
            f"<tr><td><b>{E(s['pravilo'])}</b> {E(s['ime'])}</td>"
            f"<td>{E(names.get(s['S_plus']['izbrani'], '—'))}<div class='muted'>{exc}: {E(', '.join(s['S_plus']['izloceni']) or '—')}</div></td>"
            f"<td>{E(names.get(s['B_minus']['izbrani'], '—'))}<div class='muted'>{exc}: {E(', '.join(s['B_minus']['izloceni']) or '—')}</div></td></tr>"
            for s in z["obcutljivost"])
        policy_items = "".join(f"<li><b>{E(k)}</b> {E(tr['policy'][k] if en else v)}</li>"
                               for k, v in sl["politika_izbire"].items() if k in ("P1", "P2", "P3"))
        hash_rows = "".join(f"<tr><td><code>{E(h['pot'])}</code></td><td><code class='hash'>{E(h['sha256'])}</code></td></tr>"
                            for h in record["viri_in_programi"])
        nobody = T("nihče", "nobody")
        c0t = R0["kandidati"][R0["izbrani"]]
        excl_txt = "; ".join(
            f"{E(names[k])} ({', '.join(E(a + ' ' + lab(atoms[a]['oznaka'])) for a, v in R0['kandidati'][k]['atomi'].items() if v == 'F' and atoms[a]['drevo'] == 'T_M')}"
            f" · {T('jedro', 'core')} {', '.join(R0['kandidati'][k]['jedra'].get(roots['T_M']['id'], []))})" for k in R0["izloceni"]) or nobody
        excl1 = ", ".join(E(names[k]) for k in R1["izloceni"]) or nobody
        rank0 = " → ".join(
            (f"{E(names[k])} ({R0['kandidati'][k]['items']} post., {R0['kandidati'][k]['aT']} atomov T, manjka ≥ {len(R0['kandidati'][k]['manjka_najmanj'])})" if not en else
             f"{E(names[k])} (items: {R0['kandidati'][k]['items']}, atoms T: {R0['kandidati'][k]['aT']}, missing ≥ {len(R0['kandidati'][k]['manjka_najmanj'])})")
            for k in R0["vrstni_red"])
        rank1 = " → ".join(E(names[k]) for k in R1["vrstni_red"]) or "—"
        d0 = decisive[0] if decisive else None
        d0_txt = (f"S + {E(d0['pravilo'])} → {E(names.get(d0['S_plus']['izbrani'], '—'))}; {exc} "
                  f"{E(', '.join(names[x] for x in d0['S_plus']['izloceni']))}") if d0 else "—"
        proven_items = [i for i, v in c0t["postavke"].items() if v == "T"]
        vv = cmp["vrednosti"]
        diff_rows = "".join(f"<li>{E(d)}</li>" for d in vv["razlike"]) or f"<li>{T('ni razlik', 'no differences')}</li>"
        smt_rows = "".join(f"<tr><td><code>{E(x['datoteka'])}</code></td><td>{chip(x['T_M'])}</td><td>{chip(x['ponovitev_iz_smt2'])}</td></tr>"
                           for x in z["smt2"])
        glossary = "" if not en else """
<details><summary>Glossary of record keys (the record is in Slovenian)</summary><table class="small"><tbody>
<tr><td><code>zapis</code></td><td>record</td><td><code>jedro</code></td><td>core (engine)</td></tr>
<tr><td><code>jedra_T_M</code></td><td>minimal unsat cores for T_M</td><td><code>manjka_najmanj</code></td><td>fewest missing proofs</td></tr>
<tr><td><code>rezultat</code> / <code>izbrani</code> / <code>izloceni</code></td><td>result / selected / excluded</td><td><code>obcutljivost</code></td><td>sensitivity</td></tr>
<tr><td><code>primerjava_tree</code></td><td>comparison with TREE</td><td><code>smt2_ponovitev</code></td><td>SMT-LIB2 re-check</td></tr>
<tr><td><code>meja_dopustnosti</code></td><td>admissibility boundary</td><td><code>podpisi</code> / <code>pecat_sha256</code></td><td>signatures / seal</td></tr>
</tbody></table></details>"""

        return f"""
<h1>{T('Klasifikacija prijav', 'Application classification')} · Senior AI Engineer <span class="engine">Z3 / SMT</span></h1>
<div class="muted">Citi Job Req 26984690 · {T('5 prijav', '5 applications')} · {T('jedro', 'core')} Z3 {E(z['z3'])} · {T('ustvarjeno', 'generated')} {E(now)} · {T('pečat zapisa', 'record seal')} <code class="hash">{record['pecat_sha256'][:16]}…</code></div>
<p class="small muted" style="margin:6px 0 0">{T('Učni eksperiment: prijave so izmišljene, oglas je javno objavljen. Ni produkcijska različica. Enaki vhodi in politika kot poročilo TREE (report.html) – za neposredno primerjavo.', 'Learning experiment: the applications are fictional; the job ad was publicly posted. Not a production version. Same inputs and policy as the TREE report (report.html) – for direct comparison.')}</p>
<nav class="toc" style="margin-top:10px">
<a href="#{P}s1">1 {T('Vhodi', 'Inputs')}</a><a href="#{P}s2">2 {T('Sklep', 'Conclusion')}</a><a href="#{P}s3">3 {T('Kaj Z3 dokazuje', 'What Z3 proves')}</a><a href="#{P}s4">4 {T('Česa ne dokazuje', 'What it does not prove')}</a>
<a href="#{P}s5">5 {T('Predpostavke in omejitve', 'Assumptions & limitations')}</a><a href="#{P}s6">6 {T('Pregledljivi zapis', 'Inspectable record')}</a><a href="#{P}s7">7 TREE ↔ Z3</a><a href="#{P}kand">{T('Kandidati', 'Candidates')}</a></nav>

<section class="card hero">
  <div class="lbl">{T('Izbrani kandidat po klasifikaciji', 'Selected candidate by classification')} ({T('način', 'mode')} {mode0}, {T('pravilo', 'rule')} {E(R0['pravilo'])})</div>
  <div class="big">{E(names[R0['izbrani']])} ({E(R0['izbrani'])}) — {E(tr['status'].get(R0['status'], R0['status']) if en else R0['status'])}</div>
  <p>{T('Noben kandidat <b>ni dokazano</b> izpolnil vseh obveznih zahtev: T_M = T pri 0 od 5.', 'No candidate is <b>proven</b> to meet all mandatory requirements: T_M = T for 0 of 5.')}
  {T('Dokazano izločeni', 'Provably excluded')}: <b>{excl_txt}</b>.
  {T(f'{E(names[R0["izbrani"]])} je prvi po politiki P3', f'{E(names[R0["izbrani"]])} ranks first under policy P3')}: {T('dokazanih obveznih postavk', 'proven mandatory items')} {c0t['items']} ({E(', '.join(proven_items)) or '—'}), {T('dokazanih obveznih atomov', 'proven mandatory atoms')} {c0t['aT']}; {T('do T_M = T manjka najmanj', 'at least')} <b>{len(c0t['manjka_najmanj'])}</b> {T('dokazil', 'more proofs are needed for T_M = T')}.</p>
  <p class="small"><b>{T('Alternativa', 'Alternative')} ({mode1}, {T('s premostitvenimi pravili', 'with bridge rules')}):</b> {E(names.get(R1['izbrani'], '—'))} · {exc}: {excl1}. {T('Izbiro spremeni pravilo', 'The selection is changed by rule')} {E(', '.join(d['pravilo'] + ' ' + d['ime'] for d in decisive) or '—')} ({d0_txt}).</p>
  <p class="small"><b>TREE ↔ Z3:</b> {T('ujemanje vrednosti', 'value agreement')} {vv['ujemanje']}/{vv['primerjav']} · {T('enak izbor', 'same selection')} S: {'✓' if cmp['S']['enak_izbor'] else '✗'}, B: {'✓' if cmp['B']['enak_izbor'] else '✗'} · {T('enaka občutljivost', 'same sensitivity')}: {'✓' if cmp['obcutljivost_enaka'] else '✗'} · SMT-LIB2 {T('ponovitev', 're-check')} {smt_ok}/{len(z['smt2'])}</p>
  <p class="small muted">{T('To je predlog za preverjanje in ni odločitev o zaposlitvi. Vsako dejstvo, premostitveno pravilo in politiko izbire mora potrditi človek.', 'This is a recommendation for verification, not a hiring decision. Every fact, bridge rule and the selection policy must be confirmed by a human.')}</p>
</section>

<h2 id="{P}s1">1 · {T('Vhodi, dejstva, pravila in propozicije', 'Exact Z3 inputs, facts, rules and propositions')}</h2>
<div class="card">
<p>{T(f'<b>Propozicije</b> so isti atomi ({len(atoms)}) kot pri TREE, a <b>številske</b>: raven <code>L_aXX ∈ 0..4</code>, leta <code>Y_aXX ≥ 0</code>, sicer logična spremenljivka <code>B_aXX</code>. <b>Pravila</b> so celotno drevo kot <b>ena formula</b> (brez omejitve 4 spremenljivk). <b>Dejstva</b> ({len(facts)}) so omejitve: „raven 3“ je <code>L ≥ 3</code> (spodnja meja), negacija je <code>¬(L ≥ 3)</code>, „4 leta“ je <code>Y = 4</code>. Vsako dejstvo je sledljiva predpostavka <code>d_Dxxx</code>; dejstva vrste I so vklopljena le z njihovim pravilom B1–B11.',
   f'<b>Propositions</b> are the same atoms ({len(atoms)}) as for TREE, but <b>numeric</b>: level <code>L_aXX ∈ 0..4</code>, years <code>Y_aXX ≥ 0</code>, otherwise a Boolean <code>B_aXX</code>. <b>Rules</b> are the whole tree as <b>one formula</b> (no 4-variable limit). <b>Facts</b> ({len(facts)}) are constraints: “level 3” is <code>L ≥ 3</code> (a lower bound), a negation is <code>¬(L ≥ 3)</code>, “4 years” is <code>Y = 4</code>. Each fact is a tracked assumption <code>d_Dxxx</code>; type-I facts are switched on only together with their rule B1–B11. Quotes stay in the original Slovenian; English glosses are unofficial.')}</p>
<details><summary>{T('Propozicije', 'Propositions')} ({len(atoms)})</summary><div class="scroll"><table><thead><tr><th>id</th><th>{T('propozicija', 'proposition')}</th><th>{T('drevo', 'tree')}</th><th>{T('obv.', 'obl.')}</th><th>Z3</th></tr></thead><tbody>{atom_rows}</tbody></table></div></details>
<details><summary>{T('Pravila – drevesa kot ena formula', 'Rules – each tree as one formula')}</summary><div class="scroll"><table><tbody>{rule_rows}</tbody></table></div>
<details><summary>{T('Vsa notranja vozlišča', 'All internal nodes')} ({len(nodes)})</summary><div class="scroll"><table><tbody>{node_rows}</tbody></table></div></details></details>
<details><summary>{T('Premostitvena pravila B1–B11 (samo v načinu B)', 'Bridge rules B1–B11 (mode B only)')}</summary><div class="scroll"><table><thead><tr><th>{T('pravilo', 'rule')}</th><th>{T('vsebina', 'content')}</th><th>{T('tveganje', 'risk')}</th><th>{T('vpliv', 'impact')}</th></tr></thead><tbody>{brule_rows}</tbody></table></div></details>
<details><summary>{T('Točni vhodi SMT-LIB2', 'Exact SMT-LIB2 inputs')} ({len(z['smt2'])} {T('datotek', 'files')})</summary>
<p class="small">{T('Vsaka datoteka vsebuje deklaracije, domene, dejstva kot implikacije <code>d_Dxxx ⇒ omejitev</code> in dve poizvedbi za T_M: <b>dokaz</b> <code>(assert (not T_M))</code> – UNSAT pomeni T; <b>ovržba</b> <code>(assert T_M)</code> – UNSAT pomeni F. Datoteke lahko prebere katerikoli reševalnik SMT (npr. cvc5). Celoten izvoz je bil ponovno naložen in preverjen', 'Each file contains declarations, domains, facts as implications <code>d_Dxxx ⇒ constraint</code> and two queries for T_M: <b>proof</b> <code>(assert (not T_M))</code> – UNSAT means T; <b>refutation</b> <code>(assert T_M)</code> – UNSAT means F. Any SMT solver (e.g. cvc5) can read the files. The whole export was reloaded and re-checked')}: {smt_ok}/{len(z['smt2'])}.</p>
<div class="scroll"><table><thead><tr><th>{T('datoteka', 'file')}</th><th>T_M</th><th>{T('iz datoteke', 'from file')}</th></tr></thead><tbody>{smt_rows}</tbody></table></div></details>
</div>

<h2 id="{P}s2">2 · {T('Kaj logično sledi', 'What conclusion logically follows')}</h2>
<div class="card"><ol>
<li><b>{T('Izločitev.', 'Exclusion.')}</b> {T(f'V načinu {mode0} je <code>dejstva ∧ T_M</code> nezadovoljivo za', f'In mode {mode0}, <code>facts ∧ T_M</code> is unsatisfiable for')}: {excl_txt}. {T('Minimalno jedro je najmanjši nabor dejstev, ki izločitev povzroči.', 'The minimal core is the smallest set of facts that causes the exclusion.')}</li>
<li><b>{T('Ustreznost.', 'Suitability.')}</b> {T('Za nobenega kandidata <code>dejstva ∧ ¬T_M</code> ni nezadovoljivo, zato T_M = T pri nikomer ne sledi. MaxSAT pove, koliko dokazil najmanj manjka.', 'For no candidate is <code>facts ∧ ¬T_M</code> unsatisfiable, so T_M = T follows for nobody. MaxSAT reports how many proofs are missing at minimum.')}</li>
<li><b>{T('Vrstni red', 'Ranking')} ({mode0}, P3):</b> {rank0}.</li>
<li><b>{T('Način', 'Mode')} {mode1}:</b> {exc} {excl1}; {T('vrstni red', 'ranking')}: {rank1}.</li>
<li><b>{T('Pogojnost.', 'Conditionality.')}</b> {T('Izbira je odvisna od pravila', 'The selection depends on rule')} {E(', '.join(d['pravilo'] for d in decisive))} – {T('enako kot pri TREE.', 'the same as with TREE.')}</li>
</ol></div>

<h2 id="{P}s3">3 · {T('Kaj rezultat Z3 dejansko dokazuje', 'What Z3’s result actually proves')}</h2>
<div class="card"><ul>
<li>{T('Za vsak atom in vsako vozlišče (vsak kandidat, vsak način) je Z3 odločil, ali je <code>dejstva ∧ ¬φ</code> ali <code>dejstva ∧ φ</code> nezadovoljivo. Pri obeh odgovorih UNSAT vrne jedro, ki je bilo z brisanjem po eno skrčeno do <b>minimalnega</b> (odstranitev kateregakoli dejstva bi dokaz podrla).', 'For every atom and node (each candidate, each mode) Z3 decided whether <code>facts ∧ ¬φ</code> or <code>facts ∧ φ</code> is unsatisfiable. For every UNSAT answer it returned a core that was shrunk one by one to a <b>minimal</b> one (removing any fact would break the proof).')}</li>
<li>{T('Dokazano je samo to: <i>če</i> dejstva veljajo kot zapisane omejitve, <i>potem</i> je φ nujno resnična (T), nujno neresnična (F) ali neodločena (U).', 'Only this is proven: <i>if</i> the facts hold as the stated constraints, <i>then</i> φ is necessarily true (T), necessarily false (F) or undetermined (U).')}</li>
<li>{T('Dejstva vsakega kandidata so konsistentna v obeh načinih (ni protislovnih trditev).', 'Each candidate’s facts are consistent in both modes (no contradictory claims).') if all(c['konsistentna'] for r in z['nacini'].values() for c in r['kandidati'].values()) else T('Pri nekaterih kandidatih so dejstva protislovna – glej kartice.', 'For some candidates the facts are contradictory – see the cards.')}</li>
<li>{T('Najmanj manjkajočih dokazil je optimum MaxSAT: manj dokazil ne zadošča za T_M = T.', 'The fewest missing proofs is a MaxSAT optimum: fewer proofs cannot make T_M = T.')}</li>
</ul></div>

<h2 id="{P}s4">4 · {T('Česa rezultat izrecno NE dokazuje', 'What it explicitly does NOT prove')}</h2>
<div class="card"><ul>
<li>{T('Ne dokazuje, da so trditve v prošnjah <b>resnične</b> niti da je <b>interpretacija</b> citatov pravilna – vhod je isti kot pri TREE.', 'It does not prove the claims are <b>true</b> or that the <b>interpretation</b> of the quotes is correct – the input is the same as for TREE.')}</li>
<li>{T('Ne dokazuje, da je izbrani kandidat <b>primeren</b>; rang P3 je štetje, ne ocena.', 'It does not prove the selected candidate is <b>suitable</b>; the P3 ranking is a count, not an assessment.')}</li>
<li>{T('Minimalno jedro je <b>en</b> najmanjši razlog; lahko obstajajo še drugi neodvisni razlogi (npr. pri Tjaši v načinu B dva).', 'A minimal core is <b>one</b> smallest reason; other independent reasons may exist (e.g. two for Tjaša in mode B).')}</li>
<li>{T('Ne ocenjuje stališč in osebnosti ter ničesar zunaj besedil.', 'It does not assess attitudes or personality, or anything outside the texts.')}</li>
<li>{T('Ne dokazuje pravilnosti samega reševalnika Z3 (velika koda C++); zato je rezultat primerjan s TREE in ponovljen iz SMT-LIB2.', 'It does not prove the Z3 solver itself is correct (a large C++ codebase); that is why the result is compared with TREE and re-checked from SMT-LIB2.')}</li>
</ul></div>

<h2 id="{P}s5">5 · {T('Predpostavke, manjkajoči sklepi in omejitve', 'Assumptions, missing inferences and limitations')}</h2>
<div class="card">
<h3>{T('Predpostavke', 'Assumptions')}</h3>
<ol class="small">
<li>{T('Enaka klasifikacija oglasa, slovar signalov in politika P1–P3 kot pri TREE.', 'The same ad classification, cue lexicon and policy P1–P3 as with TREE.')}</li>
<li>{T('Navedena raven je <b>spodnja meja</b>; Z3 to zapiše neposredno kot <code>L ≥ n</code>, zato nižja raven naravno da U.', 'A stated level is a <b>lower bound</b>; Z3 encodes it directly as <code>L ≥ n</code>, so a lower level naturally yields U.')}</li>
<li>{T('MaxSAT za manjkajoča dokazila uporablja monotono abstrakcijo drevesa (vsak atom ima svojo spremenljivko, drevo ima samo ∧/∨) – za naše drevo je to natančno.', 'MaxSAT for missing proofs uses a monotone abstraction of the tree (each atom has its own variable; the tree has only ∧/∨) – exact for this tree.')}</li>
</ol>
<details><summary>{T('Politika izbire', 'Selection policy')}</summary><ul class="small">{policy_items}</ul></details>
<h3>{T('Občutljivost na premostitvena pravila', 'Sensitivity to bridge rules')}</h3>
<div class="scroll"><table><thead><tr><th>{T('pravilo', 'rule')}</th><th>{T('S + pravilo → izbran', 'S + rule → selected')}</th><th>{T('B − pravilo → izbran', 'B − rule → selected')}</th></tr></thead><tbody>{sens_rows}</tbody></table></div>
<h3>{T('Manjkajoči sklepi', 'Missing inferences')}</h3>
<p class="small">{T('Na vsaki kartici je optimalen (najmanjši) nabor manjkajočih dokazil, ki bi T_M naredil resničen. Pri izločenih kandidatih takega nabora ni.', 'Each card shows an optimal (smallest) set of missing proofs that would make T_M true. For excluded candidates no such set exists.')}</p>
<h3>{T('Omejitve', 'Limitations')}</h3>
<ul class="small">
<li>{T('Dejstva je izluščil jezikovni model; mehansko je preverjeno le, da je vsak citat dobeseden.', 'The facts were extracted by a language model; only the verbatim presence of each quote is checked mechanically.')}</li>
<li>{T('Z3 nima grafičnega prikaza drevesa kot TREE; drevo je prikazano kot formula.', 'Z3 has no graphical tree view like TREE; the tree is shown as a formula.')}</li>
<li>{T('Večja „zaupanja vredna osnova“: TREE je majhna, pregledna koda Java, Z3 je velik industrijski reševalnik. Zato sta rezultata medsebojno preverjena.', 'Larger trusted base: TREE is small, readable Java code; Z3 is a large industrial solver. That is why the two results are cross-checked.')}</li>
<li>{T('Odločitev o zaposlitvi, ki bi temeljila izključno na avtomatizirani obdelavi, bi verjetno sprožila pravila o avtomatiziranem odločanju (npr. čl. 22 GDPR).', 'A hiring decision based solely on automated processing would likely trigger rules on automated decision-making (e.g. GDPR Art. 22).')}</li>
</ul></div>

<h2 id="{P}s6">6 · {T('Minimalni pregledljivi zapis', 'Minimum inspectable record for an independent authority')}</h2>
<div class="card">
<p>{T('Zapis <code>out/zapis_z3.json</code> vsebuje zgostitve vseh virov, programov in datotek SMT-LIB2, rezultate z minimalnimi jedri, občutljivost, primerjavo s TREE in polja za podpise. Neodvisni presojevalec lahko datoteke SMT-LIB2 preveri s <b>katerimkoli</b> reševalnikom SMT.', 'The record <code>out/zapis_z3.json</code> contains hashes of all sources, programs and SMT-LIB2 files, results with minimal cores, sensitivity, the comparison with TREE and signature fields. An independent reviewer can check the SMT-LIB2 files with <b>any</b> SMT solver.')}</p>
<p><b>{T('Pečat', 'Seal')}:</b> <code class="hash">{record['pecat_sha256']}</code></p>
<p><button class="dl">{T('Prenesi zapis (JSON)', 'Download record (JSON)')}</button></p>
{glossary}
<details><summary>{T('Zgostitve virov in programov (SHA-256)', 'Hashes of sources and programs (SHA-256)')}</summary><div class="scroll"><table><tbody>{hash_rows}</tbody></table></div></details>
<details><summary>{T('Ponovitev postopka', 'Reproducing the procedure')}</summary><pre class="small" style="white-space:pre-wrap"><code>pip install z3-solver
python3 run_z3.py      # {T('kandidati → dejstva → TREE/Kleene (za primerjavo) → Z3 → poročilo', 'candidates → facts → TREE/Kleene (for comparison) → Z3 → report')}</code></pre></details>
<p class="small muted">{T('Meja dopustnosti: zapis je zanesljiv glede na to, kaj je bilo izračunano iz česa. Resničnosti dejstev ne jamči. Dokler podpisna polja niso izpolnjena, gre za delovni osnutek.', 'Admissibility boundary: the record is reliable as to what was computed from what. It does not vouch for the truth of the facts. Until the signature fields are filled in, it is a working draft.')}</p>
</div>

<h2 id="{P}s7">7 · {T('Primerjava TREE ↔ Z3', 'Comparison TREE ↔ Z3')}</h2>
<div class="card">
<div class="scroll"><table><thead><tr><th></th><th>TREE (propMinimization)</th><th>Z3 (SMT)</th></tr></thead><tbody>
<tr><td>{T('Propozicije', 'Propositions')}</td><td>{T('0/1; primerjava ravni pred vhodom', '0/1; level comparison done before input')}</td><td>{T('števila in omejitve (L ≥ 4, Y = 4)', 'numbers and constraints (L ≥ 4, Y = 4)')}</td></tr>
<tr><td>{T('Velikost formule', 'Formula size')}</td><td>{T('≤ 4 spremenljivke → 19 formul, veriga dokazov', '≤ 4 variables → 19 formulas, chain of proofs')}</td><td>{T('celo drevo kot ena formula', 'whole tree as one formula')}</td></tr>
<tr><td>{T('Trivrednostnost (U)', 'Three values (U)')}</td><td>{T('dva testa protislovja (D/O) nad dvovrednostnim jedrom', 'two contradiction tests (D/O) over a two-valued core')}</td><td>{T('enako (dva testa UNSAT), a neposredno nad dejstvi', 'the same (two UNSAT tests), but directly over the facts')}</td></tr>
<tr><td>{T('Razlaga', 'Explanation')}</td><td>{T('minimalna DNF / ostanek', 'minimal DNF / residual')}</td><td>{T('minimalno jedro (katera dejstva) + MaxSAT (koliko manjka)', 'minimal core (which facts) + MaxSAT (how much is missing)')}</td></tr>
<tr><td>{T('Načini in občutljivost', 'Modes and sensitivity')}</td><td>{T('ponovni izračun dejstev', 'recompute facts')}</td><td>{T('drug nabor predpostavk v istem reševalniku', 'a different assumption set in the same solver')}</td></tr>
<tr><td>{T('Prenosljiv vhod', 'Portable input')}</td><td>{T('niz formule za GUI', 'formula string for the GUI')}</td><td>{T('standard SMT-LIB2', 'SMT-LIB2 standard')}</td></tr>
<tr><td>{T('Pregledljivost jedra', 'Inspectability of the core')}</td><td>{T('majhna koda Java, vidno drevo', 'small Java code, visible tree')}</td><td>{T('velik reševalnik, ni vidnega drevesa', 'large solver, no visible tree')}</td></tr>
<tr><td>{T('Ujemanje', 'Agreement')}</td><td colspan="2"><b>{vv['ujemanje']}/{vv['primerjav']}</b> {T('vrednosti atomov in vozlišč', 'atom and node values')} · {T('izbor', 'selection')} S {'✓' if cmp['S']['enak_izbor'] else '✗'} B {'✓' if cmp['B']['enak_izbor'] else '✗'} · {T('občutljivost', 'sensitivity')} {'✓' if cmp['obcutljivost_enaka'] else '✗'}</td></tr>
</tbody></table></div>
<details><summary>{T('Razlike', 'Differences')} ({len(vv['razlike'])})</summary><ul class="small">{diff_rows}</ul></details>
</div>

<h2 id="{P}kand">{T('Kandidati', 'Candidates')}</h2>
{''.join(cand_card(k) for k in names)}
"""

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Application Classification – Z3</title>
<style>{CSS}</style></head><body><main>
<div class="langsw" role="group" aria-label="Language"><button data-l="en" aria-pressed="true">English</button><button data-l="sl" aria-pressed="false">Slovenščina</button></div>
<div class="lb" data-lang="en" lang="en">{body("en")}</div>
<div class="lb" data-lang="sl" lang="sl" hidden>{body("sl")}</div>
<script type="application/json" id="zapis">{embedded}</script>
<script>
(function(){{
  function setLang(l){{
    document.querySelectorAll('.lb').forEach(function(d){{d.hidden=d.getAttribute('data-lang')!==l;}});
    document.querySelectorAll('.langsw button').forEach(function(b){{b.setAttribute('aria-pressed',String(b.getAttribute('data-l')===l));}});
    document.documentElement.lang=l;
    try{{localStorage.setItem('report-lang',l);}}catch(e){{}}
  }}
  var q=(location.search.match(/[?&]lang=(en|sl)/)||[])[1], s=null;
  try{{s=localStorage.getItem('report-lang');}}catch(e){{}}
  setLang(q||s||'en');
  document.querySelectorAll('.langsw button').forEach(function(b){{b.addEventListener('click',function(){{setLang(b.getAttribute('data-l'));}});}});
  document.querySelectorAll('button.dl').forEach(function(btn){{btn.addEventListener('click',function(){{
    var t=document.getElementById('zapis').textContent;
    var bl=new Blob([t],{{type:'application/json'}});var a=document.createElement('a');
    a.href=URL.createObjectURL(bl);a.download='zapis_z3.json';document.body.appendChild(a);a.click();a.remove();
  }});}});
}})();
</script>
</main></body></html>"""
    (OUT / "report_z3.html").write_text(page, encoding="utf-8")
    print(f"-> out/report_z3.html ({len(page) // 1024} KB, EN + SL), out/zapis_z3.json, seal {record['pecat_sha256'][:16]}")


if __name__ == "__main__":
    main()
