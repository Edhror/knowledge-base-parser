from pathlib import Path
from src.knowledge_base.document import Document
import json


class KnowledgeBaseIndex:

    def __init__(self, documents: list[Document]):
        """Inizializza l'indice della knowledge base con una lista di oggetti Document.

        Args:
          documents (list[Document]): Una lista di oggetti Document da indicizzare.
        """
        self.documents = documents

    def add_document(self, document: Document):
        """Aggiunge un oggetto Document all'indice della knowledge base.

        Args:
          document (Document): L'oggetto Document da aggiungere.
        """
        if not any(doc.document_id == document.document_id for doc in self.documents):
            self.documents.append(document)
        else:
            while True:
                choice = input(
                    f"Documento con ID '{document.document_id}' già presente. "
                    "Il vecchio documento verrà cancellato. "
                    "Vuoi sostituirlo con quello nuovo? (Y/n): "
                ).strip().lower()
                if choice == "y":
                    self.documents = [
                        doc for doc in self.documents
                        if doc.document_id != document.document_id
                    ]
                    self.documents.append(document)
                    break
                if choice == "n":
                    print("Documento non aggiunto.")
                    break

    def remove_document(self, document_id: str):
        """Rimuove un oggetto Document dall'indice della knowledge base in base al suo ID.

        Args:
          document_id (str): L'ID del documento da rimuovere.
        """
        if not any(doc.document_id == document_id for doc in self.documents):
            print(f"Nessun documento trovato con ID '{document_id}'.")
            return

        self.documents = [doc for doc in self.documents if doc.document_id != document_id]

    def get_document_by_id(self, document_id: str) -> Document:
        """Recupera un oggetto Document dall'indice della knowledge base in base al suo ID.

        Args:
          document_id (str): L'ID del documento da recuperare.

        Returns:
          Document: L'oggetto Document corrispondente all'ID, se presente. Altrimenti, None.
        """
        for doc in self.documents:
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
            doc for doc in self.documents
            if query_lower in doc.title.lower() or query_lower in doc.content.lower()
        ]
        return results

    def get_statistics(self) -> dict:
        """Restituisce statistiche sull'indice della knowledge base.

        Returns:
          dict: Un dizionario contenente statistiche come il numero totale di documenti, la lunghezza media dei contenuti e altre informazioni utili.
        """
        total_documents = len(self.documents)
        total_word_count = sum(doc.word_count for doc in self.documents)
        average_word_count = total_word_count / total_documents if total_documents > 0 else 0

        return {
            "total_documents": total_documents,
            "total_word_count": total_word_count,
            "average_word_count": average_word_count
        }

    def create_json_index(self, documents: list[Document], output_path: Path):
        """Crea un indice JSON da una lista di oggetti Document.

        Args:
          documents (list[Document]): Una lista di oggetti Document da indicizzare.
          output_path (Path): Il percorso del file di output JSON.
        """
        documents_data = [document.to_dict() for document in documents]

        with output_path.open("w", encoding="utf-8") as json_file:
            json.dump(documents_data, json_file, indent=4, ensure_ascii=False)

    def load_json_index(self, input_path: Path):
        """Carica un indice JSON da un file e popola la lista di oggetti Document.

        Args:
          input_path (Path): Il percorso del file di input JSON.
        """
        with input_path.open("r", encoding="utf-8") as json_file:
            documents_data = json.load(json_file)

        self.documents = [Document.from_dict(doc_data) for doc_data in documents_data]
