# TREE dependency, reuse boundaries, attribution and verification

> **SYNTHETIC / DEMO ONLY.** This folder is a learning experiment. The job ad is publicly posted (Citi Job Req 26984690); the five applications are **fictional**. Nothing here is a hiring decision, a production integration or a validated TREE integration.

This note responds to §4.5 of *TREE — Preliminary Viability and Success-Probability Assessment* (public working draft v0.1, 27 September 2026). That section asks for four things to be documented before the example is treated as a validated TREE integration:

1. the exact technical dependency;
2. reuse boundaries;
3. attribution;
4. the verification method.

All four are answered below and can be checked against the files in this folder.

---

## 1. Technical dependency

| what | detail |
|---|---|
| TREE version used | Source bundle `AllSourceCode4UPloadToAI-TreeOfKnowledge-1.0.0.zip`, SHA-256 `2062b782edbd4d5697ae53a09c210b481296089ca353ae6fc520c1b49fe3f4d1` |
| TREE package used | **`propMinimization` only**. `common` and `propositional` are compiled alongside it only because `propMinimization` depends on them (e.g. `propositional.DisjunktivnaFormaZaLS`). `firstorder` is not compiled or used. |
| TREE functions called | `StabloFormule.parsiraj()` (parser → AST); `Formula.eliminiramNegacije()` (NNF); `FormulaUNormalnoj.disjunktivnojFormi()` (DNF); `PrimeImplicants.primeImplicants()`; `MinimalneNormalneForme.minimalneNormalneForme()` (minimal forms, only for satisfiable formulas) |
| How TREE is called | Through separate test classes in this folder: `verify/Harness.java` (Part 1) and `verify/HarnessProof.java` (Part 2). They are placed temporarily into a **copy** of `propMinimization` and compiled against the unmodified TREE sources. No TREE file is edited. |
| Runtime used | OpenJDK 21.0.10, headless (`-Djava.awt.headless=true`); GUI panels are replaced by empty Swing objects so the calculator logic can run without a window |
| What TREE decides | For every node formula **R** and the known literals **K** of a candidate, TREE decides whether two formulas are contradictions (empty DNF): **D-input** `(K)⋀¬(R)` and **O-input** `(K)⋀(R)` (see §4) |
| What TREE does *not* decide | Parsing of the PDF files, classification of the job ad, extraction of facts from applications, the grading scale, the selection policy and the report are all done by the Python scripts in this folder. They are **not** TREE functionality. |
| Independent second core | `z3_core.py` evaluates the same propositions with the Z3 SMT solver (5.1.0). It does not use TREE at all and serves only as a cross-check. |

In one sentence: **TREE is used as a propositional contradiction/minimization engine on formulas of at most 4 variables. Everything else is external to TREE.**

## 2. Reuse boundaries

- **No TREE source code, binaries or the source ZIP are included** in this folder or its repository. To reproduce the TREE step, a user must obtain TREE from its official repository under its own licence.
- The two harness classes (`verify/*.java`) contain no TREE code. They only call public and package-level TREE methods. They must be placed next to the TREE sources at build time; this is documented in `README.md`.
- Files in `out/` that contain TREE output (`out/tree_outputs.tsv`, `out/preverjanje_java.txt`) contain **results** (formula strings, status words, prime implicants), not TREE code.
- TREE was not modified, forked, repackaged or redistributed. The two engine defects we found are **reported** to the author (see `TREE-ISSUE-engine-findings.md`), not patched.
- This work does **not** imply authorship, endorsement or production integration by the TREE author or by any component named in the assessment (OMNIX, Fidacy, SignalLink). None of these components is used here.

## 3. Attribution

- **TREE (TreeOfKnowledge)** © Ana Kovačević (JAnicaTZ), TreeOfKnowledge.eu. Original academic work 2002–2004, PMF Zagreb. Licence: `docs/LICENCE.txt` in the TREE repository.
- **This folder (Klasifikacija):** author Marko, with Claude (Anthropic) as an AI coding and analysis assistant. The facts in `data/dejstva.json` were extracted by the language model and are marked as requiring human confirmation.
- **Z3:** Microsoft Research, MIT licence, used via the `z3-solver` Python package.
- **Job ad:** publicly posted text, used unchanged as input; no affiliation with the employer.

## 4. Verification method

**Three-valued evaluation over a two-valued engine.** TREE is two-valued, but many facts in an application are simply unknown. Each node is therefore evaluated with two contradiction checks:

| check | formula | if TREE reports a contradiction |
|---|---|---|
| D (proof) | `(K)⋀¬(R)` | K ⇒ R holds → node is **T** |
| O (refutation) | `(K)⋀(R)` | K and R are incompatible → node is **F** |
| neither | — | node is **U** (not proven) |

Both checks are contradiction tests. TREE's tautology path could not be used because of a defect (see the issue file).

**Cross-checks performed:**

| check | result |
|---|---|
| All Part 1 formulas parsed completely by the original TREE parser; TREE's prime implicants compared with an independent Python Quine–McCluskey | 19/19 |
| TREE result compared with an independent Python truth-table / Kleene evaluation (5 candidates × 19 nodes × 2 modes) | 190/190 |
| TREE/Kleene values compared with Z3 SMT for every atom and node (5 candidates × 75 values × 2 modes) | 750/750 |
| Same selection in both modes, TREE vs Z3 | ✓ / ✓ |
| Same sensitivity to all 11 bridge rules, TREE vs Z3 | ✓ |
| All 10 SMT-LIB2 exports reloaded from file and re-checked | 10/10 |
| Every quote used as a fact found verbatim in the source PDF (mechanical check) | 77/77 |

**Reproducibility:**

```bash
python3 run_proof.py   # TREE path (needs a TREE source copy and JDK 15+ for the engine step)
python3 run_z3.py      # Z3 path (pip install z3-solver)
```

Every input, program and output is listed with its SHA-256 hash in `out/zapis_odlocitve.json` (TREE) and `out/zapis_z3.json` (Z3). Each record carries a seal: a SHA-256 hash of the whole record, which detects later changes but is not a signature.

**What is *not* verified:**

- whether the applicants' claims are true;
- whether the extraction of facts from Slovenian text is correct (done by a language model);
- whether the grading scale and selection policy are appropriate.

These require human review. The signature fields in both records are intentionally left empty.

## Status relative to the assessment

This example corresponds to **S2 – reproducible demonstration** in the assessment's scale. It is not S3 (integrated bounded prototype) and not a pilot. To become a pilot in the sense of §13 it would still need:

- the expected output and success/failure criteria written down **before** execution;
- a named problem owner;
- a reproduction by a third party from these instructions.

## References

- TREE repository: <https://github.com/JAnicaTZ/TreeOfKnowledge>
- TREE website: <https://TreeOfKnowledge.eu>
- Z3 SMT solver: <https://github.com/Z3Prover/z3>
- Components named in the assessment (**not used here**):
  - SignalLink – <https://github.com/Drewbiee123/Signallink-AI>
  - Fidacy – <https://glama.ai/mcp/servers/lucaslubi/fidacy-mcp>
  - OMNIX Quantum – <https://zenodo.org/records/19375792>
- Related, independent concept of an execution grant: <https://arxiv.org/abs/2609.11596>
