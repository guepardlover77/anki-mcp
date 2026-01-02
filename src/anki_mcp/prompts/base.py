"""MCP Prompts for Anki operations."""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register prompts with the MCP server.

    Prompts:
    Generation:
    - generate_basic_cards: Generate basic Q&A cards
    - generate_cloze_cards: Generate cloze deletion cards
    - twenty_rules: Apply the 20 rules of formulating knowledge

    Review:
    - explain_card: Explain a card in depth
    - rate_difficulty: Help rate card difficulty
    - generate_mnemonics: Create mnemonics for a card

    Analysis:
    - analyze_weak_areas: Analyze areas needing improvement
    - suggest_study_plan: Create a study plan
    """

    @mcp.prompt()
    def generate_basic_cards(topic: str, count: int = 5) -> str:
        """Generate basic Q&A flashcards for a topic.

        Args:
            topic: The topic to create cards about.
            count: Number of cards to generate.
        """
        return f"""You are an expert flashcard creator. Generate {count} high-quality flashcards about: {topic}

Follow these best practices:
1. ONE concept per card
2. Questions should be specific and unambiguous
3. Answers should be concise but complete
4. Avoid yes/no questions - use "What", "How", "Why" questions
5. Include context when needed to avoid ambiguity

Format each card as:
Q: [Question]
A: [Answer]

After generating the cards, use the add_notes_batch tool to add them to Anki.
"""

    @mcp.prompt()
    def generate_cloze_cards(content: str) -> str:
        """Generate cloze deletion cards from content.

        Args:
            content: The source content to create cloze cards from.
        """
        return f"""Create cloze deletion flashcards from this content:

{content}

Guidelines:
1. Identify key facts, definitions, and important details
2. Use {{{{c1::hidden text}}}} syntax for cloze deletions
3. Don't hide too much - one key concept per deletion
4. Ensure the surrounding context makes the answer clear
5. Create multiple cards if the content has several important points

Format each card as a single text with cloze deletions.

After generating, use the generate_cloze_cards tool to create them in Anki.
"""

    @mcp.prompt()
    def twenty_rules() -> str:
        """Apply the 20 rules of formulating knowledge to create better cards."""
        return """Apply Piotr Wozniak's 20 Rules of Formulating Knowledge to create effective flashcards.

Key principles to follow:

1. **Do not learn if you do not understand** - Ensure comprehension before creating cards
2. **Learn before you memorize** - Build context first
3. **Build upon the basics** - Start with fundamentals
4. **Stick to the minimum information principle** - Simple, atomic cards
5. **Use cloze deletion** - For lists and enumerations
6. **Use imagery** - Visual memory is powerful
7. **Use mnemonic techniques** - Memory palaces, acronyms, stories
8. **Personalize examples** - Relate to your own experience
9. **Rely on emotional states** - Connect to feelings
10. **Provide context** - Avoid ambiguity
11. **Avoid sets** - Break down enumerations
12. **Avoid enumerations** - Use overlapping cloze deletions
13. **Combat interference** - Make cards distinct
14. **Optimize wording** - Clear, unambiguous language
15. **Refer to other memories** - Build connections
16. **Use sources** - Add references
17. **Date-stamp knowledge** - For time-sensitive info
18. **Prioritize** - Focus on high-value knowledge

When creating cards, I will:
- Keep each card focused on ONE concept
- Make questions specific and unambiguous
- Use active recall (not recognition)
- Include enough context to eliminate confusion
- Format for easy reading
"""

    @mcp.prompt()
    def explain_card(card_question: str, card_answer: str) -> str:
        """Explain a flashcard in depth.

        Args:
            card_question: The question/front of the card.
            card_answer: The answer/back of the card.
        """
        return f"""Explain this flashcard concept in depth:

**Question:** {card_question}
**Answer:** {card_answer}

Please provide:
1. A clear, detailed explanation of the concept
2. Why this information is important
3. Real-world examples or applications
4. Common misconceptions to avoid
5. Related concepts to explore
6. A mnemonic or memory technique to remember it

This will help deepen understanding and improve retention.
"""

    @mcp.prompt()
    def rate_difficulty(card_question: str, card_answer: str, context: str = "") -> str:
        """Help rate the difficulty of a card during review.

        Args:
            card_question: The question being reviewed.
            card_answer: The correct answer.
            context: Optional context about the review.
        """
        return f"""Help me decide how to rate this flashcard:

**Question:** {card_question}
**Answer:** {card_answer}
{f"**Context:** {context}" if context else ""}

Anki rating options:
- **Again (1)**: I forgot completely or got it very wrong
- **Hard (2)**: I remembered but with significant difficulty
- **Good (3)**: I remembered correctly with normal effort
- **Easy (4)**: I remembered instantly with no effort

