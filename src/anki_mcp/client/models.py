"""Pydantic models for AnkiConnect data structures."""

from enum import IntEnum
from typing import Any

from pydantic import BaseModel, Field


class CardEase(IntEnum):
    """Card answer ease values for reviews."""

    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4


class CardType(IntEnum):
    """Card types in Anki."""

    NEW = 0
    LEARNING = 1
    REVIEW = 2
    RELEARNING = 3


class CardQueue(IntEnum):
    """Card queue values in Anki."""

    SUSPENDED = -1
    SIBLING_BURIED = -2
    MANUALLY_BURIED = -3
    NEW = 0
    LEARNING = 1
    REVIEW = 2
    DAY_LEARNING = 3
    PREVIEW = 4


# ============ Note Models ============


class NoteField(BaseModel):
    """A field in a note."""

    value: str = ""
    order: int = 0


class NoteInput(BaseModel):
    """Input model for creating a note."""

    model_config = {"populate_by_name": True, "protected_namespaces": ()}

    deck_name: str = Field(..., alias="deckName", description="Target deck name")
    model_name: str = Field(..., alias="modelName", description="Note type/model name")
    fields: dict[str, str] = Field(..., description="Field name to value mapping")
    tags: list[str] = Field(default_factory=list, description="Tags for the note")
    audio: list[dict[str, Any]] | None = Field(
        default=None, description="Audio attachments"
    )
    video: list[dict[str, Any]] | None = Field(
        default=None, description="Video attachments"
    )
    picture: list[dict[str, Any]] | None = Field(
        default=None, description="Picture attachments"
    )
    options: dict[str, Any] | None = Field(
        default=None, description="Additional options like allowDuplicate"
    )


class NoteInfo(BaseModel):
    """Information about an existing note."""

    model_config = {"populate_by_name": True, "protected_namespaces": ()}

    note_id: int = Field(..., alias="noteId")
    model_name: str = Field(..., alias="modelName")
    tags: list[str] = Field(default_factory=list)
    fields: dict[str, NoteField] = Field(default_factory=dict)
    cards: list[int] = Field(default_factory=list, description="Card IDs for this note")


# ============ Card Models ============


class CardInfo(BaseModel):
    """Information about a card."""

    model_config = {"populate_by_name": True, "protected_namespaces": ()}

    card_id: int = Field(..., alias="cardId")
    note_id: int = Field(..., alias="noteId")
    deck_name: str = Field(..., alias="deckName")
    model_name: str = Field(..., alias="modelName")
    fields: dict[str, NoteField] = Field(default_factory=dict)
    question: str = ""
    answer: str = ""
    ord: int = 0
    type: int = 0
    queue: int = 0
    due: int = 0
    interval: int = 0
    factor: int = 0
    reps: int = 0
    lapses: int = 0
    left: int = 0


# ============ Deck Models ============


class DeckInfo(BaseModel):
    """Information about a deck."""

    name: str
    deck_id: int = Field(..., alias="id")

    model_config = {"populate_by_name": True}


class DeckStats(BaseModel):
    """Statistics for a deck."""

    deck_id: int
    name: str
    new_count: int = 0
    learn_count: int = 0
    review_count: int = 0
    total_in_deck: int = 0


class DeckConfig(BaseModel):
    """Deck configuration/options."""

    id: int
    name: str
    autoplay: bool = True
    dyn: bool = False
    lapse: dict[str, Any] = Field(default_factory=dict)
    max_taken: int = Field(default=60, alias="maxTaken")
    new: dict[str, Any] = Field(default_factory=dict)
    replayq: bool = True
    rev: dict[str, Any] = Field(default_factory=dict)
    timer: int = 0

    model_config = {"populate_by_name": True}


# ============ Model (Note Type) Models ============


class ModelFieldInfo(BaseModel):
    """Information about a field in a note model."""

    name: str
    ord: int = 0
    sticky: bool = False
    rtl: bool = False
    font: str = "Arial"
    size: int = 20


class ModelInfo(BaseModel):
    """Information about a note model/type."""

    model_config = {"populate_by_name": True, "protected_namespaces": ()}

    name: str
    model_id: int = Field(default=0, alias="id")
    fields: list[str] = Field(default_factory=list, alias="flds")
    css: str = ""
    templates: list[dict[str, Any]] = Field(default_factory=list, alias="tmpls")


# ============ Review Models ============


class ReviewInfo(BaseModel):
    """Information about a review."""

    review_time: int = Field(..., alias="reviewTime")
    card_id: int = Field(..., alias="cardId")
    usn: int = 0
    button_chosen: int = Field(..., alias="buttonChosen")
    new_interval: int = Field(default=0, alias="newInterval")
    previous_interval: int = Field(default=0, alias="previousInterval")
    new_factor: int = Field(default=0, alias="newFactor")
    review_duration: int = Field(default=0, alias="reviewDuration")
    review_type: int = Field(default=0, alias="reviewType")

    model_config = {"populate_by_name": True}


# ============ Statistics Models ============


class CollectionStats(BaseModel):
    """Collection-wide statistics."""

    total_notes: int = 0
    total_cards: int = 0
    total_decks: int = 0
    total_models: int = 0
    reviews_today: int = 0
    new_today: int = 0


class DeckTreeNode(BaseModel):
    """A node in the deck tree."""

    name: str
    deck_id: int = Field(..., alias="id")
    children: list["DeckTreeNode"] = Field(default_factory=list)
    new_count: int = Field(default=0, alias="newCount")
    learn_count: int = Field(default=0, alias="learnCount")
    review_count: int = Field(default=0, alias="reviewCount")

    model_config = {"populate_by_name": True}
