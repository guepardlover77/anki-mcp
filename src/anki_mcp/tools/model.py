"""MCP Tools for Anki model (note type) operations."""

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.server import get_anki_actions


def register_model_tools(mcp: FastMCP) -> None:
    """Register model-related tools with the MCP server.

    Tools:
    - list_models: List all note types
    - get_model_info: Get model details
    - get_model_fields: Get model field names
    - find_notes_by_model: Find notes using a specific model
    """

    @mcp.tool()
    async def list_models() -> dict:
        """List all note types (models) in Anki.

        Returns:
            List of all models with their IDs and field names.
        """
        try:
            actions = get_anki_actions()
            models = await actions.get_model_names_and_ids()

            result = []
            for name, model_id in sorted(models.items()):
                fields = await actions.get_model_field_names(name)
                result.append({
                    "name": name,
                    "id": model_id,
                    "fields": fields,
                    "field_count": len(fields),
                })

            return {
                "models": result,
                "total": len(result),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_model_info(model_name: str) -> dict:
        """Get detailed information about a note type.

        Args:
            model_name: The name of the model (e.g., "Basic", "Cloze").

        Returns:
            Model details including fields.
        """
        try:
            actions = get_anki_actions()

            # Verify model exists
            models = await actions.get_model_names()
            if model_name not in models:
                return {"error": f"Model '{model_name}' not found"}

            model = await actions.get_model_info(model_name)

            # Count notes using this model
            notes = await actions.find_notes(f'note:"{model_name}"')

            return {
                "name": model.name,
                "id": model.model_id,
                "fields": model.fields,
                "notes_using_model": len(notes),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_model_fields(model_name: str) -> dict:
        """Get field names for a specific note type.

        Args:
            model_name: The name of the model.

        Returns:
            List of field names in order.
        """
        try:
            actions = get_anki_actions()

            # Verify model exists
            models = await actions.get_model_names()
            if model_name not in models:
                return {"error": f"Model '{model_name}' not found"}

            fields = await actions.get_model_field_names(model_name)

            return {
                "model": model_name,
                "fields": fields,
                "first_field": fields[0] if fields else None,
                "field_count": len(fields),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def find_notes_by_model(
        model_name: str,
        limit: int | None = None,
    ) -> dict:
        """Find all notes using a specific model.

        Args:
            model_name: The model name to search for.
            limit: Maximum number of results.

        Returns:
            List of note IDs using this model.
        """
        try:
            actions = get_anki_actions()

            # Verify model exists
            models = await actions.get_model_names()
            if model_name not in models:
                return {"error": f"Model '{model_name}' not found"}

            note_ids = await actions.find_notes(f'note:"{model_name}"')

            if limit:
                note_ids = note_ids[:limit]

            return {
                "model": model_name,
                "note_ids": note_ids,
                "count": len(note_ids),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
