"""Artifact cards for the 3CB simulator."""
from typing import List, Optional, TYPE_CHECKING

from .base import Card, Action, CardType

if TYPE_CHECKING:
    from ..solver import GameState


class Artifact(Card):
    """An artifact card."""

    def __init__(self, name: str, owner: int, mana_cost: int = 0,
                 mana_produced: Optional[str] = None):
        super().__init__(name, owner)
        self.mana_cost = mana_cost
        self.mana_produced = mana_produced
        self.card_type = CardType.ARTIFACT

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        if self.mana_cost > 0:
            if state.get_available_mana(self.owner) < self.mana_cost:
                return []

        def play(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    card_copy = ns.hands[self.owner].pop(i)
                    ns.artifacts[self.owner].append(card_copy)
                    break
            return ns

        return [Action(f"Play {self.name}", play)]

    def copy(self) -> 'Artifact':
        new_artifact = Artifact(self.name, self.owner, self.mana_cost, self.mana_produced)
        new_artifact.tapped = self.tapped
        return new_artifact


def create_mox_jet(owner: int) -> Artifact:
    return Artifact("Mox Jet", owner, mana_cost=0, mana_produced='B')
