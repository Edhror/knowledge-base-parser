from pathlib import Path
from src.knowledge_base.knowledge_base_index import KnowledgeBaseIndex


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
        "\033[1;35m3.\033[0m Esporta la knowledge base in JSON\n"
        "\033[1;35m4.\033[0m Carica una knowledge base esistente (JSON)\n"
        "\033[1;35m5.\033[0m Esci dall'applicazione\n"
    )
    print(menu)

print_intro()

while True:
    choice = input("Seleziona un'opzione (1, 2 o 3): ")
    if choice == "1":
        print("Hai scelto di creare una nuova knowledge base.")
        kb = KnowledgeBaseIndex()
        try:
            kb.get_docs_from_parsing(Path("data/input"))
        except NotADirectoryError as e:
            print(f"\033[1;31mErrore durante il parsing: {e}\033[0m")
            continue
        break
    elif choice == "2":
        print("Hai scelto di caricare una knowledge base esistente.")
        kb = KnowledgeBaseIndex()
        try:
            kb.load_json_index(Path("data/load/knowledge_base.json"))
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print(f"\033[1;31mErrore durante il caricamento: {e}\033[0m")
            continue
        break
    elif choice == "3":
        print("Uscita dall'applicazione. Arrivederci!")
        exit(0)
    else:
        print("Scelta non valida. Per favore, seleziona 1, 2 o 3.")

print_menu()

while True:
    choice = input("Seleziona un'opzione (1, 2, 3, 4 o 5): ")
    if choice == "1":
        print("Hai scelto di visualizzare le statistiche della knowledge base.")
        stats = kb.get_statistics()
        print(f"\033[1;32mStatistiche della knowledge base:\033[0m")
        for key, value in stats.items():
            print(f"- {key}: {value}")
    elif choice == "2":
        print("Hai scelto di cercare documenti per parola chiave.")
        keyword = input("Inserisci la parola chiave da cercare: ")
        results = kb.search_documents(keyword)
        if results:
            print(f"\033[1;32mTrovati {len(results)} documenti contenenti la parola chiave '{keyword}':\033[0m")
            for doc in results:
                print(f"- {doc.title} (ID: {doc.document_id})")
        else:
            print(f"\033[1;31mNessun documento trovato contenente la parola chiave '{keyword}'.\033[0m")
    elif choice == "3":
        print("Hai scelto di esportare la knowledge base in JSON.")
        output_path = Path("data/output/knowledge_base_export.json")
        try:
            kb.create_json_index(output_path)
            print(f"\033[1;32mKnowledge base esportata con successo in {output_path}.\033[0m")
        except Exception as e:
            print(f"\033[1;31mErrore durante l'esportazione: {e}\033[0m")
    elif choice == "4":
        print("Hai scelto di caricare una knowledge base esistente.")
        try:
            kb.load_json_index(Path("data/load/knowledge_base.json"))
            print("\033[1;32mKnowledge base caricata con successo.\033[0m")
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print(f"\033[1;31mErrore durante il caricamento: {e}\033[0m")
    elif choice == "5":
        print("Uscita dall'applicazione. Arrivederci!")
        exit(0)
    else:
        print("Scelta non valida. Per favore, seleziona un'opzione tra 1 e 5.")