Consider:
- How quickly did you recall the answer?
- Did you need hints or partial recall?
- How confident are you in your answer?
- Will you remember this in the future?

Be honest - accurate ratings lead to better learning!
"""

    @mcp.prompt()
    def generate_mnemonics(concept: str, details: str = "") -> str:
        """Create memory techniques for a concept.

        Args:
            concept: The main concept to memorize.
            details: Additional details to include.
        """
        return f"""Create effective mnemonics and memory techniques for:

**Concept:** {concept}
{f"**Details:** {details}" if details else ""}

Generate multiple types of memory aids:

1. **Acronym/Acrostic**: Create a memorable word or phrase
2. **Visual Association**: Describe a vivid mental image
3. **Story Method**: Create a short narrative
4. **Rhyme or Rhythm**: Make it musical
5. **Memory Palace**: Place elements in a familiar location
6. **Personal Connection**: Relate to your own experience

Choose techniques that:
- Are easy to recall
- Create strong mental images
- Have emotional resonance
- Are personally meaningful

The best mnemonic is one you create yourself!
"""

    @mcp.prompt()
    def analyze_weak_areas(deck_name: str = "") -> str:
        """Analyze areas that need improvement.

        Args:
            deck_name: Optional specific deck to analyze.
        """
        deck_filter = f' in deck "{deck_name}"' if deck_name else ""
        return f"""Analyze my weak areas{deck_filter} and suggest improvements.

Please:
1. Use get_learning_insights to analyze my collection
2. Use analyze_retention to check retention rates
3. Look at cards with high lapse counts
4. Identify patterns in difficult cards

Then provide:
- **Weak Areas**: Topics/cards I struggle with most
- **Patterns**: Common characteristics of difficult cards
- **Root Causes**: Why these might be difficult
- **Actionable Improvements**:
  - Cards to reformulate
  - Topics to study more
  - Techniques to try
- **Study Priorities**: What to focus on next

Use the available tools to gather data before making recommendations.
"""

    @mcp.prompt()
    def suggest_study_plan(
        available_time: str = "30 minutes",
        goal: str = "maintain knowledge",
    ) -> str:
        """Create a personalized study plan.

        Args:
            available_time: Time available for study.
            goal: Study goal (maintain, catch up, intensive).
        """
        return f"""Create a study plan for me.

**Available Time:** {available_time}
**Goal:** {goal}

Please:
1. Check my current review load with get_reviews_today
2. Predict upcoming workload with predict_workload
3. Analyze my retention with analyze_retention

Then create a plan including:

**Immediate Session:**
- Which decks to prioritize
- How many new cards to add
- Review vs new card balance

**This Week:**
- Daily study targets
- Decks to focus on
- Topics to reinforce

**Recommendations:**
- Optimal study times
- Break patterns
- Techniques for difficult cards

**Motivation:**
- Progress highlights
- Achievable milestones
- Tips for consistency

Use the statistics tools to make data-driven suggestions.
"""

    @mcp.prompt()
    def create_deck_from_topic(topic: str, depth: str = "introductory") -> str:
        """Create a complete deck about a topic.

        Args:
            topic: The topic to create a deck for.
            depth: Level of depth (introductory, intermediate, advanced).
        """
        return f"""Create a complete Anki deck about: {topic}

**Depth Level:** {depth}

Please:
1. Create a deck using create_deck with an appropriate name
2. Generate cards covering:
   - Key definitions and concepts
   - Important facts and details
   - Relationships and connections
   - Common applications
   - Potential pitfalls/misconceptions

3. Use appropriate card types:
   - Basic cards for definitions
   - Cloze cards for facts with context
   - Reversed cards for bidirectional recall

4. Apply good flashcard principles:
   - One concept per card
   - Clear, specific questions
   - Appropriate context
   - Good formatting

5. Add helpful tags for organization

After creating, provide a summary of what was created.
"""

    @mcp.prompt()
    def improve_card(note_id: int) -> str:
        """Improve an existing card.

        Args:
            note_id: The note ID to improve.
        """
        return f"""Improve the flashcard with note ID: {note_id}

Please:
1. Use get_note_info to see the current card content
2. Use suggest_card_improvements to analyze issues
3. Consider:
   - Is the question clear and specific?
   - Is the answer concise but complete?
   - Is there enough context?
   - Could it benefit from mnemonics or images?

4. Suggest improvements:
   - Reworded question/answer
   - Additional context
   - Memory techniques
   - Related cards to create

5. If approved, use update_note to apply changes

Focus on making the card more memorable and effective for learning.
"""
