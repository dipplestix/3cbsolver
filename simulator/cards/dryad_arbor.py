"""Dryad Arbor card for the 3CB simulator."""
from typing import List, TYPE_CHECKING

from .base import Card, Action, CardType
from .creature import Creature

if TYPE_CHECKING:
    from ..solver import GameState


class DryadArbor(Creature):
    """
    Dryad Arbor
    Land Creature - Forest Dryad
    1/1
    (Dryad Arbor isn't a spell, it's affected by summoning sickness,
    and it has "T: Add G.")

    Note: As a creature, it has summoning sickness and can't tap for mana
    the turn it enters. It counts as your land play for the turn.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Dryad Arbor",
            owner=owner,
            power=1,
            toughness=1,
            # No mana cost - it's a land, not a spell
            keywords=[]
        )
        self.card_type = CardType.LAND  # It's also a land
        self.mana_produced = 'G'
        self.is_land = True

    def get_mana_output(self) -> int:
        """Dryad Arbor produces 1 green mana."""
        return 1

    def tap_for_mana(self) -> int:
        """Tap for 1 green mana."""
        if self.tapped:
            return 0
        self.tapped = True
        return 1

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        """Play as a land (uses land drop, not a spell)."""
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
                    arbor = ns.hands[self.owner].pop(i)
                    arbor.entered_this_turn = True
                    ns.battlefield[self.owner].append(arbor)
                    break
            ns.land_played_this_turn = True
            # Trigger landfall for any creatures that care
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'plus_counters') and card.name != self.name:
                    card.plus_counters += 1
            return ns

        return [Action(f"Play {self.name}", play_land)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Can tap for G, but not if it has summoning sickness."""
        # Creatures can't tap for mana if they have summoning sickness
        # (entered this turn)
        if self.entered_this_turn:
            return []
        if self.tapped:
            return []
        # No activated abilities needed - mana is handled by get_available_mana
        return []

    def copy(self) -> 'DryadArbor':
        new_arbor = DryadArbor(self.owner)
        new_arbor.tapped = self.tapped
        new_arbor.damage = self.damage
        new_arbor.attacking = self.attacking
        new_arbor.entered_this_turn = self.entered_this_turn
        return new_arbor


def create_dryad_arbor(owner: int) -> DryadArbor:
    return DryadArbor(owner)
