# Klasifikacija – requirements → logic trees → TREE proofs

> Slovenska različica: [README.sl.md](README.sl.md)

A learning experiment built on the **TreeOfKnowledge** (TREE) symbolic logic engine by JAnica Tesla Zrinski (folder `../Tree`). The experiment has two parts:

1. **Classification.** A job ad (PDF or TXT) is split into items. Each item is graded **from the text alone** and turned into a hierarchy of logic formulas that the TREE viewer can read.
2. **Proof.** Five applications are checked against that hierarchy. The TREE engine proves or refutes each node, and the result is written up as an offline bilingual report together with a minimal inspectable record.

The applications are **fictional**. The job ad (Citi Job Req 26984690, Senior AI Engineer) was publicly posted. This is **not** a production tool and makes no hiring decisions.

---

## Part 1 – Classifying the job ad

### Run

```bash
python3 run_all.py                              # default: data/JobReqId26984690.pdf
python3 run_all.py path/to/another_ad.pdf
python3 evaluate.py --predloga                  # empty candidate profile -> out/profil_predloga.json
python3 evaluate.py data/primer_kandidat.json   # evaluate a (fictional) test profile
```

Requirements: Python 3.8+ and `pdftotext` (poppler). No third-party Python packages are needed.

### Pipeline

| step | script | output | what it does |
|---|---|---|---|
| 1 | `segment.py` | `out/items.json` | splits the text into `Label: …` items and sentences, and assigns each a section (K/P/M) |
| 2 | `classify.py` | `out/classified.json` | clauses → atoms with obligation, level, year threshold, cue word and examples |
| 3 | `build_tree.py` | `out/tree.json` | builds three trees (T_M, T_N, T_P) and splits any node with more than 4 children |
| 4 | `export_tree.py` | `out/formule.md`, `out/formule.json` | writes formulas A–D (propMinimization) and P–R (propositional), with a legend and the minimal DNF |
| 5 | `evaluate.py` | `out/ocena.json` | evaluates a candidate profile and lists only the atoms that actually block a pass |

All classification rules live in **`cues.json`**, so you can change them without touching the code.

### Grading

- **Obligation:**
  - M = mandatory (Qualifications section)
  - N = nice to have (“is a plus”, “Nice to Have”)
  - P = expected responsibility (Key Responsibilities section)
  - K = context, not used in the logic
- **Level:** 1 familiarity · 2 working · 3 practical · 4 expert.
  - The noun sets the base: familiarity = 1; understanding / knowledge = 2; experience / proficiency = 3.
  - `working` sets the level to 2, and `hands-on` / `practical` set it to 3.
  - `strong`, `solid` and `demonstrated` each add 1.
- **Logic:**
  - `and/or` and `or` → ⋁; a plain list → ⋀.
  - `e.g.` and `such as` introduce examples, which do not become atoms.
  - `including` introduces constituent parts (⋀).
- **Truth of an atom:** an atom is true when the candidate has at least the required level (or at least the required years).

### Trees

- **T_M – mandatory requirements:** a gate (⋀ of all mandatory items).
- **T_N – nice to have:** a score. The viewer shows it as ⋁, meaning “at least one plus”.
- **T_P – responsibilities:** a score.

The viewer accepts at most 4 variables (A–D). The hierarchy is therefore a **tree of trees**: a letter in a formula can stand for the result of another node `nXX` (see the legend in `formule.md`). The parser reads left to right without operator precedence, so mixed sub-expressions are always put in parentheses.

### Flagged ambiguities (decisions)

- The range “6–10 years” → threshold **≥ 6**. The upper bound does not exclude anyone.
- “Python and/or Java” → inclusive **⋁**.
- A list in parentheses without “e.g.” (TensorFlow, PyTorch …) → a specification of the concept, not separate obligations.
- “including” → constituent parts (⋀).
- A Master's includes a Bachelor's. The formula keeps `A⋁B`, and the minimal form makes this visible.

---

## Part 2 – Applications → selection → offline report

```bash
python3 run_proof.py        # → out/report.html (offline, English by default + Slovenian) + out/zapis_odlocitve.json
```

