package propMinimization;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import javax.swing.*;

/**
 * Ločen testni harness (NI del izvirne kode TreeOfKnowledge; izvirnih datotek ne spreminja).
 * Vhod:  TSV "ključ<TAB>formula" (formule v sintaksi propMinimization: A–D, ¬ ⋀ ⋁ ⇒ ( )).
 * Izhod: TSV "ključ<TAB>formula<TAB>celotna<TAB>status<TAB>primarni_implikanti<TAB>minimalne_forme"
 *   status = TAUTOLOGY | CONTRADICTION | SATISFIABLE | PARSE_ERROR
 * Uporablja izvirni parser (StabloFormule), pretvorbo v DNF (FormulaUNormalnoj.disjunktivnojFormi)
 * in izvirni izračun primarnih implikantov (PrimeImplicants). Java 11+.
 */
public class HarnessProof {
  static String one(String s) { return s == null ? "" : s.replace("\t", " ").replace("\n", " | ").trim(); }

  public static void main(String[] a) throws Exception {
    PrintStream out = new PrintStream(new FileOutputStream(a[1]), true, "UTF-8");
    PrintStream sysout = System.out;
    Calc.stablaPanel = new JPanel();
    Calc.interpretacijePanel = new JPanel();
    for (int k = 0; k < 20; k++) Calc.interpretacijePanel.add(new JButton());
    for (String line : Files.readAllLines(Paths.get(a[0]), StandardCharsets.UTF_8)) {
      if (line.trim().isEmpty()) continue;
      String[] p = line.split("\t");
      String key = p[0], formula = p[1];
      Calc.formulaLS = " " + formula;
      Calc.minimalneNormalneForme = new JTextArea();
      try {
        System.setOut(new PrintStream(new ByteArrayOutputStream()));
        Formula f = StabloFormule.parsiraj();
        boolean full = StabloFormule.i == StabloFormule.d;
        List dnf = ((FormulaUNormalnoj) ((Formula) f.clone()).eliminiramNegacije()).disjunktivnojFormi();
        String status, pis = "", mins = "";
        if (dnf.isEmpty()) {
          status = "CONTRADICTION";
        } else {
          List pi = PrimeImplicants.primeImplicants(new ArrayList(dnf));
          pis = String.valueOf(pi);
          if (pi.contains("tautologija;)!)")) {
            status = "TAUTOLOGY";
          } else {
            status = "SATISFIABLE";
            try {
              MinimalneNormalneForme.minimalneNormalneForme(f);
              mins = Calc.minimalneNormalneForme.getText();
            } catch (Exception e) { mins = "minimizacija: " + e; }
          }
        }
        System.setOut(sysout);
        out.println(key + "\t" + formula + "\t" + full + "\t" + status + "\t" + one(pis) + "\t" + one(mins));
      } catch (Exception e) {
        System.setOut(sysout);
        out.println(key + "\t" + formula + "\tfalse\tPARSE_ERROR\t" + one(e.toString()) + "\t");
      }
    }
    out.close();
  }
}
