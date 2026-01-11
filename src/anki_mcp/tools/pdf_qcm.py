"""MCP Tools for PDF QCM flashcard generation.

This module provides tools to extract multiple-choice questions (QCM)
from PDF files and convert them to Anki flashcards.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None  # type: ignore

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import NoteInput
from anki_mcp.server import get_anki_actions


@dataclass
class QCMQuestion:
    """Structured QCM question."""

    number: int
    question_text: str
    options: dict[str, str]  # {'a': 'text', 'b': 'text', ...}
    correct_answers: list[str]  # ['a', 'c']
    raw_text: str  # Original text for reference


def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from PDF file using PyMuPDF.

    Args:
        file_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        ImportError: If PyMuPDF is not installed.
        FileNotFoundError: If PDF file doesn't exist.
        ValueError: If file is not a valid PDF.
    """
    if fitz is None:
        raise ImportError(
            "PyMuPDF (fitz) is required for PDF extraction. "
            "Install with: pip install anki-mcp[pdf]"
        )

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"File must be a PDF, got: {path.suffix}")

    try:
        doc = fitz.open(file_path)
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text_parts.append(page.get_text())

        doc.close()
        return "\n".join(text_parts)

    except Exception as e:
        raise ValueError(f"Failed to read PDF: {str(e)}")


def parse_qcm_from_text(text: str, language: str = "fr") -> list[QCMQuestion]:
    """Parse QCM questions from extracted text.

    Supports multiple formats:
    - Numbered questions (1., 2., etc.)
    - Options labeled a), b), c), d) or a., b., c., d.
    - Answer indicators: "Réponse:", "Answer:", "Correct:", etc.

    Args:
        text: Extracted PDF text.
        language: Language code for answer keyword detection.

    Returns:
        List of parsed QCM questions.
    """
    questions = []

    # Answer keywords by language
    answer_keywords = {
        "fr": r"(?:Réponse|Réponses|Correct|Bonne réponse)s?\s*:",
        "en": r"(?:Answer|Answers|Correct|Solution)s?\s*:",
        "es": r"(?:Respuesta|Respuestas|Correcto)s?\s*:",
    }

    answer_pattern = answer_keywords.get(language, answer_keywords["fr"])

    # Split text into lines for processing
    lines = text.split("\n")

    # Find question starts (lines starting with numbers)
    question_starts = []
    for i, line in enumerate(lines):
        # Match lines starting with a number followed by dot or parenthesis
        if re.match(r"^\s*(\d+)[\.\)]\s+", line):
            match = re.match(r"^\s*(\d+)[\.\)]\s+", line)
            if match:
                question_starts.append((i, int(match.group(1))))

    # Process each question block
    for idx, (start_line, question_num) in enumerate(question_starts):
        try:
            # Determine end of this question block
            if idx + 1 < len(question_starts):
                end_line = question_starts[idx + 1][0]
            else:
                end_line = len(lines)

            # Extract the block
            block_lines = lines[start_line:end_line]
            block_text = "\n".join(block_lines)

            # Extract question text (first line, remove number)
            first_line = block_lines[0]
            question_text = re.sub(r"^\s*\d+[\.\)]\s+", "", first_line).strip()

            # Find where options start
            options = {}
            option_lines_idx = []

            for i, line in enumerate(block_lines):
                # Match option lines (a), b), c), d) or a., b., c., d.)
                option_match = re.match(r"^\s*([a-d])[\)\.]?\s+(.+)", line, re.IGNORECASE)
                if option_match:
                    letter = option_match.group(1).lower()
                    text = option_match.group(2).strip()
                    options[letter] = text
                    option_lines_idx.append(i)

            # If question text is too short and first option exists,
            # it might be multi-line question
            if len(question_text) < 10 and option_lines_idx:
                # Question text is everything before first option
                first_option_idx = option_lines_idx[0]
                question_lines = block_lines[:first_option_idx]
                question_text = " ".join(
                    re.sub(r"^\s*\d+[\.\)]\s+", "", line).strip()
                    for line in question_lines
                    if line.strip()
                )

            # Extract correct answers
            answer_match = re.search(
                answer_pattern + r"\s*([a-d](?:\s*[,;]\s*[a-d])*)",
                block_text,
                re.IGNORECASE,
            )

            correct_answers = []
            if answer_match:
                answers_str = answer_match.group(1)
                # Split by comma or semicolon
                correct_answers = [
                    a.strip().lower() for a in re.split(r"[,;]\s*", answers_str) if a.strip()
                ]

            # Validate we have complete question
            if question_text and len(options) >= 2 and correct_answers:
                questions.append(
                    QCMQuestion(
                        number=question_num,
                        question_text=question_text,
                        options=options,
                        correct_answers=correct_answers,
                        raw_text=block_text,
                    )
                )

        except (ValueError, AttributeError, IndexError):
            # Skip malformed questions
            continue

    return questions


