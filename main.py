import os
import sys
from pathlib import Path
from src.knowledge_base.knowledge_base_index import KnowledgeBaseIndex

# Con questi percorsi assoluti, main.py può essere lanciato da qualsiasi cartella senza problemi.
# La cartella dati può essere sovrascritta con la variabile d'ambiente KB_DATA_DIR, così da poter utilizzare una directory personalizzata.
ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("KB_DATA_DIR", ROOT_DIR / "data"))
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
LOAD_FILE = DATA_DIR / "load" / "knowledge_base.json"
EXPORT_FILE = OUTPUT_DIR / "knowledge_base.json"

RED, GREEN = "\033[1;31m", "\033[1;32m"
RESET = "\033[0m"


def print_intro():
    title = " KnowledgeBase Builder - Benvenuto! "
    border = "=" * len(title)
    print(f"\033[1;34m{border}\033[0m")
    print(f"\033[1;32m{title}\033[0m")
    print(f"\033[1;34m{border}\033[0m")

    description = (
        "Questa applicazione ti permette di creare e gestire una knowledge base.\n"
        "Puoi creare la knowledge base dai documenti della cartella di input o caricarne una in formato JSON.\n"
        "Puoi cercare documenti e visualizzare statistiche sui contenuti.\n"
        "Sfrutta le funzionalità avanzate per organizzare le informazioni in modo efficiente!"
    )
    print(f"\033[1;33m{description}\033[0m")

    menu = (
        "\n\033[1;36m=== Menu Principale ===\033[0m\n"
        "\033[1;35m1.\033[0m Crea una nuova knowledge base\n"
        "\033[1;35m2.\033[0m Carica una knowledge base esistente (JSON)\n"
        "\033[1;35m3.\033[0m Esci dall'applicazione\n"
    )
    print(menu)


def print_menu():
    menu = (
        "\n\033[1;36m=== Menu Principale ===\033[0m\n"
        "\033[1;35m1.\033[0m Visualizza statistiche della knowledge base\n"
        "\033[1;35m2.\033[0m Cerca documenti per parola chiave\n"
        "\033[1;35m3.\033[0m Filtra per estensione\n"
        "\033[1;35m4.\033[0m Esporta la knowledge base in JSON\n"
        "\033[1;35m5.\033[0m Carica una knowledge base esistente (JSON)\n"
        "\033[1;35m6.\033[0m Esci dall'applicazione\n"
    )
    print(menu)


def json_to_load() -> Path:
    """Restituisce il JSON da caricare: quello in data/load se presente,
    altrimenti l'ultimo export in data/output."""
    if LOAD_FILE.is_file() or not EXPORT_FILE.is_file():
        return LOAD_FILE
    return EXPORT_FILE


def load_kb(kb: KnowledgeBaseIndex) -> bool:
    """Carica la knowledge base da JSON. Restituisce True se il caricamento riesce."""
    try:
        kb.load_json_index(json_to_load())
        return True
    except (FileNotFoundError, PermissionError, ValueError) as e:
        print(f"{RED}Errore durante il caricamento: {e}{RESET}")
        return False


def choose_initial_kb() -> KnowledgeBaseIndex:
    """Primo menu: crea la knowledge base dal parsing o la carica da JSON."""
    while True:
        choice = input("Seleziona un'opzione (1, 2 o 3): ").strip()
        kb = KnowledgeBaseIndex()
        if choice == "1":
            print("Hai scelto di creare una nuova knowledge base.")
            try:
                kb.get_docs_from_parsing(INPUT_DIR, OUTPUT_DIR)
                return kb
            except NotADirectoryError as e:
                print(f"{RED}Errore durante il parsing: {e}{RESET}")
        elif choice == "2":
            print("Hai scelto di caricare una knowledge base esistente.")
            if load_kb(kb):
                return kb
        elif choice == "3":
            print("Uscita dall'applicazione. Arrivederci!")
            sys.exit(0)
        else:
            print("Scelta non valida. Per favore, seleziona 1, 2 o 3.")


def main_menu(kb: KnowledgeBaseIndex):
    """Secondo menu: consultazione, export e ricaricamento della knowledge base."""
    while True:
        print_menu()
        choice = input("Seleziona un'opzione (1, 2, 3, 4, 5 o 6): ").strip()
        if choice == "1":
            print("Hai scelto di visualizzare le statistiche della knowledge base.")
            print(f"{GREEN}Statistiche della knowledge base:{RESET}")
            for key, value in kb.get_statistics().items():
                print(f"- {key}: {value}")
        elif choice == "2":
            print("Hai scelto di cercare documenti per parola chiave.")
            keyword = input("Inserisci la parola chiave da cercare: ").strip()
            if not keyword:
                print(f"{RED}La parola chiave non può essere vuota.{RESET}")
                continue
            results = kb.search_documents(keyword)
            if not results:
                print(f"{RED}Nessun documento trovato contenente la parola chiave '{keyword}'.{RESET}")
        elif choice == "3":
            print("Hai scelto di filtrare per estensione.")
            extension = input("Inserisci l'estensione da filtrare (txt, md, csv): ").strip().lower()
            if extension not in ["txt", "md", "csv"]:
                print(f"{RED}Estensione non valida. Per favore, inserisci txt, md o csv.{RESET}")
                continue
            results = kb.filter_by_extension(extension)
            if not results:
                print(f"{RED}Nessun documento trovato con l'estensione '{extension}'.{RESET}")
        elif choice == "4":
            print("Hai scelto di esportare la knowledge base in JSON.")
            try:
                kb.create_json_index(EXPORT_FILE)
            except (ValueError, OSError) as e:
                print(f"{RED}Errore durante l'esportazione: {e}{RESET}")
        elif choice == "5":
            print("Hai scelto di caricare una knowledge base esistente.")
            load_kb(kb)
        elif choice == "6":
            print("Uscita dall'applicazione. Arrivederci!")
            return
        else:
            print("Scelta non valida. Per favore, seleziona un'opzione tra 1 e 6.")


def main():
    print_intro()
    try:
        kb = choose_initial_kb()
        main_menu(kb)
    except (KeyboardInterrupt, EOFError):
        print("\nUscita dall'applicazione. Arrivederci!")


if __name__ == "__main__":
    main()
