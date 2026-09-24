# Formule za pregledovalnik – JobReqId26984690.pdf

Lestvica ravni: 1 poznavanje · 2 delovno · 3 praktično · 4 ekspert. Atom je resničen, ko ima kandidat vsaj zahtevano raven (oz. prag let).

Vnos: **propMinimization** (A–D) ali **propositional** (P–R, kadar ≤3 spremenljivke). Črka, ki kaže na vozlišče `nXX`, je rezultat formule tega vozlišča.

## n01 · Obvezne zahteve  _(drevo T_M)_

- propMinimization: `A⋀B⋀C`
- propositional: `P⋀Q⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C` · resničnih vrstic 1/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Obvezne zahteve – del 1/3 (`n02`) | glej formulo n02 |  |
| B | Obvezne zahteve – del 2/3 (`n12`) | glej formulo n12 |  |
| C | Obvezne zahteve – del 3/3 (`n16`) | glej formulo n16 |  |

## n22 · Dodatno (nice to have)  _(drevo T_N)_

- propMinimization: `A⋁B⋁C`
- propositional: `P⋁Q⋁R`
- minimalna DNF (najmanjše zadostne kombinacije): `A  ⋁  B  ⋁  C` · resničnih vrstic 7/8
- opomba: točkovanje: ⋁ = vsaj en izpolnjen; štej izpolnjene

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Full-stack experience (`a12`) | raven ≥3 | experience |
| B | data science (statistical modeling, experimentation) (`a39`) | raven ≥3 | experience |
| C | mentoring junior AI engineers (`a40`) | raven ≥1 | interest |

## n23 · Naloge (pričakovano)  _(drevo T_P)_

- propMinimization: `A⋁B`
- propositional: `P⋁Q`
- minimalna DNF (najmanjše zadostne kombinacije): `A  ⋁  B` · resničnih vrstic 3/4
- opomba: točkovanje: ⋁ = vsaj en izpolnjen; štej izpolnjene

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Naloge (pričakovano) – del 1/2 (`n24`) | glej formulo n24 |  |
| B | Naloge (pričakovano) – del 2/2 (`n25`) | glej formulo n25 |  |

## n02 · Obvezne zahteve – del 1/3  _(drevo T_M)_

- propMinimization: `A⋀B⋀C`
- propositional: `P⋀Q⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C` · resničnih vrstic 1/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Programming (`n03`) | glej formulo n03 |  |
| B | AI/ML Expertise (`n05`) | glej formulo n05 |  |
| C | Software Engineering (`n09`) | glej formulo n09 |  |

## n12 · Obvezne zahteve – del 2/3  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Architecture (`n13`) | glej formulo n13 |  |
| B | Platforms (`n14`) | glej formulo n14 |  |
| C | Strong analytical skills (`a35`) | raven ≥4 | strong skills |
| D | clearly communicate complex technical concepts (`a36`) | raven ≥3 | ability |

## n16 · Obvezne zahteve – del 3/3  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | banking/financial services (`a37`) | raven ≥3 | solid understanding |
| B | regulated environments (`a38`) | raven ≥3 | solid understanding |
| C | Experience (`n18`) | glej formulo n18 |  |
| D | Education (`n20`) | glej formulo n20 |  |

## n24 · Naloge (pričakovano) – del 1/2  _(drevo T_P)_

- propMinimization: `A⋁B⋁C⋁D`
- minimalna DNF (najmanjše zadostne kombinacije): `A  ⋁  B  ⋁  C  ⋁  D` · resničnih vrstic 15/16
- opomba: točkovanje: ⋁ = vsaj en izpolnjen; štej izpolnjene

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | AI Solution Development (`a01`) | izpolnjeno |  |
| B | Agentic Systems (`a02`) | izpolnjeno |  |
| C | Full-Stack AI Engineering (`a03`) | izpolnjeno |  |
| D | Iterative Delivery (`a04`) | izpolnjeno |  |

## n25 · Naloge (pričakovano) – del 2/2  _(drevo T_P)_

