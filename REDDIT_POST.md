# Reddit Post for r/Anki

## Title
I built an AI assistant for Anki using Claude - Generate flashcards automatically from any text

## Post Body

Hey r/Anki,

I've been working on a project that connects Claude AI with Anki through the Model Context Protocol (MCP), and I wanted to share it with the community.

**What it does:**

Anki MCP lets you control your entire Anki collection using natural language through Claude Desktop. Think of it as having an AI assistant that understands Anki inside and out.

**Key features:**

- **AI-powered card generation**: Paste an article, lecture notes, or any text, and Claude will automatically extract key concepts and create quality flashcards following best practices (one concept per card, clear questions, proper cloze deletions)

- **Smart analytics**: Ask "analyze my weak areas in Spanish deck" and get detailed retention analysis, difficulty patterns, and personalized study recommendations

- **Batch operations**: Import CSV files, export to Markdown, manage tags - all through simple conversational commands

- **Natural language control**: No need to navigate menus. Just say "create a deck for Japanese vocabulary" or "find all suspended cards" and it works

**Example workflows:**

```
You: "Generate flashcards from this Wikipedia article about mitosis"
Claude: Creates 10 well-structured cards with proper Q&A format

You: "Show me today's review statistics and predict my workload for next week"
Claude: Analyzes your collection and provides detailed insights

You: "Improve this card: What is photosynthesis?"
Claude: Suggests better phrasing, context, and memory techniques
```

**Technical details:**

- 55 MCP tools covering decks, notes, cards, reviews, statistics, import/export
- Built with Python 3.11+, async HTTP, Pydantic validation
- Works with AnkiConnect (no modifications to Anki itself)
- Open source (MIT license)

**Requirements:**

- Anki with AnkiConnect add-on (code: 2055492159)
- Claude Desktop
- Python 3.11+

**GitHub:** https://github.com/guepardlover77/anki-mcp

I've been using it for a few weeks and it's transformed how I create and manage cards. The AI suggestions for card improvements are surprisingly good - it catches vague questions, suggests better wording, and even recommends mnemonics.

Happy to answer questions or hear feedback! If anyone tries it, I'd love to know what you think.

---

**Edit:** Wow, thanks for all the interest! A few people asked about specific use cases:

- Language learners: Import vocabulary lists, auto-generate example sentences
- Medical students: Convert lecture PDFs to cloze cards (coming soon)
- Programmers: Create flashcards from documentation
- General: Analyze your retention rates and get study plan suggestions

---

*Note: This requires Claude Desktop (currently in beta). If you don't have access yet, you can still check out the code and star the repo for when you do!*
