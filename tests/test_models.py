"""Tests for Pydantic models."""

import pytest

from anki_mcp.client.models import (
    CardEase,
    CardType,
    CardQueue,
    NoteInput,
    NoteInfo,
    CardInfo,
    DeckStats,
)


class TestEnums:
    """Test enum values."""

    def test_card_ease_values(self):
        """Test CardEase enum values."""
        assert CardEase.AGAIN == 1
        assert CardEase.HARD == 2
        assert CardEase.GOOD == 3
        assert CardEase.EASY == 4

    def test_card_type_values(self):
        """Test CardType enum values."""
        assert CardType.NEW == 0
        assert CardType.LEARNING == 1
        assert CardType.REVIEW == 2
        assert CardType.RELEARNING == 3

    def test_card_queue_values(self):
        """Test CardQueue enum values."""
        assert CardQueue.SUSPENDED == -1
        assert CardQueue.NEW == 0
        assert CardQueue.LEARNING == 1
        assert CardQueue.REVIEW == 2


class TestNoteInput:
    """Test NoteInput model."""

    def test_create_basic_note(self):
        """Test creating a basic note."""
        note = NoteInput(
            deckName="Test",
            modelName="Basic",
            fields={"Front": "Question", "Back": "Answer"},
            tags=["test"],
        )

        assert note.deck_name == "Test"
        assert note.model_name == "Basic"
        assert note.fields["Front"] == "Question"
        assert note.tags == ["test"]

    def test_note_optional_fields(self):
        """Test optional fields default to None/empty."""
        note = NoteInput(
            deckName="Test",
            modelName="Basic",
            fields={"Front": "Q", "Back": "A"},
        )

        assert note.tags == []
        assert note.audio is None
        assert note.video is None
        assert note.picture is None
        assert note.options is None


class TestDeckStats:
    """Test DeckStats model."""

    def test_create_deck_stats(self):
        """Test creating deck stats."""
        stats = DeckStats(
            deck_id=1,
            name="Test",
            new_count=10,
            learn_count=5,
            review_count=20,
            total_in_deck=100,
        )

        assert stats.deck_id == 1
        assert stats.name == "Test"
        assert stats.new_count == 10
        assert stats.total_in_deck == 100
