"""MCP Tools for generating flashcards from course PDF materials.

This module provides intelligent analysis of course PDFs to extract key concepts
and generate appropriate flashcards using a mix of Basic (Q&A) and Cloze (fill-in) formats.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import NoteInput
from anki_mcp.server import get_anki_actions
from anki_mcp.tools.pdf_qcm import extract_text_from_pdf


@dataclass
class ConceptIndicator:
    """A detected concept in the PDF."""

    text: str
    type: str  # "definition", "fact", "list_item", "formula"
    priority: int  # 1-5 (5 is highest)
    page_number: int
    context: str  # Surrounding text
    suggested_card_type: str  # "basic" or "cloze"


@dataclass
class PDFAnalysis:
    """Analysis results of PDF content."""

    page_count: int
    word_count: int
    section_count: int
    technical_terms: list[str]
    definitions_found: int
    formulas_found: int
    lists_found: int
    key_concepts: list[ConceptIndicator]
    density_score: float  # 0-100
    importance_factors: dict[str, float] = field(default_factory=dict)


@dataclass
class CardCountSuggestion:
    """Suggestion for number of cards to create."""

    suggested: int
    min_recommended: int
    max_recommended: int
    reasoning: str


def analyze_pdf_content(pdf_text: str, file_path: str) -> PDFAnalysis:
    """Analyze PDF content and extract metadata.

    Args:
        pdf_text: Extracted text from PDF.
        file_path: Path to the PDF file (for page counting).

    Returns:
        PDFAnalysis with content metrics and detected concepts.
    """
    # Basic metrics
    lines = pdf_text.split("\n")
    words = pdf_text.split()
    word_count = len(words)

    # Estimate page count from text (rough estimate: ~300 words per page)
    page_count = max(1, word_count // 300)

    # Count sections (headings in CAPS, numbered sections, etc.)
    section_patterns = [
        r"^[A-Z\s]{10,}$",  # All caps headings
        r"^\d+\.\s+[A-Z]",  # Numbered sections: "1. Title"
        r"^[IVX]+\.\s+[A-Z]",  # Roman numerals: "I. Title"
    ]

    section_count = 0
    for line in lines:
        line_stripped = line.strip()
        for pattern in section_patterns:
            if re.match(pattern, line_stripped):
                section_count += 1
                break

    # Find technical terms (capitalized words, acronyms)
    technical_terms = []
    for word in words:
        # Capitalized words (not at sentence start), acronyms (2-6 uppercase letters)
        if re.match(r"^[A-Z][a-z]+$", word) or re.match(r"^[A-Z]{2,6}$", word):
            if word not in technical_terms and len(word) > 2:
                technical_terms.append(word)

    # Limit to most common terms
    technical_terms = technical_terms[:50]

    # Count definitions (patterns like "X is Y", "X refers to", etc.)
    definition_patterns = [
        r"\w+\s+(?:est|est un|est une|signifie|désigne|se réfère à)\s+",  # French
        r"\w+\s+(?:is|is a|is an|means|refers to|denotes)\s+",  # English
    ]

    definitions_found = 0
    for pattern in definition_patterns:
        definitions_found += len(re.findall(pattern, pdf_text, re.IGNORECASE))

    # Count formulas/equations (simple heuristic: mathematical symbols)
    formulas_found = len(re.findall(r"[=∑∫∂π√±×÷]", pdf_text))

    # Count lists (bulleted/numbered)
    list_patterns = [
        r"^\s*[-•*]\s+",  # Bulleted lists
        r"^\s*\d+[\.)]\s+",  # Numbered lists
    ]

    lists_found = 0
    for line in lines:
        for pattern in list_patterns:
            if re.match(pattern, line):
                lists_found += 1
                break

    # Extract key concepts (will be implemented fully)
    key_concepts = extract_concepts_from_text(pdf_text, max_concepts=100)

    # Calculate density score
    density_score = calculate_density_score_from_metrics(
        word_count=word_count,
        page_count=page_count,
        section_count=section_count,
        technical_terms_count=len(technical_terms),
        definitions_found=definitions_found,
        formulas_found=formulas_found,
    )

    # Calculate importance factors
    importance_factors = {
        "high_priority_terms": len([t for t in technical_terms if len(t) > 4]),
        "definition_ratio": definitions_found / max(1, page_count),
        "technical_density": len(technical_terms) / max(1, word_count) * 1000,
    }

    return PDFAnalysis(
        page_count=page_count,
        word_count=word_count,
        section_count=section_count,
        technical_terms=technical_terms,
        definitions_found=definitions_found,
        formulas_found=formulas_found,
        lists_found=lists_found,
        key_concepts=key_concepts,
        density_score=density_score,
        importance_factors=importance_factors,
    )


def calculate_density_score_from_metrics(
    word_count: int,
    page_count: int,
    section_count: int,
    technical_terms_count: int,
    definitions_found: int,
    formulas_found: int,
) -> float:
    """Calculate content density score (0-100).

    Args:
        word_count: Total words in document.
        page_count: Estimated page count.
        section_count: Number of sections/headings.
        technical_terms_count: Number of technical terms found.
        definitions_found: Number of definitions found.
        formulas_found: Number of formulas/equations.

    Returns:
        Density score normalized to 0-100.
    """
    # Calculate concepts per page
    concepts_per_page = (definitions_found + formulas_found) / max(1, page_count)

    # Calculate technical terms ratio (per 1000 words)
    technical_ratio = (technical_terms_count / max(1, word_count)) * 1000

    # Calculate structural score
    structural_score = min(20, section_count * 2)

    # Weighted score
    score = (
        (concepts_per_page * 20) +
        (technical_ratio * 30) + (definitions_found * 5) + structural_score
    )

    # Normalize to 0-100
    return min(100.0, max(0.0, score))


def extract_concepts_from_text(text: str, max_concepts: int = 100) -> list[ConceptIndicator]:
    """Extract key concepts from text.

    Args:
        text: PDF text content.
        max_concepts: Maximum number of concepts to extract.

    Returns:
        List of ConceptIndicator objects, prioritized by importance.
    """
    concepts = []
    lines = text.split("\n")

    # Pattern 1: Definitions ("X est Y", "X is Y")
    definition_patterns = [
        (r"^(.{3,50}?)\s+(?:est|est un|est une)\s+(.+)$", "definition", "fr"),
        (r"^(.{3,50}?)\s+(?:is|is a|is an)\s+(.+)$", "definition", "en"),
    ]

    for line in lines:
        line = line.strip()
        if len(line) < 10 or len(line) > 300:
            continue

        # Check definition patterns
        for pattern, concept_type, lang in definition_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                term = match.group(1).strip()
                definition = match.group(2).strip()

                # Skip if too long or contains special chars
                if len(term) < 50 and len(definition) > 5:
                    concepts.append(
                        ConceptIndicator(
                            text=line,
                            type=concept_type,
                            priority=4,  # High priority for explicit definitions
                            page_number=0,  # Placeholder
                            context=line,
                            suggested_card_type="basic",
                        )
                    )

        # Pattern 2: Facts with numbers/dates
        if re.search(r"\b\d{4}\b|\b\d+%|\b\d+\s+(?:km|kg|m|cm|€|$)", line):
            concepts.append(
                ConceptIndicator(
                    text=line,
                    type="fact",
                    priority=3,
                    page_number=0,
                    context=line,
                    suggested_card_type="cloze",
                )
            )

        # Pattern 3: Lists (if line starts with bullet/number)
        if re.match(r"^\s*[-•*\d+[\.)]\s+", line):
            # Check if it's a meaningful list item
            content = re.sub(r"^\s*[-•*\d+[\.)]\s+", "", line).strip()
            if len(content) > 10:
                concepts.append(
                    ConceptIndicator(
                        text=content,
                        type="list_item",
                        priority=2,
                        page_number=0,
                        context=line,
                        suggested_card_type="cloze",
                    )
                )

    # Limit and sort by priority
    concepts.sort(key=lambda c: c.priority, reverse=True)
    return concepts[:max_concepts]


def calculate_optimal_card_count(analysis: PDFAnalysis) -> CardCountSuggestion:
    """Calculate optimal number of cards using heuristics.

    Args:
        analysis: PDF analysis results.

    Returns:
        CardCountSuggestion with suggested count and reasoning.
    """
    concepts_found = len(analysis.key_concepts)

    # Density factor (0.5 - 2.0)
    density_factor = 1.0
    if analysis.density_score > 70:
        density_factor = 1.5  # Dense content = more cards
    elif analysis.density_score > 50:
        density_factor = 1.2
    elif analysis.density_score < 30:
        density_factor = 0.7  # Light content = fewer cards

    # Importance factor (0.8 - 1.3)
    importance_factor = 1.0
    high_priority = analysis.importance_factors.get("high_priority_terms", 0)
    if high_priority > 20:
        importance_factor = 1.2
    elif high_priority > 10:
        importance_factor = 1.1

    # Calculate base count
    base_count = concepts_found * density_factor * importance_factor

    # Calculate range
    min_cards = max(5, int(base_count * 0.7))  # At least 5 cards
    max_cards = min(50, int(base_count * 1.3))  # Cap at 50
    suggested = max(min_cards, min(max_cards, int(base_count)))

    # Generate reasoning
    if analysis.density_score > 70:
        density_desc = "très dense"
    elif analysis.density_score > 50:
        density_desc = "moyennement dense"
    else:
        density_desc = "léger"

    reasoning = (
        f"Trouvé {concepts_found} concepts avec {analysis.density_score:.0f}% de densité. "
        f"Contenu {density_desc}."
    )

    return CardCountSuggestion(
        suggested=suggested,
        min_recommended=min_cards,
        max_recommended=max_cards,
        reasoning=reasoning,
    )


def decide_card_type(concept: ConceptIndicator, card_type_mix: bool) -> str:
    """Decide whether to use Basic or Cloze card type.

    Args:
        concept: The concept to format.
        card_type_mix: Whether to intelligently choose type.

    Returns:
        "basic" or "cloze"
    """
    if not card_type_mix:
        return concept.suggested_card_type

    # Use the suggested type from concept extraction
    if concept.type == "definition":
        # Short definitions work well as Basic Q&A
        if len(concept.text) < 100:
            return "basic"
        return "cloze"

    if concept.type in ["fact", "list_item", "formula"]:
        return "cloze"

    return "basic"


def format_concept_as_basic_card(concept: ConceptIndicator) -> dict[str, str]:
    """Format concept as Basic flashcard (front/back).

    Args:
        concept: The concept to format.

    Returns:
        Dict with 'front' and 'back' keys.
    """
    # Extract term and definition from text
    # Pattern: "X est Y" or "X is Y"
    definition_match = re.match(
        r"^(.+?)\s+(?:est|est un|est une|is|is a|is an)\s+(.+)$",
        concept.text,
        re.IGNORECASE,
    )

    if definition_match:
        term = definition_match.group(1).strip()
        definition = definition_match.group(2).strip()

        # Create question
        front = f"Qu'est-ce que {term} ?"
        back = definition.capitalize()
    else:
        # Fallback: Use the whole text as context
        front = f"Expliquez: {concept.text[:80]}"
        back = concept.text

    return {"front": front, "back": back}


def format_concept_as_cloze_card(concept: ConceptIndicator) -> dict[str, str]:
    """Format concept as Cloze flashcard.

    Args:
        concept: The concept to format.

    Returns:
        Dict with 'text' key containing cloze-formatted text.
    """
    text = concept.text

    if concept.type == "fact":
        # Replace numbers, dates, percentages with cloze deletions
        # Pattern 1: Years (4 digits)
        text = re.sub(r"\b(\d{4})\b", r"{{c1::\1}}", text, count=1)

        # Pattern 2: Percentages
        text = re.sub(r"\b(\d+%)\b", r"{{c2::\1}}", text, count=1)

        # Pattern 3: Other numbers with units
        text = re.sub(
            r"\b(\d+\s*(?:km|kg|m|cm|€|\$))\b", r"{{c3::\1}}", text, count=1
        )

    elif concept.type == "list_item":
        # For list items, hide the first key term (longest word)
        words = text.split()
        if words:
            # Find longest meaningful word (> 4 chars)
            key_words = [w for w in words if len(w) > 4 and w.isalpha()]
            if key_words:
                longest = max(key_words, key=len)
                text = text.replace(longest, f"{{{{c1::{longest}}}}}", 1)

    elif concept.type == "formula":
        # For formulas, hide the result or key variable
        # Simple heuristic: hide what comes after '='
        if "=" in text:
            parts = text.split("=", 1)
            if len(parts) == 2:
                result = parts[1].strip()
                text = f"{parts[0]}= {{{{c1::{result}}}}}"

    # Fallback: Hide first capitalized term or technical term
    if "{{c" not in text:
        # Find capitalized words
        cap_match = re.search(r"\b([A-Z][a-z]{3,})\b", text)
        if cap_match:
            term = cap_match.group(1)
            text = text.replace(term, f"{{{{c1::{term}}}}}", 1)

    return {"text": text}


def register_pdf_course_tools(mcp: FastMCP) -> None:
    """Register PDF course tools with the MCP server.

    Tools:
    - generate_cards_from_course_pdf: Generate flashcards from course PDFs
    """

    @mcp.tool()
    async def generate_cards_from_course_pdf(
        file_path: str,
        deck_name: str,
        max_cards: int | None = None,
        auto_count: bool = False,
        card_type_mix: bool = True,
        card_type_preference: str = "basic",
        tags: list[str] | None = None,
        auto_create: bool = False,
        language: str = "fr",
    ) -> dict:
        """Generate flashcards from course PDF materials.

        This tool intelligently extracts key concepts from course PDFs and creates
        appropriate flashcards using a mix of Basic (Q&A) and Cloze (fill-in) formats.

        MODES OF OPERATION:

        1. Auto-Count Mode (Recommended):
           - Set auto_count=True
           - The tool analyzes content density, technical terms, and importance
           - Automatically determines optimal number of cards
           - Returns analysis showing why N cards were suggested

        2. Manual Count Mode:
           - Set auto_count=False and provide max_cards=N
           - Generates exactly N cards (or fewer if insufficient content)

        CARD TYPE SELECTION:

        - card_type_mix=True (default): Intelligently chooses Basic or Cloze per concept
          - Basic for: definitions, "what is X?" questions
          - Cloze for: facts with numbers/dates, lists, formulas

        - card_type_mix=False: Uses only card_type_preference ("basic" or "cloze")

        WORKFLOW:

        1. Preview First (auto_create=False):
           - Review suggested cards and analysis
           - See density score, concepts found, card count reasoning

        2. Then Create (auto_create=True):
           - Creates cards in specified deck
           - Returns note IDs for created cards

        Args:
            file_path: Path to course PDF file.
            deck_name: Target Anki deck name.
            max_cards: Maximum cards to generate (required if auto_count=False).
            auto_count: If True, intelligently determines optimal card count.
            card_type_mix: If True, mix Basic and Cloze; if False, use preference.
            card_type_preference: Default type when not mixing ("basic" or "cloze").
            tags: Optional tags (auto-adds "course" and "pdf-generated").
            auto_create: If True, create cards immediately; if False, return suggestions.
            language: Language for better analysis ("fr", "en", "es").

        Returns:
            Dictionary with:
            - success: bool
            - analysis: PDF analysis metadata
            - card_count_suggestion: Auto-count reasoning (if auto_count=True)
            - cards: List of generated cards
            - created: Number created (if auto_create=True)
            - note_ids: Created note IDs (if auto_create=True)

        Example - Auto-count with preview:
            generate_cards_from_course_pdf(
                file_path="/path/to/course.pdf",
                deck_name="Biology",
                auto_count=True,
                auto_create=False
            )

        Example - Auto-count with immediate creation:
            generate_cards_from_course_pdf(
                file_path="/path/to/course.pdf",
                deck_name="Biology",
                auto_count=True,
                auto_create=True
            )
        """
        try:
            # Validation: Must have either auto_count or max_cards
            if not auto_count and max_cards is None:
                return {
                    "success": False,
                    "error": "Either set auto_count=True or provide max_cards parameter",
                }

            # Step 1: Extract text from PDF
            try:
                pdf_text = extract_text_from_pdf(file_path)
            except (ImportError, FileNotFoundError, ValueError) as e:
                return {
                    "success": False,
                    "error": str(e),
                }

            if not pdf_text.strip():
                return {
                    "success": False,
                    "error": "PDF appears to be empty or is a scanned document with no extractable text",
                    "suggestion": "If this is a scanned PDF, use OCR software first (e.g., Adobe Acrobat, Tesseract)",
                }

            # Step 2: Analyze PDF content
            analysis = analyze_pdf_content(pdf_text, file_path)

            if not analysis.key_concepts:
                return {
                    "success": False,
                    "error": "Could not extract meaningful concepts from the PDF",
                    "analysis": {
                        "word_count": analysis.word_count,
                        "page_count": analysis.page_count,
                        "density_score": analysis.density_score,
                    },
                    "suggestion": "This PDF may be too short, too general, or poorly structured.",
                    "extracted_sample": pdf_text[:300] if len(pdf_text) > 300 else pdf_text,
                }

            # Step 3: Determine number of cards to generate
            if auto_count:
                suggestion = calculate_optimal_card_count(analysis)
                cards_to_generate = suggestion.suggested
            else:
                cards_to_generate = max_cards or 10
                suggestion = None

            # Limit concepts to requested count
            concepts_to_use = analysis.key_concepts[:cards_to_generate]

            # Step 4: Format concepts as flashcards
            cards_data = []
            for i, concept in enumerate(concepts_to_use):
                card_type = decide_card_type(concept, card_type_mix)

                if card_type == "basic" or (not card_type_mix and card_type_preference == "basic"):
                    card = format_concept_as_basic_card(concept)
                    cards_data.append(
                        {
                            "type": "basic",
                            "front": card["front"],
                            "back": card["back"],
                            "source_page": concept.page_number,
                            "priority": concept.priority,
                        }
                    )
                else:  # cloze
                    card = format_concept_as_cloze_card(concept)
                    cards_data.append(
                        {
                            "type": "cloze",
                            "text": card["text"],
                            "source_page": concept.page_number,
                            "priority": concept.priority,
                        }
                    )

            # Build result
            result: dict[str, Any] = {
                "success": True,
                "file": file_path,
                "analysis": {
                    "page_count": analysis.page_count,
                    "word_count": analysis.word_count,
                    "section_count": analysis.section_count,
                    "density_score": round(analysis.density_score, 1),
                    "concepts_found": len(analysis.key_concepts),
                },
                "cards": cards_data,
            }

            if auto_count and suggestion:
                result["card_count_suggestion"] = {
                    "suggested": suggestion.suggested,
                    "min_recommended": suggestion.min_recommended,
                    "max_recommended": suggestion.max_recommended,
                    "reasoning": suggestion.reasoning,
                }

            # Step 5: Create cards if requested
            if auto_create:
                actions = get_anki_actions()

                # Prepare tags
                card_tags = list(tags or [])
                card_tags.extend(["course", "pdf-generated"])

                # Create NoteInput objects
                notes_to_add = []
                for card in cards_data:
                    if card["type"] == "basic":
                        notes_to_add.append(
                            NoteInput(
                                deckName=deck_name,
                                modelName="Basic",
                                fields={
                                    "Front": card["front"],
                                    "Back": card["back"],
                                },
                                tags=card_tags,
                            )
                        )
                    else:  # cloze
                        notes_to_add.append(
                            NoteInput(
                                deckName=deck_name,
                                modelName="Cloze",
                                fields={"Text": card["text"]},
                                tags=card_tags,
                            )
                        )

                # Batch create notes
                note_ids = await actions.add_notes(notes_to_add)
                successful = [nid for nid in note_ids if nid is not None]
                failed_count = len(notes_to_add) - len(successful)

                if len(successful) == 0:
                    result.update(
                        {
                            "success": False,
                            "error": f"Failed to create all {failed_count} cards. Check that deck '{deck_name}' exists.",
                            "created": 0,
                            "failed": failed_count,
                        }
                    )
                else:
                    result.update(
                        {
                            "created": len(successful),
                            "failed": failed_count,
                            "note_ids": successful,
                            "deck": deck_name,
                            "message": f"Créé {len(successful)} flashcards depuis le cours PDF"
                            + (f" ({failed_count} échecs)" if failed_count > 0 else ""),
                        }
                    )
            else:
                card_count = len(cards_data)
                result["message"] = (
                    f"Trouvé {card_count} cartes potentielles. "
                    "Mettre auto_create=True pour les créer."
                )

            return result

        except AnkiConnectError as e:
            return {
                "success": False,
                "error": f"Erreur AnkiConnect: {str(e)}",
                "suggestion": "Vérifier qu'Anki est lancé avec addon AnkiConnect installé",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur inattendue: {str(e)}",
            }
