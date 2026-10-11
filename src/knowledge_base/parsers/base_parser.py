import hashlib
import re
import unicodedata
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