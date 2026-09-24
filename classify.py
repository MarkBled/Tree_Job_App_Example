#!/usr/bin/env python3
"""2. korak: postavke -> klavzule -> atomi z oceno (out/classified.json).

Vsak atom nosi:
  obveznost  M (obvezno) / N (dodatno) / P (pričakovano – naloga)
  raven      1 poznavanje, 2 delovno, 3 praktično, 4 ekspert (None = besedilo ne določa)
  prag_let   spodnji prag let izkušenj (če gre za leta)
  signal     beseda(e) v besedilu, ki so določile oceno  -> sledljivost
Vse odločitve izhajajo iz cues.json.
"""
import json, re
from pathlib import Path
import sys

if hasattr(sys.stdout, "reconfigure"):  # Windows konzola: izpis znakov ≥ ⋀ ✗ brez napake
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
CUES = json.loads((BASE / "cues.json").read_text(encoding="utf-8"))
NOUNS = CUES["samostalniki_raven"]
PREP_AFTER_CUE = r"^(?:in|of|with|on|to|for|designing|building|focused on|delivering)\b\s*"


class AtomCounter:
    n = 0

    @classmethod
    def next(cls):
        cls.n += 1
        return f"a{cls.n:02d}"


# ---------- pomožne funkcije za besedilo ----------

def protect_parens(s):
    """Vejice in vezniki znotraj oklepajev se ne smejo upoštevati pri deljenju."""
    out, depth = [], 0
    for ch in s:
        depth += ch == "("
        depth -= ch == ")"
        out.append("\x00" if (ch == "," and depth > 0) else ch)
    return "".join(out)


def unprotect(s):
    return s.replace("\x00", ",")


def strip_parens(s):
    return re.sub(r"\s*\([^)]*\)", "", s).strip()


def clean_label(s):
    s = unprotect(s).strip(" .,;")
    s = re.sub(r"^(?:a|an|the)\s+", "", s, flags=re.I)
    return s


def extract_examples(clause):
    """Odstrani primere ('e.g.', 'such as') in jih vrne ločeno."""
    examples = []

    def paren_eg(m):
        examples.extend(x.strip() for x in m.group(1).split(","))
        return ""

    clause = re.sub(r"\s*\(\s*e\.g\.,?\s*([^)]*)\)", paren_eg, clause)
    m = re.search(r"\s+such as\s+(.*)$", clause)
    if m:
        items = re.split(r",\s*(?:and\s+|or\s+)?|\s+and\s+|\s+or\s+", m.group(1).rstrip("."))
        examples.extend(x.strip() for x in items if x.strip())
        clause = clause[: m.start()]
    return clause.strip(), [e for e in examples if e]


def split_clauses(sentence):
    parts = [sentence]
    for sep in CUES["locila_klavzul"]:
        parts = [p for x in parts for p in x.split(sep)]
    out = []
    for p in parts:
        stack = [p.strip()]
        for conn in CUES["vezniki_klavzul_and"]:
            nxt = []
            for x in stack:
                if conn in x:
                    left, right = x.split(conn, 1)
                    tail = conn.strip()
                    for w in ("with the ", "with a ", "and "):
                        if tail.startswith(w):
                            tail = tail[len(w):]
                    nxt += [left, f"{tail} {right}"]
                else:
                    nxt.append(x)
            stack = nxt
        out += [s.strip(" .") for s in stack if s.strip(" .")]
    return out


def level_of(clause):
    """Raven iz samostalnika + modifikatorjev pred njim."""
    words = re.findall(r"[A-Za-z][A-Za-z\-']*", clause.lower())
    for i, w in enumerate(words):
        if w in NOUNS or (w.endswith("s") and w[:-1] in NOUNS and w[:-1] != "year"):
            key = w if w in NOUNS else w[:-1]
            base = NOUNS[key]
            if base == 0:
                return None, [key], i
            mods = words[max(0, i - 3):i]
            lvl, sig = base, [key]
            for m in mods:
                if m in CUES["modifikatorji_nastavi"]:
                    lvl = CUES["modifikatorji_nastavi"][m]
                    sig.insert(0, m)
            for m in mods:
                if m in CUES["modifikatorji_plus"]:
                    lvl = min(4, lvl + 1)
                    sig.insert(0, m)
            return lvl, sig, i
    return None, [], None


