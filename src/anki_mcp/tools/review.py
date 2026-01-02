"""MCP Tools for Anki review operations."""

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import CardEase, CardType
from anki_mcp.server import get_anki_actions


def register_review_tools(mcp: FastMCP) -> None:
    """Register review-related tools with the MCP server.

    Tools:
    - get_due_for_review: Get cards due for review
    - start_review_session: Start reviewing a deck
    - get_current_card: Get the current card in review
    - show_answer: Show the answer of current card
    - answer_card: Answer the current card
    - get_review_suggestion: Get AI suggestion for card difficulty
    """

    @mcp.tool()
    async def get_due_for_review(
        deck_name: str | None = None,
        limit: int = 20,
    ) -> dict:
        """Get cards that are due for review with their content.

        Args:
            deck_name: Optional deck to filter by.
            limit: Maximum number of cards to return (default: 20).

        Returns:
            List of due cards with question and answer previews.
        """
        try:
            actions = get_anki_actions()

            # Build query for due and new cards
            query = "(is:due OR is:new)"
            if deck_name:
                query = f'deck:"{deck_name}" {query}'

            card_ids = await actions.find_cards(query)
            card_ids = card_ids[:limit]

            if not card_ids:
                return {
                    "cards": [],
                    "total": 0,
                    "message": "No cards due for review",
                }

            cards = await actions.get_cards_info(card_ids)

            result = []
            new_count = 0
            review_count = 0

            for card in cards:
                is_new = card.type == CardType.NEW
                if is_new:
                    new_count += 1
                else:
                    review_count += 1

                # Clean HTML from question/answer for preview
                question = card.question.replace("<br>", " ").replace("\n", " ")
                answer = card.answer.replace("<br>", " ").replace("\n", " ")

                result.append({
                    "card_id": card.card_id,
                    "deck_name": card.deck_name,
                    "question": question[:200],
                    "answer": answer[:200],
                    "is_new": is_new,
                    "interval_days": card.interval if not is_new else None,
                    "ease_percent": round(card.factor / 10) if card.factor else None,
                })

            return {
                "cards": result,
                "total": len(result),
                "new_count": new_count,
                "review_count": review_count,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def start_review_session(deck_name: str) -> dict:
        """Start a review session for a deck in Anki.

        This opens the deck in Anki's review mode.

        Args:
            deck_name: The deck to start reviewing.

        Returns:
            Information about the review session.
        """
        try:
            actions = get_anki_actions()

            # Verify deck exists
            decks = await actions.get_deck_names()
            if deck_name not in decks:
                return {"error": f"Deck '{deck_name}' not found"}

            # Start the deck review in Anki GUI
            success = await actions.gui_deck_review(deck_name)

            if success:
                # Get current card
                current = await actions.gui_current_card()

                if current:
                    return {
                        "success": True,
                        "deck": deck_name,
                        "current_card": {
                            "card_id": current.card_id,
                            "question": current.question[:300],
                        },
                        "message": f"Started review session for '{deck_name}'",
                    }
                else:
                    return {
                        "success": True,
                        "deck": deck_name,
                        "current_card": None,
                        "message": "Review session started but no cards due",
                    }
            else:
                return {"error": "Failed to start review session"}
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_current_card() -> dict:
        """Get the current card being reviewed in Anki.

        Returns:
            The current card's question (answer hidden until show_answer is called).
        """
        try:
            actions = get_anki_actions()
            card = await actions.gui_current_card()

            if not card:
                return {
                    "card": None,
                    "message": "No card currently being reviewed. Start a review session first.",
                }

            return {
                "card_id": card.card_id,
                "deck_name": card.deck_name,
                "question": card.question,
                "note_id": card.note_id,
                "is_new": card.type == CardType.NEW,
                "interval_days": card.interval,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def show_answer() -> dict:
        """Show the answer side of the current card in Anki.

        Returns:
            The card's answer content.
        """
        try:
            actions = get_anki_actions()

            # Show answer in Anki GUI
            success = await actions.gui_show_answer()

            if not success:
                return {"error": "Failed to show answer. Is a card being reviewed?"}

            # Get the current card with answer
            card = await actions.gui_current_card()

            if not card:
                return {"error": "No card being reviewed"}

            return {
                "card_id": card.card_id,
                "question": card.question,
                "answer": card.answer,
                "interval_days": card.interval,
                "ease_percent": round(card.factor / 10) if card.factor else None,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def answer_card(ease: int) -> dict:
        """Answer the current card in Anki's review.

        Args:
            ease: The answer button to press:
                1 = Again (forgot, reset interval)
                2 = Hard (longer delay before Again reset)
                3 = Good (normal progression)
                4 = Easy (longer interval bonus)

        Returns:
            Confirmation and next card info if available.
        """
        try:
            if ease not in [1, 2, 3, 4]:
                return {"error": "Ease must be 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy)"}

            actions = get_anki_actions()

            # Get current card before answering
            current = await actions.gui_current_card()
            if not current:
                return {"error": "No card being reviewed"}

            # Answer the card
            ease_enum = CardEase(ease)
            success = await actions.gui_answer_card(ease_enum)

            if not success:
                return {"error": "Failed to answer card"}

            # Get next card
            next_card = await actions.gui_current_card()

            ease_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}

            result = {
                "success": True,
                "answered_card_id": current.card_id,
                "answer": ease_names[ease],
            }

            if next_card:
                result["next_card"] = {
                    "card_id": next_card.card_id,
                    "question": next_card.question[:300],
                }
            else:
                result["message"] = "Review session complete! No more cards due."

            return result
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_review_suggestion(card_id: int) -> dict:
        """Get a review suggestion based on card history.

        Analyzes the card's review history to suggest the appropriate ease.

        Args:
            card_id: The card ID to analyze.

        Returns:
            Suggestion with reasoning based on card statistics.
        """
        try:
            actions = get_anki_actions()

            # Get card info
            cards = await actions.get_cards_info([card_id])
            if not cards:
                return {"error": f"Card {card_id} not found"}

            card = cards[0]

            # Get review history
            reviews = await actions.get_reviews_of_cards([card_id])
            card_reviews = reviews.get(card_id, [])

            # Analyze
            total_reviews = card.reps
            lapses = card.lapses
            interval = card.interval
            ease_factor = card.factor / 1000 if card.factor else 2.5

            # Calculate lapse rate
            lapse_rate = lapses / total_reviews if total_reviews > 0 else 0

            # Build suggestion
            if card.type == CardType.NEW:
                suggestion = "This is a new card. Answer based on how well you know it."
                recommended = None
            elif lapse_rate > 0.3:
                suggestion = f"High lapse rate ({lapse_rate:.0%}). Consider using 'Again' or 'Hard' to strengthen memory."
                recommended = 2  # Hard
            elif ease_factor < 2.0:
                suggestion = f"Low ease factor ({ease_factor:.2f}). This card is difficult. Take your time."
                recommended = 2  # Hard
            elif interval > 60 and lapse_rate < 0.1:
                suggestion = f"Long interval ({interval} days) with low lapse rate. Card is well learned."
                recommended = 3  # Good
            else:
                suggestion = "Card has normal difficulty. Answer honestly."
                recommended = 3  # Good

            return {
                "card_id": card_id,
                "statistics": {
                    "total_reviews": total_reviews,
                    "lapses": lapses,
                    "lapse_rate": f"{lapse_rate:.1%}",
                    "interval_days": interval,
                    "ease_factor": f"{ease_factor:.2f}",
                },
                "suggestion": suggestion,
                "recommended_ease": recommended,
                "ease_options": {
                    1: "Again - Forgot completely",
                    2: "Hard - Recalled with difficulty",
                    3: "Good - Recalled correctly",
                    4: "Easy - Very easy recall",
                },
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
