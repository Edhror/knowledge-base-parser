import hashlib
import re
import unicodedata
import json
from pathlib import Path
from typing import Any
from src.knowledge_base.document import Document


class BaseParser:
  """Classe base per i parsers di documenti
  """

  def parse_file(self, file_path: Path) -> dict[str, Any]:
    """Metodo astratto per il parsing di un file.
    Deve essere implementato dalle sottoclassi per definire la logica di parsing specifica.

    Returns:
      dict[str, str]: Un dizionario contenente i dati estratti dal file.
    """
    pass

  def create_id(self, title: str, date: str, source_format: str, content: str) -> str:
    """Genera un ID univoco per il documento basato su titolo, data, formato sorgente e contenuto.

    Args:
      title (str): Titolo del documento.
      date (str): Data del documento.
      source_format (str): Formato della sorgente del documento.
      content (str): Contenuto del documento.

    Returns:
      str: L'ID univoco generato per il documento.
    """
    normalized_title = self.normalize_string(title)
    normalized_date = self.normalize_string(date)
    normalized_source_format = self.normalize_string(source_format)
    dati_per_hash = f"{normalized_title}|{normalized_date}|{normalized_source_format}|{content}"
    hash_object = hashlib.sha256(dati_per_hash.encode("utf-8")).hexdigest()[:16]
    return f"{normalized_date}_{normalized_title}_{normalized_source_format}_{hash_object}"

  def normalize_string(self, string: str) -> str:
    """Normalizza una stringa rimuovendo accenti, convertendo in minuscolo,
    sostituendo caratteri non alfanumerici con underscore e rimuovendo underscore consecutivi.

    Args:
      string (str): La stringa da normalizzare.

    Returns:
      str: La stringa normalizzata.
    """
    string = string.strip().lower()
    string = unicodedata.normalize("NFD", string)
    string = "".join(
        char for char in string if unicodedata.category(char) != "Mn"
    )
    string = re.sub(r"[^a-z0-9]", "_", string)
    string = re.sub(r"_+", "_", string)
    string = string.strip("_")
    return string

  def create_document(self, file: dict[str,Any]) -> Document:
    """Crea un oggetto Document da un dizionario di dati del file.

    Args:
      file (dict[str, Any]): Un dizionario contenente i dati del documento, come titolo, contenuto, ecc.

    Returns:
      Document: Un'istanza della classe Document.
    """
    title = file["title"]
    content = file["content"]
    source_format = file["source_format"]
    source_filename = file["source_filename"]
    date = file["date"]
    metadata = file["metadata"]
    document_id = self.create_id(title, date, source_format, content)
    # Assuming Document class is defined elsewhere and its constructor matches these arguments
    doc = Document(document_id,title, content, source_format, date, source_filename, metadata)
    return doc

  def create_json_index(self, documents: list[Document], output_path: Path):
    """Crea un indice JSON da una lista di oggetti Document.

    Args:
      documents (list[Document]): Una lista di oggetti Document da indicizzare.
      output_path (Path): Il percorso del file di output JSON.
    """
    documents_data = [document.to_dict() for document in documents]

    with output_path.open("w", encoding="utf-8") as json_file:
      json.dump(documents_data, json_file, indent=4, ensure_ascii=False)