def object_after_cue(clause, cue_word):
    """Besedilo za ključnim samostalnikom (predmet zahteve)."""
    m = re.search(rf"\b{re.escape(cue_word)}s?\b", clause, flags=re.I)
    if not m:
        return clause
    rest = clause[m.end():].strip()
    rest = re.sub(PREP_AFTER_CUE, "", rest, flags=re.I)
    return rest or clause


def distribute_head(elems):
    """'API-first, microservices-based and event-driven architectures' -> skupni samostalnik vsem."""
    bare = [strip_parens(unprotect(e)).split() for e in elems]
    if len(elems) >= 2 and all(len(b) == 1 and "-" in b[0] for b in bare[:-1]) and len(bare[-1]) >= 2:
        head = bare[-1][-1]
        return [f"{e} {head}" for e in elems[:-1]] + [elems[-1]]
    return elems


def split_list(obj):
    """Vrne (op, [elementi]); upošteva and/or, or, and, vejice; oklepaji so zaščiteni."""
    p = protect_parens(obj)
    amb = []
    if "and/or" in p:
        amb.append("and_or")
        parts = re.split(r",?\s*and/or\s+|,\s*", p)
        op = "OR"
    elif re.search(r"(?:^|\s|,)or\s", p):
        parts = re.split(r",?\s+or\s+|,\s*", p)
        op = "OR"
    elif "," in p:
        parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", p)
        op = "AND"
    elif " and " in p:
        l, r = p.split(" and ", 1)
        # dvočlenski 'X and Y' razdelimo le, če sta oba dela večbesedna (sicer je to ena sestavljenka)
        if len(strip_parens(l).split()) >= 2 and len(strip_parens(r).split()) >= 2:
            parts, op = [l, r], "AND"
        else:
            parts, op = [p], "ATOM"
    else:
        parts, op = [p], "ATOM"
    parts = [x for x in (clean_label(x) for x in parts) if x]
    if len(parts) == 1:
        op = "ATOM"
    if any("(" in x for x in parts):
        amb.append("oklepaj_brez_eg")
    return op, distribute_head(parts), amb


def atom(label, obligation, level, signal, **extra):
    a = {"op": "ATOM", "id": AtomCounter.next(), "oznaka": label, "obveznost": obligation,
         "raven": level, "signal": signal}
    a.update({k: v for k, v in extra.items() if v not in (None, [], "")})
    return a


def node(op, label, children, **extra):
    if len(children) == 1 and not extra:
        return children[0]
    n = {"op": op, "oznaka": label, "otroci": children}
    n.update(extra)
    return n


# ---------- klasifikacija klavzule ----------

