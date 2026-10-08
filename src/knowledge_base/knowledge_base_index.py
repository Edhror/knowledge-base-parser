import csv
import json
from pathlib import Path
from src.knowledge_base.document import Document
from src.knowledge_base.parsers.csv_parser import CsvParser
from src.knowledge_base.parsers.md_parser import MdParser
from src.knowledge_base.parsers.txt_parser import TxtParser


class KnowledgeBaseIndex:
    """Indice della knowledge base.

    I documenti possono essere ottenuti soltanto tramite ``get_docs_from_parsing``
    (parsing della cartella di input) o ``load_json_index`` (caricamento da JSON)
    e sono accessibili in sola lettura tramite la property ``documents``.
    """

    def __init__(self):
        """Inizializza un indice vuoto della knowledge base."""
        self._documents: list[Document] = []

    @property
    def documents(self) -> list[Document]:
        """list[Document]: Copia della lista dei documenti indicizzati (sola lettura).

        Modificare la lista restituita non altera lo stato dell'indice.
        """
        return list(self._documents)

    def get_document_by_id(self, document_id: str) -> Document | None:
        """Recupera un oggetto Document dall'indice della knowledge base in base al suo ID.

        Args:
          document_id (str): L'ID del documento da recuperare.

        Returns:
          Document: L'oggetto Document corrispondente all'ID, se presente. Altrimenti, None.
        """
        for doc in self._documents:
            if doc.document_id == document_id:
                return doc
        return None

    def search_documents(self, query: str) -> list[Document]:
        """Cerca documenti nell'indice della knowledge base in base a una query.

        Args:
          query (str): La query di ricerca.

        Returns:
          list[Document]: Una lista di oggetti Document con titolo o contenuto corrispondenti alla query.
        """
        query_lower = query.lower()
        results = [
            doc for doc in self._documents
            if query_lower in doc.title.lower() or query_lower in doc.content.lower()
        ]
        return results

    def get_statistics(self) -> dict:
        """Restituisce statistiche sull'indice della knowledge base.

        Returns:
          dict: Un dizionario contenente statistiche come il numero totale di documenti, la lunghezza media dei contenuti e altre informazioni utili.
        """
        total_documents = len(self._documents)
        total_word_count = sum(doc.word_count for doc in self._documents)
        average_word_count = total_word_count / total_documents if total_documents > 0 else 0

        return {
            "total_documents": total_documents,
            "total_word_count": total_word_count,
            "average_word_count": average_word_count
        }

    def create_json_index(self, output_path: Path) -> Path:
        """Salva i documenti dell'indice in un file JSON.

        La serializzazione avviene prima della scrittura e il file viene scritto
        su un file temporaneo poi rinominato: in caso di errore un eventuale
        file JSON già esistente non viene corrotto.

        Args:
          output_path (Path): Il percorso del file di output JSON (estensione ``.json``).
            Le cartelle mancanti vengono create automaticamente.

        Returns:
          Path: Il percorso del file JSON creato.

        Raises:
          ValueError: Se l'indice è vuoto, se il percorso non ha estensione ``.json``
            o se i documenti contengono dati non serializzabili in JSON.
          IsADirectoryError: Se il percorso indicato è una cartella.
          PermissionError: Se non si hanno i permessi di scrittura.
          OSError: Per altri errori del file system durante la scrittura.
        """
        if not self._documents:
            raise ValueError("L'indice è vuoto: nessun documento da salvare.")
        if output_path.is_dir():
            raise IsADirectoryError(f"Il percorso indicato è una cartella, non un file: {output_path}")
        if output_path.suffix.lower() != ".json":
            raise ValueError(f"Il file di output deve avere estensione .json: {output_path}")

        try:
            json_data = json.dumps(
                [document.to_dict() for document in self._documents],
                indent=4,
                ensure_ascii=False,
            )
        except (TypeError, ValueError) as e:
            raise ValueError(f"Impossibile serializzare i documenti in JSON: {e}") from e

        tmp_path = output_path.with_name(output_path.name + ".tmp")
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path.write_text(json_data, encoding="utf-8")
            tmp_path.replace(output_path)
        except PermissionError as e:
            raise PermissionError(f"Permessi insufficienti per scrivere '{output_path}': {e}") from e
        except OSError as e:
            raise OSError(f"Errore durante la scrittura di '{output_path}': {e}") from e
        finally:
            tmp_path.unlink(missing_ok=True)

        print(f"Indice JSON salvato in '{output_path}' ({len(self._documents)} documenti).")
        return output_path

    def load_json_index(self, input_path: Path):
        """Carica un indice JSON da un file e popola la lista di oggetti Document.

        L'indice corrente viene sostituito solo se il caricamento va a buon fine:
        in caso di errore i documenti già presenti restano invariati.

        Args:
          input_path (Path): Il percorso del file di input JSON.

        Raises:
          FileNotFoundError: Se il file non esiste o non è un file regolare.
          PermissionError: Se non si hanno i permessi di lettura sul file.
          ValueError: Se il file non è un JSON valido, non è codificato in UTF-8
            o se la sua struttura non corrisponde a una lista di documenti validi.
        """
        if not input_path.is_file():
            raise FileNotFoundError(f"File JSON non trovato: {input_path}")

        try:
            with input_path.open("r", encoding="utf-8") as json_file:
                documents_data = json.load(json_file)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"JSON non valido in '{input_path}' (riga {e.lineno}, colonna {e.colno}): {e.msg}"
            ) from e
        except UnicodeDecodeError as e:
            raise ValueError(f"Il file '{input_path}' non è codificato in UTF-8.") from e

        if not isinstance(documents_data, list):
            raise ValueError(
                f"Formato non valido: attesa una lista di documenti, trovato '{type(documents_data).__name__}'."
            )

        documents = []
        for i, doc_data in enumerate(documents_data):
            if not isinstance(doc_data, dict):
                raise ValueError(f"Documento #{i} non valido: atteso un oggetto JSON.")
            try:
                documents.append(Document.from_dict(doc_data))
            except KeyError as e:
                raise ValueError(f"Documento #{i}: campo obbligatorio mancante {e}.") from e
            except (TypeError, AttributeError) as e:
                raise ValueError(f"Documento #{i}: valori non validi ({e}).") from e

        self._documents = documents
        print(f"Indice JSON caricato con successo ({len(documents)} documenti).")

    def get_docs_from_parsing(self, input_path: Path, output_path: Path = Path("data/output")) -> list[Document]:
        """Legge i documenti supportati presenti nella cartella indicata e popola l'indice.

        Per ogni file della cartella viene scelto il parser in base all'estensione
        (.txt, .md, .csv); il dizionario restituito viene convertito in Document.
        I file con estensione non ammessa o che generano errori durante il parsing
        vengono saltati e registrati nel file ``log_error.txt`` della cartella di output,
        nel formato ``nome_file.estensione = messaggio di errore``.

        Args:
          input_path (Path): Cartella contenente i file da analizzare.
          output_path (Path, optional): Cartella in cui scrivere ``log_error.txt``.
            Defaults to ``data/output``.

        Returns:
          list[Document]: I documenti analizzati con successo (salvati anche nell'indice).

        Raises:
          NotADirectoryError: Se la cartella di input non esiste o non è una cartella.
        """
        if not input_path.is_dir():
            raise NotADirectoryError(f"La cartella di input non esiste: {input_path}")

        parsers = {
            ".txt": TxtParser(),
            ".md": MdParser(),
            ".csv": CsvParser(),
        }
        documents: list[Document] = []
        errors: dict[str, str] = {}

        for file_path in sorted(input_path.iterdir()):
            if not file_path.is_file():
                continue

            parser = parsers.get(file_path.suffix.lower())
            if parser is None:
                errors[file_path.name] = (
                    f"Estensione '{file_path.suffix or '(nessuna)'}' non ammessa. "
                    f"Estensioni supportate: {', '.join(parsers)}"
                )
                continue

            try:
                documents.append(Document.from_dict(parser.parse_file(file_path)))
            except UnicodeDecodeError:
                errors[file_path.name] = "Il file non è codificato in UTF-8."
            except KeyError as e:
                errors[file_path.name] = f"Campo obbligatorio mancante {e}."
            except (OSError, ValueError, csv.Error) as e:
                errors[file_path.name] = str(e)
            except Exception as e:
                errors[file_path.name] = f"Errore imprevisto ({type(e).__name__}): {e}"

        self._documents = documents

        try:
            output_path.mkdir(parents=True, exist_ok=True)
            log_file = output_path / "log_error.txt"
            with log_file.open("w", encoding="utf-8") as log:
                for filename, message in errors.items():
                    log.write(f"{filename} = {message}\n")
        except OSError as e:
            print(f"Impossibile scrivere il file di log in '{output_path}': {e}")

        print(
            f"Parsing completato: {len(documents)} documenti caricati, "
            f"{len(errors)} file non parsati (vedi {output_path / 'log_error.txt'})."
        )
        return documents

