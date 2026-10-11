import unittest

from src.knowledge_base.document import Document


def make_doc(content="uno due tre", **kwargs):
    data = {
        "document_id": "id_1",
        "title": "Titolo",
        "content": content,
        "source_format": "text",
        "date": "2026-10-08 10:00:00",
    }
    data.update(kwargs)
    return Document(**data)


class TestDocument(unittest.TestCase):

    def test_attributi_obbligatori(self):
        doc = make_doc()
        self.assertEqual(doc.document_id, "id_1")
        self.assertEqual(doc.title, "Titolo")
        self.assertEqual(doc.source_format, "text")
        self.assertEqual(doc.date, "2026-10-08 10:00:00")

    def test_default_opzionali(self):
        doc = make_doc()
        self.assertIsNone(doc.source_filename)
        self.assertEqual(doc.metadata, {})

    def test_metadata_non_condivisi_tra_istanze(self):
        a, b = make_doc(), make_doc()
        a.metadata["x"] = 1
        self.assertEqual(b.metadata, {})

    def test_word_count(self):
        self.assertEqual(make_doc("uno  due\ntre\tquattro").word_count, 4)
        self.assertEqual(make_doc("").word_count, 0)

    def test_excerpt_corto_senza_puntini(self):
        content = "a" * 100
        self.assertEqual(make_doc(content).excerpt, content)

    def test_excerpt_lungo_troncato(self):
        doc = make_doc("a" * 150)
        self.assertEqual(doc.excerpt, "a" * 100 + "...")

    def test_to_dict_contiene_tutte_le_chiavi(self):
        d = make_doc(source_filename="f.txt", metadata={"k": "v"}).to_dict()
        self.assertEqual(
            set(d),
            {"document_id", "title", "content", "source_format", "date",
             "source_filename", "metadata", "word_count", "excerpt"},
        )
        self.assertEqual(d["metadata"], {"k": "v"})

    def test_roundtrip_to_dict_from_dict(self):
        doc = make_doc("x " * 80, source_filename="f.txt", metadata={"k": 1})
        copia = Document.from_dict(doc.to_dict())
        self.assertIsInstance(copia, Document)
        self.assertEqual(copia.to_dict(), doc.to_dict())

    def test_from_dict_campo_mancante(self):
        data = make_doc().to_dict()
        del data["title"]
        with self.assertRaises(KeyError):
            Document.from_dict(data)


if __name__ == "__main__":
    unittest.main()

