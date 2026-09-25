# Klasifikacija zahtev → logična drevesa

Besedilo oglasa (PDF ali TXT) razčleni na postavke, vsako oceni **zgolj na podlagi besedila** in zgradi hierarhijo, ki jo izvozi v formule za pregledovalnik **TreeOfKnowledge** (mapa `../Tree`).

## Zagon

```bash
python3 run_all.py                          # privzeto data/JobReqId26984690.pdf
python3 run_all.py pot/do/drugega_oglasa.pdf
python3 evaluate.py --predloga              # prazen profil kandidata -> out/profil_predloga.json
python3 evaluate.py data/primer_kandidat.json   # ocena (izmišljen testni profil)
```

Potrebno: Python 3.8+, `pdftotext` (poppler). Brez zunanjih knjižnic.

## Cevovod

| korak | skripta | izhod | kaj naredi |
|---|---|---|---|
| 1 | `segment.py` | `out/items.json` | razreže besedilo na postavke `Naziv: …` in stavke; razdelek določi K/P/M |
| 2 | `classify.py` | `out/classified.json` | klavzule → atomi z obveznostjo, ravnijo, pragom let, signalom in primeri |
| 3 | `build_tree.py` | `out/tree.json` | tri drevesa (T_M, T_N, T_P); vozlišča z >4 otroki razdeli |
| 4 | `export_tree.py` | `out/formule.md`, `out/formule.json` | formule A–D (propMinimization) in P–R (propositional), legenda, minimalna DNF |
| 5 | `evaluate.py` | `out/ocena.json` | ovrednoti profil kandidata; izpiše samo atome, ki dejansko blokirajo |

Vsa pravila so v **`cues.json`**, kode ni treba spreminjati.

## Ocene

- **Obveznost:** M obvezno (razdelek Qualifications) · N dodatno („is a plus“, „Nice to Have“) · P pričakovano (Key Responsibilities) · K kontekst (ni v logiki)
- **Raven:** 1 poznavanje · 2 delovno · 3 praktično · 4 ekspert
  Raven = osnova samostalnika (familiarity 1, understanding/knowledge 2, experience/proficiency 3 …), `working` jo nastavi na 2, `hands-on`/`practical` na 3, `strong`/`solid`/`demonstrated` prištejejo 1.
- **Logika:** `and/or` in `or` → ⋁, naštevanje → ⋀, `e.g.`/`such as` → primeri (niso atomi), `including` → sestavni deli (⋀).
- **Atom** je resničen, ko ima kandidat raven ≥ zahtevana (oz. leta ≥ prag).

## Drevesa

- **T_M Obvezne zahteve**: vrata (⋀ vseh obveznih postavk)
- **T_N Dodatno**: točkovanje (v pregledovalniku ⋁ = „vsaj en plus“)
- **T_P Naloge**: točkovanje

Pregledovalnik sprejme največ 4 spremenljivke (A–D), zato je hierarhija **drevo drevesc**: črka v formuli lahko pomeni rezultat drugega vozlišča `nXX` (glej legendo v `formule.md`). Parser bere levo → desno brez prednosti operatorjev, zato so mešani podizrazi vedno v oklepajih.

## Preverjanje

`verify/Harness.java` je ločen testni razred (izvirna koda ostane nespremenjena). Z njim se vse formule parsirajo z izvirnim parserjem `propMinimization`; rezultat je v `out/preverjanje_java.txt` (19/19 parsiranih, primarni implikanti se ujemajo z `minimalna_DNF`).

```bash
# iz kopije mape Tree, potreben JDK (javac)
cp ../Klasifikacija/verify/Harness.java propMinimization/
javac -encoding UTF-8 -d cls common/*.java propositional/*.java propMinimization/*.java
python3 -c "import json;[print(f['id']+'\t'+f['formula_propMinimization']) for f in json.load(open('../Klasifikacija/out/formule.json'))]" > forms.tsv
java -Djava.awt.headless=true -Dstdout.encoding=UTF-8 -cp cls propMinimization.Harness forms.tsv
```

## Označene dvoumnosti (odločitve)

- Razpon „6–10 let“ → prag **≥ 6**; zgornja meja ni izločilna.
- „Python and/or Java“ → vključujoči **⋁**.
- Naštevanje v oklepaju brez „e.g.“ (npr. TensorFlow, PyTorch …) → specifikacija pojma, ne ločene obveznosti.
- „including“ → sestavni deli (⋀).
- Master's vključuje Bachelor's → ostane `A⋁B`; minimalna oblika to pokaže.

---

# Dokazni del: prijave kandidatov → izbira → offline poročilo

```bash
python3 run_proof.py        # → out/report.html (offline, angleščina privzeto + slovenščina) + out/zapis_odlocitve.json
```

| korak | skripta | izhod | kaj naredi |
|---|---|---|---|
| 1 | `candidates.py` | `out/kandidati.json` | razreže `data/Prosnje_kandidatov.pdf` na kandidate (s stranmi) |
| 2 | `facts.py` | `out/dejstva_ocenjena.json` | preveri, da je vsak citat v `data/dejstva.json` **dobeseden**; iz signala (`cues_sl.json`) izračuna raven; vrednost atoma T/F/U |
| 3 | `decide.py` | `out/odlocitev.json`, `out/tree_inputs.tsv` | Kleenejeva evalvacija drevesa, politika P1–P3, občutljivost na pravila B1–B11, D/O-vhodi za TREE |
| 4 | `verify/HarnessProof.java` | `out/tree_outputs.tsv` | izvirni pogon propMinimization na vseh vhodih (zahteva JDK 15+) |
| 5 | `verify_engine.py` | `out/odlocitev.json` | TREE ↔ Python: mora se ujemati 100 % |
| 6 | `report.py` | `out/report.html`, `out/zapis_odlocitve.json` | dvojezično poročilo (EN privzeto, SL s stikalom ali `?lang=sl`) s 6 razdelki + zapis z zgostitvami in pečatom; prevodi so v `i18n_en.json` (citati ostanejo v izvirniku, angleški prevod je neuraden) |

**Trivrednostna logika:** T dokazano · F ovrženo · U ni dokazano. Navedena raven je spodnja meja (nižja → U, ne F).
**Načina:** S = samo izrecna dejstva (E); B = E + premostitvena pravila (I, B1–B11). Primarni je S (`cues_sl.json → politika_izbire.privzeti_nacin`).
**TREE vhodi:** D `(K)⋀¬(R)` protislovje ⇒ T; O `(K)⋀(R)` protislovje ⇒ F. Oba sta testa protislovja, ker pot za tavtologije v propMinimization pade (ClassCastException, neujemanje `tautologija`/`tautology`).

Dejstva (`data/dejstva.json`) je izluščil jezikovni model; pred uporabo jih mora potrditi človek.
