"""Input validation utilities for Anki MCP operations.

This module provides validation functions to check inputs before sending to AnkiConnect,
providing clear error messages and suggestions when validation fails.
"""

from typing import Any

from anki_mcp.client.actions import AnkiActions


class ValidationError(Exception):
    """Validation error with user-friendly message and suggestions."""

    def __init__(self, message: str, suggestions: list[str] | None = None):
        self.message = message
        self.suggestions = suggestions or []
        super().__init__(message)


class NoteValidator:
    """Validates note input before sending to AnkiConnect."""

    def __init__(self, actions: AnkiActions):
        self.actions = actions
        # Caches to avoid repeated API calls
        self._deck_cache: list[str] | None = None
        self._model_cache: dict[str, list[str]] = {}

    async def validate_deck(self, deck_name: str) -> None:
        """Validate that a deck exists.

        Args:
            deck_name: Name of the deck to validate.

        Raises:
            ValidationError: If deck doesn't exist.
        """
        if self._deck_cache is None:
            self._deck_cache = await self.actions.get_deck_names()

        if deck_name not in self._deck_cache:
            # Provide helpful suggestions
            available = self._deck_cache[:5]  # Show first 5
            suggestions = [f"Available decks: {', '.join(available)}"]
            if len(self._deck_cache) > 5:
                suggestions.append(f"... and {len(self._deck_cache) - 5} more")
            suggestions.append("Tip: Use create_deck to create a new deck")

            raise ValidationError(
                f"Deck '{deck_name}' does not exist",
                suggestions=suggestions,
            )

    async def validate_model(self, model_name: str) -> list[str]:
        """Validate that a model exists and return its field names.

        Args:
            model_name: Name of the model to validate.

        Returns:
            List of field names for this model.

        Raises:
            ValidationError: If model doesn't exist.
        """
        if model_name not in self._model_cache:
            model_names = await self.actions.get_model_names()
            if model_name not in model_names:
                # Common models for suggestions
                common_models = ["Basic", "Cloze", "Basic (and reversed card)"]
                available_common = [m for m in common_models if m in model_names]

                suggestions = []
                if available_common:
                    suggestions.append(f"Common models: {', '.join(available_common)}")
                suggestions.append(f"All available: {', '.join(model_names[:5])}")
                if len(model_names) > 5:
                    suggestions.append(f"... and {len(model_names) - 5} more")

                raise ValidationError(
                    f"Model '{model_name}' does not exist",
                    suggestions=suggestions,
                )

            # Cache field names
            self._model_cache[model_name] = await self.actions.get_model_field_names(
                model_name
            )

        return self._model_cache[model_name]

    async def validate_fields(
        self, model_name: str, fields: dict[str, str]
    ) -> None:
        """Validate that fields match model schema and are not empty.

        Args:
            model_name: Name of the model.
            fields: Dictionary of field names to values.

        Raises:
            ValidationError: If fields don't match or are empty.
        """
        # Get required fields for this model
        required_fields = await self.validate_model(model_name)

        # Check for missing fields
        required_set = set(required_fields)
        provided_set = set(fields.keys())

        missing = required_set - provided_set
        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(sorted(missing))}",
                suggestions=[
                    f"Model '{model_name}' requires: {', '.join(required_fields)}"
                ],
            )

        # Check for extra fields
        extra = provided_set - required_set
        if extra:
            raise ValidationError(
                f"Unknown fields: {', '.join(sorted(extra))}",
                suggestions=[
                    f"Valid fields for '{model_name}': {', '.join(required_fields)}",
                    "Tip: Check for typos in field names",
                ],
            )

        # Check for empty fields
        empty_fields = []
        for field_name, value in fields.items():
            if not value or not str(value).strip():
                empty_fields.append(field_name)

        if empty_fields:
            raise ValidationError(
                f"Empty or whitespace-only fields: {', '.join(empty_fields)}",
                suggestions=[
                    "All fields must contain meaningful content",
                    "Provide text for each field",
                ],
            )

    async def validate_note_input(
        self, deck_name: str, model_name: str, fields: dict[str, str]
    ) -> None:
        """Validate all inputs for creating a note.

        Args:
            deck_name: Name of the deck.
            model_name: Name of the model.
            fields: Dictionary of field names to values.

        Raises:
            ValidationError: If any validation fails.
        """
        # Validate in order of specificity
        await self.validate_deck(deck_name)
        await self.validate_fields(model_name, fields)


def format_error_response(
    error: Exception, context: str = "Operation failed"
) -> dict[str, Any]:
    """Format an error into a standardized response.

    Args:
        error: The exception that occurred.
        context: Context about what operation failed.

    Returns:
        Dictionary with error information.
    """
    if isinstance(error, ValidationError):
        return {
            "success": False,
            "error": error.message,
            "suggestions": error.suggestions,
            "error_type": "validation",
        }

    # Generic error
    error_msg = str(error)
    return {
        "success": False,
        "error": f"{context}: {error_msg}",
        "error_type": "unknown",
    }
