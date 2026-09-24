#!/usr/bin/env python3
"""Offline poročilo (out/report.html, angleščina privzeto + slovenščina) + minimalni pregledljivi zapis (out/zapis_odlocitve.json).

HTML je samostojen (brez spletnih virov), zapis je vgrajen in ga je mogoče prenesti s strani.
"""
import datetime, hashlib, html, json, re
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
OUT = BASE / "out"
J = lambda p: json.loads((BASE / p).read_text(encoding="utf-8"))
E = lambda s: html.escape(str(s if s is not None else ""))

ZA_ZGOSTITEV = [
    "data/JobReqId26984690.pdf", "data/Prosnje_kandidatov.pdf", "cues.json", "cues_sl.json", "data/dejstva.json",
    "segment.py", "classify.py", "build_tree.py", "export_tree.py", "candidates.py", "facts.py", "decide.py",
    "verify_engine.py", "report.py", "run_proof.py", "i18n_en.json", "verify/HarnessProof.java",
    "out/tree.json", "out/formule.json", "out/tree_inputs.tsv", "out/tree_outputs.tsv", "out/pogon_meta.json",
]


def sha(p):
    return hashlib.sha256((BASE / p).read_bytes()).hexdigest()


def chip(v, label=None):
    cls = {"T": "t", "F": "f", "U": "u"}.get(v, "u")
    txt = label or {"T": "T · dokazano", "F": "F · ovrženo", "U": "U · ni dokazano"}.get(v, v)
    return f'<span class="chip {cls}">{E(txt)}</span>'


def v1(v):
    return chip(v, v)


