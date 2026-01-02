"""Undiscovered Paradise card for the 3CB simulator."""
from typing import List, TYPE_CHECKING

from .base import Action
from .land import Land

if TYPE_CHECKING:
    from ..solver import GameState


class UndiscoveredParadise(Land):
    """
    Undiscovered Paradise - Land
    T: Add one mana of any color.
    During your next untap step, as you untap your permanents,
    return Undiscovered Paradise to its owner's hand.
    """

    def __init__(self, owner: int):
        super().__init__("Undiscovered Paradise", owner, 'any')
        self.return_to_hand = False

    def get_signature_state(self) -> tuple:
        """Return paradise-specific state including bounce flag."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            self.return_to_hand,
        )

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.land_played_this_turn:
            return []
        if state.phase != "main1":
            return []

        def play_land(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    card_copy = ns.hands[self.owner].pop(i)
                    card_copy.entered_this_turn = True
                    ns.battlefield[self.owner].append(card_copy)
                    break
            ns.land_played_this_turn = True
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'plus_counters'):
                    card.plus_counters += 1
            return ns

        return [Action(f"Play {self.name}", play_land)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Can tap Paradise to trigger the bounce (for landfall synergy)."""
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []
        if self.tapped:
            return []
        if self.return_to_hand:
            return []

        def tap_for_mana(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, UndiscoveredParadise):
                    card.tapped = True
                    card.return_to_hand = True
                    break
            return ns

        return [Action(f"Tap {self.name} (will bounce)", tap_for_mana)]

    def copy(self) -> 'UndiscoveredParadise':
        new_land = UndiscoveredParadise(self.owner)
        new_land.tapped = self.tapped
        new_land.entered_this_turn = self.entered_this_turn
        new_land.return_to_hand = self.return_to_hand
        return new_land


def create_undiscovered_paradise(owner: int) -> UndiscoveredParadise:
    return UndiscoveredParadise(owner)
