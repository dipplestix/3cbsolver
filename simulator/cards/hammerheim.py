"""Hammerheim - Legendary land with creature-targeting ability."""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class Hammerheim(Land):
    """
    Hammerheim
    Legendary Land

    {T}: Add {R}.
    {T}: Target creature loses all landwalk abilities until end of turn.
    """

    def __init__(self, owner: int):
        super().__init__("Hammerheim", owner, mana_produced='R')
        self.is_legendary = True

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Can tap to target a creature (useful for triggering Valiant)."""
        if self.tapped:
            return []

        actions = []

        # Target each creature on our side (for Valiant triggers)
        for card in state.battlefield[self.owner]:
            if hasattr(card, 'power'):  # It's a creature
                def make_target_action(creature_name):
                    def target_creature(s: 'GameState') -> 'GameState':
                        ns = s.copy()
                        # Tap Hammerheim
                        for c in ns.battlefield[self.owner]:
                            if c.name == "Hammerheim":
                                c.tapped = True
                                break
                        # Trigger "becomes target" for the creature
                        for c in ns.battlefield[self.owner]:
                            if c.name == creature_name:
                                if hasattr(c, 'on_become_target'):
                                    ns = c.on_become_target(ns)
                                break
                        return ns
                    return target_creature
                actions.append(Action(f"Hammerheim targets {card.name}",
                                     make_target_action(card.name)))

        return actions

    def copy(self) -> 'Hammerheim':
        new_land = Hammerheim(self.owner)
        new_land.tapped = self.tapped
        return new_land


def create_hammerheim(owner: int) -> Hammerheim:
    """Factory function for Hammerheim."""
    return Hammerheim(owner)
