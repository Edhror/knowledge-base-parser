import datetime
from pathlib import Path
from typing import Any

from src.knowledge_base.base_parser import BaseParser


class MdParser(BaseParser):
    def parse_file(self, file_path: Path) -> dict[str, Any]:
        # usando il file_path, apre un file .md
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"File non valido o inesistente: {file_path}")

        with file_path.open("r", encoding="utf-8") as md_file:
            lines = md_file.readlines()

        # content: intero testo del file Markdown
        content = "".join(lines)

        # Parsing dei titoli per trovare il primo H1 e calcolare i metadati
        title = None
        num_titles = 0
        title_levels = {}

        for line in lines:
            stripped_line = line.strip()
            if stripped_line.startswith("#"):
                level = len(stripped_line) - len(stripped_line.lstrip('#'))
                if level > 0 and stripped_line[level:].startswith(" "):
                    num_titles += 1
                    level_name = f"H{level}"
                    title_levels[level_name] = title_levels.get(level_name, 0) + 1

                    if level == 1 and title is None:
                        title = stripped_line[1:].strip()

        # Se non è stato trovato alcun titolo di livello 1, facciamo il fallback
        if not title:
            title = file_path.stem

        source_format = "markdown"

        source_filename = file_path.name

        try:
            mtime = file_path.stat().st_mtime
            date = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            date = ""

        metadata = {
            "num_lines": len(lines),
            "num_titles": num_titles,
            "title_levels": title_levels
        }

        if not content.strip():
            raise ValueError("Errore di parsing: il contenuto del file è vuoto.")
        if not date:
            raise ValueError("Errore di parsing: non è stato possibile determinare la data di ultima modifica del file.")

        # crea un dizionario contenente gli elementi richiesti
        return {
            "title": title,
            "content": content,
            "source_format": source_format,
            "source_filename": source_filename,
            "date": date,
            "metadata": metadata
        }