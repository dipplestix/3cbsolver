"""Old-Growth Dryads card for the 3CB simulator."""
from typing import List, TYPE_CHECKING

from .base import Action
from .creature import Creature

if TYPE_CHECKING:
    from ..solver import GameState


class OldGrowthDryads(Creature):
    """
    Old-Growth Dryads - G
    Creature - Dryad
    3/3
    When Old-Growth Dryads enters the battlefield, each opponent may search
    their library for a basic land card, put it onto the battlefield tapped,
    then shuffle.

    Note: In 3CB format, there is no library, so the ETB has no effect.
    This is effectively a 3/3 for G with no drawback.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Old-Growth Dryads",
            owner=owner,
            power=3,
            toughness=3,
            mana_cost=1,
            mana_color='G',
            keywords=[]
        )

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        available = state.get_available_mana_by_color(self.owner)
        if available.get('G', 0) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    dryads = ns.hands[self.owner].pop(i)
                    dryads.entered_this_turn = True
                    ns.battlefield[self.owner].append(dryads)
                    break
            # Tap a green source to pay for it
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'mana_produced') and card.mana_produced == 'G' and not card.tapped:
                    card.tapped = True
                    break
            # ETB: Opponent may search for basic land - no effect in 3CB (no library)
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def copy(self) -> 'OldGrowthDryads':
        new_dryads = OldGrowthDryads(self.owner)
        new_dryads.tapped = self.tapped
        new_dryads.damage = self.damage
        new_dryads.attacking = self.attacking
        new_dryads.entered_this_turn = self.entered_this_turn
        return new_dryads


def create_old_growth_dryads(owner: int) -> OldGrowthDryads:
    return OldGrowthDryads(owner)
