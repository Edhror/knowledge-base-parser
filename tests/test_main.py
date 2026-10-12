"""Test end-to-end del menu interattivo di main.py (eseguito come sottoprocesso).

Menu principale: 1 statistiche, 2 visualizza knowledge base, 3 ricerca,
4 filtro per estensione, 5 export, 6 caricamento JSON, 7 uscita.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.py"
FIXTURES = Path(__file__).parent / "fixtures"
ANSI = re.compile(r"\x1b\[[0-9;]*m")  # codici colore del terminale


class TestMain(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self._tmp.name)
        for d in ("input", "load", "output"):
            (self.cwd / "data" / d).mkdir(parents=True)
        (self.cwd / "data" / "input" / ".gitkeep").touch()

    def tearDown(self):
        self._tmp.cleanup()

    def run_main(self, stdin, cwd=None):
        env = {
            **os.environ,
            "KB_DATA_DIR": str(self.cwd / "data"),
            "PYTHONIOENCODING": "utf-8",
        }
        env.pop("PYTHONPATH", None)
        r = subprocess.run(
            [sys.executable, str(MAIN)], input=stdin, capture_output=True,
            text=True, encoding="utf-8", cwd=cwd or self.cwd, env=env, timeout=20,
        )
        r.stdout = ANSI.sub("", r.stdout)  # rimuove i codici colore
        return r

    def copy_fixtures(self):
        for f in FIXTURES.iterdir():
            shutil.copy(f, self.cwd / "data" / "input" / f.name)

    def test_uscita_immediata(self):
        r = self.run_main("3\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Arrivederci", r.stdout)

    def test_scelta_non_valida(self):
        r = self.run_main("x\n3\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Scelta non valida", r.stdout)

    def test_menu_principale_opzioni(self):
        self.copy_fixtures()
        r = self.run_main("1\n7\n")
        for voce in ("1. Visualizza statistiche", "2. Visualizza Knowledge",
                     "3. Cerca documenti", "4. Filtra per estensione",
                     "5. Esporta", "6. Carica", "7. Esci"):
            self.assertIn(voce, r.stdout)

    def test_menu_principale_scelta_non_valida(self):
        self.copy_fixtures()
        r = self.run_main("1\n8\n7\n")
        self.assertIn("Scelta non valida. Per favore, seleziona un'opzione tra 1 e 7.", r.stdout)

    def test_flusso_completo_parsing_ricerca_export(self):
        self.copy_fixtures()
        r = self.run_main("1\n1\n3\nroma\n0\n5\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("total_documents: 3", r.stdout)
        self.assertIn("source_filename: sample.csv", r.stdout)  # unico risultato per "roma"
        self.assertIn("Visualizza contenuto completo", r.stdout)
        export = self.cwd / "data" / "output" / "knowledge_base.json"
        self.assertTrue(export.is_file())
        self.assertEqual(len(json.loads(export.read_text(encoding="utf-8"))), 3)
        self.assertEqual(r.stdout.count("Indice JSON salvato"), 1)  # nessun messaggio duplicato
        log = (self.cwd / "data" / "output" / "log_error.txt").read_text(encoding="utf-8")
        self.assertEqual(log, "")  # .gitkeep ignorato

    def test_ricerca_vuota_rifiutata(self):
        self.copy_fixtures()
        r = self.run_main("1\n3\n   \n7\n")
        self.assertIn("La parola chiave non può essere vuota", r.stdout)

    def test_ricerca_nessun_risultato(self):
        self.copy_fixtures()
        r = self.run_main("1\n3\ninesistente\n7\n")
        self.assertIn("Nessun documento trovato contenente la parola chiave 'inesistente'", r.stdout)

    def test_ricerca_risultati_multipli_dal_menu(self):
        """Più risultati: scelgo un documento, vedo il contenuto completo,
        torno all'elenco, annullo e il menu principale resta utilizzabile."""
        self.copy_fixtures()
        r = self.run_main("1\n3\na\n2\n1\n0\n0\n1\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Sono stati trovati 3 documenti", r.stdout)
        self.assertIn("Attenzione: il contenuto potrebbe essere molto lungo", r.stdout)
        self.assertIn("Ricerca annullata.", r.stdout)
        self.assertIn("total_documents: 3", r.stdout)  # opzione 1 del menu dopo la ricerca
        self.assertNotIn("Scelta non valida", r.stdout)

    def test_visualizza_knowledge_base_dal_menu(self):
        """Opzione 2: elenco, scelta di un documento, contenuto completo, ritorno al menu."""
        self.copy_fixtures()
        r = self.run_main("1\n2\n2\n1\n0\n0\n1\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Hai scelto di visualizzare la knowledge base.", r.stdout)
        self.assertIn("Sono presenti 3 documenti nella knowledge base:", r.stdout)
        self.assertIn("Attenzione: il contenuto potrebbe essere molto lungo", r.stdout)
        self.assertIn("total_documents: 3", r.stdout)  # il menu resta utilizzabile
        self.assertNotIn("Scelta non valida", r.stdout)

    def test_visualizza_knowledge_base_vuota_dal_menu(self):
        r = self.run_main("1\n2\n7\n")  # data/input contiene solo .gitkeep
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("La knowledge base è vuota.", r.stdout)

    def test_filtro_estensione_dal_menu(self):
        self.copy_fixtures()
        r = self.run_main("1\n4\nMD\n0\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Hai scelto di filtrare per estensione.", r.stdout)
        self.assertIn("source_filename: sample.md", r.stdout)
        self.assertNotIn("Scelta non valida", r.stdout)

    def test_filtro_estensione_non_valida_dal_menu(self):
        self.copy_fixtures()
        r = self.run_main("1\n4\npdf\n4\n\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(
            r.stdout.count("Estensione non valida. Per favore, inserisci txt, md o csv."), 2
        )

    def test_filtro_estensione_nessun_risultato_dal_menu(self):
        shutil.copy(FIXTURES / "sample.md", self.cwd / "data" / "input" / "sample.md")
        r = self.run_main("1\n4\ntxt\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Nessun documento trovato con l'estensione 'txt'.", r.stdout)

    def test_data_load_ha_precedenza_sull_export(self):
        self.copy_fixtures()
        self.run_main("1\n5\n7\n")
        export = self.cwd / "data" / "output" / "knowledge_base.json"
        docs = json.loads(export.read_text(encoding="utf-8"))[:1]
        (self.cwd / "data" / "load" / "knowledge_base.json").write_text(json.dumps(docs), encoding="utf-8")
        r = self.run_main("2\n7\n")
        self.assertIn("Indice JSON caricato con successo (1 documenti)", r.stdout)

    def test_export_ricaricabile_dal_menu(self):
        """Ciò che esporta l'opzione 5 dovrebbe poter essere ricaricato con l'opzione 6."""
        self.copy_fixtures()
        r = self.run_main("1\n5\n6\n7\n")
        self.assertIn("Indice JSON caricato con successo (3 documenti)", r.stdout)
        r = self.run_main("2\n7\n")
        self.assertIn("Indice JSON caricato con successo (3 documenti)", r.stdout)

    def test_caricamento_json_mancante(self):
        r = self.run_main("2\n3\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Errore durante il caricamento", r.stdout)

    def test_export_con_indice_vuoto(self):
        r = self.run_main("1\n5\n7\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Errore durante l'esportazione", r.stdout)

    def test_stdin_chiuso_non_genera_traceback(self):
        for stdin in ("", "1\n", "1\n2\n", "1\n3\n", "1\n4\n"):
            with self.subTest(stdin=stdin):
                r = self.run_main(stdin)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn("Arrivederci", r.stdout)

    def test_avvio_da_altra_cartella(self):
        """main.py deve funzionare indipendentemente dalla cartella corrente."""
        self.copy_fixtures()
        r = self.run_main("1\n1\n7\n", cwd=self.cwd / "data" / "input")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("total_documents: 3", r.stdout)

    def test_percorsi_predefiniti_assoluti(self):
        """Senza KB_DATA_DIR la cartella dati è quella del progetto, non quella corrente."""
        env = {k: v for k, v in os.environ.items() if k != "KB_DATA_DIR"}
        r = subprocess.run(
            [sys.executable, "-c", "import main; print(main.DATA_DIR)"],
            capture_output=True, text=True, cwd=ROOT, env=env, timeout=20,
        )
        self.assertEqual(Path(r.stdout.strip()), ROOT / "data")


if __name__ == "__main__":
    unittest.main()

