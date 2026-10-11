import re
import tempfile
import unittest
from pathlib import Path

from src.knowledge_base.parsers.txt_parser import TxtParser

FIXTURES = Path(__file__).parent / "fixtures"
ID_PATTERN = re.compile(r"^\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}_[a-z0-9_]+_[0-9a-f]{16}$")


class TestTxtParser(unittest.TestCase):

    def setUp(self):
        self.parser = TxtParser()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content, encoding="utf-8"):
        path = self.tmp / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding=encoding)
        return path

    def test_fixture(self):
        result = self.parser.parse_file(FIXTURES / "sample.txt")
        self.assertEqual(
            set(result),
            {"document_id", "title", "content", "source_format", "source_filename", "date", "metadata"},
        )
        self.assertEqual(result["title"], "sample")
        self.assertEqual(result["source_format"], "text")
        self.assertEqual(result["source_filename"], "sample.txt")
        self.assertIn("documento di prova", result["content"])
        self.assertEqual(result["metadata"]["num_lines"], 3)
        self.assertEqual(result["metadata"]["num_characters"], len(result["content"]))
        self.assertRegex(result["date"], r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")

    def test_formato_e_determinismo_id(self):
        path = FIXTURES / "sample.txt"
        id1 = self.parser.parse_file(path)["document_id"]
        id2 = self.parser.parse_file(path)["document_id"]
        self.assertEqual(id1, id2)
        self.assertRegex(id1, ID_PATTERN)

    def test_id_cambia_con_il_contenuto(self):
        a = self.parser.parse_file(self.write("a.txt", "uno"))
        b = self.parser.parse_file(self.write("b.txt", "due"))
        self.assertNotEqual(a["document_id"], b["document_id"])

    def test_titolo_normalizzato(self):
        result = self.parser.parse_file(self.write("Città Bella-2026.txt", "testo"))
        self.assertEqual(result["title"], "citta_bella_2026")

    def test_file_vuoto(self):
        with self.assertRaises(ValueError):
            self.parser.parse_file(self.write("vuoto.txt", ""))

    def test_file_solo_spazi(self):
        with self.assertRaises(ValueError):
            self.parser.parse_file(self.write("spazi.txt", "  \n\t\n"))

    def test_file_inesistente(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(self.tmp / "manca.txt")

    def test_cartella_invece_di_file(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(self.tmp)

    def test_codifica_non_utf8(self):
        with self.assertRaises(UnicodeDecodeError):
            self.parser.parse_file(self.write("latin.txt", "città".encode("latin-1")))


if __name__ == "__main__":
    unittest.main()

