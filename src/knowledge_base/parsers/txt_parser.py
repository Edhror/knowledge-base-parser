import datetime
from pathlib import Path
from typing import Any

from src.knowledge_base.base_parser import BaseParser


class TxtParser(BaseParser):
    """Parser che estrae i dati normalizzati da un file di testo semplice (.txt).

    Il titolo viene ricavato dal nome del file senza estensione.
    """

    def parse_file(self, file_path: Path) -> dict[str, Any]:
        """Legge e analizza un file di testo semplice.

        Args:
            file_path (Path): Percorso del file .txt da analizzare.

        Returns:
            dict[str, Any]: Dizionario con le chiavi:
                - ``document_id`` (str): ID univoco del documento.
                - ``title`` (str): il nome del file normalizzato e senza estensione.
                - ``content`` (str): intero testo del file.
                - ``source_format`` (str): sempre ``"text"``.
                - ``source_filename`` (str): nome del file con estensione.
                - ``date`` (str): data di ultima modifica (``%Y-%m-%d %H:%M:%S``).
                - ``metadata`` (dict): dizionario con il numero di righe e il numero di caratteri.

        Raises:
            FileNotFoundError: Se il percorso non esiste o non è un file.
            ValueError: Se il contenuto è vuoto o la data di modifica non è determinabile.
        """
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File non valido o inesistente: {file_path}")

        with file_path.open("r", encoding="utf-8") as txt_file:
            lines = txt_file.readlines()

        content = "".join(lines)
        title = self.normalize_string(file_path.stem)
        metadata = {
            "num_lines": len(lines),
            "num_characters": len(content)
        }

        try:
            mtime = file_path.stat().st_mtime
            date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date = ""

        source_format = "text"

        if not content.strip():
            raise ValueError("Errore di parsing: il contenuto del file è vuoto.")
        if not date:
            raise ValueError("Errore di parsing: non è stato possibile determinare la data di ultima modifica del file.")

        document_id = self.create_id(title, date, source_format, content)

        return {
            "document_id": document_id,
            "title": title,
            "content": content,
            "source_format": source_format,
            "source_filename": file_path.name,
            "date": date,
            "metadata": metadata
        }