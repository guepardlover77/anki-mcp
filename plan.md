# Plan: Serveur MCP Python pour Anki

## Objectif
Créer un serveur MCP Python complet pour gérer Anki depuis Claude, avec génération automatique de flashcards.

## Choix techniques
- **Langage**: Python 3.11+
- **Framework MCP**: FastMCP (développement rapide)
- **Client HTTP**: httpx (async)
- **Validation**: Pydantic
- **Bridge Anki**: AnkiConnect (add-on requis)

---

## Structure du projet

```
anki-mcp-server/
├── pyproject.toml
├── README.md
├── .env.example
├── src/anki_mcp/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   ├── server.py                # FastMCP setup
│   ├── config.py                # Settings
│   ├── client/                  # AnkiConnect client
│   │   ├── base.py              # HTTP client async
│   │   ├── actions.py           # API wrappers
│   │   └── models.py            # Pydantic models
│   ├── tools/                   # MCP Tools (55 total)
│   │   ├── deck.py              # 5 outils
│   │   ├── note.py              # 8 outils
│   │   ├── card.py              # 6 outils
│   │   ├── review.py            # 6 outils
│   │   ├── statistics.py        # 7 outils
│   │   ├── import_export.py     # 6 outils
│   │   ├── media.py             # 4 outils
│   │   ├── model.py             # 4 outils
│   │   ├── generation.py        # 6 outils (PRIORITÉ)
│   │   └── sync.py              # 3 outils
│   ├── resources/               # MCP Resources (12)
│   ├── prompts/                 # MCP Prompts (14)
│   ├── generators/              # Auto-génération
│   │   ├── text.py
│   │   ├── pdf.py
│   │   ├── web.py
│   │   └── markdown.py
│   └── utils/
└── tests/
```

---

## Fonctionnalités clés

### Outils MCP (55 total)

| Catégorie | Outils | Priorité |
|-----------|--------|----------|
| **Génération auto** | generate_cards_from_text, generate_cards_from_pdf, generate_cards_from_webpage, generate_cloze_deletions, improve_existing_cards, generate_related_cards | HAUTE |
| **CRUD Notes** | add_note, add_notes_batch, update_note, delete_notes, find_notes, get_note_info, add_tags, remove_tags | HAUTE |
| **CRUD Decks** | list_decks, create_deck, delete_deck, rename_deck, get_deck_config | HAUTE |
| **Review** | get_due_cards, start_review_session, present_card, answer_card, show_answer, get_review_suggestion | MOYENNE |
| **Stats** | get_collection_stats, get_deck_stats, get_reviews_today, predict_workload, analyze_retention | MOYENNE |
| **Import/Export** | import_markdown, import_csv, import_obsidian_notes, export_deck_to_markdown/csv/json | MOYENNE |

### Resources MCP (12)
- `anki://decks`, `anki://decks/{name}`, `anki://decks/{name}/due`
- `anki://models`, `anki://models/{name}`
- `anki://notes/{id}`, `anki://cards/{id}`
- `anki://stats/today`, `anki://stats/collection`, `anki://stats/forecast`
- `anki://tags`, `anki://current-card`

### Prompts MCP (14)
- Génération: `generate_basic_cards`, `generate_cloze_cards`, `twenty_rules`
- Review: `explain_card`, `rate_difficulty`, `generate_mnemonics`
- Analyse: `analyze_weak_areas`, `suggest_study_plan`

---

## Phases d'implémentation

### Phase 1: Foundation (Semaine 1-2)
- [ ] Setup projet (pyproject.toml, structure)
- [ ] Client AnkiConnect async (httpx)
- [ ] Serveur FastMCP de base
- [ ] Outils deck (5): list, create, delete, rename, config
- [ ] Outils note (8): add, batch, update, delete, find, info, tags
- [ ] Outils card (6): find, info, suspend, unsuspend, due, move
- [ ] Resources de base (decks, models)
- [ ] Tests unitaires

### Phase 2: Review & Stats (Semaine 3)
- [ ] Outils review (6): due, session, present, answer, show, suggest
- [ ] Outils stats (7): collection, deck, today, history, predict, retention, insights
- [ ] Resources stats
- [ ] Prompts review

### Phase 3: Import/Export (Semaine 4)
- [ ] Import Markdown (Q&A, cloze, headers)
- [ ] Import CSV avec mapping
- [ ] Import Obsidian (liens, tags)
- [ ] Export Markdown/CSV/JSON
- [ ] Gestion média

### Phase 4: Auto-génération (Semaine 5-6) - PRIORITÉ
- [ ] Framework génération texte
- [ ] Extraction PDF (pymupdf)
- [ ] Extraction web (beautifulsoup)
- [ ] Détection cloze automatique
- [ ] Amélioration cartes existantes
- [ ] Prompts "20 rules"

### Phase 5: Production (Semaine 7-8)
- [ ] Error handling complet
- [ ] Tests >80% coverage
- [ ] Documentation
- [ ] Package PyPI
- [ ] Guide Claude Desktop

---

## Dépendances

```toml
[project]
dependencies = [
    "mcp>=1.2.0",
    "httpx>=0.27.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "rich>=13.0",
]

[project.optional-dependencies]
pdf = ["pymupdf>=1.24"]
web = ["beautifulsoup4>=4.12", "lxml>=5.0"]
```

---

## Configuration Claude Desktop

```json
{
  "mcpServers": {
    "anki": {
      "command": "python",
      "args": ["-m", "anki_mcp"],
      "env": {
        "ANKI_MCP_PORT": "8765"
      }
    }
  }
}
```

---

## Prérequis
1. Anki installé et lancé
2. Add-on AnkiConnect installé (code: 2055492159)
3. Python 3.11+

---

## Fichiers à créer (ordre)

1. `pyproject.toml` - Config projet
2. `src/anki_mcp/__init__.py` - Package init
3. `src/anki_mcp/config.py` - Settings Pydantic
4. `src/anki_mcp/client/base.py` - Client HTTP async
5. `src/anki_mcp/client/actions.py` - Wrappers AnkiConnect
6. `src/anki_mcp/server.py` - FastMCP setup
7. `src/anki_mcp/tools/deck.py` - Premier groupe d'outils
8. `src/anki_mcp/__main__.py` - Entry point
