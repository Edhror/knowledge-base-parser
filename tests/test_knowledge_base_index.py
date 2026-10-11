import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.knowledge_base.knowledge_base_index import KnowledgeBaseIndex

FIXTURES = Path(__file__).parent / "fixtures"


class BaseIndexTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.input = self.tmp / "input"
        self.output = self.tmp / "output"
        self.input.mkdir()
        self.kb = KnowledgeBaseIndex()

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, name, content):
        path = self.input / name
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
        return path

    def copy_fixtures(self):
        for f in FIXTURES.iterdir():
            shutil.copy(f, self.input / f.name)

    def parse(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.kb.get_docs_from_parsing(self.input, self.output)

    def quiet(self, func, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            return func(*args)

    def read_log(self):
        return (self.output / "log_error.txt").read_text(encoding="utf-8")


class TestParsing(BaseIndexTest):

    def test_parsing_fixture(self):
        self.copy_fixtures()
        docs = self.parse()
        self.assertEqual(len(docs), 3)
        self.assertEqual({d.source_format for d in docs}, {"text", "markdown", "csv"})
        self.assertEqual(len(self.kb.documents), 3)
        self.assertEqual(self.read_log(), "")

    def test_log_errori(self):
        self.write("ok.txt", "testo")
        self.write("vuoto.txt", "")
        self.write("img.png", "x")
        self.write("latin.md", "città".encode("latin-1"))
        docs = self.parse()
        self.assertEqual(len(docs), 1)
        log = self.read_log().splitlines()
        self.assertEqual(len(log), 3)
        self.assertTrue(any(l.startswith("img.png = Estensione '.png' non ammessa") for l in log))
        self.assertIn("latin.md = Il file non è codificato in UTF-8.", log)
        self.assertTrue(any(l.startswith("vuoto.txt = ") for l in log))

    def test_estensione_maiuscola(self):
        self.write("UPPER.TXT", "testo")
        self.assertEqual(len(self.parse()), 1)

    def test_sottocartelle_ignorate(self):
        (self.input / "sub").mkdir()
        (self.input / "sub" / "x.txt").write_text("testo", encoding="utf-8")
        self.assertEqual(self.parse(), [])
        self.assertEqual(self.read_log(), "")

    def test_file_nascosti_ignorati(self):
        """data/input contiene .gitkeep: non dovrebbe finire nel log degli errori."""
        self.write(".gitkeep", "")
        self.write(".DS_Store", "x")
        self.parse()
        self.assertEqual(self.read_log(), "")

    def test_cartella_inesistente(self):
        with self.assertRaises(NotADirectoryError):
            self.kb.get_docs_from_parsing(self.tmp / "manca", self.output)

    def test_documenti_duplicati_nel_log(self):
        """Due .md con stesso H1 e contenuto e stessa data producono lo stesso ID."""
        a = self.write("a.md", "# Uguale\ntesto\n")
        b = self.write("b.md", "# Uguale\ntesto\n")
        os.utime(b, (a.stat().st_atime, a.stat().st_mtime))
        docs = self.parse()
        self.assertEqual(len(docs), 1)
        self.assertTrue(self.read_log().startswith("b.md = Documento duplicato di 'a.md'"))

    def test_parsing_sostituisce_indice(self):
        self.write("a.txt", "uno")
        self.parse()
        (self.input / "a.txt").unlink()
        self.write("b.txt", "due")
        self.parse()
        self.assertEqual([d.title for d in self.kb.documents], ["b"])


class TestConsultazione(BaseIndexTest):

    def setUp(self):
        super().setUp()
        self.copy_fixtures()
        self.parse()

    def test_documents_sola_lettura(self):
        with self.assertRaises(AttributeError):
            self.kb.documents = []
        self.kb.documents.clear()
        self.assertEqual(len(self.kb.documents), 3)

    def test_ricerca_case_insensitive(self):
        self.assertEqual([d.title for d in self.kb.search_documents("ROMA")], ["sample"])
        self.assertEqual(len(self.kb.search_documents("guida")), 1)
        self.assertEqual(self.kb.search_documents("inesistente"), [])

    def test_get_document_by_id(self):
        doc = self.kb.documents[0]
        self.assertIs(self.kb.get_document_by_id(doc.document_id), doc)
        self.assertIsNone(self.kb.get_document_by_id("nessuno"))

    def test_statistiche(self):
        stats = self.kb.get_statistics()
        self.assertEqual(stats["total_documents"], 3)
        self.assertEqual(stats["total_word_count"], sum(d.word_count for d in self.kb.documents))
        self.assertAlmostEqual(stats["average_word_count"], stats["total_word_count"] / 3)

    def test_statistiche_indice_vuoto(self):
        self.assertEqual(
            KnowledgeBaseIndex().get_statistics(),
            {"total_documents": 0, "total_word_count": 0, "average_word_count": 0},
        )


class TestJson(BaseIndexTest):

    def test_roundtrip(self):
        self.copy_fixtures()
        self.parse()
        path = self.quiet(self.kb.create_json_index, self.tmp / "out" / "kb.json")
        kb2 = KnowledgeBaseIndex()
        self.quiet(kb2.load_json_index, path)
        self.assertEqual(
            [d.to_dict() for d in kb2.documents],
            [d.to_dict() for d in self.kb.documents],
        )
        self.assertEqual(list((self.tmp / "out").iterdir()), [path])  # nessun .tmp residuo

    def test_roundtrip_csv_con_valori_in_eccesso(self):
        """Le chiavi intere di extra_values diventano stringhe dopo il passaggio in JSON."""
        self.write("e.csv", "a,b\n1,2,3\n")
        self.parse()
        path = self.quiet(self.kb.create_json_index, self.tmp / "kb.json")
        kb2 = KnowledgeBaseIndex()
        self.quiet(kb2.load_json_index, path)
        self.assertEqual(kb2.documents[0].metadata, self.kb.documents[0].metadata)

    def test_export_indice_vuoto(self):
        with self.assertRaises(ValueError):
            self.kb.create_json_index(self.tmp / "kb.json")

    def test_export_errori_percorso(self):
        self.write("a.txt", "testo")
        self.parse()
        with self.assertRaises(IsADirectoryError):
            self.kb.create_json_index(self.tmp)
        with self.assertRaises(ValueError):
            self.kb.create_json_index(self.tmp / "kb.txt")

    def write_json(self, data):
        path = self.tmp / "in.json"
        path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
        return path

    def test_load_errori(self):
        casi = {
            "inesistente": (self.tmp / "manca.json", FileNotFoundError),
            "json malformato": (self.write_json("[1,"), ValueError),
            "non lista": (self.write_json({"a": 1}), ValueError),
            "elemento non oggetto": (self.write_json([1]), ValueError),
            "campo mancante": (self.write_json([{"title": "x"}]), ValueError),
        }
        for nome, (path, exc) in casi.items():
            with self.subTest(nome):
                with self.assertRaises(exc):
                    self.kb.load_json_index(path)

    def test_load_fallito_non_altera_indice(self):
        self.write("a.txt", "testo")
        self.parse()
        with self.assertRaises(ValueError):
            self.kb.load_json_index(self.write_json("{rotto"))
        self.assertEqual(len(self.kb.documents), 1)

    def test_load_valori_null_rifiutati(self):
        """Un JSON con content/title null va rifiutato, altrimenti la ricerca va in errore."""
        doc = {
            "document_id": "x", "title": None, "content": None, "source_format": "text",
            "date": "2026-01-01 00:00:00", "source_filename": None, "metadata": {},
        }
        with self.assertRaises(ValueError):
            self.kb.load_json_index(self.write_json([doc]))

    def test_load_metadata_tipo_errato(self):
        doc = {
            "document_id": "x", "title": "t", "content": "c", "source_format": "text",
            "date": "2026-01-01 00:00:00", "source_filename": None, "metadata": [1, 2],
        }
        with self.assertRaises(ValueError):
            self.kb.load_json_index(self.write_json([doc]))

    def test_load_id_duplicati(self):
        doc = {
            "document_id": "dup", "title": "t", "content": "c", "source_format": "text",
            "date": "2026-01-01 00:00:00", "source_filename": None, "metadata": {},
        }
        with self.assertRaises(ValueError):
            self.kb.load_json_index(self.write_json([doc, doc]))


if __name__ == "__main__":
    unittest.main()

