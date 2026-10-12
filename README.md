# KnowledgeBase Builder

KnowledgeBase Builder è un'applicazione Python progettata per scansionare, analizzare e normalizzare una cartella di documenti eterogenei in una knowledge base strutturata.
I documenti supportati includono:
- Markdown (.md)
- Text (.txt)
- CSV (.csv)

La knowledge base risultante potrà essere analizzata e interrogata tramite menu testuale e sarà esportabile in formato JSON. Tale file JSON potrà essere successivamente importato da KnowledgeBase Builder per ulteriori analisi.

## Funzionalità principali
- Parsing di file `.txt`, `.md` e `.csv`
- Normalizzazione dei dati in un formato comune
- Generazione di identificativi univoci per i documenti
- Calcolo automatico del numero di parole e di un estratto testuale
- Conversione di ogni file in un oggetto `Document`
- Gestione di una collezione di oggetti `Document`, che compongono la knowledge base
- Ricerca case-insensitive in titolo e contenuto
- Statistiche sull'indice: numero di documenti, parole totali e media di parole per documento
- Esportazione dell'indice in formato JSON
- Caricamento e ricostruzione dell'indice da file JSON
- Gestione di file non validi, contenuti vuoti, documenti duplicati e formati non supportati
- Registrazione degli errori di parsing nel file `log_error.txt`

## Architettura del progetto
Il progetto è strutturato in moduli Python, ognuno con responsabilità specifiche seguendo la logica del paradigma object-oriented.
È stata creata una classe base `BaseParser` da cui ereditano i parser specifici per ciascun formato di file. Questa struttura consente di aggiungere facilmente nuovi parser per formati di file futuri senza modificare il codice esistente.

```text
knowledge-base-parser/
├── main.py
├── requirements.txt
├── data/
│   ├── input/
│   ├── load/
│   └── output/
├── src/
│   └── knowledge_base/
│       ├── parsers/
│       │   ├── base_parser.py
│       │   ├── txt_parser.py
│       │   ├── md_parser.py
│       │   └── csv_parser.py
│       ├── document.py
│       └── knowledge_base_index.py
└── tests/
    ├── fixtures/
    └── test_*.py
```

## Flusso di esecuzione
Il flusso principale di esecuzione è gestito dal file `main.py`, che coordina l'interazione con l'utente e l'elaborazione dei documenti tramite due menu testuali, fornendo feedback e report sugli errori riscontrati.

**Menu iniziale**
1. Crea una nuova knowledge base (parsing della cartella di input)
2. Carica una knowledge base esistente (JSON)
3. Esci dall'applicazione

**Menu principale**
1. Visualizza statistiche della knowledge base
2. Visualizza la knowledge base: mostra l'elenco numerato di tutti i documenti, da cui scegliere quale visualizzare oppure tornare al menu principale (`0`); tornando indietro dalla visualizzazione si ritorna all'elenco. Se la knowledge base è vuota viene mostrato un avviso. Se è presente un solo documento viene visualizzato direttamente.
3. Cerca documenti per parola chiave (ricerca case-insensitive in titolo e contenuto): mostra i documenti il cui titolo o contenuto contiene la parola chiave, con lo stesso comportamento di `Visualizza la knowledge base` (visualizzazione diretta se c'è un solo risultato, elenco con possibilità di annullare se ce ne sono di più, messaggio se non ce ne sono).
4. Filtra per estensione (`txt`, `md` o `csv`, senza distinzione tra maiuscole e minuscole): mostra i documenti il cui file sorgente ha l'estensione indicata, con lo stesso comportamento di `Visualizza la knowledge base` (visualizzazione diretta se c'è un solo risultato, elenco con possibilità di annullare se ce ne sono di più, messaggio se non ce ne sono). Estensioni diverse da quelle supportate vengono rifiutate.
5. Esporta la knowledge base in JSON
6. Carica una knowledge base esistente (JSON)
7. Esci dall'applicazione

Per le opzioni 2, 3 e 4 la visualizzazione di un documento funziona così:
- **visualizzazione standard**: mostra tutti gli attributi del documento tranne `content`, con la possibilità di visualizzare il contenuto completo (`1`) o tornare indietro (`0`);
- **contenuto completo**: avvisa che il contenuto potrebbe essere molto lungo (indicando numero di caratteri e parole) e stampa l'intero attributo `content`.

