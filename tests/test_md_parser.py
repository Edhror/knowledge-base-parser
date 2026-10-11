import tempfile
import unittest
from pathlib import Path

from src.knowledge_base.parsers.md_parser import MdParser

FIXTURES = Path(__file__).parent / "fixtures"


class TestMdParser(unittest.TestCase):

    def setUp(self):
        self.parser = MdParser()
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
        result = self.parser.parse_file(FIXTURES / "sample.md")
        self.assertEqual(result["title"], "Guida di esempio")
        self.assertEqual(result["source_format"], "markdown")
        self.assertEqual(result["source_filename"], "sample.md")
        self.assertEqual(result["metadata"]["num_titles"], 4)
        self.assertEqual(result["metadata"]["title_levels"], {"H1": 1, "H2": 2, "H3": 1})
        self.assertEqual(result["metadata"]["num_lines"], 13)
        self.assertTrue(result["document_id"])

    def test_primo_h1_vince(self):
        result = self.parser.parse_file(self.write("a.md", "## Sotto\n# Primo\n# Secondo\n"))
        self.assertEqual(result["title"], "Primo")

    def test_fallback_titolo_nome_file(self):
        result = self.parser.parse_file(self.write("Note Varie.md", "## Solo H2\ntesto\n"))
        self.assertEqual(result["title"], "note_varie")

    def test_hashtag_senza_spazio_non_e_titolo(self):
        result = self.parser.parse_file(self.write("tag.md", "#hashtag\ntesto\n"))
        self.assertEqual(result["metadata"]["num_titles"], 0)
        self.assertEqual(result["title"], "tag")

    def test_titolo_indentato(self):
        result = self.parser.parse_file(self.write("ind.md", "   # Indentato\n"))
        self.assertEqual(result["title"], "Indentato")

    def test_commento_in_blocco_codice_non_e_titolo(self):
        content = "```bash\n# installa le dipendenze\npip install x\n```\n\n# Titolo vero\n"
        result = self.parser.parse_file(self.write("code.md", content))
        self.assertEqual(result["title"], "Titolo vero")
        self.assertEqual(result["metadata"]["num_titles"], 1)

    def test_blocco_codice_tilde(self):
        content = "~~~\n# non titolo\n~~~\n## Sotto\n"
        result = self.parser.parse_file(self.write("tilde.md", content))
        self.assertEqual(result["metadata"]["title_levels"], {"H2": 1})
        self.assertEqual(result["title"], "tilde")

    def test_piu_di_sei_cancelletti_non_e_titolo(self):
        result = self.parser.parse_file(self.write("h7.md", "####### troppi\n"))
        self.assertEqual(result["metadata"]["num_titles"], 0)

    def test_file_vuoto(self):
        with self.assertRaises(ValueError):
            self.parser.parse_file(self.write("vuoto.md", ""))

    def test_file_inesistente(self):
        with self.assertRaises(FileNotFoundError):
            self.parser.parse_file(self.tmp / "manca.md")

    def test_codifica_non_utf8(self):
        with self.assertRaises(UnicodeDecodeError):
            self.parser.parse_file(self.write("latin.md", "# Città".encode("latin-1")))


if __name__ == "__main__":
    unittest.main()

