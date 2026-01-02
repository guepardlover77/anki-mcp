# Anki MCP Server

Serveur MCP Python pour gérer Anki depuis Claude avec génération automatique de flashcards.

## Prérequis

1. **Anki** installé et lancé
2. **AnkiConnect** add-on installé (code: `2055492159`)
3. **Python 3.11+**

### Installation d'AnkiConnect

1. Ouvrir Anki
2. Aller dans `Outils > Add-ons > Obtenir des add-ons`
3. Entrer le code: `2055492159`
4. Redémarrer Anki

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

## Exemples d'utilisation

### Ajouter une carte basique

```
Ajoute une carte dans le paquet "French" avec:
- Recto: "Bonjour"
- Verso: "Hello"
- Tags: vocabulary, greetings
```

### Rechercher des notes

```
Trouve toutes les notes du paquet "French" avec le tag "vocabulary"
```

### Créer un paquet imbriqué

```
Crée le paquet "Languages::French::Vocabulary"
```

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

## Licence

MIT
