# propMinimization: every tautology crashes minimal-form output (ClassCastException) + bundled README still says Java 8

> Ready to paste as a GitHub issue in `JAnicaTZ/TreeOfKnowledge`. Found while building the independent experiment described in `TREE-DEPENDENCY.md` (§4.5 of the assessment). No TREE file was modified; the findings are reported, not patched.

**Tested on:**

- Source bundle `AllSourceCode4UPloadToAI-TreeOfKnowledge-1.0.0.zip`, SHA-256 `2062b782edbd4d5697ae53a09c210b481296089ca353ae6fc520c1b49fe3f4d1`
- OpenJDK 21.0.10 (Linux), headless

---

## Finding 1 — Tautology marker mismatch → `ClassCastException` (propMinimization)

**Severity:** high for the minimization calculator. Every tautology fails in the minimal-normal-form step. The truth-table highlighting runs earlier and still works.

### Cause

Two classes use different spellings of the same sentinel string:

| file | line | string |
|---|---|---|
| `propMinimization/PrimeImplicants.java` | 21, 29, 42 | `"tautologija;)!)"` (written when a tautology is detected) |
| `propMinimization/IreducibilneDNF.java` | 76 | `"tautologija;)!)"` |
| `propMinimization/MinimalneNormalneForme.java` | **33** | `"tautology;)!)"` (checked before calling `IreducibilneDNF`) |

Because the check on line 33 never matches, the list `[ "tautologija;)!)" ]` (one `String`, not a `List` of literals) is passed to `IreducibilneDNF.ireducibilneDNF(...)`. There it is cast to `List`.

### Reproduce

1. Open the propMinimization calculator.
2. Enter any tautology, for example `A⋁¬A`, `A⇒A` or `(A⋀B)⇒(A⋁B)`.
3. Or run it headless: set `Calc.formulaLS = " A⋁¬A"` and call `MinimalneNormalneForme.minimalneNormalneForme(StabloFormule.parsiraj())`.

### Actual

```
PRIME IMPLICANTS:
[tautologija;)!)]
Exception in thread "main" java.lang.ClassCastException: class java.lang.String cannot be cast to class java.util.List
	at propMinimization.IreducibilneDNF.kopirajListuListi(IreducibilneDNF.java:94)
	at propMinimization.IreducibilneDNF.pruneBySubsumption(IreducibilneDNF.java:52)
	at propMinimization.IreducibilneDNF.ireducibilneDNF(IreducibilneDNF.java:25)
	at propMinimization.MinimalneNormalneForme.minimalneNormalneForme(MinimalneNormalneForme.java:34)
```

### Expected

The `else` branch on line 96 runs and the output panel shows `TAUTOLOGY`.

### Suggested fix (one line)

In `MinimalneNormalneForme.java`, line 33:

```java
// before
if (!primeImplicants.contains(new String("tautology;)!)"))) {
// after
if (!primeImplicants.contains(new String("tautologija;)!)"))) {
```

A named constant shared by the three classes, e.g. `static final String TAUTOLOGY_MARKER`, would prevent a recurrence.

### Workaround used in our experiment

Instead of testing whether `K ⇒ R` is a tautology, we test whether `(K)⋀¬(R)` is a contradiction, i.e. whether the DNF is empty. The two are logically equivalent, and the contradiction path works correctly. We ran 380 inputs this way with no failures.

---

## Finding 2 — Bundled README states Java 8, but the source requires Java 15+

**Severity:** low (documentation).

- The repository `README.md` correctly says **Java 21**, and that older versions should not be claimed.
- The `README.md` **inside the source ZIP** (1.0.0) still says `Java 8 or newer` (around line 139).
- `common/UIStrings.java` uses text blocks (`"""`, lines 20–28). Text blocks require **Java 15+**, so compiling with `javac --release 11` fails with:

```
common/UIStrings.java:20: error: text blocks are not supported in -source 11
```

**Suggested fix:** update the README inside the ZIP to match the repository (Java 21). Alternatively, if older Java support is wanted, replace the text blocks in `UIStrings.java` with ordinary string concatenation.

---

*Found by:* Marko (Klasifikacija experiment), with Claude (Anthropic) as analysis assistant. Happy to provide the headless test harness (`verify/HarnessProof.java`) and the 380 test inputs and outputs if useful.
