# Social Media Posts

## HackerNews (Show HN)

### Title
```
Show HN: Anki MCP - AI-powered flashcard generation with Claude
```

### Post Body
```
I built an MCP server that connects Claude AI with Anki for automated flashcard creation and learning analytics.

What it does:

- Generate flashcards from any text using AI (follows spaced repetition best practices)
- Analyze retention patterns and get personalized study recommendations
- Control your entire Anki collection through natural language
- Import/export in multiple formats (Markdown, CSV, JSON)

Technical details:

- Python 3.11+ with async/await
- 55 MCP tools covering decks, notes, cards, reviews, statistics
- Pydantic models for type safety
- Communicates with Anki via AnkiConnect

Built this because I was spending too much time manually creating cards and wanted to leverage Claude's understanding to automate the tedious parts while maintaining quality.

Example: Paste a Wikipedia article, ask Claude to "generate flashcards about mitosis", and get 10 well-structured cards with proper Q&A format and cloze deletions where appropriate.

Open source (MIT): https://github.com/guepardlover77/anki-mcp

Would love feedback, especially from other Anki users or anyone interested in using AI for learning.
```

### Tips for HN
- Post on weekday mornings (8-10 AM EST)
- Be technical and honest
- Respond to comments with substance
- Don't ask for upvotes
- Share your learnings and challenges

---

## Twitter/X Thread

### Tweet 1 (Hook)
```
I built an AI assistant for @ankisrs using Claude 🧠

No more manually creating flashcards - just paste text and get high-quality cards automatically.

Open source, 55 tools, works with Claude Desktop.

Thread 🧵
```

### Tweet 2 (Problem)
```
The problem with Anki:

Creating good flashcards is time-consuming:
- Extract key concepts manually
- Follow best practices (one fact per card)
- Avoid vague questions
- Add proper context

I love Anki but hated the card creation grind.
```

### Tweet 3 (Solution)
```
Enter Anki MCP 🚀

Connected Claude AI to Anki through Model Context Protocol.

Now I can:
- Paste an article → get flashcards
- "Analyze my weak areas" → get insights
- "Import this CSV" → done
- "Improve this card" → better phrasing

All in natural language.
```

### Tweet 4 (Features)
```
What's included:

✓ 55 MCP tools (generation, CRUD, analytics)
✓ 9 resources (real-time data access)
✓ 10 smart prompts (guided workflows)
✓ Import: Markdown, CSV, JSON
✓ Export: Multiple formats
✓ Smart analytics & retention analysis
```

### Tweet 5 (Example)
```
Example workflow:

Me: "Generate flashcards from this article about Python decorators"

Claude:
- Extracts key concepts
- Creates Q&A pairs
- Applies best practices
- Adds to chosen deck

10 quality cards in 30 seconds vs 30 minutes manually.
```

### Tweet 6 (Tech)
```
Built with:

- Python 3.11+ (async/await)
- FastMCP framework
- Pydantic for validation
- AnkiConnect for integration
- 100% type hints
- Unit tested

Open source (MIT) so you can extend it for your workflow.
```

### Tweet 7 (CTA)
```
Try it yourself:

⭐ GitHub: https://github.com/guepardlover77/anki-mcp

Works with:
- Anki (+ AnkiConnect add-on)
- Claude Desktop
- Python 3.11+

Perfect for students, language learners, or anyone using spaced repetition.

Questions? Drop them below 👇
```

### Single Tweet Version (for quote tweets)
```
Built an AI assistant for Anki using Claude MCP 🧠

→ Generate flashcards from any text
→ Smart learning analytics
→ Natural language control
→ 55 tools, open source

No more manual card creation. Just paste & go.

Perfect for students & language learners.

GitHub: https://github.com/guepardlover77/anki-mcp
```

---

## LinkedIn Post

### Title
```
How I Used AI to Automate Flashcard Creation for Better Learning
```