def main():
    kand = J("out/kandidati.json")
    fo = J("out/dejstva_ocenjena.json")
    dec = J("out/odlocitev.json")
    tree = J("out/tree.json")
    form = J("out/formule.json")
    sl = J("cues_sl.json")
    meta = J("out/pogon_meta.json")
    names = {k["id"]: k["ime"] for k in kand["kandidati"]}
    atoms = {}

    def walk(n, root):
        if n["op"] == "ATOM":
            atoms[n["id"]] = dict(n, drevo=root)
        else:
            for c in n["otroci"]:
                walk(c, root)
    for t in tree["drevesa"]:
        walk(t, t["koren"])

    mode0 = sl["politika_izbire"].get("privzeti_nacin", "S")
    mode1 = "B" if mode0 == "S" else "S"
    R0, R1 = dec["po_nacinu"][mode0], dec["po_nacinu"][mode1]
    ver = dec["preverjanje_tree"]
    sens = dec["obcutljivost"]
    facts = fo["dejstva"]
    now = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

    def req(a):
        a = atoms[a]
        if a.get("raven"):
            return f"raven ≥ {a['raven']}"
        if a.get("prag_let"):
            return f"≥ {a['prag_let']} let"
        return "da/ne"

    # ---------------- zapis ----------------
    record = {
        "zapis": "Minimalni pregledljivi zapis odločitve – klasifikacija prijav",
        "razpis": "Citi Job Req 26984690 – Senior AI Engineer, Banking Technology",
        "ustvarjeno": now,
        "viri_in_programi": [{"pot": p, "sha256": sha(p)} for p in ZA_ZGOSTITEV if (BASE / p).exists()],
        "pogon": meta,
        "nacin_primarni": mode0,
        "nacini": sl["nacini"],
        "politika_izbire": sl["politika_izbire"],
        "premostitvena_pravila": sl["premostitvena_pravila"],
        "propozicije": [{"id": a, "oznaka": x["oznaka"], "drevo": x["drevo"], "obveznost": x["obveznost"],
                         "pogoj": req(a), "signal_v_oglasu": " ".join(x.get("signal", []))} for a, x in atoms.items()],
        "pravila_formule": [{"vozlisce": f["id"], "oznaka": f["oznaka"], "R": f["formula_propMinimization"],
                             "crke": {L: d["id"] for L, d in f["legenda"].items()}} for f in form],
        "dejstva": [{k: f.get(k) for k in ("idx", "k", "atom", "citat", "signal", "vrsta", "pravilo", "leta",
                                              "kvantifikator", "raven", "vrednost_dejstva", "razlaga")} for f in facts],
        "dejstva_izluscil": fo.get("izluscil"),
        "neuporabljene_izjave": fo["neuporabljene_izjave"],
        "dokazi_tree": [{"kljuc": f"{m}|{k}|{p['vozlisce']}", "K": p["K"], "R": p["R"],
                         "D_vhod": p["D_vhod"], "D_izhod": p["tree"]["D"]["status"],
                         "O_vhod": p["O_vhod"], "O_izhod": p["tree"]["O"]["status"],
                         "vrednost": p["tree"]["vrednost"]}
                        for m, r in dec["po_nacinu"].items() for k, c in r["kandidati"].items() for p in c["dokazi"]],
        "preverjanje": {"tree_proti_python": f"{ver['ujemanje']}/{ver['dokazov']}", "neujemanja": ver["neujemanja"]},
        "rezultat": {m: {"izloceni": r["izloceni"], "dokazano_ustrezni": r["dokazano_ustrezni"], "pravilo": r["pravilo"],
                         "vrstni_red": r["vrstni_red"], "izbrani": r["izbrani"], "status": r["status"],
                         "T_M": {k: c["T_M"] for k, c in r["kandidati"].items()}}
                     for m, r in dec["po_nacinu"].items()},
        "obcutljivost": sens,
        "meja_dopustnosti": {
            "dokazano_s_TREE": "Samo logična veljavnost: ob navedenih vrednostih propozicij je vsaka formula R dokazana (K⋀¬R protislovje), ovržena (K⋀R protislovje) ali neodločena.",
            "ni_dokazano": "Resničnost dejstev, pravilnost interpretacije citatov, primernost kandidata, pravičnost politike izbire.",
            "zahteva_cloveka": ["potrditev vsakega dejstva in njegove vrste (E/I)", "odobritev ali zavrnitev vsakega premostitvenega pravila",
                                "odobritev politike izbire P1–P3", "odločitev o zaposlitvi (avtomatizirana odločitev ni dopustna brez človeškega pregleda)"],
        },
        "podpisi": {"pregledal_dejstva": None, "odobril_pravila": None, "odobril_politiko": None, "datum": None},
    }
    canon = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    record["pecat_sha256"] = hashlib.sha256(canon.encode("utf-8")).hexdigest()
    record["_pecat"] = "SHA-256 kanonične JSON oblike zapisa brez polj 'pecat_sha256' in '_pecat' (sort_keys, brez presledkov). Pečat zaznava spremembe, NI podpis."
    (OUT / "zapis_odlocitve.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------------- HTML (EN default + SL) ----------------
    tr = J("i18n_en.json")
    top0, top1 = R0["izbrani"], R1["izbrani"]
    c0 = R0["kandidati"][top0]
    izl0 = R0["izloceni"]
    decisive = [r for r in sens["pravila"] if r["spremeni_izbiro"] or r["spremeni_izlocene"]]
    unused_en = {u["citat"]: tr["unused_reasons"][i] for i, u in enumerate(fo["neuporabljene_izjave"])}
    embedded = json.dumps(record, ensure_ascii=False).replace("</", "<\\/")

    def tr_label(s):
        if s in tr["labels"]:
            return tr["labels"][s]
        for pat, rep in tr["label_patterns"]:
            s = re.sub(pat, rep, s)
        for k, v in tr["labels"].items():
            s = s.replace(k, v)
        return s

    def tr_expl(s):
        for pat, rep in tr["explanations"]:
            if re.match(pat, s):
                return re.sub(pat, rep, s)
        return s

    def body(lang):
        en = lang == "en"
        T = (lambda s, e: e) if en else (lambda s, e: s)
        lab = tr_label if en else (lambda s: s)
        P = lang + "-"  # predpona id-jev (dva jezika na isti strani)

        def chipL(v):
            txt = {"T": T("T · dokazano", "T · proven"), "F": T("F · ovrženo", "F · refuted"),
                   "U": T("U · ni dokazano", "U · not proven")}[v]
            return chip(v, txt)

        def req(a):
            a = atoms[a]
            if a.get("raven"):
                return T(f"raven ≥ {a['raven']}", f"level ≥ {a['raven']}")
            if a.get("prag_let"):
                return T(f"≥ {a['prag_let']} let", f"≥ {a['prag_let']} yrs")
            return T("da/ne", "yes/no")

        def quote(q, block=False):
            g = tr["quotes"].get(q) if en else None
            tag = "p" if block else "span"
            out = f"<{tag} class='q'>„{E(q)}“</{tag}>"
            if g:
                out += f"<div class='gloss'>EN: {E(g)}</div>"
            return out

        def status(s):
            return tr["status"].get(s, s) if en else s

        def fact_rows(k):
            rows = []
            for f in facts:
                if f["k"] != k:
                    continue
                a = atoms[f["atom"]]
                lvl = f.get("raven") or sl["ravni_signalov"].get(f.get("signal") or "", "")
                ev = (f"{f['kvantifikator']}{f['leta']} " + T("let", "yrs") if f.get("leta") is not None else
                      (T("da", "yes") if f.get("vrednost") is True else T("ne", "no") if f.get("vrednost") is False
                       else T("raven ", "level ") + str(lvl)))
                rows.append(
                    f"<tr><td><code>{E(f['idx'])}</code></td><td><code>{E(f['atom'])}</code> {E(lab(a['oznaka']))}"
                    f"<div class='muted'>{E(a['obveznost'])} · {T('zahteva', 'requires')} {E(req(f['atom']))}</div></td>"
                    f"<td>{quote(f['citat'])}</td><td>{E(f.get('signal') or '—')}</td><td>{E(ev)}</td>"
                    f"<td>{E(f['vrsta'])}{(' · ' + E(f['pravilo'])) if f.get('pravilo') else ''}</td>"
                    f"<td>{v1(f['vrednost_dejstva'])}<div class='muted'>{E(tr_expl(f['razlaga']) if en else f['razlaga'])}</div></td></tr>")
            return "".join(rows)

        def cand_card(k):
            c0k, c1k = R0["kandidati"][k], R1["kandidati"][k]
            kt = next(x for x in kand["kandidati"] if x["id"] == k)
            items = "".join(f"<tr><td>{E(i)}</td><td>{v1(v)}</td><td>{v1(c1k['postavke'][i])}</td></tr>"
                            for i, v in c0k["postavke"].items())
            u_atoms = [a for a in atoms if atoms[a]["drevo"] == "T_M" and fo["vrednosti"][k][mode0][a]["v"] == "U"]
            miss = ", ".join(f"<code>{a}</code> {E(lab(atoms[a]['oznaka']))}" for a in u_atoms)
            unused = "".join(f"<li>{quote(u['citat'])} — {E(unused_en[u['citat']] if en else u['razlog'])}</li>"
                             for u in fo["neuporabljene_izjave"] if u["k"] == k)
            badge = (T("izločen", "excluded") if c0k["T_M"] == "F" else T("rang ", "rank ") + str(c0k.get("rang"))) + f" ({mode0})"
            pages = f"{kt['strani'][0]}" + (f"–{kt['strani'][1]}" if kt["strani"][1] != kt["strani"][0] else "")
            letter = (f"<p class='q small'>{E(kt['besedilo'])}</p>" +
                      (f"<div class='gloss'><b>EN (unofficial translation, not evidence):</b> {E(tr['letters'][k])}</div>" if en else ""))
            unused_block = (f"<details><summary>{T('Izjave, ki jih TREE ne upošteva', 'Statements TREE does not use')}</summary>"
                            f"<ul class='small'>{unused}</ul></details>") if unused else ""
            return f"""
<article class="card cand" id="{P}{k}">
  <header><h3>{E(k)} · {E(names[k])}</h3><span class="pill">{E(badge)}</span></header>
  <div class="grid3">
    <div><div class="lbl">{T('Obvezne', 'Mandatory')} T_M ({mode0})</div>{chipL(c0k['T_M'])}</div>
    <div><div class="lbl">{T('Obvezne', 'Mandatory')} T_M ({mode1})</div>{chipL(c1k['T_M'])}</div>
    <div><div class="lbl">{T('Atomi', 'Atoms')} T_M ({mode0}) T/F/U</div><b>{c0k['atomi_M']['T']} / {c0k['atomi_M']['F']} / {c0k['atomi_M']['U']}</b> {T('od', 'of')} {c0k['atomi_M']['vseh']}</div>
  </div>
  <details><summary>{T('Obvezne postavke', 'Mandatory items')} ({mode0} / {mode1})</summary>
    <table><thead><tr><th>{T('postavka', 'item')}</th><th>{mode0}</th><th>{mode1}</th></tr></thead><tbody>{items}</tbody></table></details>
  <details><summary>{T('Dejstva z dobesednimi citati', 'Facts with verbatim quotes')} ({T('str.', 'p.')} {pages})</summary>
    <div class="scroll"><table class="facts"><thead><tr><th>#</th><th>{T('propozicija', 'proposition')}</th><th>{T('citat', 'quote (original)')}</th><th>{T('signal', 'cue')}</th><th>{T('dokaz', 'evidence')}</th><th>{T('vrsta', 'type')}</th><th>{T('vrednost', 'value')}</th></tr></thead>
    <tbody>{fact_rows(k)}</tbody></table></div></details>
  <details><summary>{T('Manjkajoči sklepi – obvezni atomi brez dokaza', 'Missing inferences – mandatory atoms without evidence')} ({len(u_atoms)})</summary><p class="small">{miss}</p></details>
  {unused_block}
  <details><summary>{T('Izvirno besedilo prošnje', 'Original application text (Slovenian)')}</summary>{letter}</details>
</article>"""

        def proof_table(k, mode):
            rows = []
            for p in dec["po_nacinu"][mode]["kandidati"][k]["dokazi"]:
                leg = " ".join(f"{L}={v['v']}" for L, v in p["crke"].items())
                resid = (f"<div class='muted'>{T('ostanek', 'residual')}: {E(' ⋁ '.join(p['ostanek']))}</div>") if p["ostanek"] else ""
                rows.append(
                    f"<tr><td><code>{E(p['vozlisce'])}</code><div class='muted'>{E(lab(p['oznaka']))}</div></td>"
                    f"<td><code>{E(p['R'])}</code></td><td class='muted'>{E(leg)}</td>"
                    f"<td><code>{E(p['D_vhod'])}</code><div class='muted'>{E(p['tree']['D']['status'])}</div></td>"
                    f"<td><code>{E(p['O_vhod'])}</code><div class='muted'>{E(p['tree']['O']['status'])}</div></td>"
                    f"<td>{v1(p['tree']['vrednost'])}{resid}</td></tr>")
            return (f"<div class='scroll'><table><thead><tr><th>{T('vozlišče', 'node')}</th><th>{T('pravilo', 'rule')} R</th><th>{T('črke', 'letters')}</th>"
                    f"<th>{T('D-vhod (dokaz)', 'D-input (proof)')}</th><th>{T('O-vhod (ovržba)', 'O-input (refutation)')}</th><th>{T('rezultat', 'result')}</th></tr></thead><tbody>"
                    + "".join(rows) + "</tbody></table></div>")

        formula_rows = "".join(
            f"<tr><td><code>{E(f['id'])}</code></td><td>{E(lab(f['oznaka']))}</td><td><code>{E(f['formula_propMinimization'])}</code></td>"
            f"<td class='small'>{'; '.join(E(L + ' = ' + d['id'] + ' ' + lab(d['oznaka'])) for L, d in f['legenda'].items())}</td></tr>"
            for f in form)
        atom_rows = "".join(
            f"<tr><td><code>{a}</code></td><td>{E(lab(x['oznaka']))}</td><td>{E(x['drevo'])}</td><td>{E(x['obveznost'])}</td>"
            f"<td>{E(req(a))}</td><td class='muted'>{E(' '.join(x.get('signal', [])))}</td></tr>" for a, x in atoms.items())

        def impact(r):
            if any(d["pravilo"] == r for d in decisive):
                return f"<b>{T('odločilno', 'decisive')}</b>"
            if any(s["pravilo"] == r and s["spremeni_red"] for s in sens["pravila"]):
                return T("vpliva na vrstni red", "changes the ranking")
            return "—"
        rule_rows = "".join(
            f"<tr><td><b>{E(r)}</b> {E(x['ime'])}</td><td>{E(tr['rules'][r][0] if en else x['pravilo'])}</td>"
            f"<td class='muted'>{E(tr['rules'][r][1] if en else x['tveganje'])}</td><td>{impact(r)}</td></tr>"
            for r, x in sl["premostitvena_pravila"].items())
        exc = T("izločeni", "excluded")
        sens_rows = "".join(
            f"<tr><td><b>{E(s['pravilo'])}</b> {E(s['ime'])}</td>"
            f"<td>{E(names.get(s['S_plus']['izbrani'], '—'))}<div class='muted'>{exc}: {E(', '.join(s['S_plus']['izloceni']) or '—')}</div></td>"
            f"<td>{E(names.get(s['B_minus']['izbrani'], '—'))}<div class='muted'>{exc}: {E(', '.join(s['B_minus']['izloceni']) or '—')}</div></td></tr>"
            for s in sens["pravila"])
        amb_rows = "".join(
            f"<li><b>{E(d['koda'])}</b> ({E(d['postavka'])}) „{E(d['klavzula'])}“ – {E(tr['ambiguities'].get(d['koda'], d['razlaga']) if en else d['razlaga'])}</li>"
            for d in tree["dvoumnosti"])
        hash_rows = "".join(f"<tr><td><code>{E(h['pot'])}</code></td><td><code class='hash'>{E(h['sha256'])}</code></td></tr>"
                            for h in record["viri_in_programi"])
        proofs_html = "".join(
            f"<details><summary>{E(k)} · {E(names[k])} – {T('način', 'mode')} {m}</summary>{proof_table(k, m)}</details>"
            for m in (mode0, mode1) for k in names)
        rank0 = " → ".join(
            (f"{E(names[k])} ({R0['kandidati'][k]['postavke_T']} post., {R0['kandidati'][k]['atomi_M']['T']} atomov T)" if not en else
             f"{E(names[k])} (items: {R0['kandidati'][k]['postavke_T']}, atoms T: {R0['kandidati'][k]['atomi_M']['T']})")
            for k in R0["vrstni_red"])
        rank1 = " → ".join(E(names[k]) for k in R1["vrstni_red"]) or "—"
        nobody = T("nihče", "nobody")
        excl_txt = "; ".join(f"{E(names[k])} ({E(', '.join(a + ' ' + lab(atoms[a]['oznaka']) for a in R0['kandidati'][k]['F_atomi']))})"
                             for k in izl0) or nobody
        excl1_txt = ", ".join(E(names[k]) for k in R1["izloceni"]) or nobody
        top0_proven = [i for i, v in c0["postavke"].items() if v == "T"]
        dec_rules = ", ".join(d["pravilo"] + " " + d["ime"] for d in decisive) or "—"
        d0 = decisive[0] if decisive else None
        d0_txt = (f"S + {E(d0['pravilo'])} → {E(names.get(d0['S_plus']['izbrani'], '—'))}; {exc} "
                  f"{E(', '.join(names[x] for x in d0['S_plus']['izloceni']))}") if d0 else "—"
        policy_items = "".join(
            f"<li><b>{E(k)}</b> {E(tr['policy'][k] if en else v)}</li>"
            for k, v in sl["politika_izbire"].items() if k in ("P1", "P2", "P3"))
        engine_notes = "".join(f"<li>{T('Pogon', 'Engine')}: {E(x)}</li>"
                               for x in (tr["engine_notes"] if en else meta["ugotovljene_napake_pogona"]))
        glossary = "" if not en else """
<details><summary>Glossary of record keys (the record is in Slovenian)</summary><table class="small"><tbody>
<tr><td><code>zapis</code></td><td>record</td><td><code>dejstva</code></td><td>facts</td></tr>
<tr><td><code>propozicije</code></td><td>propositions</td><td><code>pravila_formule</code></td><td>rules (formulas R)</td></tr>
<tr><td><code>premostitvena_pravila</code></td><td>bridge rules</td><td><code>politika_izbire</code></td><td>selection policy</td></tr>
<tr><td><code>citat</code> / <code>vrsta</code></td><td>quote / type (E, I)</td><td><code>vrednost</code></td><td>value (T, F, U)</td></tr>
<tr><td><code>dokazi_tree</code></td><td>TREE proofs</td><td><code>rezultat</code></td><td>result</td></tr>
<tr><td><code>izbrani</code> / <code>izloceni</code></td><td>selected / excluded</td><td><code>obcutljivost</code></td><td>sensitivity</td></tr>
<tr><td><code>meja_dopustnosti</code></td><td>admissibility boundary</td><td><code>podpisi</code></td><td>signatures</td></tr>
<tr><td><code>pecat_sha256</code></td><td>seal (SHA-256)</td><td><code>viri_in_programi</code></td><td>sources and programs</td></tr>
</tbody></table></details>"""

        return f"""
<h1>{T('Klasifikacija prijav', 'Application classification')} · Senior AI Engineer</h1>
<div class="muted">Citi Job Req 26984690 · {T('5 prijav', '5 applications')} · {T('ustvarjeno', 'generated')} {E(now)} · {T('pečat zapisa', 'record seal')} <code class="hash">{record['pecat_sha256'][:16]}…</code></div>
<p class="small muted" style="margin:6px 0 0">{T('Učni eksperiment: prijave so izmišljene, oglas je javno objavljen. Ni produkcijska različica.', 'Learning experiment: the applications are fictional; the job ad was publicly posted. Not a production version.')}</p>
<nav class="toc" style="margin-top:10px">
<a href="#{P}s1">1 {T('Vhodi', 'Inputs')}</a><a href="#{P}s2">2 {T('Sklep', 'Conclusion')}</a><a href="#{P}s3">3 {T('Kaj TREE dokazuje', 'What TREE proves')}</a><a href="#{P}s4">4 {T('Česa ne dokazuje', 'What it does not prove')}</a>
<a href="#{P}s5">5 {T('Predpostavke in omejitve', 'Assumptions & limitations')}</a><a href="#{P}s6">6 {T('Pregledljivi zapis', 'Inspectable record')}</a><a href="#{P}kand">{T('Kandidati', 'Candidates')}</a></nav>

<section class="card hero">
  <div class="lbl">{T('Izbrani kandidat po klasifikaciji', 'Selected candidate by classification')} ({T('način', 'mode')} {mode0}, {T('pravilo', 'rule')} {E(R0['pravilo'])})</div>
  <div class="big">{E(names[top0])} ({E(top0)}) — {E(status(R0['status']))}</div>
  <p>{T('Noben kandidat <b>ni dokazano</b> izpolnil vseh obveznih zahtev: T_M = T pri 0 od 5.', 'No candidate is <b>proven</b> to meet all mandatory requirements: T_M = T for 0 of 5.')}
  {T('Dokazano izločeni', 'Provably excluded')}: <b>{excl_txt}</b>.
  {T(f'{E(names[top0])} je prvi po politiki P3: dokazanih obveznih postavk {c0["postavke_T"]}', f'{E(names[top0])} ranks first under policy P3: proven mandatory items {c0["postavke_T"]}')} ({E(', '.join(top0_proven)) or '—'}), {T('dokazanih obveznih atomov', 'proven mandatory atoms')} {c0['atomi_M']['T']} {T('od', 'of')} {c0['atomi_M']['vseh']}.</p>
  <p class="small"><b>{T('Alternativa', 'Alternative')} ({mode1}, {T('s premostitvenimi pravili', 'with bridge rules')}):</b> {E(names.get(top1, '—'))} · {exc}: {excl1_txt}.
  {T('Izbiro spremeni pravilo', 'The selection is changed by rule')} {E(dec_rules)}: {T('samo to pravilo, dodano strogemu načinu, vpliva na izločitev in izbiro', 'this rule alone, added to strict mode, changes exclusion and selection')} ({d0_txt}).</p>
  <p class="small muted">{T('To je predlog za preverjanje in ni odločitev o zaposlitvi. Vsako dejstvo, premostitveno pravilo in politiko izbire mora potrditi človek.', 'This is a recommendation for verification, not a hiring decision. Every fact, bridge rule and the selection policy must be confirmed by a human.')}</p>
</section>

<h2 id="{P}s1">1 · {T('Vhodi, dejstva, pravila in propozicije', 'Exact TREE inputs, facts, rules and propositions')}</h2>
<div class="card">
<p>{T(f'<b>Propozicije</b> so atomi, izpeljani iz oglasa ({len(atoms)}). Atom je resničen, ko ima kandidat vsaj zahtevano raven ali prag let. <b>Pravila</b> so formule R ({len(form)} vozlišč, ≤ 4 spremenljivke za propMinimization); črka lahko pomeni rezultat nižjega vozlišča. <b>Dejstva</b> so izjave iz prošenj z dobesednim citatom ({len(facts)}; vsak citat je bil mehansko najden v besedilu).',
   f'<b>Propositions</b> are atoms derived from the job ad ({len(atoms)}). An atom is true when the candidate has at least the required level or years. <b>Rules</b> are formulas R ({len(form)} nodes, ≤ 4 variables for propMinimization); a letter may stand for the result of a lower node. <b>Facts</b> are statements from the applications with a verbatim quote ({len(facts)}; each quote was found mechanically in the text). Quotes stay in the original Slovenian because they are the evidence; English glosses are unofficial.')}</p>
<p class="small muted">{T('Lestvica ravni: 1 poznavanje · 2 delovno · 3 praktično · 4 ekspert. Obveznost: M obvezno · N dodatno · P pričakovana naloga.', 'Level scale: 1 familiarity · 2 working · 3 practical · 4 expert. Obligation: M mandatory · N nice to have · P expected responsibility.')}</p>
<details><summary>{T('Propozicije', 'Propositions')} ({len(atoms)} {T('atomov', 'atoms')})</summary><div class="scroll"><table><thead><tr><th>id</th><th>{T('propozicija', 'proposition')}</th><th>{T('drevo', 'tree')}</th><th>{T('obv.', 'obl.')}</th><th>{T('pogoj', 'condition')}</th><th>{T('signal v oglasu', 'cue in the ad')}</th></tr></thead><tbody>{atom_rows}</tbody></table></div></details>
<details><summary>{T('Pravila – formule R za pregledovalnik', 'Rules – formulas R for the viewer')}</summary><div class="scroll"><table><thead><tr><th>{T('vozlišče', 'node')}</th><th>{T('oznaka', 'label')}</th><th>R</th><th>{T('črke', 'letters')}</th></tr></thead><tbody>{formula_rows}</tbody></table></div></details>
<details><summary>{T('Premostitvena pravila B1–B11 (samo v načinu B)', 'Bridge rules B1–B11 (mode B only)')}</summary><div class="scroll"><table><thead><tr><th>{T('pravilo', 'rule')}</th><th>{T('vsebina', 'content')}</th><th>{T('tveganje', 'risk')}</th><th>{T('vpliv', 'impact')}</th></tr></thead><tbody>{rule_rows}</tbody></table></div></details>
<details><summary>{T('Točni vhodi za TREE po kandidatih', 'Exact TREE inputs per candidate')} ({ver['vhodov']} {T('formul', 'formulas')})</summary>
<p class="small">{T('Za vozlišče z R in znanimi literali K se vneseta dve formuli. <b>D-vhod</b> <code>(K)⋀¬(R)</code>: protislovje pomeni, da K ⇒ R velja, in je vozlišče <b>T</b>. <b>O-vhod</b> <code>(K)⋀(R)</code>: protislovje pomeni, da sta K in R nezdružljiva, in je vozlišče <b>F</b>. Sicer je vozlišče <b>U</b>, ostanek pa pove, kaj še manjka. Formule se vnašajo v <b>propMinimization</b>.',
   'For a node with rule R and known literals K two formulas are entered. <b>D-input</b> <code>(K)⋀¬(R)</code>: a contradiction means K ⇒ R holds, so the node is <b>T</b>. <b>O-input</b> <code>(K)⋀(R)</code>: a contradiction means K and R are incompatible, so the node is <b>F</b>. Otherwise the node is <b>U</b>, and the residual shows what is still missing. Formulas are entered into <b>propMinimization</b>.')}</p>
{proofs_html}</details>
</div>

<h2 id="{P}s2">2 · {T('Kaj logično sledi', 'What conclusion logically follows')}</h2>
<div class="card"><ol>
<li><b>{T('Izločitev.', 'Exclusion.')}</b> {T(f'V načinu {mode0} iz dejstev in pravil sledi T_M = F za', f'In mode {mode0} the facts and rules entail T_M = F for')}: {excl_txt}. {T('Vsaka taka izločitev je dokazana z O-vhodom (protislovje) v verigi od atoma do korena.', 'Each such exclusion is proven by an O-input (contradiction) along the chain from atom to root.')}</li>
<li><b>{T('Ustreznost.', 'Suitability.')}</b> {T('Za nobenega kandidata ni T_M = T. Pri vseh ostajajo obvezni atomi brez dokaza. Pri vseh sta neznana npr. izobrazba (<code>a50</code>) in „enterprise-scale AI v produkciji“ (<code>a47</code>). Sklep „kandidat X ustreza“ zato <b>ne sledi</b>.', 'No candidate has T_M = T. Every candidate still has mandatory atoms without evidence; for all of them, e.g., education (<code>a50</code>) and “enterprise-scale AI in production” (<code>a47</code>) are unknown. The conclusion “candidate X is suitable” therefore <b>does not follow</b>.')}</li>
<li><b>{T('Vrstni red', 'Ranking')} ({mode0}, P3):</b> {rank0}.</li>
<li><b>{T('Način', 'Mode')} {mode1}:</b> {exc} {excl1_txt}; {T('vrstni red', 'ranking')}: {rank1}.</li>
<li><b>{T('Pogojnost.', 'Conditionality.')}</b> {T(f'Kdo je prednostni kandidat, je odvisno od pravila {E(", ".join(d["pravilo"] for d in decisive))} (glej 5). Obe izbiri sta logično veljavni vsaka v svojem sistemu predpostavk.', f'Who the priority candidate is depends on rule {E(", ".join(d["pravilo"] for d in decisive))} (see 5). Both selections are logically valid, each within its own set of assumptions.')}</li>
</ol></div>

<h2 id="{P}s3">3 · {T('Kaj rezultat TREE dejansko dokazuje', 'What TREE’s result actually proves')}</h2>
<div class="card"><ul>
<li>{T(f'Za vsako od {ver["dokazov"]} kombinacij (vozlišče × kandidat × način) je izvirni pogon propMinimization (parser + DNF + primarni implikanti) ugotovil protislovje oz. zadovoljivost ustrezne formule. Ujemanje z neodvisnim Python/Kleene izračunom', f'For each of the {ver["dokazov"]} combinations (node × candidate × mode) the original propMinimization engine (parser + DNF + prime implicants) determined the contradiction or satisfiability of the corresponding formula. Agreement with an independent Python/Kleene computation')}: <b>{ver['ujemanje']}/{ver['dokazov']}</b>.</li>
<li>{T('Dokazano je samo to: <i>če</i> imajo propozicije navedene vrednosti, <i>potem</i> je pravilo R v tem vozlišču nujno resnično (T), nujno neresnično (F) ali neodločeno (U).', 'Only this is proven: <i>if</i> the propositions have the stated values, <i>then</i> rule R at that node is necessarily true (T), necessarily false (F) or undetermined (U).')}</li>
<li>{T(f'Izločitev {excl_txt} je veljavna posledica v načinu {mode0}: ne glede na vse neznane propozicije koren T_M ne more biti resničen.', f'The exclusion of {excl_txt} is a valid consequence in mode {mode0}: whatever the unknown propositions are, the root T_M cannot be true.')}</li>
<li>{T('Minimalne oblike (primarni implikanti) pokažejo najmanjše zadostne kombinacije. Ker so skoraj vse obvezne postavke povezane z ⋀, zahteve skoraj ne omogočajo nadomestitve (izjemi sta Python ⋁ Java in Bachelor ⋁ Master).', 'Minimal forms (prime implicants) show the smallest sufficient combinations. Because almost all mandatory items are joined by ⋀, the requirements allow almost no substitution (the exceptions are Python ⋁ Java and Bachelor ⋁ Master).')}</li>
</ul></div>

<h2 id="{P}s4">4 · {T('Česa rezultat izrecno NE dokazuje', 'What it explicitly does NOT prove')}</h2>
<div class="card"><ul>
<li>{T('Ne dokazuje, da so trditve v prošnjah <b>resnične</b>. Prošnje so samoizjave; nobena ni preverjena z dokazili (diplome, reference, preizkus).', 'It does not prove the claims in the applications are <b>true</b>. Applications are self-statements; none is verified by evidence (diplomas, references, tests).')}</li>
<li>{T('Ne dokazuje, da je <b>interpretacija</b> citata pravilna. Preslikavo „citat → propozicija → raven“ je naredil jezikovni model po slovarju <code>cues_sl.json</code>. TREE je ne vidi in je ne preverja.', 'It does not prove the <b>interpretation</b> of a quote is correct. The mapping “quote → proposition → level” was made by a language model using the lexicon <code>cues_sl.json</code>; TREE neither sees nor checks it.')}</li>
<li>{T(f'Ne dokazuje, da je {E(names[top0])} (ali {E(names.get(top1, "—"))}) <b>primeren</b> ali najboljši kandidat. Rang P3 je štetje, ne ocena. Pravilo štetja ni izpeljano iz oglasa.', f'It does not prove that {E(names[top0])} (or {E(names.get(top1, "—"))}) is <b>suitable</b> or the best candidate. The P3 ranking is a count, not an assessment, and the counting rule is not derived from the ad.')}</li>
<li>{T('Ne dokazuje, da izločeni kandidati <b>ne znajo</b> česa. U pomeni le, da prošnja tega ne navaja. Nižja navedena raven je spodnja meja, ne zgornja.', 'It does not prove that candidates <b>lack</b> a skill. U only means the application does not state it; a lower stated level is a lower bound, not an upper bound.')}</li>
<li>{T('Ne ocenjuje stališč in osebnosti (poslušnost, kritičnost do MVP, samozavest). Oglas jih ne zahteva kot propozicije, zato so izpuščene (glej kartice kandidatov).', 'It does not assess attitudes or personality (obedience, criticism of MVPs, self-confidence). The ad does not require them as propositions, so they are left out (see the candidate cards).')}</li>
<li>{T('Ne upošteva ničesar zunaj besedil: CV, razgovor, reference, delovno dovoljenje, lokacija, plača.', 'It considers nothing outside the texts: CV, interview, references, work permit, location, salary.')}</li>
</ul></div>

<h2 id="{P}s5">5 · {T('Predpostavke, manjkajoči sklepi in omejitve', 'Assumptions, missing inferences and limitations')}</h2>
<div class="card">
<h3>{T('Predpostavke', 'Assumptions')}</h3>
<ol class="small">
<li>{T('Klasifikacija oglasa (obveznost, raven, ⋀/⋁) je izpeljana po pravilih v <code>cues.json</code>. Označene dvoumnosti oglasa:', 'The classification of the ad (obligation, level, ⋀/⋁) follows the rules in <code>cues.json</code>. Flagged ambiguities in the ad:')}<ul>{amb_rows}</ul></li>
<li>{T('Lestvica 1–4 in slovar signalov (<code>cues_sl.json</code>): npr. „odlično obvladam“ = 4, „znanje obsega“ = 2. Enaka besedila bi drug ocenjevalec lahko ocenil drugače.', 'The 1–4 scale and the cue lexicon (<code>cues_sl.json</code>): e.g. „odlično obvladam“ (“excellent command of”) = 4, „znanje obsega“ (“knowledge covers”) = 2. Another assessor could grade the same texts differently.')}</li>
<li>{T('Navedena raven je <b>spodnja meja</b>: nižja raven od zahtevane da U, ne F. F nastane samo iz izrecne negacije ali natančnega števila let.', 'A stated level is a <b>lower bound</b>: a level below the requirement gives U, not F. F arises only from an explicit negation or an exact number of years.')}</li>
<li>{T(f'Trivrednostna logika (Kleene). Formule so monotone in vsaka črka nastopa enkrat, zato se Kleene ujema z D/O-testom (preverjeno {ver["ujemanje"]}/{ver["dokazov"]}).', f'Three-valued (Kleene) logic. The formulas are monotone and each letter occurs once, so Kleene agrees with the D/O test (verified {ver["ujemanje"]}/{ver["dokazov"]}).')}</li>
<li>{T('Politika izbire P1–P3 (spodaj) ni del oglasa in jo mora odobriti naročnik.', 'The selection policy P1–P3 (below) is not part of the ad and must be approved by the hiring party.')}</li>
</ol>
<details><summary>{T('Politika izbire', 'Selection policy')}</summary><ul class="small">{policy_items}</ul></details>
<h3>{T('Občutljivost na premostitvena pravila', 'Sensitivity to bridge rules')}</h3>
<p class="small">{T('Vsako pravilo posebej je dodano strogemu načinu (S+Bi) in odvzeto premostitvenemu (B−Bi).', 'Each rule is individually added to strict mode (S+Bi) and removed from bridge mode (B−Bi).')}</p>
<div class="scroll"><table><thead><tr><th>{T('pravilo', 'rule')}</th><th>{T('S + pravilo → izbran', 'S + rule → selected')}</th><th>{T('B − pravilo → izbran', 'B − rule → selected')}</th></tr></thead><tbody>{sens_rows}</tbody></table></div>
<h3>{T('Manjkajoči sklepi', 'Missing inferences')}</h3>
<p class="small">{T('Za vsakega kandidata so obvezni atomi brez dokaza našteti na njegovi kartici. Za T_M = T bi moral vsak od njih postati T. Najpogostejše vrzeli pri vseh so izobrazba (<code>a48–a50</code>), produkcija v podjetniškem merilu (<code>a47</code>), Git/testiranje/pregledi kode (<code>a21–a24</code>) in OpenShift (<code>a34</code>).', 'The mandatory atoms without evidence are listed on each candidate card; for T_M = T every one of them would have to become T. The most common gaps for everyone are education (<code>a48–a50</code>), enterprise-scale production (<code>a47</code>), Git/testing/code reviews (<code>a21–a24</code>) and OpenShift (<code>a34</code>).')}</p>
<h3>{T('Omejitve', 'Limitations')}</h3>
<ul class="small">
<li>{T('Dejstva je izluščil jezikovni model', 'The facts were extracted by a language model')} ({E(fo.get('izluscil'))}). {T('Mehansko je preverjeno le, da je vsak citat dobeseden.', 'Only the verbatim presence of each quote is checked mechanically.')}</li>
<li>{T('Pregledovalnik sprejme največ 4 spremenljivke, zato je drevo razdeljeno na 19 formul. Dokaz korena je veriga dokazov, ne ena formula.', 'The viewer accepts at most 4 variables, so the tree is split into 19 formulas. The proof of the root is a chain of proofs, not a single formula.')}</li>
{engine_notes}
<li>{T(f'Pogon je bil zagnan v oblaku ({E(meta["java"])}). Na računalniku z Java 11 se ga ne da prevesti.', f'The engine was run in a cloud sandbox ({E(meta["java"])}); it cannot be compiled on a machine with Java 11.')}</li>
<li>{T('Odločitev o zaposlitvi, ki bi temeljila izključno na avtomatizirani obdelavi, bi verjetno sprožila pravila o avtomatiziranem odločanju (npr. čl. 22 GDPR). Zato je nujen človeški pregled.', 'A hiring decision based solely on automated processing would likely trigger rules on automated decision-making (e.g. GDPR Art. 22); human review is therefore required.')}</li>
</ul></div>

<h2 id="{P}s6">6 · {T('Minimalni pregledljivi zapis', 'Minimum inspectable record for an independent authority')}</h2>
<div class="card">
<p>{T('Neodvisni presojevalec mora imeti: (1) oba izvirna PDF-ja, (2) pravila klasifikacije in slovar, (3) seznam dejstev z dobesednimi citati in vrsto E/I, (4) premostitvena pravila in politiko, (5) točne vhode in izhode pogona TREE, (6) programe z zgostitvami, da lahko postopek ponovi, in (7) polja za podpise ljudi, ki potrdijo dejstva, pravila in politiko. Vse to je v <code>out/zapis_odlocitve.json</code>. Pečat SHA-256 zapisa zazna vsako spremembo, ni pa elektronski podpis.',
   'An independent reviewer needs: (1) both original PDFs, (2) the classification rules and lexicon, (3) the list of facts with verbatim quotes and type E/I, (4) the bridge rules and policy, (5) the exact inputs and outputs of the TREE engine, (6) the programs with hashes so the procedure can be repeated, and (7) signature fields for the people who confirm facts, rules and policy. All of this is in <code>out/zapis_odlocitve.json</code>. The SHA-256 seal of the record detects any change; it is not an electronic signature.')}</p>
<p><b>{T('Pečat', 'Seal')}:</b> <code class="hash">{record['pecat_sha256']}</code></p>
<p><button class="dl">{T('Prenesi zapis (JSON)', 'Download record (JSON)')}</button></p>
{glossary}
<details><summary>{T('Zgostitve virov in programov (SHA-256)', 'Hashes of sources and programs (SHA-256)')}</summary><div class="scroll"><table><tbody>{hash_rows}
<tr><td><code>{E(meta['zip'])}</code></td><td><code class="hash">{E(meta['zip_sha256'])}</code></td></tr></tbody></table></div></details>
<details><summary>{T('Ponovitev postopka', 'Reproducing the procedure')}</summary><pre class="small" style="white-space:pre-wrap"><code>python3 run_proof.py   # {T('kandidati → dejstva → odločitev → (TREE, če je na voljo JDK 15+) → poročilo', 'candidates → facts → decision → (TREE, if JDK 15+ is available) → report')}
# {T('ročno, s kopijo mape Tree in JDK 15+:', 'manually, with a copy of the Tree folder and JDK 15+:')}
cp Klasifikacija/verify/HarnessProof.java Tree/propMinimization/
javac -encoding UTF-8 -d cls Tree/common/*.java Tree/propositional/*.java Tree/propMinimization/*.java
java -Djava.awt.headless=true -cp cls propMinimization.HarnessProof out/tree_inputs.tsv out/tree_outputs.tsv
python3 verify_engine.py &amp;&amp; python3 report.py</code></pre></details>
<p class="small muted">{T('Meja dopustnosti: zapis je zanesljiv glede na to, kaj je bilo izračunano iz česa (sledljivost in ponovljivost). Resničnosti dejstev ne jamči. Dokler podpisna polja niso izpolnjena, gre za delovni osnutek.', 'Admissibility boundary: the record is reliable as to what was computed from what (traceability and reproducibility). It does not vouch for the truth of the facts. Until the signature fields are filled in, it is a working draft.')}</p>
</div>

<h2 id="{P}kand">{T('Kandidati', 'Candidates')}</h2>
{''.join(cand_card(k) for k in names)}
"""

    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Application Classification</title>
<style>
:root{{--bg:#f7f7f5;--card:#fff;--ink:#1d1d1b;--muted:#6b6b66;--line:#e3e2dc;--acc:#2f5d8a;
--t:#1f7a4a;--tbg:#e3f3ea;--f:#a8322d;--fbg:#f8e4e2;--u:#8a6a12;--ubg:#f6eed6;--code:#f1f0ec}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--muted:#9d9c95;--line:#33332f;--acc:#8db4dc;
--t:#7fd3a3;--tbg:#17352a;--f:#f0948e;--fbg:#3d1f1d;--u:#e2c275;--ubg:#3a311a;--code:#2a2a27}}}}
:root[data-theme="dark"]{{--bg:#161615;--card:#1f1f1d;--ink:#ecebe6;--muted:#9d9c95;--line:#33332f;--acc:#8db4dc;
--t:#7fd3a3;--tbg:#17352a;--f:#f0948e;--fbg:#3d1f1d;--u:#e2c275;--ubg:#3a311a;--code:#2a2a27}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
main{{max-width:1120px;margin:0 auto;padding:24px 16px 64px}}
h1{{font-size:1.6rem;margin:0 0 4px}} h2{{font-size:1.2rem;margin:36px 0 10px;padding-top:8px;border-top:1px solid var(--line)}}
h3{{margin:0;font-size:1.05rem}} .card h3{{margin:14px 0 4px}}
.muted{{color:var(--muted);font-size:.85em}} .small{{font-size:.88em}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}}
.hero{{border-left:5px solid var(--acc)}}
.hero .big{{font-size:1.25rem;font-weight:600;margin:4px 0 8px}}
.grid3{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:10px 0}}
.lbl{{font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin-bottom:3px}}
.chip{{display:inline-block;padding:1px 9px;border-radius:999px;font-size:.82em;font-weight:600;white-space:nowrap}}
.chip.t{{background:var(--tbg);color:var(--t)}} .chip.f{{background:var(--fbg);color:var(--f)}} .chip.u{{background:var(--ubg);color:var(--u)}}
.pill{{font-size:.8rem;border:1px solid var(--line);border-radius:999px;padding:2px 10px;color:var(--muted)}}
.cand header{{display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap}}
table{{border-collapse:collapse;width:100%;font-size:.88rem;margin:8px 0}}
th,td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}
th{{font-weight:600;color:var(--muted);font-size:.8rem}}
.scroll{{overflow-x:auto}} .q{{font-style:italic}}
.gloss{{color:var(--muted);font-size:.85em;margin-top:2px}}
code{{background:var(--code);padding:1px 5px;border-radius:5px;font-size:.88em;word-break:break-word}}
code.hash{{font-size:.75em}} td:first-child code{{white-space:nowrap}}
details{{margin:8px 0}} summary{{cursor:pointer;font-weight:600;color:var(--acc)}}
ul,ol{{padding-left:20px}} li{{margin:3px 0}}
button{{font:inherit;padding:7px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}}
.langsw{{display:flex;gap:4px;justify-content:flex-end;margin-bottom:8px}}
.langsw button{{padding:3px 10px;font-size:.82rem}} .langsw button[aria-pressed="true"]{{background:var(--acc);color:var(--card);border-color:var(--acc)}}
nav.toc a{{color:var(--acc);text-decoration:none;margin-right:14px;font-size:.9rem;display:inline-block}}
.lb[hidden]{{display:none}}
@media print{{details{{display:block}} details>*{{display:block}} button,nav,.langsw{{display:none}}}}
</style></head><body><main>
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
    a.href=URL.createObjectURL(bl);a.download='zapis_odlocitve.json';document.body.appendChild(a);a.click();a.remove();
  }});}});
}})();
</script>
</main></body></html>"""
    (OUT / "report.html").write_text(page, encoding="utf-8")
    # stara pot ostane kot preusmeritev (ne brišemo datotek v mapi uporabnika)
    (OUT / "porocilo.html").write_text(
        '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=report.html?lang=sl">'
        '<title>Poročilo</title><a href="report.html?lang=sl">Poročilo je v report.html</a>', encoding="utf-8")
    print(f"-> out/report.html ({len(page) // 1024} KB, EN + SL), out/zapis_odlocitve.json, seal {record['pecat_sha256'][:16]}")


if __name__ == "__main__":
    main()
