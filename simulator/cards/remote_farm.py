"""Remote Farm - Depletion land that produces WW."""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class RemoteFarm(Land):
    """
    Remote Farm
    Land

    Remote Farm enters the battlefield tapped.
    T, Remove a depletion counter from Remote Farm: Add WW.
    If there are no depletion counters on Remote Farm, sacrifice it.

    Remote Farm enters with 2 depletion counters.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Remote Farm",
            owner=owner,
            mana_produced='W'
        )
        self.depletion_counters = 2  # Enters with 2

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []
        if state.land_played_this_turn:
            return []

        def play(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    farm = ns.hands[self.owner].pop(i)
                    farm.tapped = True  # Enters tapped
                    farm.depletion_counters = 2  # Enters with 2 depletion counters
                    ns.battlefield[self.owner].append(farm)
                    break
            ns.land_played_this_turn = True
            return ns

        return [Action(f"Play {self.name}", play)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        actions = []

        # T, Remove a depletion counter: Add WW
        if not self.tapped and self.depletion_counters > 0:
            def tap_for_mana(s: 'GameState') -> 'GameState':
                ns = s.copy()
                for card in ns.battlefield[self.owner]:
                    if card.name == self.name and isinstance(card, RemoteFarm):
                        card.tapped = True
                        card.depletion_counters -= 1
                        # If no counters remain, sacrifice it
                        if card.depletion_counters <= 0:
                            ns.battlefield[self.owner].remove(card)
                            ns.graveyard[self.owner].append(card)
                        break
                return ns
            counters_after = self.depletion_counters - 1
            if counters_after > 0:
                desc = f"Tap {self.name} for WW ({counters_after} counter{'s' if counters_after > 1 else ''} left)"
            else:
                desc = f"Tap {self.name} for WW (sacrifices)"
            actions.append(Action(desc, tap_for_mana))

        return actions

    def copy(self) -> 'RemoteFarm':
        new_farm = RemoteFarm(self.owner)
        new_farm.tapped = self.tapped
        new_farm.depletion_counters = self.depletion_counters
        return new_farm


def create_remote_farm(owner: int) -> RemoteFarm:
    """Factory function for Remote Farm."""
    return RemoteFarm(owner)