### Post Body
```
I've been using Anki for years to learn languages, technical concepts, and retain information long-term. But creating good flashcards took forever.

So I built an AI assistant that does it for me.

THE PROBLEM:
Creating effective flashcards requires:
- Following spaced repetition best practices
- One concept per card
- Clear, unambiguous questions
- Proper use of cloze deletions
- Regular analysis of what's working

This takes time. A lot of time.

THE SOLUTION:
I connected Claude AI with Anki through the Model Context Protocol (MCP).

Now I can:
- Paste an article and get quality flashcards automatically
- Ask "analyze my weak areas" and get actionable insights
- Import/export in multiple formats
- Control everything through natural language

TECHNICAL DETAILS:
- Python 3.11+ with async architecture
- 55 MCP tools covering all Anki operations
- Type-safe with Pydantic models
- Integrates via AnkiConnect (no Anki modifications)

RESULTS:
Card creation time: 30 minutes → 30 seconds
Quality: Better (AI catches vague questions I'd miss)
Analysis: Now I actually review my retention patterns

OPEN SOURCE:
Released under MIT license so others can benefit.
GitHub: https://github.com/guepardlover77/anki-mcp

If you're into learning, productivity, or AI tools, check it out.

Happy to discuss the technical implementation or how you could adapt this for your own use cases.

#AI #Productivity #Learning #OpenSource #Python
```

---

## Reddit (r/MachineLearning)

### Title
```
[P] Anki MCP - AI Assistant for Flashcard Learning using Claude
```

### Post Body
```
**Project:** https://github.com/guepardlover77/anki-mcp

**What it does:**

MCP server connecting Claude AI with Anki (spaced repetition software) for automated flashcard generation and learning analytics.

**Motivation:**

Spaced repetition is proven effective for long-term retention, but creating quality flashcards is time-consuming and requires expertise in card design. I wanted to leverage LLMs to automate the tedious parts while maintaining quality.

**Technical Implementation:**

- **Architecture:** FastMCP server exposing 55 tools to Claude
- **Language:** Python 3.11+ with async/await
- **Validation:** Pydantic models for type safety
- **Integration:** AnkiConnect (REST API for Anki)
- **Features:** CRUD operations, analytics, import/export, card generation

**Key Capabilities:**

1. **Card Generation:** Extract concepts from text and format as effective flashcards
2. **Analytics:** Analyze retention patterns, predict workload, identify weak areas
3. **Batch Operations:** Import from CSV/Markdown, export in multiple formats
4. **Quality Checks:** Validate cards against best practices before creation

**Example Workflow:**

```python
# User pastes text about topic
# Claude extracts key facts
# Creates cards following best practices:
# - One concept per card
# - Clear questions
# - Appropriate cloze deletions
# - Proper context
```

**Results:**

- Card creation: 30min → 30sec (60x faster)
- Quality: Improved (AI catches issues humans miss)
- Adoption: Using daily for learning

**Interesting Challenges:**

- Balancing automation with educational effectiveness
- Prompt engineering for different card types
- Handling edge cases in card validation
- Making AI suggestions explainable

Open to feedback, especially on the ML/prompt engineering aspects.

**Tech Stack:**
- Python 3.11+
- FastMCP
- Pydantic
- httpx (async)
- AnkiConnect

**License:** MIT
```

---

## Usage Instructions

### Reddit Posts
1. **r/Anki**: Use the dedicated post in REDDIT_POST.md
2. **r/MachineLearning**: Use the [P] post above
3. **r/productivity**: Adapt the r/Anki post, focus on productivity gains
4. **r/learnprogramming**: Focus on using it for coding flashcards

### Twitter
- Post the thread during high-engagement times (10 AM - 2 PM EST)
- Use relevant hashtags: #AnkiMCP #AI #Learning #OpenSource
- Tag @AnthropicAI if appropriate
- Engage with replies quickly

### HackerNews
- Post Tuesday-Thursday, 8-10 AM EST
- Monitor comments closely first 2 hours
- Be technical and humble in responses
- Don't delete if it doesn't get traction immediately

### LinkedIn
- Post during business hours
- Tag relevant people in your network
- Share in relevant groups (AI, EdTech, Developer Tools)
- Follow up in comments

### Timing Strategy

**Week 1:**
- Monday: Add GitHub topics, prepare assets
- Tuesday: Post on Twitter
- Wednesday: Post on r/Anki
- Thursday: Submit to Product Hunt
- Friday: Post on HackerNews

**Week 2:**
- Continue engaging with comments
- Post on r/MachineLearning
- Share on LinkedIn
- Cross-post successes

Remember: Quality engagement > quantity of posts. Respond thoughtfully to every comment.
