"""Tomb of Urami - Legendary land that creates a 5/5 flying Demon."""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action
from .urami_token import UramiToken

if TYPE_CHECKING:
    from ..solver import GameState


class TombOfUrami(Land):
    """
    Tomb of Urami
    Legendary Land

    T: Add B. Tomb of Urami deals 1 damage to you if you don't control an Ogre.
    2BB, T, Sacrifice all lands you control: Create Urami, a legendary 5/5
    black Demon Spirit creature token with flying.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Tomb of Urami",
            owner=owner,
            mana_produced='B'
        )

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
                    tomb = ns.hands[self.owner].pop(i)
                    ns.battlefield[self.owner].append(tomb)
                    break
            ns.land_played_this_turn = True
            return ns

        return [Action(f"Play {self.name}", play)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Can tap for B (taking 1 damage) or activate for Urami."""
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        actions = []

        # Note: No standalone "tap for B" action - it costs 1 life for mana that floats
        # away unused. Tomb is only useful for its Urami activation.

        if not self.tapped:
            # Check if we can activate Urami ability (need 2BB from other sources)
            # Tomb is tapped as part of cost, so exclude it from mana calculation
            available_black = state.get_available_mana_by_color(self.owner).get('B', 0)
            # Subtract 1 if Tomb itself was counted (it's untapped and produces B)
            available_black -= 1  # Tomb is being tapped for T cost, not for mana
            # 2BB = 4 total mana, at least 2 black. With only B sources, need 4B.
            if available_black >= 4:
                def create_urami(s: 'GameState') -> 'GameState':
                    # First tap Tomb as part of activation cost (T in the cost)
                    ns = s.copy()
                    for card in ns.battlefield[self.owner]:
                        if card.name == self.name and isinstance(card, TombOfUrami):
                            card.tapped = True
                            break

                    # Now pay 2BB from other sources (Tomb is already tapped)
                    # With only black sources, we pay 4B (2B for colorless, 2B for black)
                    ns = ns.pay_mana(self.owner, 'B', 4)

                    # Sacrifice all lands
                    lands_to_sac = [c for c in ns.battlefield[self.owner]
                                   if hasattr(c, 'mana_produced')]
                    for land in lands_to_sac:
                        ns.battlefield[self.owner].remove(land)
                        ns.graveyard[self.owner].append(land)

                    # Create Urami token
                    urami = UramiToken(self.owner)
                    urami.entered_this_turn = True
                    ns.battlefield[self.owner].append(urami)

                    return ns

                actions.append(Action(
                    f"Activate {self.name}: Create Urami (5/5 flying)",
                    create_urami
                ))

        return actions

    def copy(self) -> 'TombOfUrami':
        new_tomb = TombOfUrami(self.owner)
        new_tomb.tapped = self.tapped
        return new_tomb


def create_tomb_of_urami(owner: int) -> TombOfUrami:
    """Factory function for Tomb of Urami."""
    return TombOfUrami(owner)
