<div align="center">

# Anki MCP Server

**Transform Claude into your AI-powered Anki assistant**

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.2+-green.svg)](https://modelcontextprotocol.io/)
[![GitHub stars](https://img.shields.io/github/stars/guepardlover77/anki-mcp?style=social)](https://github.com/guepardlover77/anki-mcp/stargazers)

[Features](#features) • [Installation](#installation) • [Usage](#usage-examples) • [Contributing](#contributing)

</div>

---

## What is Anki MCP?

A complete **Model Context Protocol (MCP)** server that connects **Claude AI** with **Anki**, enabling:

- **AI-powered flashcard generation** from any text, PDF, or webpage
- **Smart review analytics** and learning insights
- **Automatic card improvements** using spaced repetition science
- **Natural language control** of your entire Anki collection

> **MCP** allows Claude to interact directly with Anki, making spaced repetition learning effortless.

## Features

### 55 MCP Tools across 10 categories

| Category | Tools | What you can do |
|----------|-------|-----------------|
| **Generation** (Priority) | 6 tools | Generate cards from text, create cloze deletions, improve existing cards |
| **Notes** | 8 tools | Create, update, search, and manage notes |
| **Decks** | 5 tools | Organize your collection with deck management |
| **Cards** | 6 tools | Find, suspend, move cards with precision |
| **Statistics** | 7 tools | Analyze retention, predict workload, get insights |
| **Review** | 6 tools | Smart review sessions with AI suggestions |
| **Models** | 4 tools | Manage note types and templates |
| **Media** | 4 tools | Handle images, audio, and video |
| **Sync** | 3 tools | Sync with AnkiWeb seamlessly |
| **Import/Export** | 6 tools | Markdown, CSV, JSON support |

### Additional Features

- **9 MCP Resources**: Real-time access to decks, stats, and cards
- **10 Smart Prompts**: Guided workflows for card creation and review
- **Pydantic Models**: Type-safe data validation
- **Async HTTP**: Lightning-fast AnkiConnect integration
- **Unit Tests**: Reliable and tested codebase

## Quick Start

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
# Clone the repository
git clone https://github.com/guepardlover77/anki-mcp.git
cd anki-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Or with extras for PDF and web
pip install -e ".[all]"
```

## Claude Desktop Configuration

Add to your Claude Desktop config file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "anki": {
      "command": "python",
      "args": ["-m", "anki_mcp"]
    }
  }
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANKI_MCP_HOST` | AnkiConnect host | `localhost` |
| `ANKI_MCP_PORT` | AnkiConnect port | `8765` |
| `ANKI_MCP_API_KEY` | AnkiConnect API key (optional) | - |
| `ANKI_MCP_TIMEOUT` | HTTP timeout in seconds | `30` |
| `ANKI_MCP_DEBUG` | Debug mode | `false` |

## MCP Resources

- `anki://decks` - List all decks
- `anki://decks/{name}` - Deck details
- `anki://decks/{name}/due` - Due cards for a deck
- `anki://models` - List note types
- `anki://models/{name}` - Model details
- `anki://tags` - All tags
- `anki://stats/today` - Today's statistics
- `anki://notes/{id}` - Note details
- `anki://cards/{id}` - Card details

## Usage Examples

### AI-Powered Card Generation

```
You: "Generate flashcards from this article about Python decorators"

Claude will:
- Extract key concepts
- Create Q&A pairs
- Add to your chosen deck
- Apply best practices automatically
```

### Smart Analytics

```
You: "Analyze my weak areas in the Spanish deck"

Claude provides:
- Retention analysis
- Difficult card patterns
- Personalized study recommendations
- Predicted review workload
```

### Batch Operations

```
You: "Import these 50 vocabulary words from CSV"

Claude handles:
- Format detection
- Duplicate checking
- Tag organization
- Progress reporting
```

### Natural Language Commands

- "Create a deck for learning Japanese"
- "Find all suspended cards in my collection"
- "Export my French deck to Markdown"
- "Show me today's review statistics"
- "Generate cloze cards from this text about photosynthesis"

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Check linting
ruff check src/

# Type checking
mypy src/
```

## Verify Connection

```bash
python -m anki_mcp --check
```

## Contributing

We welcome contributions! Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

### Ways to Contribute

- Report bugs or request features via [Issues](https://github.com/guepardlover77/anki-mcp/issues)
- Submit PRs for new features or bug fixes
- Improve documentation with examples and tutorials
- Star the repo to show support
- Share with the Anki and MCP communities

### Roadmap

- [ ] PDF content extraction for auto-generation
- [ ] Web scraping tools for online content
- [ ] Advanced AI card improvements
- [ ] Obsidian integration
- [ ] More export formats (Notion, Roam)

## Show Your Support

If you find Anki MCP useful:

- Star this repository on GitHub
- Share it on social media
- Write a blog post or tutorial
- Create a demo video
- Join discussions and help others

## License

MIT License - see [LICENSE](LICENSE) for details

---

<div align="center">

**Built for the Anki and MCP communities**

[Back to top](#anki-mcp-server)

</div>