Quando l'utente seleziona l'opzione di parsing, il programma scansiona la cartella di input (`data/input`, oppure `$KB_DATA_DIR/input` se è impostata la variabile d'ambiente), identifica i file supportati in base all'estensione e li passa ai parser appropriati. Ogni parser legge il contenuto del file ed estrae le informazioni rilevanti in un dizionario, che `KnowledgeBaseIndex` converte in un oggetto `Document`. Questi oggetti vengono raccolti in una collezione che rappresenta la knowledge base.

Sottocartelle e file nascosti (che iniziano con `.`) vengono ignorati. I file con estensione non supportata, quelli che generano errori durante il parsing (es. contenuto vuoto, codifica non UTF-8) e i documenti duplicati (stesso ID) vengono scartati e registrati nel file `data/output/log_error.txt`, nel formato `nome_file.ext = messaggio di errore`.

Successivamente, la knowledge base può essere analizzata per ottenere statistiche, effettuare ricerche ed essere esportata nel file `data/output/knowledge_base.json`.
L'utente può anche importare un file JSON precedentemente esportato per continuare l'analisi. Il programma carica il file `data/load/knowledge_base.json`; se questo non esiste, utilizza l'ultimo export presente in `data/output/knowledge_base.json`. Il caricamento sostituisce completamente la knowledge base corrente (i documenti non vengono uniti); in caso di errore, la knowledge base corrente resta invariata.

## Formato del documento normalizzato
Ogni documento viene normalizzato in un oggetto `Document` con i seguenti attributi:

```text
{
    "document_id": "identificativo univoco",
    "title": "titolo del documento",
    "content": "contenuto testuale normalizzato",
    "source_format": "text | markdown | csv",
    "date": "YYYY-MM-DD HH:MM:SS",
    "source_filename": "nome_file.ext",
    "metadata": {},
    "word_count": 0,
    "excerpt": "primi 100 caratteri del contenuto, seguiti da '...' se il contenuto è più lungo"
}
```

Dettagli sui campi:
- `document_id`: generato nel formato `data_titolo_formato_hash`, dove `hash` sono i primi 16 caratteri dello SHA-256 calcolato su titolo, data, formato e contenuto.
- `title`: per i file `.md` è il primo titolo di livello 1 (`# Titolo`); per i file `.txt`, `.csv` e per i Markdown senza H1 è il nome del file normalizzato (minuscolo, senza accenti, caratteri non alfanumerici sostituiti da `_`) e senza estensione.
- `content`: per `.txt` e `.md` è il testo integrale del file; per `.csv` è una riga `Colonne: ...` seguita da una riga per record nel formato `colonna: valore | colonna: valore`.
- `date`: data di ultima modifica del file sorgente.
- `metadata`: dipende dal formato:
  - `.txt`: `num_lines`, `num_characters`
  - `.md`: `num_lines`, `num_titles`, `title_levels` (es. `{"H1": 1, "H2": 3}`)
  - `.csv`: `num_rows`, `num_cols`, `delimiter` ed eventualmente `extra_values` (valori in eccesso rispetto alle colonne, indicizzati per numero di riga)

## Installazione
1. Clonare il repository:
```bash
git clone https://github.com/username/knowledge-base-parser.git
```
2. Navigare nella directory del progetto:
```bash
cd knowledge-base-parser
```
3. Eseguire il programma:
```bash
python main.py
```
Nota: il programma può essere lanciato da qualsiasi cartella, perché i percorsi sono risolti a partire dalla posizione di `main.py`. Per impostazione predefinita viene usata la cartella dati `data/` del progetto, con la seguente struttura:
- `data/input/`: documenti da analizzare
- `data/output/`: export JSON (`knowledge_base.json`) e log degli errori di parsing (`log_error.txt`)
- `data/load/`: knowledge base JSON da caricare (`knowledge_base.json`)

Per usare una cartella dati diversa, impostare la variabile d'ambiente `KB_DATA_DIR` (le sottocartelle `input`, `output` e `load` verranno cercate al suo interno):
```bash
KB_DATA_DIR=/percorso/assoluto/dati python main.py
```

## Test
I test sono scritti con `unittest` e si trovano nella cartella `tests/` (i file di esempio sono in `tests/fixtures/`). Per eseguirli dalla root del progetto:
```bash
python -m unittest discover -s tests -t .
```
In alternativa è possibile usare `pytest` (dipendenza opzionale, non inclusa nella libreria standard).

## Requisiti di sistema
- Python 3.10 o superiore
- Librerie Python standard (nessuna libreria esterna richiesta)