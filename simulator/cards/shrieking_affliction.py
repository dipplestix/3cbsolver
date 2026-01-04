"""Shrieking Affliction - Enchantment that punishes empty hands."""
from typing import TYPE_CHECKING

from .enchantment import Enchantment

if TYPE_CHECKING:
    from ..game_state import GameState


class ShriekingAffliction(Enchantment):
    """
    Shrieking Affliction - {B}
    Enchantment

    At the beginning of each opponent's upkeep, if that player has
    one or fewer cards in hand, they lose 3 life.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Shrieking Affliction",
            owner=owner,
            color_costs={'B': 1}
        )

    def on_opponent_upkeep(self, state: 'GameState') -> 'GameState':
        """Check if opponent has <= 1 card in hand, deal 3 damage if so."""
        opponent = state.active_player  # The active player is our opponent

        # Check condition: opponent has one or fewer cards in hand
        if len(state.hands[opponent]) <= 1:
            ns = state.copy()
            ns.life[opponent] -= 3

            # Check for game over
            if ns.life[opponent] <= 0:
                ns.game_over = True
                ns.winner = self.owner

            return ns

        return state

    def copy(self) -> 'ShriekingAffliction':
        """Create a deep copy of this card."""
        new_card = ShriekingAffliction(self.owner)
        new_card.tapped = self.tapped
        return new_card


def create_shrieking_affliction(owner: int) -> ShriekingAffliction:
    """Factory function for Shrieking Affliction."""
    return ShriekingAffliction(owner)
