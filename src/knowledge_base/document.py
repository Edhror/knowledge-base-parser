from typing import Any


class Document:
  """Questa classe rappresenta un generico documento normalizzato.

  Attributes:
    document_id (str): Identificativo unico del documento.
    title (str): Titolo del documento.
    content (str): Contenuto testuale del documento.
    source_format (str): Formato della sorgente da cui proviene il documento (es. 'PDF', 'HTML', 'Markdown').
    source_filename (str, optional): Nome del file originale da cui è stato estratto il documento. Defaults to None.
    date (str): Data di creazione o modifica del documento.
    metadata (dict, optional): Dizionario per metadati aggiuntivi. Defaults to {}.
    word_count (int, optional): Numero di parole nel contenuto del documento. Viene calcolato automaticamente. Defaults to 0.
    excerpt (str, optional): Breve estratto del contenuto del documento. Vengono presi i primi 100 caratteri.
  """
  def __init__(self, document_id: str, title: str, content: str, source_format: str, date, source_filename: str = None, metadata: dict = None):
    """Inizializza una nuova istanza della classe Document.

    Args:
      document_id (str): Identificativo unico del documento.
      title (str): Titolo del documento.
      content (str): Contenuto testuale del documento.
      source_format (str): Formato della sorgente del documento.
      date (str): Data di creazione o modifica del documento.
      source_filename (str, optional): Nome del file originale. Defaults to None.
      metadata (dict, optional): Dizionario di metadati aggiuntivi. Defaults to {}.
    """
    # Attributi obbligatori

    self.document_id = document_id
    self.title = title
    self.content = content
    self.source_format = source_format
    self.date = date

    # Attributi opzionali
    self.source_filename = source_filename
    self.metadata = metadata if metadata is not None else {}

    # Attributi derivati e calcolati alla creazione
    self.word_count = len(content.split()) if content else 0
    self.excerpt = content[:100] + '...' if content and len(content) > 100 else content

  def to_dict(self):
    """
    Converte l'istanza della classe Document in un dizionario.

    Returns:
      dict: Dizionario che rappresenta l'istanza della classe Document.
    """
    return {
        "document_id": self.document_id,
        "title": self.title,
        "content": self.content,
        "source_format": self.source_format,
        "date": self.date,
        "source_filename": self.source_filename,
        "metadata": self.metadata,
        "word_count": self.word_count,
        "excerpt": self.excerpt
    }

  def from_dict(self, data: dict[str, Any]) -> "Document":
    """
    Crea un'istanza di Document a partire dai dati dell'indice della knowledge base.

    Args:
      data (dict[str, Any]): Dizionario contenente i dati del documento.

    Returns:
      Document: Istanza del documento ricostruita dal dizionario.
    """
    document_id = data["document_id"]
    title = data["title"]
    content = data["content"]
    source_format = data["source_format"]
    date = data["date"]
    source_filename = data["source_filename"]
    metadata = data["metadata"]
    return Document(document_id, title, content, source_format, date, source_filename, metadata)