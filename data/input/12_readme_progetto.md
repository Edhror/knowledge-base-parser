# Fatturazione Facile

Piccola libreria Python per generare **fatture elettroniche** in formato XML.

[![Build](https://img.shields.io/badge/build-passing-green.svg)](https://example.com)

## Installazione

```bash
pip install fatturazione-facile
```

## Utilizzo rapido

```python
from fatturazione import Fattura

f = Fattura(numero="2026/001", cliente="Rossi S.r.l.")
f.aggiungi_riga("Consulenza", quantita=10, prezzo=85.0)
print(f.totale())  # 850.0
```

## Opzioni di configurazione

| Opzione      | Tipo   | Default | Descrizione                    |
|--------------|--------|---------|--------------------------------|
| `iva`        | float  | `0.22`  | Aliquota IVA                   |
| `valuta`     | str    | `EUR`   | Codice valuta ISO 4217         |
| `arrotonda`  | bool   | `true`  | Arrotonda al centesimo         |

## Roadmap

- [x] Generazione XML base
- [x] Calcolo IVA
- [ ] Firma digitale
- [ ] Invio al Sistema di Interscambio

## Licenza

Distribuito con licenza MIT. Vedi [LICENSE](./LICENSE).