- propMinimization: `A⋁B⋁C⋁D`
- minimalna DNF (najmanjše zadostne kombinacije): `A  ⋁  B  ⋁  C  ⋁  D` · resničnih vrstic 15/16
- opomba: točkovanje: ⋁ = vsaj en izpolnjen; štej izpolnjene

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Evaluation & Optimization (`a05`) | izpolnjeno |  |
| B | Emerging Technologies (`a06`) | izpolnjeno |  |
| C | Technical Collaboration (`a07`) | izpolnjeno |  |
| D | Domain Alignment (`a08`) | izpolnjeno |  |

## n03 · Programming  _(drevo T_M)_

- propMinimization: `(A⋁B)⋀C`
- propositional: `(P⋁Q)⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀C  ⋁  B⋀C` · resničnih vrstic 3/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Python (`a09`) | raven ≥4 | strong proficiency |
| B | Java (Spring Boot) (`a10`) | raven ≥4 | strong proficiency |
| C | JavaScript/TypeScript (Angular, Node.js) (`a11`) | raven ≥2 | working knowledge |

## n05 · AI/ML Expertise  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | core AI concepts (`a13`) | raven ≥3 | solid understanding |
| B | LLMs, RAG, prompt engineering, MCPs, and agent frameworks (`n06`) | glej formulo n06 |  |
| C | ML frameworks and libraries (TensorFlow, PyTorch, Scikit-learn, NumPy, Pandas) (`a19`) | raven ≥3 | practical experience |
| D | AI coding tools (`a20`) | raven ≥1 | familiarity |

## n09 · Software Engineering  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Software Engineering – del 1/2 (`n10`) | glej formulo n10 |  |
| B | agile delivery (`a25`) | raven ≥4 | strong grounding |
| C | application resiliency (`a26`) | raven ≥4 | strong grounding |
| D | security (`a27`) | raven ≥4 | strong grounding |

## n13 · Architecture  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | API-first architectures (`a28`) | raven ≥3 | experience |
| B | microservices-based architectures (`a29`) | raven ≥3 | experience |
| C | event-driven architectures (`a30`) | raven ≥3 | experience |
| D | data engineering patterns for AI systems (`a31`) | raven ≥3 | experience |

## n14 · Platforms  _(drevo T_M)_

- propMinimization: `A⋀B⋀C`
- propositional: `P⋀Q⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C` · resničnih vrstic 1/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Docker (`a32`) | raven ≥3 | hands-on experience |
| B | Kubernetes (`a33`) | raven ≥3 | hands-on experience |
| C | OpenShift (`a34`) | raven ≥3 | hands-on experience |

## n18 · Experience  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | ≥6 let: progressive software engineering experience (`a41`) | prag ≥6 let | 6–10 years |
| B | strong hands-on coding background (`a42`) | raven ≥4 | strong hands-on background |
| C | 2+ years focused on AI software development, LLM-based solutions, agentic systems, and/or machine learning (`n19`) | glej formulo n19 |  |
| D | enterprise-scale AI capabilities into production (`a47`) | raven ≥4 | demonstrated experience |

## n20 · Education  _(drevo T_M)_

- propMinimization: `(A⋁B)⋀C`
- propositional: `(P⋁Q)⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀C  ⋁  B⋀C` · resničnih vrstic 3/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | diploma: Bachelor's (`a48`) | izpolnjeno | degree |
| B | diploma: Master's (`a49`) | izpolnjeno | degree |
| C | področje: Computer Science / AI / Robotics / related quantitative discipline (`a50`) | izpolnjeno | degree in |

## n06 · LLMs, RAG, prompt engineering, MCPs, and agent frameworks  _(drevo T_M)_

- propMinimization: `A⋀B⋀C`
- propositional: `P⋀Q⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C` · resničnih vrstic 1/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | LLMs, RAG, prompt engineering, MCPs, and agent frameworks – del 1/2 (`n07`) | glej formulo n07 |  |
| B | MCPs (`a17`) | raven ≥3 | hands-on experience |
| C | agent frameworks (`a18`) | raven ≥3 | hands-on experience |

