"""Crystal Vein - Land that can sacrifice for extra colorless mana.

Scryfall Oracle Text:
---------------------
Crystal Vein
Land

{T}: Add {C}.
{T}, Sacrifice Crystal Vein: Add {C}{C}.
"""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action

if TYPE_CHECKING:
    from ..game_state import GameState


class CrystalVein(Land):
    """Crystal Vein - taps for {C} or sacrifices for {C}{C}.

    In 3CB context, we model Crystal Vein as always sacrificing for {C}{C}
    when tapped. This is a simplification that works for decks that need
    the extra mana (like the SOLDIER deck). The normal tap-for-1 mode
    is rarely optimal when you have limited lands.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Crystal Vein",
            owner=owner,
            mana_produced='C'
        )

    def get_mana_output(self) -> int:
        """Crystal Vein produces 2 colorless when sacrificed."""
        return 2

    def tap_for_mana(self) -> int:
        """Tap and sacrifice for 2 colorless mana."""
        if self.tapped:
            return 0
        self.tapped = True
        return 2

    def should_sacrifice_after_tap(self) -> bool:
        """Crystal Vein sacrifices when tapped for mana."""
        return True

    def get_signature_state(self) -> tuple:
        """Return state for memoization."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
        )

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Crystal Vein has no activated abilities - sacrifice is automatic."""
        return []

    def copy(self) -> 'CrystalVein':
        new_vein = CrystalVein(self.owner)
        new_vein.tapped = self.tapped
        new_vein.entered_this_turn = self.entered_this_turn
        return new_vein


def create_crystal_vein(owner: int) -> CrystalVein:
    """Factory function for Crystal Vein."""
    return CrystalVein(owner)
