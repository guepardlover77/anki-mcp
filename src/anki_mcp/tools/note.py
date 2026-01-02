"""MCP Tools for Anki note operations."""

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import NoteInput
from anki_mcp.server import get_anki_actions


def register_note_tools(mcp: FastMCP) -> None:
    """Register note-related tools with the MCP server.

    Tools:
    - add_note: Add a single note
    - add_notes_batch: Add multiple notes at once
    - update_note: Update note fields
    - delete_notes: Delete notes
    - find_notes: Search for notes
    - get_note_info: Get note details
    - add_tags: Add tags to notes
    - remove_tags: Remove tags from notes
    """

    @mcp.tool()
    async def add_note(
        deck_name: str,
        model_name: str,
        fields: dict[str, str],
        tags: list[str] | None = None,
        allow_duplicate: bool = False,
    ) -> dict:
        """Add a single note to Anki.

        Args:
            deck_name: Target deck name.
            model_name: Note type (e.g., "Basic", "Cloze", "Basic (and reversed card)").
            fields: Dictionary of field names to values (e.g., {"Front": "Question", "Back": "Answer"}).
            tags: Optional list of tags.
            allow_duplicate: Allow adding duplicate notes (default: False).

        Returns:
            The created note's ID.

        Example:
            add_note(
                deck_name="French",
                model_name="Basic",
                fields={"Front": "Bonjour", "Back": "Hello"},
                tags=["vocabulary", "greetings"]
            )
        """
        try:
            actions = get_anki_actions()

            options = None
            if allow_duplicate:
                options = {"allowDuplicate": True}

            note = NoteInput(
                deckName=deck_name,
                modelName=model_name,
                fields=fields,
                tags=tags or [],
                options=options,
            )

            note_id = await actions.add_note(note)
            return {
                "success": True,
                "note_id": note_id,
                "deck": deck_name,
                "model": model_name,
                "message": "Note added successfully",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def add_notes_batch(
        deck_name: str,
        model_name: str,
        notes_data: list[dict],
        tags: list[str] | None = None,
    ) -> dict:
        """Add multiple notes at once.

        Args:
            deck_name: Target deck name for all notes.
            model_name: Note type for all notes.
            notes_data: List of dictionaries, each containing:
                - fields: Dictionary of field names to values
                - tags: Optional list of tags (in addition to common tags)
            tags: Optional common tags for all notes.

        Returns:
            List of created note IDs (None for failed notes).

        Example:
            add_notes_batch(
                deck_name="French",
                model_name="Basic",
                notes_data=[
                    {"fields": {"Front": "Bonjour", "Back": "Hello"}},
                    {"fields": {"Front": "Merci", "Back": "Thank you"}, "tags": ["polite"]},
                ],
                tags=["vocabulary"]
            )
        """
        try:
            actions = get_anki_actions()

            notes = []
            for note_data in notes_data:
                note_tags = list(tags or [])
                if "tags" in note_data:
                    note_tags.extend(note_data["tags"])

                notes.append(
                    NoteInput(
                        deckName=deck_name,
                        modelName=model_name,
                        fields=note_data["fields"],
                        tags=note_tags,
                    )
                )

            note_ids = await actions.add_notes(notes)

            successful = sum(1 for nid in note_ids if nid is not None)
            failed = len(note_ids) - successful

            return {
                "success": True,
                "note_ids": note_ids,
                "total": len(note_ids),
                "successful": successful,
                "failed": failed,
                "message": f"Added {successful} notes, {failed} failed",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def update_note(
        note_id: int,
        fields: dict[str, str] | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Update an existing note.

        Args:
            note_id: The note ID to update.
            fields: New field values (only specified fields are updated).
            tags: New tags (replaces all existing tags).

        Returns:
            Confirmation of update.
        """
        try:
            actions = get_anki_actions()

            if fields:
                await actions.update_note_fields(note_id, fields)

            if tags is not None:
                await actions.update_note_tags(note_id, tags)

            return {
                "success": True,
                "note_id": note_id,
                "fields_updated": bool(fields),
                "tags_updated": tags is not None,
                "message": "Note updated successfully",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def delete_notes(note_ids: list[int]) -> dict:
        """Delete notes from Anki.

        Args:
            note_ids: List of note IDs to delete.

        Returns:
            Confirmation of deletion.
        """
        try:
            actions = get_anki_actions()
            await actions.delete_notes(note_ids)
            return {
                "success": True,
                "deleted_count": len(note_ids),
                "message": f"Deleted {len(note_ids)} notes",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def find_notes(
        query: str,
        limit: int | None = None,
    ) -> dict:
        """Search for notes using Anki's search syntax.

        Args:
            query: Anki search query. Examples:
                - "deck:French" - notes in French deck
                - "tag:vocabulary" - notes with vocabulary tag
                - "front:*bonjour*" - notes with bonjour in Front field
                - "is:new" - new notes
                - "is:due" - due notes
                - "added:7" - added in last 7 days
                - "rated:1" - reviewed today
            limit: Maximum number of results to return.

        Returns:
            List of matching note IDs.
        """
        try:
            actions = get_anki_actions()
            note_ids = await actions.find_notes(query)

            if limit:
                note_ids = note_ids[:limit]

            return {
                "note_ids": note_ids,
                "count": len(note_ids),
                "query": query,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_note_info(note_ids: list[int]) -> dict:
        """Get detailed information about notes.

        Args:
            note_ids: List of note IDs to retrieve.

        Returns:
            Detailed note information including fields, tags, and cards.
        """
        try:
            actions = get_anki_actions()
            notes = await actions.get_notes_info(note_ids)

            result = []
            for note in notes:
                fields_dict = {
                    name: field.value for name, field in note.fields.items()
                }
                result.append({
                    "note_id": note.note_id,
                    "model_name": note.model_name,
                    "tags": note.tags,
                    "fields": fields_dict,
                    "card_ids": note.cards,
                })

            return {
                "notes": result,
                "count": len(result),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def add_tags(note_ids: list[int], tags: list[str]) -> dict:
        """Add tags to notes.

        Args:
            note_ids: List of note IDs.
            tags: Tags to add.

        Returns:
            Confirmation of tag addition.
        """
        try:
            actions = get_anki_actions()
            tags_str = " ".join(tags)
            await actions.add_tags(note_ids, tags_str)
            return {
                "success": True,
                "note_count": len(note_ids),
                "tags_added": tags,
                "message": f"Added {len(tags)} tags to {len(note_ids)} notes",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def remove_tags(note_ids: list[int], tags: list[str]) -> dict:
        """Remove tags from notes.

        Args:
            note_ids: List of note IDs.
            tags: Tags to remove.

        Returns:
            Confirmation of tag removal.
        """
        try:
            actions = get_anki_actions()
            tags_str = " ".join(tags)
            await actions.remove_tags(note_ids, tags_str)
            return {
                "success": True,
                "note_count": len(note_ids),
                "tags_removed": tags,
                "message": f"Removed {len(tags)} tags from {len(note_ids)} notes",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