def classify_clause(clause, obligation):
    clause, examples = extract_examples(clause)
    amb = []

    # 1) leta izkušenj
    ym = re.search(r"(\d+)\s*[–-]\s*(\d+)\s*years|(\d+)\+?\s*years", clause)
    if ym:
        lo = int(ym.group(1) or ym.group(3))
        if ym.group(2):
            amb.append("range_years")
        obj = re.sub(r"^(?:of|in|focused on|with)\s+", "", clause[ym.end():].strip(), flags=re.I)
        op, elems, a2 = split_list(obj)
        amb += a2
        sig = [ym.group(0)]
        kids = [atom(f"≥{lo} let: {e}", obligation, None, sig, prag_let=lo) for e in elems]
        if len(kids) == 1:
            if examples:
                kids[0]["primeri"] = examples
            return kids[0], amb
        return node(op, clause, kids, primeri=examples), amb

    lvl, sig, _ = level_of(clause)

    # 2) diploma: "<stopnje> degree in <področja>"
    dm = re.search(r"^(.*?)\s+degree\s+in\s+(.*)$", clause)
    if dm:
        op1, levels, _ = split_list(dm.group(1))
        op2, fields, _ = split_list(dm.group(2))
        amb.append("degree_implication")
        k1 = node(op1 if op1 != "ATOM" else "AND", "stopnja izobrazbe",
                  [atom(f"diploma: {x}", obligation, None, ["degree"]) for x in levels])
        k2 = atom("področje: " + " / ".join(fields), obligation, None, ["degree in"], alternative=fields) \
            if op2 == "OR" else atom("področje: " + fields[0], obligation, None, ["degree in"])
        return node("AND", clause, [k1, k2], primeri=examples), amb

    # 3) splošna klavzula: raven + predmet (+ 'including' komponente)
    cue = sig[-1] if sig else None
    obj = object_after_cue(clause, cue) if cue else clause
    comps = []
    for kw in CUES["komponente_uvod"]:
        m = re.search(rf",?\s*\b{kw}\b\s+", obj)
        if m:
            comps_txt = obj[m.end():]
            obj = obj[: m.start()]
            _, comps, a3 = split_list(comps_txt)
            amb += a3 + ["including"]
    op, elems, a2 = split_list(obj)
    amb += a2
    if comps:
        if len(elems) == 1:  # krovni pojem + komponente
            head = elems[0]
            kids = [atom(c, obligation, lvl, sig, krovni_pojem=head) for c in comps]
            return node("AND", head, kids, primeri=examples, raven=lvl, signal=sig), amb
        elems = elems + comps
        op = "AND" if op == "ATOM" else op
    kids = [atom(e, obligation, lvl, sig) for e in elems]
    if len(kids) == 1:
        if examples:
            kids[0]["primeri"] = examples
        return kids[0], amb
    return node(op, clean_label(obj), kids, primeri=examples, raven=lvl, signal=sig), amb


def classify_item(item):
    out = {k: item[k] for k in ("id", "oznaka", "razdelek")}
    out["obveznost"] = item["obveznost_oznake"]
    out["klavzule"] = []
    if item["razdelek"] == "K":
        out["opomba"] = "kontekst – ni v logiki"
        return out
    if item["obveznost_oznake"] == "P":
        # naloga = en atom; besedilo ne določa ravni
        text, examples = extract_examples(item["besedilo"])
        a = atom(item["oznaka"], "P", None, [], besedilo=item["besedilo"], primeri=examples)
        out["klavzule"].append({"tekst": item["besedilo"], "obveznost": "P", "vozlisce": a, "dvoumnosti": []})
        return out
    for sent in item["stavki"]:
        obl = "N" if any(f in sent.lower() for f in CUES["fraze_dodatno"]) else item["obveznost_oznake"]
        for cl in split_clauses(sent):
            for f in CUES["fraze_dodatno"]:
                cl = re.sub(rf"\s+{re.escape(f)}\s*$", "", cl, flags=re.I)
            n, amb = classify_clause(cl, obl)
            if obl == "N" and n.get("raven") is None and n["op"] == "ATOM":
                lvl, sig, _ = level_of(cl)
                n["raven"], n["signal"] = lvl, sig
            out["klavzule"].append({"tekst": cl, "obveznost": obl, "vozlisce": n,
                                    "dvoumnosti": [{"koda": a, "razlaga": CUES["dvoumnosti"][a]} for a in dict.fromkeys(amb)]})
    return out


def main():
    items = json.loads((BASE / "out" / "items.json").read_text(encoding="utf-8"))
    res = {"vir": items.get("vir"), "meta": items["meta"],
           "lestvica": {"1": "poznavanje", "2": "delovno", "3": "praktično", "4": "ekspert"},
           "postavke": [classify_item(i) for i in items["postavke"]]}
    (BASE / "out" / "classified.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{AtomCounter.n} atomov -> out/classified.json")


if __name__ == "__main__":
    main()
