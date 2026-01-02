"""MCP Tools for Anki statistics operations."""

from datetime import datetime, timedelta

from mcp.server.fastmcp import FastMCP

from anki_mcp.client.base import AnkiConnectError
from anki_mcp.client.models import CardType
from anki_mcp.server import get_anki_actions


def register_statistics_tools(mcp: FastMCP) -> None:
    """Register statistics-related tools with the MCP server.

    Tools:
    - get_collection_stats: Get overall collection statistics
    - get_deck_stats: Get statistics for a specific deck
    - get_reviews_today: Get today's review statistics
    - get_review_history: Get review history over time
    - predict_workload: Predict future review workload
    - analyze_retention: Analyze card retention rates
    - get_learning_insights: Get insights about learning patterns
    """

    @mcp.tool()
    async def get_collection_stats() -> dict:
        """Get overall statistics for the entire Anki collection.

        Returns:
            Total counts for notes, cards, decks, and models.
        """
        try:
            actions = get_anki_actions()

            # Get counts
            decks = await actions.get_deck_names()
            models = await actions.get_model_names()
            all_notes = await actions.find_notes("deck:*")
            all_cards = await actions.find_cards("deck:*")

            # Get card states
            new_cards = await actions.find_cards("is:new")
            learning_cards = await actions.find_cards("is:learn")
            review_cards = await actions.find_cards("is:review")
            suspended_cards = await actions.find_cards("is:suspended")

            # Today's reviews
            reviews_today = await actions.get_num_cards_reviewed_today()

            return {
                "total_notes": len(all_notes),
                "total_cards": len(all_cards),
                "total_decks": len(decks),
                "total_models": len(models),
                "card_states": {
                    "new": len(new_cards),
                    "learning": len(learning_cards),
                    "review": len(review_cards),
                    "suspended": len(suspended_cards),
                },
                "reviews_today": reviews_today,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_deck_stats(deck_name: str) -> dict:
        """Get detailed statistics for a specific deck.

        Args:
            deck_name: The deck name to analyze.

        Returns:
            Detailed statistics including card counts and averages.
        """
        try:
            actions = get_anki_actions()

            # Verify deck exists
            decks = await actions.get_deck_names()
            if deck_name not in decks:
                return {"error": f"Deck '{deck_name}' not found"}

            # Get basic stats
            stats = await actions.get_deck_stats([deck_name])
            deck_stats = stats.get(deck_name)

            # Get card IDs for analysis
            all_cards_query = f'deck:"{deck_name}"'
            card_ids = await actions.find_cards(all_cards_query)

            if not card_ids:
                return {
                    "deck": deck_name,
                    "total_cards": 0,
                    "message": "Deck is empty",
                }

            # Get detailed card info (sample for large decks)
            sample_ids = card_ids[:100]
            cards = await actions.get_cards_info(sample_ids)

            # Calculate averages
            intervals = [c.interval for c in cards if c.interval > 0]
            ease_factors = [c.factor for c in cards if c.factor > 0]
            lapses = [c.lapses for c in cards]

            avg_interval = sum(intervals) / len(intervals) if intervals else 0
            avg_ease = sum(ease_factors) / len(ease_factors) / 1000 if ease_factors else 0
            total_lapses = sum(lapses)

            # Count by type
            type_counts = {
                "new": sum(1 for c in cards if c.type == CardType.NEW),
                "learning": sum(1 for c in cards if c.type == CardType.LEARNING),
                "review": sum(1 for c in cards if c.type == CardType.REVIEW),
                "relearning": sum(1 for c in cards if c.type == CardType.RELEARNING),
            }

            return {
                "deck": deck_name,
                "total_cards": len(card_ids),
                "due_now": {
                    "new": deck_stats.new_count if deck_stats else 0,
                    "learning": deck_stats.learn_count if deck_stats else 0,
                    "review": deck_stats.review_count if deck_stats else 0,
                },
                "card_types": type_counts,
                "averages": {
                    "interval_days": round(avg_interval, 1),
                    "ease_factor": round(avg_ease, 2),
                },
                "total_lapses": total_lapses,
                "sample_size": len(cards),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_reviews_today() -> dict:
        """Get detailed statistics about today's reviews.

        Returns:
            Number of reviews, cards studied, and estimated time.
        """
        try:
            actions = get_anki_actions()

            reviews_today = await actions.get_num_cards_reviewed_today()

            # Get cards due
            due_cards = await actions.find_cards("is:due")
            new_cards = await actions.find_cards("is:new")

            # Estimate remaining time (rough: 10 seconds per card)
            remaining_reviews = len(due_cards)
            estimated_minutes = remaining_reviews * 10 / 60

            return {
                "reviews_completed": reviews_today,
                "cards_remaining": {
                    "due": len(due_cards),
                    "new": len(new_cards),
                    "total": len(due_cards) + len(new_cards),
                },
                "estimated_time_minutes": round(estimated_minutes, 1),
                "message": f"Completed {reviews_today} reviews today. {len(due_cards)} cards still due.",
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_review_history(days: int = 30) -> dict:
        """Get review history over a period of time.

        Args:
            days: Number of days to look back (default: 30).

        Returns:
            Daily review counts and trends.
        """
        try:
            actions = get_anki_actions()

            # Get reviews by day
            reviews_by_day = await actions.get_num_cards_reviewed_by_day()

            # Filter to requested period
            today = datetime.now().date()
            cutoff = today - timedelta(days=days)

            filtered_reviews = []
            total_reviews = 0

            for entry in reviews_by_day:
                if len(entry) >= 2:
                    # Entry format: [timestamp, count]
                    date_str = str(entry[0])
                    count = entry[1]

                    # Parse date (Anki uses days since epoch)
                    try:
                        review_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        continue

                    if review_date >= cutoff:
                        filtered_reviews.append({
                            "date": review_date.isoformat(),
                            "count": count,
                        })
                        total_reviews += count

            # Calculate average
            avg_per_day = total_reviews / days if days > 0 else 0

            # Find streaks
            streak = 0
            current_date = today
            for entry in sorted(filtered_reviews, key=lambda x: x["date"], reverse=True):
                entry_date = datetime.fromisoformat(entry["date"]).date()
                if entry_date == current_date and entry["count"] > 0:
                    streak += 1
                    current_date -= timedelta(days=1)
                else:
                    break

            return {
                "period_days": days,
                "total_reviews": total_reviews,
                "average_per_day": round(avg_per_day, 1),
                "current_streak": streak,
                "daily_reviews": filtered_reviews[-14:],  # Last 14 days
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def predict_workload(days_ahead: int = 7) -> dict:
        """Predict future review workload.

        Args:
            days_ahead: Number of days to predict (default: 7).

        Returns:
            Predicted daily review counts.
        """
        try:
            actions = get_anki_actions()

            predictions = []
            today = datetime.now().date()

            for i in range(days_ahead):
                target_date = today + timedelta(days=i)

                # Query for cards due on this day
                # prop:due uses days from today (0 = today)
                query = f"prop:due={i}"
                due_cards = await actions.find_cards(query)

                predictions.append({
                    "date": target_date.isoformat(),
                    "day_name": target_date.strftime("%A"),
                    "predicted_reviews": len(due_cards),
                })

            total_predicted = sum(p["predicted_reviews"] for p in predictions)
            avg_predicted = total_predicted / days_ahead if days_ahead > 0 else 0

            return {
                "period_days": days_ahead,
                "predictions": predictions,
                "total_predicted": total_predicted,
                "average_per_day": round(avg_predicted, 1),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def analyze_retention(deck_name: str | None = None) -> dict:
        """Analyze card retention rates.

        Args:
            deck_name: Optional deck to analyze. Analyzes all decks if not specified.

        Returns:
            Retention analysis including mature card retention.
        """
        try:
            actions = get_anki_actions()

            # Build query
            base_query = f'deck:"{deck_name}"' if deck_name else "deck:*"

            # Get mature cards (interval >= 21 days)
            mature_query = f"{base_query} prop:ivl>=21"
            mature_ids = await actions.find_cards(mature_query)

            if not mature_ids:
                return {
                    "deck": deck_name or "All decks",
                    "mature_cards": 0,
                    "message": "Not enough mature cards for retention analysis",
                }

            # Sample mature cards
            sample_ids = mature_ids[:200]
            cards = await actions.get_cards_info(sample_ids)

            # Calculate retention (cards with low lapse rate)
            total_reviews = sum(c.reps for c in cards)
            total_lapses = sum(c.lapses for c in cards)

            retention_rate = 1 - (total_lapses / total_reviews) if total_reviews > 0 else 0

            # Categorize by ease
            easy_cards = [c for c in cards if c.factor >= 2500]
            normal_cards = [c for c in cards if 2000 <= c.factor < 2500]
            hard_cards = [c for c in cards if c.factor < 2000]

            return {
                "deck": deck_name or "All decks",
                "mature_cards": len(mature_ids),
                "sample_analyzed": len(cards),
                "retention_rate": f"{retention_rate:.1%}",
                "total_reviews": total_reviews,
                "total_lapses": total_lapses,
                "difficulty_distribution": {
                    "easy": len(easy_cards),
                    "normal": len(normal_cards),
                    "hard": len(hard_cards),
                },
                "interpretation": (
                    "Excellent retention" if retention_rate >= 0.9
                    else "Good retention" if retention_rate >= 0.8
                    else "Could improve - consider adding more context to hard cards"
                ),
            }
        except AnkiConnectError as e:
            return {"error": str(e)}

    @mcp.tool()
    async def get_learning_insights(deck_name: str | None = None) -> dict:
        """Get insights about learning patterns and suggestions.

        Args:
            deck_name: Optional deck to analyze.

        Returns:
            Learning insights and recommendations.
        """
        try:
            actions = get_anki_actions()

            base_query = f'deck:"{deck_name}"' if deck_name else "deck:*"

            # Gather data
            all_cards = await actions.find_cards(base_query)
            suspended = await actions.find_cards(f"{base_query} is:suspended")
            leeches = await actions.find_cards(f"{base_query} tag:leech")

            # Sample for detailed analysis
            sample_ids = all_cards[:100]
            cards = await actions.get_cards_info(sample_ids) if sample_ids else []

            # Calculate metrics
            avg_ease = sum(c.factor for c in cards if c.factor) / len([c for c in cards if c.factor]) / 1000 if cards else 0
            high_lapse_cards = [c for c in cards if c.lapses >= 5]

            insights = []
            recommendations = []

            # Analyze suspended cards
            if len(suspended) > len(all_cards) * 0.1:
                insights.append(f"High suspension rate: {len(suspended)}/{len(all_cards)} cards suspended")
                recommendations.append("Review suspended cards and consider deleting or reformulating")

            # Analyze leeches
            if leeches:
                insights.append(f"Found {len(leeches)} leech cards (repeatedly forgotten)")
                recommendations.append("Leech cards need reformulation - add mnemonics or split into simpler cards")

            # Analyze ease
            if avg_ease < 2.0:
                insights.append(f"Low average ease factor ({avg_ease:.2f}) indicates difficulty")
                recommendations.append("Cards may be too difficult - consider adding more context")
            elif avg_ease > 2.8:
                insights.append(f"High average ease factor ({avg_ease:.2f}) indicates good retention")

            # High lapse cards
            if high_lapse_cards:
                insights.append(f"{len(high_lapse_cards)} cards have 5+ lapses")
                recommendations.append("High-lapse cards need attention - add images, mnemonics, or reformulate")

            if not insights:
                insights.append("Collection looks healthy!")

            if not recommendations:
                recommendations.append("Keep up the consistent review schedule")

            return {
                "deck": deck_name or "All decks",
                "total_cards": len(all_cards),
                "suspended_cards": len(suspended),
                "leech_cards": len(leeches),
                "average_ease": round(avg_ease, 2),
                "insights": insights,
                "recommendations": recommendations,
            }
        except AnkiConnectError as e:
            return {"error": str(e)}