| step | script | output | what it does |
|---|---|---|---|
| 1 | `candidates.py` | `out/kandidati.json` | splits `data/Prosnje_kandidatov.pdf` into candidates, with page numbers |
| 2 | `facts.py` | `out/dejstva_ocenjena.json` | checks that every quote in `data/dejstva.json` appears **verbatim**, computes the level from the cue word (`cues_sl.json`) and gives each atom the value T, F or U |
| 3 | `decide.py` | `out/odlocitev.json`, `out/tree_inputs.tsv` | evaluates the tree with Kleene logic, applies the selection policy P1–P3, tests sensitivity to bridge rules B1–B11 and writes the D/O inputs for TREE |
| 4 | `verify/HarnessProof.java` | `out/tree_outputs.tsv` | runs the original propMinimization engine on every input (requires JDK 15+) |
| 5 | `verify_engine.py` | `out/odlocitev.json` | compares TREE with the Python result; they must agree 100 % |
| 6 | `report.py` | `out/report.html`, `out/zapis_odlocitve.json` | builds the bilingual report (English by default; Slovenian via the switch or `?lang=sl`) with 6 sections, plus the record with hashes and a seal. Translations live in `i18n_en.json`. Quotes stay in the original Slovenian because they are the evidence; the English glosses are unofficial |

**Three-valued logic:** T = proven · F = refuted · U = not proven. A stated level is a lower bound, so a lower level gives U, not F.

**Modes:**

- **S (strict)** uses only explicit facts (type E). This is the primary mode, set in `cues_sl.json → politika_izbire.privzeti_nacin`.
- **B (bridge)** uses E facts plus bridge rules (type I, B1–B11).

**TREE inputs:**

- **D-input** `(K)⋀¬(R)`: a contradiction ⇒ the node is **T**.
- **O-input** `(K)⋀(R)`: a contradiction ⇒ the node is **F**.

Both are contradiction checks because the tautology path in propMinimization crashes: it raises a ClassCastException, caused by a string mismatch between `tautologija` and `tautology`.

The facts in `data/dejstva.json` were extracted by a language model. A human must confirm them before any real use. `facts.py` refuses to run if `out/tree.json` has different propositions from the ones the facts were written for (it checks a fingerprint).

### Result (strict mode)

- **Nobody is proven suitable:** T_M = T for 0 of 5 candidates.
- **One candidate is provably excluded:** Tjaša, because she states 4 years of experience and the ad requires at least 6.
- **Priority for verification:** Liam.
- **The result depends on one bridge rule.** Adding only rule B1 (“no banking experience ⇒ no banking understanding”) changes the selection to Peter.

The report explains:

- what TREE proves and what it does not prove;
- all assumptions and missing inferences;
- the admissibility boundary of the record.

## Verification of the first part

`verify/Harness.java` is a separate test class; the original code is not modified. It parses every formula with the original `propMinimization` parser. The result is in `out/preverjanje_java.txt`: all 19 formulas parse, and the prime implicants match `minimalna_DNF`.

```bash
# from a copy of the Tree folder, JDK 15+ required
cp ../Klasifikacija/verify/Harness.java propMinimization/
javac -encoding UTF-8 -d cls common/*.java propositional/*.java propMinimization/*.java
python3 -c "import json;[print(f['id']+'\t'+f['formula_propMinimization']) for f in json.load(open('../Klasifikacija/out/formule.json'))]" > forms.tsv
java -Djava.awt.headless=true -cp cls propMinimization.Harness forms.tsv
```

## Notes on the TREE engine found during the experiment

- **Tautology crash in propMinimization.** `MinimalneNormalneForme` checks for `"tautology;)!)"`, but `PrimeImplicants` returns `"tautologija;)!)"`. As a result, every tautology raises a ClassCastException in the GUI path.
- **Java version.** The TREE README says Java 8+, but `common/UIStrings.java` uses text blocks, which need Java 15+.

## Credits and licence

The TREE engine and its source are © JAnica Tesla Zrinski (TreeOfKnowledge.eu); see `../Tree/LICENCE.txt`. The files in this folder do not modify the engine. They only produce inputs for it, and the `verify/*.java` harnesses call it from a separate class.

The folder names and most data keys are in Slovenian (e.g. `dejstva` = facts, `zapis` = record, `pecat` = seal). The English view of the report includes a glossary of the record keys.
