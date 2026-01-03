<div align="center">

# 🧠 Anki MCP Server

**Transform Claude into your AI-powered Anki assistant**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.2+-green.svg)](https://modelcontextprotocol.io/)
[![GitHub stars](https://img.shields.io/github/stars/guepardlover77/anki-mcp?style=social)](https://github.com/guepardlover77/anki-mcp/stargazers)

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Contributing](#-contributing)

</div>

---

## 🎯 What is Anki MCP?

A complete **Model Context Protocol (MCP)** server that connects **Claude AI** with **Anki**, enabling:

- 🤖 **AI-powered flashcard generation** from any text, PDF, or webpage
- 📊 **Smart review analytics** and learning insights
- 🔄 **Automatic card improvements** using spaced repetition science
- 💬 **Natural language control** of your entire Anki collection

> **MCP** allows Claude to interact directly with Anki, making spaced repetition learning effortless.

## ✨ Features

### 🎨 **55 MCP Tools** across 10 categories

| Category | Tools | What you can do |
|----------|-------|-----------------|
| **🤖 Generation** (Priority) | 6 tools | Generate cards from text, create cloze deletions, improve existing cards |
| **📝 Notes** | 8 tools | Create, update, search, and manage notes |
| **🗂️ Decks** | 5 tools | Organize your collection with deck management |
| **🃏 Cards** | 6 tools | Find, suspend, move cards with precision |
| **📈 Statistics** | 7 tools | Analyze retention, predict workload, get insights |
| **👁️ Review** | 6 tools | Smart review sessions with AI suggestions |
| **🎭 Models** | 4 tools | Manage note types and templates |
| **🎬 Media** | 4 tools | Handle images, audio, and video |
| **🔄 Sync** | 3 tools | Sync with AnkiWeb seamlessly |
| **📦 Import/Export** | 6 tools | Markdown, CSV, JSON support |

### 🎁 **Bonus Features**

- **9 MCP Resources**: Real-time access to decks, stats, and cards
- **10 Smart Prompts**: Guided workflows for card creation and review
- **Pydantic Models**: Type-safe data validation
- **Async HTTP**: Lightning-fast AnkiConnect integration
- **Unit Tests**: Reliable and tested codebase

## 🚀 Quick Start

### Prerequisites

1. **Anki** running with **AnkiConnect** add-on (code: `2055492159`)
2. **Python 3.11+**
3. **Claude Desktop**

### Install AnkiConnect

1. Open Anki → `Tools > Add-ons > Get Add-ons`
2. Enter code: `2055492159`
3. Restart Anki

## Installation

```bash
# Cloner le repository
git clone https://github.com/user/anki-mcp.git
cd anki-mcp

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -e .

# Ou avec les extras pour PDF et web
pip install -e ".[all]"
```

## Configuration Claude Desktop

Ajouter dans votre fichier de configuration Claude Desktop (`claude_desktop_config.json`):

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

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `ANKI_MCP_HOST` | Hôte AnkiConnect | `localhost` |
| `ANKI_MCP_PORT` | Port AnkiConnect | `8765` |
| `ANKI_MCP_API_KEY` | Clé API AnkiConnect (optionnel) | - |
| `ANKI_MCP_TIMEOUT` | Timeout HTTP en secondes | `30` |
| `ANKI_MCP_DEBUG` | Mode debug | `false` |

## Outils disponibles

### Decks (5 outils)
- `list_decks` - Lister tous les paquets
- `create_deck` - Créer un paquet
- `delete_deck` - Supprimer un paquet
- `rename_deck` - Renommer un paquet
- `get_deck_config` - Obtenir la configuration d'un paquet

### Notes (8 outils)
- `add_note` - Ajouter une note
- `add_notes_batch` - Ajouter plusieurs notes
- `update_note` - Modifier une note
- `delete_notes` - Supprimer des notes
- `find_notes` - Rechercher des notes
- `get_note_info` - Obtenir les détails d'une note
- `add_tags` - Ajouter des tags
- `remove_tags` - Supprimer des tags

### Cards (6 outils)
- `find_cards` - Rechercher des cartes
- `get_card_info` - Obtenir les détails d'une carte
- `suspend_cards` - Suspendre des cartes
- `unsuspend_cards` - Réactiver des cartes
- `get_due_cards` - Obtenir les cartes à réviser
- `move_cards` - Déplacer des cartes

## Resources MCP

- `anki://decks` - Liste de tous les paquets
- `anki://decks/{name}` - Détails d'un paquet
- `anki://decks/{name}/due` - Cartes à réviser d'un paquet
- `anki://models` - Liste des types de notes
- `anki://models/{name}` - Détails d'un type de note
- `anki://tags` - Liste de tous les tags
- `anki://stats/today` - Statistiques du jour
- `anki://notes/{id}` - Détails d'une note
- `anki://cards/{id}` - Détails d'une carte

## 💡 Usage Examples

### 🤖 AI-Powered Card Generation

```
You: "Generate flashcards from this article about Python decorators"

Claude will:
✓ Extract key concepts
✓ Create Q&A pairs
✓ Add to your chosen deck
✓ Apply best practices automatically
```

### 📊 Smart Analytics

```
You: "Analyze my weak areas in the Spanish deck"

Claude provides:
✓ Retention analysis
✓ Difficult card patterns
✓ Personalized study recommendations
✓ Predicted review workload
```

### 🔄 Batch Operations

```
You: "Import these 50 vocabulary words from CSV"

Claude handles:
✓ Format detection
✓ Duplicate checking
✓ Tag organization
✓ Progress reporting
```

### 🎯 Natural Language Commands

- "Create a deck for learning Japanese"
- "Find all suspended cards in my collection"
- "Export my French deck to Markdown"
- "Show me today's review statistics"
- "Generate cloze cards from this text about photosynthesis"

## Développement

```bash
# Installer les dépendances de dev
pip install -e ".[dev]"

# Lancer les tests
pytest

# Vérifier le linting
ruff check src/

# Vérifier les types
mypy src/
```

## Vérifier la connexion

```bash
python -m anki_mcp --check
```

## 🤝 Contributing

We love contributions! Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

### Ways to Contribute

- 🐛 **Report bugs** or request features via [Issues](https://github.com/guepardlover77/anki-mcp/issues)
- 💻 **Submit PRs** for new features or bug fixes
- 📝 **Improve docs** with examples and tutorials
- ⭐ **Star the repo** to show support
- 🗣️ **Share** with the Anki and MCP communities

### 🎯 Roadmap

- [ ] PDF content extraction for auto-generation
- [ ] Web scraping tools for online content
- [ ] Advanced AI card improvements
- [ ] Obsidian integration
- [ ] More export formats (Notion, Roam)

## 🌟 Show Your Support

If you find Anki MCP useful:

- ⭐ **Star this repo** on GitHub
- 🐦 **Tweet** about it: `#AnkiMCP #MCP #Claude`
- 📝 **Write** a blog post or tutorial
- 🎥 **Create** a demo video
- 💬 **Join** discussions and help others

## 📜 License

MIT License - see [LICENSE](LICENSE) for details

---

<div align="center">

**Built with ❤️ for the Anki and MCP communities**

[⬆ Back to top](#-anki-mcp-server)

</div>