## n10 · Software Engineering – del 1/2  _(drevo T_M)_

- propMinimization: `A⋀B⋀C⋀D`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C⋀D` · resničnih vrstic 1/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | Git (`a21`) | raven ≥4 | strong grounding |
| B | CI/CD (`a22`) | raven ≥4 | strong grounding |
| C | testing (`a23`) | raven ≥4 | strong grounding |
| D | code reviews (`a24`) | raven ≥4 | strong grounding |

## n19 · 2+ years focused on AI software development, LLM-based solutions, agentic systems, and/or machine learning  _(drevo T_M)_

- propMinimization: `A⋁B⋁C⋁D`
- minimalna DNF (najmanjše zadostne kombinacije): `A  ⋁  B  ⋁  C  ⋁  D` · resničnih vrstic 15/16

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | ≥2 let: AI software development (`a43`) | prag ≥2 let | 2+ years |
| B | ≥2 let: LLM-based solutions (`a44`) | prag ≥2 let | 2+ years |
| C | ≥2 let: agentic systems (`a45`) | prag ≥2 let | 2+ years |
| D | ≥2 let: machine learning (`a46`) | prag ≥2 let | 2+ years |

## n07 · LLMs, RAG, prompt engineering, MCPs, and agent frameworks – del 1/2  _(drevo T_M)_

- propMinimization: `A⋀B⋀C`
- propositional: `P⋀Q⋀R`
- minimalna DNF (najmanjše zadostne kombinacije): `A⋀B⋀C` · resničnih vrstic 1/8

| črka | pomen | pogoj | signal v besedilu |
|---|---|---|---|
| A | LLMs (`a14`) | raven ≥3 | hands-on experience |
| B | RAG (`a15`) | raven ≥3 | hands-on experience |
| C | prompt engineering (`a16`) | raven ≥3 | hands-on experience |

## Označene dvoumnosti

- **and_or** (I10) „Strong proficiency in Python and/or Java (Spring Boot)“ – 'and/or' razlagam kot vključujoči ALI (⋁).
- **oklepaj_brez_eg** (I10) „Strong proficiency in Python and/or Java (Spring Boot)“ – Naštevanje v oklepaju brez 'e.g.' razlagam kot specifikacijo pojma, ne kot ločene obveznosti.
- **oklepaj_brez_eg** (I10) „working knowledge of JavaScript/TypeScript (Angular, Node.js)“ – Naštevanje v oklepaju brez 'e.g.' razlagam kot specifikacijo pojma, ne kot ločene obveznosti.
- **oklepaj_brez_eg** (I11) „Practical experience with ML frameworks and libraries (TensorFlow, PyTorch, Scikit-learn, NumPy, Pandas)“ – Naštevanje v oklepaju brez 'e.g.' razlagam kot specifikacijo pojma, ne kot ločene obveznosti.
- **including** (I12) „Strong grounding in modern engineering practices including Git, CI/CD, testing, code reviews, agile delivery, application resiliency, and security“ – Naštevanje za 'including' razlagam kot sestavne dele (AND).
- **including** (I13) „Experience designing API-first, microservices-based and event-driven architectures, including data engineering patterns for AI systems“ – Naštevanje za 'including' razlagam kot sestavne dele (AND).
- **oklepaj_brez_eg** (I17) „Experience in data science (statistical modeling, experimentation)“ – Naštevanje v oklepaju brez 'e.g.' razlagam kot specifikacijo pojma, ne kot ločene obveznosti.
- **range_years** (I18) „6–10 years of progressive software engineering experience“ – Razpon let (npr. 6–10): razlagam kot spodnji prag (≥ min); zgornja meja NI izločilna.
- **and_or** (I18) „2+ years focused on AI software development, LLM-based solutions, agentic systems, and/or machine learning“ – 'and/or' razlagam kot vključujoči ALI (⋁).
- **degree_implication** (I19) „Bachelor's or Master's degree in Computer Science, AI, Robotics, or a related quantitative discipline“ – Master's praviloma vključuje Bachelor's; v logiki ostane A⋁B, minimalna oblika to razkrije.
