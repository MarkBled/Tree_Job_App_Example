package propMinimization;
import java.nio.file.*; import java.util.*; import javax.swing.*;
// Ločen testni harness (ni del izvirne kode): parsira formule iz formule.json z izvirnim parserjem.
public class Harness {
  public static void main(String[] a) throws Exception {
    Calc.stablaPanel = new JPanel(); Calc.interpretacijePanel = new JPanel(); for (int k = 0; k < 20; k++) Calc.interpretacijePanel.add(new JButton());
    for (String line : Files.readAllLines(Paths.get(a[0]))) {
      if (line.isBlank()) continue;
      String[] p = line.split("\t");
      Calc.formulaLS = " " + p[1]; Calc.minimalneNormalneForme = new JTextArea();
      try {
        Formula f = StabloFormule.parsiraj();
        boolean full = StabloFormule.i == StabloFormule.d;
        System.out.println("OK\t" + p[0] + "\t" + p[1] + "\tcelotna=" + full + "\tvar=" + StabloFormule.koristeneVarijable);
        MinimalneNormalneForme.minimalneNormalneForme(f);
        System.out.println("MIN\t" + p[0] + "\t" + Calc.minimalneNormalneForme.getText().replace("\n"," | "));
      } catch (Exception e) { System.out.println("NAPAKA\t" + p[0] + "\t" + p[1] + "\t" + e); }
    }
  }
}
