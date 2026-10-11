import tempfile
import unittest
from pathlib import Path

from src.knowledge_base.parsers.csv_parser import CsvParser

FIXTURES = Path(__file__).parent / "fixtures"


class TestCsvParser(unittest.TestCase):

    def setUp(self):
        self.parser = CsvParser()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content):
        path = self.tmp / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def test_fixture(self):
        result = self.parser.parse_file(FIXTURES / "sample.csv")
        self.assertEqual(result["title"], "sample")
        self.assertEqual(result["source_format"], "csv")
        self.assertEqual(result["source_filename"], "sample.csv")
        self.assertEqual(result["metadata"]["num_rows"], 3)
        self.assertEqual(result["metadata"]["num_cols"], 3)
        self.assertEqual(result["metadata"]["delimiter"], ",")
        self.assertNotIn("extra_values", result["metadata"])
        self.assertTrue(result["content"].startswith("Colonne: nome, età, città"))
        self.assertIn("nome: Anna | età: 30 | città: Roma", result["content"])

    def test_delimitatore_punto_e_virgola(self):
        result = self.parser.parse_file(self.write("pv.csv", "a;b\n1;2\n3;4\n"))
        self.assertEqual(result["metadata"]["delimiter"], ";")
        self.assertIn("a: 1 | b: 2", result["content"])

    def test_righe_vuote_ignorate(self):
        result = self.parser.parse_file(self.write("r.csv", "a,b\n1,2\n\n , \n3,4\n"))
        self.assertEqual(result["metadata"]["num_rows"], 2)

    def test_valori_in_eccesso(self):
        result = self.parser.parse_file(self.write("e.csv", "a,b\n1,2\n3,4,5,6\n"))
        self.assertEqual(result["metadata"]["extra_values"], {"2": ["5", "6"]})
        self.assertIn("a: 3 | b: 4", result["content"])

    def test_intestazione_vuota(self):
        result = self.parser.parse_file(self.write("h.csv", "a,,c\n1,2,3\n"))
        self.assertIn("column_2: 2", result["content"])

    def test_bom_utf8(self):
        result = self.parser.parse_file(self.write("bom.csv", "\ufeffnome,val\nx,1\n"))
        self.assertTrue(result["content"].startswith("Colonne: nome, val"))

    def test_colonna_singola(self):
        result = self.parser.parse_file(self.write("s.csv", "nome\nAnna\nLuca\n"))
        self.assertEqual(result["metadata"]["num_cols"], 1)
        self.assertIn("nome: Anna", result["content"])

    def test_campi_tra_virgolette(self):
        result = self.parser.parse_file(self.write("q.csv", 'a,b\n"Rossi, Mario",2\n'))
        self.assertIn("a: Rossi, Mario | b: 2", result["content"])

    def test_file_vuoto(self):
        with self.assertRaises(ValueError):
            self.parser.parse_file(self.write("vuoto.csv", ""))

    def test_file_inesistente(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(self.tmp / "manca.csv")

    def test_codifica_non_utf8(self):
        with self.assertRaises(UnicodeDecodeError):
            self.parser.parse_file(self.write("latin.csv", "città\nRoma\n".encode("latin-1")))


if __name__ == "__main__":
    unittest.main()

