import csv
from pathlib import Path
from typing import Any
import datetime

from src.knowledge_base.base_parser import BaseParser


class CsvParser(BaseParser):
  """Parser specifico per l'estrazione e la normalizzazione di documenti da file CSV.

  Eredita da BaseParser e implementa la logica per convertire un foglio elettronico
  strutturato (CSV) in un formato testuale rappresentabile all'interno di un Document.
  """

  def parse_file(self, file_path: Path) -> dict[str, Any]:
    """Analizza un file CSV, ne estrae il contenuto strutturato e restituisce un dizionario con i dati.

    Args:
        file_path (Path): Il percorso del file CSV da analizzare.

    Raises:
        FileNotFoundError: Se il file non esiste o il percorso non è valido.
        ValueError: Se il file non ha dati validi, se mancano campi obbligatori
                    o se il contenuto finale risulta vuoto.

    Returns:
        dict[str, Any]: Un dizionario contenente:
            - 'title' (str): Nome del file senza estensione.
            - 'content' (str): Contenuto testuale normalizzato in righe del tipo 'chiave: valore'.
            - 'source_format' (str): Costante 'csv'.
            - 'date' (str): Data di ultima modifica del file sorgente.
            - 'source_filename' (str): Nome originale del file con estensione.
            - 'metadata' (dict): Metadati tecnici come numero di righe, colonne,
              delimitatore rilevato ed eventuali righe con valori in eccesso ('extra_values').
    """
    # title, content, date e source_format sono valori obbligatori. Se uno solo di questi è vuoto, viene sollevata una eccezione.
    if not file_path.exists() or not file_path.is_file():
      raise FileNotFoundError(f"File non valido o inesistente: {file_path}")

    # title contiene il nome del file senza estensione
    title = file_path.stem
    if not title:
      raise ValueError("Il titolo (title) è vuoto.")

    # source_filename è il nome del file, inclusa l'estensione
    source_filename = file_path.name

    # source_format sarà "csv"
    source_format = "csv"

    # date è la data di ultima modifica del file
    try:
      mtime = file_path.stat().st_mtime
      date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
      date = ""

    if not date:
      raise ValueError("La data (date) è vuota.")

    # Leggi il file CSV per estrarre il contenuto e le informazioni tecniche (metadata)
    content_lines = []
    num_rows = 0
    num_cols = 0
    delimiter = ","
    extra_values_map = {}

    with file_path.open("r", encoding="utf-8-sig") as csv_file:
      # Cerca di rilevare il delimitatore automaticamente
      try:
        sample = csv_file.read(2048)
        dialect = csv.Sniffer().sniff(sample)
        delimiter = dialect.delimiter
        csv_file.seek(0)
      except Exception:
        csv_file.seek(0)

      reader = csv.reader(csv_file, delimiter=delimiter)
      rows = list(reader)

      if rows:
        # Gestione intestazioni vuote -> Rinomina automaticamente column_1, column_2 ecc.
        headers = []
        for i, h in enumerate(rows[0]):
          clean_h = h.strip()
          if not clean_h:
            headers.append(f"column_{i+1}")
          else:
            headers.append(clean_h)

        num_cols = len(headers)

        content_lines.append(f"Colonne: {', '.join(headers)}")
        content_lines.append("")

        for row_idx, row in enumerate(rows[1:], start=1):
          # Celle contenente solo spazi -> usa .strip()
          cleaned_row = [value.strip() for value in row]

          # Controllo riga vuota: se tutti gli elementi sono vuoti (o la riga stessa è vuota), viene ignorata
          if not cleaned_row or all(val == "" for val in cleaned_row):
            continue

          num_rows += 1
          row_parts = []

          # Se una riga ha più valori delle colonne -> mettili in un dizionario extra_values
          if len(cleaned_row) > num_cols:
            extra = cleaned_row[num_cols:]
            extra_values_map[row_idx] = extra
            usable_row = cleaned_row[:num_cols]
          else:
            usable_row = cleaned_row

          for col_idx, value in enumerate(usable_row):
            if col_idx < len(headers):
              row_parts.append(f"{headers[col_idx]}: {value}")
          content_lines.append(" | ".join(row_parts))
      else:
        raise ValueError("Il file CSV è vuoto o non contiene dati validi.")

    # content contiene l'intera tabella in formato testuale
    content = "\n".join(content_lines)
    if not content.strip():
      raise ValueError("Il contenuto (content) è vuoto.")

    # metadata è un dizionario contenente informazioni tecniche ed extra_values se presenti
    metadata = {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "delimiter": delimiter
    }
    if extra_values_map:
      metadata["extra_values"] = extra_values_map

    # Il dizionario prodotto sarà del tipo str, Any
    result = {
        "title": title,
        "content": content,
        "source_format": source_format,
        "date": date,
        "source_filename": source_filename,
        "metadata": metadata
    }

    return result