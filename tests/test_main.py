"""Test end-to-end del menu interattivo di main.py (eseguito come sottoprocesso)."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "main.py"
FIXTURES = Path(__file__).parent / "fixtures"


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
        return subprocess.run(
            [sys.executable, str(MAIN)], input=stdin, capture_output=True,
            text=True, encoding="utf-8", cwd=cwd or self.cwd, env=env, timeout=20,
        )

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

    def test_flusso_completo_parsing_ricerca_export(self):
        self.copy_fixtures()
        r = self.run_main("1\n1\n2\nroma\n3\n5\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("total_documents: 3", r.stdout)
        self.assertIn("Trovati 1 documenti", r.stdout)
        export = self.cwd / "data" / "output" / "knowledge_base.json"
        self.assertTrue(export.is_file())
        self.assertEqual(len(json.loads(export.read_text(encoding="utf-8"))), 3)
        self.assertEqual(r.stdout.count("Indice JSON salvato"), 1)  # nessun messaggio duplicato
        log = (self.cwd / "data" / "output" / "log_error.txt").read_text(encoding="utf-8")
        self.assertEqual(log, "")  # .gitkeep ignorato

    def test_ricerca_vuota_rifiutata(self):
        self.copy_fixtures()
        r = self.run_main("1\n2\n   \n5\n")
        self.assertIn("La parola chiave non può essere vuota", r.stdout)

    def test_data_load_ha_precedenza_sull_export(self):
        self.copy_fixtures()
        self.run_main("1\n3\n5\n")
        export = self.cwd / "data" / "output" / "knowledge_base.json"
        docs = json.loads(export.read_text(encoding="utf-8"))[:1]
        (self.cwd / "data" / "load" / "knowledge_base.json").write_text(json.dumps(docs), encoding="utf-8")
        r = self.run_main("2\n5\n")
        self.assertIn("Indice JSON caricato con successo (1 documenti)", r.stdout)

    def test_export_ricaricabile_dal_menu(self):
        """Ciò che esporta l'opzione 3 dovrebbe poter essere ricaricato con l'opzione 4."""
        self.copy_fixtures()
        self.run_main("1\n3\n5\n")
        r = self.run_main("2\n3\n")
        self.assertIn("Indice JSON caricato con successo (3 documenti)", r.stdout)

    def test_caricamento_json_mancante(self):
        r = self.run_main("2\n3\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Errore durante il caricamento", r.stdout)

    def test_export_con_indice_vuoto(self):
        r = self.run_main("1\n3\n5\n")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Errore durante l'esportazione", r.stdout)

    def test_stdin_chiuso_non_genera_traceback(self):
        for stdin in ("", "1\n", "1\n2\n"):
            with self.subTest(stdin=stdin):
                r = self.run_main(stdin)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertNotIn("Traceback", r.stderr)
                self.assertIn("Arrivederci", r.stdout)

    def test_avvio_da_altra_cartella(self):
        """main.py deve funzionare indipendentemente dalla cartella corrente."""
        self.copy_fixtures()
        r = self.run_main("1\n1\n5\n", cwd=self.cwd / "data" / "input")
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