def format_qcm_as_flashcard(qcm: QCMQuestion) -> dict[str, str]:
    """Convert QCM to Anki flashcard format.

    Front: Question + all options
    Back: Only correct answers

    Args:
        qcm: Parsed QCM question.

    Returns:
        Dict with 'front' and 'back' fields.
    """
    # Format front: Question with all options
    front_parts = [qcm.question_text, ""]

    for letter in sorted(qcm.options.keys()):
        front_parts.append(f"{letter}) {qcm.options[letter]}")

    front = "\n".join(front_parts)

    # Format back: Only correct answers with their text
    back_parts = []
    for letter in sorted(qcm.correct_answers):
        if letter in qcm.options:
            back_parts.append(f"{letter}) {qcm.options[letter]}")

    back = "\n".join(back_parts)

    return {"front": front, "back": back, "question_number": str(qcm.number)}


def register_pdf_qcm_tools(mcp: FastMCP) -> None:
    """Register PDF QCM tools with the MCP server.

    Tools:
    - generate_qcm_from_pdf: Extract and create QCM flashcards from PDF
    """

    @mcp.tool()
    async def generate_qcm_from_pdf(
        file_path: str,
        deck_name: str,
        tags: list[str] | None = None,
        language: str = "fr",
        auto_create: bool = False,
        max_questions: int | None = None,
    ) -> dict:
        """Generate QCM flashcards from a PDF file.

        Automatically extracts and parses multiple-choice questions (QCM) from PDF files,
        then creates Anki flashcards with questions on the front and correct answers on the back.

        Args:
            file_path: Path to the PDF file containing QCM questions.
            deck_name: Target deck for the flashcards.
            tags: Optional tags to add to all generated cards.
            language: Language of the QCM (default: "fr" for French).
            auto_create: If True, automatically create cards. If False, return suggestions.
            max_questions: Maximum number of questions to extract (default: all).

        Returns:
            Dictionary with:
            - success: bool
            - questions_found: int
            - cards: list of parsed QCM cards
            - created: int (if auto_create=True)
            - note_ids: list (if auto_create=True)
            - errors: list of parsing errors

        Example PDF Format:
            1. Question text here?
            a) Option A
            b) Option B
            c) Option C
            d) Option D
            Réponse: a, c
        """
        try:
            # Step 1: Extract text from PDF
            try:
                pdf_text = extract_text_from_pdf(file_path)
            except (ImportError, FileNotFoundError, ValueError) as e:
                return {
                    "success": False,
                    "error": str(e),
                    "questions_found": 0,
                }

            if not pdf_text.strip():
                return {
                    "success": False,
                    "error": "PDF appears to be empty or contains no extractable text",
                    "questions_found": 0,
                }

            # Step 2: Parse QCM questions
            qcm_questions = parse_qcm_from_text(pdf_text, language=language)

            if not qcm_questions:
                return {
                    "success": False,
                    "error": (
                        "No valid QCM questions found in PDF. Check format:\n"
                        "Expected: numbered questions with a), b), c), d) options "
                        f"and '{language}' answer indicator"
                    ),
                    "questions_found": 0,
                    "extracted_text_sample": (
                        pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text
                    ),
                }

            # Limit questions if requested
            if max_questions:
                qcm_questions = qcm_questions[:max_questions]

            # Step 3: Format as flashcards
            cards_data = []
            for qcm in qcm_questions:
                card = format_qcm_as_flashcard(qcm)
                cards_data.append(
                    {
                        "number": qcm.number,
                        "front": card["front"],
                        "back": card["back"],
                        "correct_answers": qcm.correct_answers,
                    }
                )

            result: dict[str, Any] = {
                "success": True,
                "questions_found": len(qcm_questions),
                "cards": cards_data,
                "file": file_path,
            }

            # Step 4: Create cards if auto_create enabled
            if auto_create:
                actions = get_anki_actions()

                # Prepare tags
                card_tags = list(tags or [])
                card_tags.append("qcm")  # Add QCM tag automatically

                # Create NoteInput objects
                notes_to_add = []
                for card in cards_data:
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

                # Batch create notes
                note_ids = await actions.add_notes(notes_to_add)
                successful = [nid for nid in note_ids if nid is not None]
                failed_count = len(notes_to_add) - len(successful)

                if len(successful) == 0:
                    result.update(
                        {
                            "success": False,
                            "error": (
                                f"Failed to create all {failed_count} cards. "
                                f"Check that deck '{deck_name}' exists."
                            ),
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
                            "message": (
                                f"Created {len(successful)} QCM flashcards"
                                + (f" ({failed_count} failed)" if failed_count > 0 else "")
                            ),
                        }
                    )
            else:
                result["message"] = (
                    f"Found {len(qcm_questions)} QCM questions. "
                    "Set auto_create=True to create cards."
                )

            return result

        except AnkiConnectError as e:
            return {
                "success": False,
                "error": f"AnkiConnect error: {str(e)}",
                "questions_found": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "questions_found": 0,
            }
