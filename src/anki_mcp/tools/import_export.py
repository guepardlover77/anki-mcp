"""MCP Tools for Anki import/export operations."""

import csv
import io
import json
import re
from typing import Any

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import NoteInput
from anki_mcp.server import get_anki_actions


def register_import_export_tools(mcp: FastMCP) -> None:
    """Register import/export tools with the MCP server.

    Tools:
    - import_markdown: Import notes from Markdown
    - import_csv: Import notes from CSV
    - import_qa_list: Import from Q&A list
    - export_to_markdown: Export deck to Markdown
    - export_to_csv: Export deck to CSV
    - export_to_json: Export deck to JSON
    """

    @mcp.tool()
    async def import_markdown(
        content: str,
        deck_name: str,
        model_name: str = "Basic",
        tags: list[str] | None = None,
    ) -> dict:
        """Import notes from Markdown content.

        Supports multiple formats:
        - Q&A format: "Q: question\\nA: answer"
        - Cloze format: "Text with {{c1::cloze deletion}}"
        - Header format: "## Front\\nBack content"

        Args:
            content: Markdown content to import.
            deck_name: Target deck name.
            model_name: Note type (default: "Basic", use "Cloze" for cloze deletions).
            tags: Optional tags for all imported notes.

        Returns:
            Import results with note IDs.
        """
        try:
            actions = get_anki_actions()

            notes_to_add: list[NoteInput] = []
            errors: list[str] = []

            # Detect format and parse
            if re.search(r'\{\{c\d+::', content):
                # Cloze format
                if model_name == "Basic":
                    model_name = "Cloze"

                # Split by double newline or ---
                sections = re.split(r'\n\n+|^---$', content, flags=re.MULTILINE)
                for section in sections:
                    section = section.strip()
                    if section and '{{c' in section:
                        notes_to_add.append(NoteInput(
                            deckName=deck_name,
                            modelName=model_name,
                            fields={"Text": section},
                            tags=tags or [],
                        ))

            elif re.search(r'^Q:|^Question:', content, re.MULTILINE | re.IGNORECASE):
                # Q&A format
                qa_pattern = r'(?:Q|Question):\s*(.+?)\n(?:A|Answer):\s*(.+?)(?=\n(?:Q|Question):|$)'
                matches = re.findall(qa_pattern, content, re.DOTALL | re.IGNORECASE)

                for question, answer in matches:
                    notes_to_add.append(NoteInput(
                        deckName=deck_name,
                        modelName=model_name,
                        fields={"Front": question.strip(), "Back": answer.strip()},
                        tags=tags or [],
                    ))

            elif re.search(r'^##\s+', content, re.MULTILINE):
                # Header format: ## Front\nBack
                sections = re.split(r'^(?=##\s+)', content, flags=re.MULTILINE)
                for section in sections:
                    section = section.strip()
                    if section.startswith('##'):
                        lines = section.split('\n', 1)
                        front = lines[0].lstrip('#').strip()
                        back = lines[1].strip() if len(lines) > 1 else ""
                        if front and back:
                            notes_to_add.append(NoteInput(
                                deckName=deck_name,
                                modelName=model_name,
                                fields={"Front": front, "Back": back},
                                tags=tags or [],
                            ))

            else:
                # Try simple line-based: Front; Back or Front | Back
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    parts = None
                    for sep in [';', '|', '\t']:
                        if sep in line:
                            parts = line.split(sep, 1)
                            break

                    if parts and len(parts) == 2:
                        notes_to_add.append(NoteInput(
                            deckName=deck_name,
                            modelName=model_name,
                            fields={"Front": parts[0].strip(), "Back": parts[1].strip()},
                            tags=tags or [],
                        ))

            if not notes_to_add:
                return {
                    "error": "No notes found in content. Supported formats: Q&A, Cloze, Header (##), or semicolon-separated.",
                }

            # Add notes
            note_ids = await actions.add_notes(notes_to_add)
            successful = [nid for nid in note_ids if nid is not None]
            failed_count = len(notes_to_add) - len(successful)

            if len(successful) == 0:
                return {
                    "success": False,
                    "error": f"Failed to import all {failed_count} notes. Check that the deck exists and the model name is correct.",
                    "total_found": len(notes_to_add),
                    "imported": 0,
                    "failed": failed_count,
                }

            return {
                "success": len(successful) > 0,
                "total_found": len(notes_to_add),
                "imported": len(successful),
                "failed": failed_count,
                "note_ids": successful,
                "deck": deck_name,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def import_csv(
        content: str,
        deck_name: str,
        model_name: str = "Basic",
        field_mapping: dict[str, int] | None = None,
        has_header: bool = True,
        tags: list[str] | None = None,
    ) -> dict:
        """Import notes from CSV content.

        Args:
            content: CSV content to import.
            deck_name: Target deck name.
            model_name: Note type (default: "Basic").
            field_mapping: Map field names to column indices (0-based).
                          Default: {"Front": 0, "Back": 1}
            has_header: Whether the CSV has a header row (default: True).
            tags: Optional tags for all imported notes.

        Returns:
            Import results with note IDs.

        Example:
            import_csv(
                content="Front,Back,Tags\\nBonjour,Hello,vocabulary\\nMerci,Thank you,vocabulary",
                deck_name="French",
                field_mapping={"Front": 0, "Back": 1},
            )
        """
        try:
            actions = get_anki_actions()

            # Parse CSV
            reader = csv.reader(io.StringIO(content))
            rows = list(reader)

            if not rows:
                return {"error": "CSV is empty"}

            # Handle header
            header = None
            if has_header:
                header = rows[0]
                rows = rows[1:]

            # Default mapping
            if field_mapping is None:
                if header:
                    # Try to use header as field names
                    field_mapping = {name: i for i, name in enumerate(header)}
                else:
                    field_mapping = {"Front": 0, "Back": 1}

            notes_to_add: list[NoteInput] = []

            for row in rows:
                if not any(cell.strip() for cell in row):
                    continue  # Skip empty rows

                fields = {}
                for field_name, col_idx in field_mapping.items():
                    if col_idx < len(row):
                        fields[field_name] = row[col_idx].strip()

                if fields:
                    notes_to_add.append(NoteInput(
                        deckName=deck_name,
                        modelName=model_name,
                        fields=fields,
                        tags=tags or [],
                    ))

            if not notes_to_add:
                return {"error": "No valid notes found in CSV"}

            # Add notes
            note_ids = await actions.add_notes(notes_to_add)
            successful = [nid for nid in note_ids if nid is not None]
            failed_count = len(notes_to_add) - len(successful)

            if len(successful) == 0:
                return {
                    "success": False,
                    "error": f"Failed to import all {failed_count} notes. Check that the deck exists and the model name is correct.",
                    "total_rows": len(rows),
                    "imported": 0,
                    "failed": failed_count,
                }

            return {
                "success": len(successful) > 0,
                "total_rows": len(rows),
                "imported": len(successful),
                "failed": failed_count,
                "note_ids": successful,
                "deck": deck_name,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def import_qa_list(
        questions_answers: list[dict[str, str]],
        deck_name: str,
        model_name: str = "Basic",
        tags: list[str] | None = None,
    ) -> dict:
        """Import a list of Q&A pairs as notes.

        Args:
            questions_answers: List of {"front": "...", "back": "..."} dicts.
            deck_name: Target deck name.
            model_name: Note type (default: "Basic").
            tags: Optional tags for all notes.

        Returns:
            Import results with note IDs.

        Example:
            import_qa_list(
                questions_answers=[
                    {"front": "What is Python?", "back": "A programming language"},
                    {"front": "What is Anki?", "back": "A spaced repetition app"},
                ],
                deck_name="Programming",
            )
        """
        try:
            actions = get_anki_actions()

            notes_to_add: list[NoteInput] = []

            for qa in questions_answers:
                front = qa.get("front", qa.get("question", ""))
                back = qa.get("back", qa.get("answer", ""))

                if front and back:
                    notes_to_add.append(NoteInput(
                        deckName=deck_name,
                        modelName=model_name,
                        fields={"Front": front, "Back": back},
                        tags=tags or [],
                    ))

            if not notes_to_add:
                return {"error": "No valid Q&A pairs found"}

            # Add notes
            note_ids = await actions.add_notes(notes_to_add)
            successful = [nid for nid in note_ids if nid is not None]
            failed_count = len(notes_to_add) - len(successful)

            if len(successful) == 0:
                return {
                    "success": False,
                    "error": f"Failed to import all {failed_count} notes. Check that the deck exists and the model name is correct.",
                    "imported": 0,
                    "failed": failed_count,
                }

            return {
                "success": len(successful) > 0,
                "imported": len(successful),
                "failed": failed_count,
                "note_ids": successful,
                "deck": deck_name,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def export_to_markdown(
        deck_name: str,
        limit: int | None = None,
        include_tags: bool = True,
    ) -> dict:
        """Export a deck to Markdown format.

        Args:
            deck_name: The deck to export.
            limit: Maximum number of notes to export.
            include_tags: Include tags in export (default: True).

        Returns:
            Markdown content with all notes.
        """
        try:
            actions = get_anki_actions()

            # Get notes from deck
            note_ids = await actions.find_notes(f'deck:"{deck_name}"')
            if limit:
                note_ids = note_ids[:limit]

            if not note_ids:
                return {"error": f"No notes found in deck '{deck_name}'"}

            notes = await actions.get_notes_info(note_ids)

            # Build Markdown
            lines = [f"# {deck_name}\n"]

            for note in notes:
                fields = {name: field.value for name, field in note.fields.items()}

                # Detect card type
                if "Text" in fields:  # Cloze
                    lines.append(f"\n{fields['Text']}\n")
                else:
                    front = fields.get("Front", fields.get(list(fields.keys())[0], ""))
                    back = fields.get("Back", fields.get(list(fields.keys())[1], "") if len(fields) > 1 else "")
                    lines.append(f"\n## {front}\n{back}\n")

                if include_tags and note.tags:
                    lines.append(f"Tags: {', '.join(note.tags)}\n")

            content = "\n".join(lines)

            return {
                "deck": deck_name,
                "notes_exported": len(notes),
                "content": content,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def export_to_csv(
        deck_name: str,
        limit: int | None = None,
        include_tags: bool = True,
    ) -> dict:
        """Export a deck to CSV format.

        Args:
            deck_name: The deck to export.
            limit: Maximum number of notes to export.
            include_tags: Include tags column (default: True).

        Returns:
            CSV content with all notes.
        """
        try:
            actions = get_anki_actions()

            # Get notes from deck
            note_ids = await actions.find_notes(f'deck:"{deck_name}"')
            if limit:
                note_ids = note_ids[:limit]

            if not note_ids:
                return {"error": f"No notes found in deck '{deck_name}'"}

            notes = await actions.get_notes_info(note_ids)

            # Get field names from first note
            if not notes:
                return {"error": "No notes to export"}

            first_fields = list(notes[0].fields.keys())

            # Build CSV
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            header = first_fields.copy()
            if include_tags:
                header.append("Tags")
            writer.writerow(header)

            # Data rows
            for note in notes:
                row = [note.fields.get(f, type("", (), {"value": ""})()).value for f in first_fields]
                if include_tags:
                    row.append(" ".join(note.tags))
                writer.writerow(row)

            content = output.getvalue()

            return {
                "deck": deck_name,
                "notes_exported": len(notes),
                "content": content,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def export_to_json(
        deck_name: str,
        limit: int | None = None,
    ) -> dict:
        """Export a deck to JSON format.

        Args:
            deck_name: The deck to export.
            limit: Maximum number of notes to export.

        Returns:
            JSON content with all notes.
        """
        try:
            actions = get_anki_actions()

            # Get notes from deck
            note_ids = await actions.find_notes(f'deck:"{deck_name}"')
            if limit:
                note_ids = note_ids[:limit]

            if not note_ids:
                return {"error": f"No notes found in deck '{deck_name}'"}

            notes = await actions.get_notes_info(note_ids)

            # Build JSON structure
            export_data: dict[str, Any] = {
                "deck": deck_name,
                "exported_at": __import__("datetime").datetime.now().isoformat(),
                "notes": [],
            }

            for note in notes:
                fields = {name: field.value for name, field in note.fields.items()}
                export_data["notes"].append({
                    "note_id": note.note_id,
                    "model": note.model_name,
                    "fields": fields,
                    "tags": note.tags,
                })

            content = json.dumps(export_data, indent=2, ensure_ascii=False)

            return {
                "deck": deck_name,
                "notes_exported": len(notes),
                "content": content,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
