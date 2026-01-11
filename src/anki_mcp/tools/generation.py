"""MCP Tools for automatic flashcard generation.

This is a PRIORITY module for the Anki MCP server.
These tools help Claude generate flashcards automatically.
"""

import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import NoteInput
from anki_mcp.server import get_anki_actions


def register_generation_tools(mcp: FastMCP) -> None:
    """Register auto-generation tools with the MCP server.

    Tools:
    - generate_cards_from_text: Generate cards from plain text
    - generate_cloze_cards: Create cloze deletion cards
    - suggest_card_improvements: Suggest improvements for existing cards
    - generate_related_cards: Generate related cards from a seed card
    - batch_create_cards: Create multiple cards at once
    - validate_card_quality: Check card quality before creation
    """

    @mcp.tool()
    async def generate_cards_from_text(
        text: str,
        deck_name: str,
        card_type: str = "basic",
        max_cards: int = 10,
        tags: list[str] | None = None,
        auto_create: bool = False,
    ) -> dict:
        """Analyze text and suggest flashcard content.

        This tool helps extract key concepts from text and format them
        as flashcards. It returns suggestions that can be reviewed
        before creating.

        Args:
            text: The source text to analyze.
            deck_name: Target deck for the cards.
            card_type: "basic" for Q&A, "cloze" for cloze deletions.
            max_cards: Maximum number of cards to generate.
            tags: Tags to add to generated cards.
            auto_create: If True, automatically create the cards.

        Returns:
            Suggested cards ready for review or creation.
        """
        try:
            actions = get_anki_actions()

            # Extract key information from text
            suggestions: list[dict[str, Any]] = []

            # Split into sentences/paragraphs
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            sentences = []
            for p in paragraphs:
                sentences.extend([s.strip() for s in re.split(r'[.!?]+', p) if s.strip()])

            # Look for patterns that make good cards
            for sentence in sentences[:max_cards * 2]:
                # Definitions: "X is Y" or "X are Y"
                def_match = re.match(r'^(.+?)\s+(?:is|are|was|were)\s+(.+)$', sentence, re.IGNORECASE)
                if def_match:
                    term = def_match.group(1).strip()
                    definition = def_match.group(2).strip()
                    if len(term) < 100 and len(definition) > 10:
                        if card_type == "cloze":
                            suggestions.append({
                                "type": "cloze",
                                "text": f"{{{{c1::{term}}}}} is {definition}",
                                "source": sentence,
                            })
                        else:
                            suggestions.append({
                                "type": "basic",
                                "front": f"What is {term}?",
                                "back": definition.capitalize(),
                                "source": sentence,
                            })
                        continue

                # Key facts with numbers/dates
                if re.search(r'\b\d{4}\b|\b\d+(?:\.\d+)?%?\b', sentence):
                    if card_type == "cloze":
                        # Create cloze for numbers
                        cloze_text = re.sub(
                            r'(\b\d{4}\b|\b\d+(?:\.\d+)?%?\b)',
                            r'{{c1::\1}}',
                            sentence,
                            count=1
                        )
                        suggestions.append({
                            "type": "cloze",
                            "text": cloze_text,
                            "source": sentence,
                        })
                    else:
                        suggestions.append({
                            "type": "basic",
                            "front": re.sub(r'(\b\d{4}\b|\b\d+(?:\.\d+)?%?\b)', '___', sentence, count=1),
                            "back": sentence,
                            "source": sentence,
                        })

                if len(suggestions) >= max_cards:
                    break

            # Limit results
            suggestions = suggestions[:max_cards]

            if not suggestions:
                return {
                    "success": False,
                    "message": "Could not extract suitable flashcard content from the text. Try providing more structured content with definitions or key facts.",
                    "suggestions": [],
                }

            # Auto-create if requested
            if auto_create and suggestions:
                notes_to_add = []
                model_name = "Cloze" if card_type == "cloze" else "Basic"

                for s in suggestions:
                    if s["type"] == "cloze":
                        notes_to_add.append(NoteInput(
                            deckName=deck_name,
                            modelName="Cloze",
                            fields={"Text": s["text"]},
                            tags=tags or [],
                        ))
                    else:
                        notes_to_add.append(NoteInput(
                            deckName=deck_name,
                            modelName="Basic",
                            fields={"Front": s["front"], "Back": s["back"]},
                            tags=tags or [],
                        ))

                note_ids = await actions.add_notes(notes_to_add)
                successful = [nid for nid in note_ids if nid is not None]
                failed_count = len(notes_to_add) - len(successful)

                if len(successful) == 0:
                    return {
                        "success": False,
                        "error": f"Failed to create all {failed_count} cards. Check that the deck exists and the model name is correct.",
                        "created": 0,
                        "failed": failed_count,
                        "suggestions": suggestions,
                    }

                return {
                    "success": len(successful) > 0,
                    "created": len(successful),
                    "failed": failed_count,
                    "note_ids": successful,
                    "suggestions": suggestions,
                }

            return {
                "success": True,
                "suggestions": suggestions,
                "count": len(suggestions),
                "message": f"Found {len(suggestions)} potential cards. Set auto_create=True to create them.",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def generate_cloze_cards(
        text: str,
        deck_name: str,
        cloze_hints: list[str] | None = None,
        tags: list[str] | None = None,
        auto_create: bool = False,
    ) -> dict:
        """Generate cloze deletion cards from text.

        Automatically identifies key terms to hide, or uses provided hints.

        Args:
            text: The source text.
            deck_name: Target deck name.
            cloze_hints: Optional list of terms to convert to cloze deletions.
            tags: Tags for the cards.
            auto_create: If True, create the cards immediately.

        Returns:
            Generated cloze cards.

        Example:
            generate_cloze_cards(
                text="Python was created by Guido van Rossum in 1991.",
                deck_name="Programming",
                cloze_hints=["Python", "1991"]
            )
        """
        try:
            actions = get_anki_actions()

            cloze_cards = []

            if cloze_hints:
                # Use provided hints
                for i, hint in enumerate(cloze_hints, 1):
                    if hint in text:
                        cloze_text = text.replace(hint, f"{{{{c{i}::{hint}}}}}", 1)
                        cloze_cards.append({
                            "text": cloze_text,
                            "hidden_term": hint,
                        })
            else:
                # Auto-detect important terms
                # Look for capitalized words, numbers, quoted terms
                patterns = [
                    r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns
                    r'\b\d{4}\b',  # Years
                    r'\b\d+(?:\.\d+)?%?\b',  # Numbers
                    r'"([^"]+)"',  # Quoted terms
                    r"'([^']+)'",  # Single-quoted terms
                ]

                terms_found = set()
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    terms_found.update(matches if isinstance(matches[0], str) else [m for m in matches] if matches else [])

                # Create cloze for each term
                cloze_index = 1
                for term in list(terms_found)[:5]:  # Limit to 5 terms
                    if len(term) > 2:  # Skip very short terms
                        cloze_text = text.replace(term, f"{{{{c{cloze_index}::{term}}}}}", 1)
                        cloze_cards.append({
                            "text": cloze_text,
                            "hidden_term": term,
                        })
                        cloze_index += 1

            if not cloze_cards:
                return {
                    "success": False,
                    "message": "Could not identify terms for cloze deletions. Try providing cloze_hints.",
                }

            if auto_create:
                notes_to_add = [
                    NoteInput(
                        deckName=deck_name,
                        modelName="Cloze",
                        fields={"Text": card["text"]},
                        tags=tags or [],
                    )
                    for card in cloze_cards
                ]

                note_ids = await actions.add_notes(notes_to_add)
                successful = [nid for nid in note_ids if nid is not None]
                failed_count = len(notes_to_add) - len(successful)

                if len(successful) == 0:
                    return {
                        "success": False,
                        "error": f"Failed to create all {failed_count} cloze cards. Check that the deck exists.",
                        "created": 0,
                        "cards": cloze_cards,
                    }

                return {
                    "success": len(successful) > 0,
                    "created": len(successful),
                    "note_ids": successful,
                    "cards": cloze_cards,
                }

            return {
                "success": True,
                "cards": cloze_cards,
                "count": len(cloze_cards),
                "message": "Set auto_create=True to create these cards.",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def suggest_card_improvements(note_id: int) -> dict:
        """Analyze a card and suggest improvements.

        Checks for common issues like:
        - Too long/complex content
        - Missing context
        - Ambiguous questions
        - Poor formatting

        Args:
            note_id: The note ID to analyze.

        Returns:
            Improvement suggestions.
        """
        try:
            actions = get_anki_actions()

            notes = await actions.get_notes_info([note_id])
            if not notes:
                return {"error": f"Note {note_id} not found"}

            note = notes[0]
            fields = {name: field.value for name, field in note.fields.items()}

            suggestions = []
            issues = []

            # Analyze front/question
            front = fields.get("Front", fields.get("Text", ""))
            back = fields.get("Back", "")

            # Check length
            if len(front) > 200:
                issues.append("Front is too long (>200 chars)")
                suggestions.append("Break into multiple simpler cards")

            if len(back) > 500:
                issues.append("Back is too long (>500 chars)")
                suggestions.append("Focus on one key concept per card")

            # Check for vague questions
            vague_words = ["thing", "stuff", "something", "etc", "and so on"]
            for word in vague_words:
                if word in front.lower():
                    issues.append(f"Question contains vague word: '{word}'")
                    suggestions.append("Use specific, precise language")
                    break

            # Check for yes/no questions
            if front.lower().startswith(("is ", "are ", "was ", "were ", "do ", "does ", "did ")):
                issues.append("Yes/no questions are less effective")
                suggestions.append("Rephrase as 'What...' or 'Why...' questions")

            # Check for missing context
            if len(front.split()) < 3:
                issues.append("Question may lack context")
                suggestions.append("Add context to make the question clearer")

            # Check formatting
            if "<" in front and ">" in front and "<br>" not in front.lower():
                suggestions.append("Consider using HTML formatting for better display")

            # Analyze based on card history
            cards = await actions.find_cards(f"nid:{note_id}")
            if cards:
                card_info = await actions.get_cards_info(cards[:1])
                if card_info:
                    card = card_info[0]
                    if card.lapses > 3:
                        issues.append(f"High lapse count ({card.lapses})")
                        suggestions.append("Card may be too difficult - add mnemonics or images")
                    if card.factor < 1800:
                        issues.append(f"Low ease factor ({card.factor/1000:.2f})")
                        suggestions.append("Consider adding more memorable content")

            quality = "good" if not issues else "needs_improvement" if len(issues) < 3 else "poor"

            return {
                "note_id": note_id,
                "quality": quality,
                "current_content": fields,
                "issues": issues,
                "suggestions": suggestions,
                "tags": note.tags,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def generate_related_cards(
        note_id: int,
        relationship_type: str = "variations",
        count: int = 3,
        auto_create: bool = False,
    ) -> dict:
        """Generate related cards based on an existing card.

        Args:
            note_id: The seed note ID.
            relationship_type: Type of related cards to generate:
                - "variations": Different ways to ask the same thing
                - "reverse": Reverse Q&A
                - "cloze": Convert to cloze format
                - "expand": Deeper questions on the topic
            count: Number of cards to generate.
            auto_create: Whether to create the cards.

        Returns:
            Generated related cards.
        """
        try:
            actions = get_anki_actions()

            notes = await actions.get_notes_info([note_id])
            if not notes:
                return {"error": f"Note {note_id} not found"}

            note = notes[0]
            fields = {name: field.value for name, field in note.fields.items()}

            # Get deck name from the first card
            deck_name = "Default"  # Fallback
            if note.cards:
                cards_info = await actions.get_cards_info(note.cards[:1])
                if cards_info:
                    deck_name = cards_info[0].deck_name

            front = fields.get("Front", "")
            back = fields.get("Back", fields.get("Text", ""))

            suggestions = []

            if relationship_type == "reverse":
                # Swap front and back
                suggestions.append({
                    "type": "basic",
                    "front": back,
                    "back": front,
                    "relationship": "reverse",
                })

            elif relationship_type == "cloze":
                # Convert to cloze format
                combined = f"{front}: {back}"
                # Create cloze from key terms in back
                words = back.split()
                if len(words) > 2:
                    key_word = max(words, key=len)  # Use longest word as key
                    cloze_text = combined.replace(key_word, f"{{{{c1::{key_word}}}}}")
                    suggestions.append({
                        "type": "cloze",
                        "text": cloze_text,
                        "relationship": "cloze_conversion",
                    })

            elif relationship_type == "variations":
                # Generate question variations
                if front.lower().startswith("what is"):
                    term = front[8:].strip(" ?")
                    suggestions.extend([
                        {"type": "basic", "front": f"Define {term}", "back": back, "relationship": "variation"},
                        {"type": "basic", "front": f"Explain {term}", "back": back, "relationship": "variation"},
                    ])
                elif front.lower().startswith("who"):
                    suggestions.append({
                        "type": "basic",
                        "front": front.replace("Who", "Which person").replace("who", "which person"),
                        "back": back,
                        "relationship": "variation",
                    })

            elif relationship_type == "expand":
                # Generate deeper questions
                if back:
                    suggestions.extend([
                        {
                            "type": "basic",
                            "front": f"Why is {front.lower().replace('what is ', '').strip('?')} important?",
                            "back": "[Expand on significance]",
                            "relationship": "expansion",
                            "needs_content": True,
                        },
                        {
                            "type": "basic",
                            "front": f"Give an example of {front.lower().replace('what is ', '').strip('?')}",
                            "back": "[Add example]",
                            "relationship": "example",
                            "needs_content": True,
                        },
                    ])

            # Limit suggestions
            suggestions = suggestions[:count]

            if not suggestions:
                return {
                    "success": False,
                    "message": f"Could not generate {relationship_type} cards for this note.",
                }

            result: dict[str, Any] = {
                "success": True,
                "original_note_id": note_id,
                "relationship_type": relationship_type,
                "suggestions": suggestions,
                "count": len(suggestions),
            }

            if auto_create:
                # Only create cards that don't need content
                notes_to_add = []
                for s in suggestions:
                    if s.get("needs_content"):
                        continue

                    if s["type"] == "cloze":
                        notes_to_add.append(NoteInput(
                            deckName=deck_name,  # Use same deck as original note
                            modelName="Cloze",
                            fields={"Text": s["text"]},
                            tags=note.tags,
                        ))
                    else:
                        notes_to_add.append(NoteInput(
                            deckName=deck_name,  # Use same deck as original note
                            modelName="Basic",
                            fields={"Front": s["front"], "Back": s["back"]},
                            tags=note.tags,
                        ))

                if notes_to_add:
                    note_ids = await actions.add_notes(notes_to_add)
                    successful = [nid for nid in note_ids if nid is not None]
                    result["created"] = len(successful)
                    result["note_ids"] = successful

            return result
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def batch_create_cards(
        cards: list[dict[str, Any]],
        deck_name: str,
        default_model: str = "Basic",
        default_tags: list[str] | None = None,
    ) -> dict:
        """Create multiple cards in a single operation.

        Args:
            cards: List of card definitions. Each can have:
                - front/back: For basic cards
                - text: For cloze cards
                - model: Override default model
                - tags: Additional tags
            deck_name: Target deck.
            default_model: Default model for cards.
            default_tags: Tags to add to all cards.

        Returns:
            Creation results.

        Example:
            batch_create_cards(
                cards=[
                    {"front": "Q1", "back": "A1"},
                    {"front": "Q2", "back": "A2", "tags": ["important"]},
                    {"text": "{{c1::Python}} is a language", "model": "Cloze"},
                ],
                deck_name="Test",
                default_tags=["batch_import"]
            )
        """
        try:
            actions = get_anki_actions()

            notes_to_add = []

            for card in cards:
                model = card.get("model", default_model)
                tags = list(default_tags or [])
                if "tags" in card:
                    tags.extend(card["tags"])

                if "text" in card:
                    # Cloze card
                    notes_to_add.append(NoteInput(
                        deckName=deck_name,
                        modelName=model if model == "Cloze" else "Cloze",
                        fields={"Text": card["text"]},
                        tags=tags,
                    ))
                elif "front" in card and "back" in card:
                    # Basic card
                    notes_to_add.append(NoteInput(
                        deckName=deck_name,
                        modelName=model,
                        fields={"Front": card["front"], "Back": card["back"]},
                        tags=tags,
                    ))
                elif "fields" in card:
                    # Custom fields
                    notes_to_add.append(NoteInput(
                        deckName=deck_name,
                        modelName=model,
                        fields=card["fields"],
                        tags=tags,
                    ))

            if not notes_to_add:
                return {"error": "No valid cards to create"}

            note_ids = await actions.add_notes(notes_to_add)
            successful = [nid for nid in note_ids if nid is not None]
            failed_count = len(notes_to_add) - len(successful)

            if len(successful) == 0:
                return {
                    "success": False,
                    "error": f"Failed to create all {failed_count} cards. Check that the deck exists and the model names are correct.",
                    "total": len(cards),
                    "created": 0,
                    "failed": failed_count,
                }

            return {
                "success": len(successful) > 0,
                "total": len(cards),
                "created": len(successful),
                "failed": failed_count,
                "note_ids": successful,
                "deck": deck_name,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def validate_card_quality(
        front: str,
        back: str,
        card_type: str = "basic",
    ) -> dict:
        """Validate card content before creation.

        Checks against best practices for effective flashcards.

        Args:
            front: The question/front content.
            back: The answer/back content.
            card_type: "basic" or "cloze".

        Returns:
            Validation results with score and issues.
        """
        issues = []
        warnings = []
        score = 100

        # Length checks
        if len(front) < 5:
            issues.append("Question is too short")
            score -= 20
        elif len(front) > 200:
            warnings.append("Question is quite long - consider splitting")
            score -= 5

        if len(back) < 3:
            issues.append("Answer is too short")
            score -= 20
        elif len(back) > 500:
            warnings.append("Answer is long - consider multiple cards")
            score -= 5

        # Content checks
        if front.lower() == back.lower():
            issues.append("Question and answer are identical")
            score -= 30

        if not front.strip() or not back.strip():
            issues.append("Empty content detected")
            score -= 50

        # Question quality
        if not any(front.endswith(c) for c in "?.:"):
            warnings.append("Question doesn't end with punctuation")
            score -= 2

        # Yes/no check
        yes_no_starters = ["is ", "are ", "was ", "were ", "do ", "does ", "did ", "can ", "will "]
        if any(front.lower().startswith(s) for s in yes_no_starters):
            warnings.append("Yes/no questions are less effective for learning")
            score -= 5

        # Vague language
        vague_terms = ["thing", "stuff", "etc", "something", "and so on", "whatever"]
        for term in vague_terms:
            if term in front.lower() or term in back.lower():
                warnings.append(f"Contains vague term: '{term}'")
                score -= 5
                break

        # Cloze-specific checks
        if card_type == "cloze":
            if "{{c1::" not in front:
                issues.append("Cloze card missing {{c1::...}} syntax")
                score -= 30
            elif front.count("{{c1::") > 3:
                warnings.append("Too many cloze deletions in one card")
                score -= 10

        # Cap score
        score = max(0, min(100, score))

        quality = (
            "excellent" if score >= 90
            else "good" if score >= 70
            else "fair" if score >= 50
            else "poor"
        )

        return {
            "valid": len(issues) == 0,
            "score": score,
            "quality": quality,
            "issues": issues,
            "warnings": warnings,
            "recommendations": [
                "Keep questions specific and unambiguous",
                "One concept per card",
                "Use active recall (avoid yes/no questions)",
                "Include context when needed",
            ] if score < 90 else [],
        }
