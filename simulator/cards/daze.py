"""Daze implementation.

Scryfall Oracle Text:
---------------------
Daze - {1}{U} - Instant
You may return an Island you control to its owner's hand rather than pay
this spell's mana cost.
Counter target spell unless its controller pays {1}.
"""
from typing import List, Optional, TYPE_CHECKING

from .base import Action
from .instant import Instant

if TYPE_CHECKING:
    from ..game_state import GameState


class Daze(Instant):
    """Daze - {1}{U} Instant

    You may return an Island you control to its owner's hand rather than pay
    this spell's mana cost.
    Counter target spell unless its controller pays {1}.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Daze",
            owner=owner,
            color_costs={'U': 1},
            generic_cost=1
        )
        self.target_spell_name: Optional[str] = None  # Name of spell we're targeting
        self.target_spell_owner: Optional[int] = None  # Owner of target spell

    def get_mana_value(self) -> int:
        """Daze has MV 2."""
        return 2

    def has_valid_target(self, state: 'GameState') -> bool:
        """Check if there's a spell on the stack to counter."""
        return len(state.stack) > 0

    def can_pay_with_mana(self, state: 'GameState') -> bool:
        """Check if we can pay {1}{U} with available mana."""
        available = state.get_available_mana_by_color(self.owner)
        # Need at least 1 blue and 2 total mana
        if available.get('U', 0) < 1:
            return False
        # Use get_available_mana for total (not sum of colors, which double-counts duals)
        total = state.get_available_mana(self.owner)
        return total >= 2

    def get_islands(self, state: 'GameState') -> List[int]:
        """Get indices of Islands we control (includes dual lands with Island type)."""
        islands = []
        for i, card in enumerate(state.battlefield[self.owner]):
            # Check if it's a basic Island
            if card.name == "Island":
                islands.append(i)
            # Check if it's a dual land with Island type
            elif hasattr(card, 'has_land_type') and card.has_land_type('Island'):
                islands.append(i)
        return islands

    def can_pay_alternative(self, state: 'GameState') -> bool:
        """Check if we can return an Island to pay the alternative cost."""
        return len(self.get_islands(state)) > 0

    def opponent_can_pay(self, state: 'GameState', spell_owner: int) -> bool:
        """Check if the spell's controller can pay {1}."""
        available = state.get_available_mana(spell_owner)
        return available >= 1

    def get_response_actions(self, state: 'GameState') -> List[Action]:
        """Get actions to counter a spell on the stack."""
        # Must be in response phase
        if state.phase != "response":
            return []

        # Must have something on the stack
        if not state.stack:
            return []

        # The responding player is the opponent of whoever owns the top spell
        top_spell_owner = state.stack[-1].owner
        if self.owner == top_spell_owner:
            return []

        # Must have valid target
        if not self.has_valid_target(state):
            return []

        actions = []
        daze_owner = self.owner
        daze_name = self.name

        # Can target any spell on the stack
        for target in state.stack:
            target_name = target.name
            target_owner = target.owner

            # Option 1: Pay with {1}{U} mana
            if self.can_pay_with_mana(state):
                def make_cast_with_mana(tgt_name, tgt_owner):
                    def cast_with_mana(s: 'GameState') -> 'GameState':
                        ns = s.copy()
                        # Pay {1}{U} for Daze
                        ns = ns.pay_mana(daze_owner, 'U', 1)
                        ns = ns.pay_generic_mana(daze_owner, 1)
                        # Remove Daze from hand and put on stack
                        for i, card in enumerate(ns.hands[daze_owner]):
                            if card.name == daze_name:
                                daze = ns.hands[daze_owner].pop(i)
                                daze.target_spell_name = tgt_name
                                daze.target_spell_owner = tgt_owner
                                ns.stack.append(daze)
                                break
                        # Stay in response phase - opponent can respond
                        return ns
                    return cast_with_mana

                actions.append(Action(
                    f"Cast Daze (pay 1U) targeting {target_name}",
                    make_cast_with_mana(target_name, target_owner)
                ))

            # Option 2: Return an Island (alternative cost)
            if self.can_pay_alternative(state):
                islands = self.get_islands(state)
                for island_idx in islands:
                    island = state.battlefield[self.owner][island_idx]

                    def make_alt_cast(idx, island_name, tgt_name, tgt_owner):
                        def cast_alt(s: 'GameState') -> 'GameState':
                            ns = s.copy()
                            # Return Island to hand
                            returned_island = ns.battlefield[daze_owner].pop(idx)
                            ns.hands[daze_owner].append(returned_island)
                            # Remove Daze from hand and put on stack
                            for i, card in enumerate(ns.hands[daze_owner]):
                                if card.name == daze_name:
                                    daze = ns.hands[daze_owner].pop(i)
                                    daze.target_spell_name = tgt_name
                                    daze.target_spell_owner = tgt_owner
                                    ns.stack.append(daze)
                                    break
                            # Stay in response phase - opponent can respond
                            return ns
                        return cast_alt

                    actions.append(Action(
                        f"Cast Daze (return {island.name}) targeting {target_name}",
                        make_alt_cast(island_idx, island.name, target_name, target_owner)
                    ))

        return actions

    def resolve(self, state: 'GameState') -> 'GameState':
        """Counter target spell unless its controller pays {1}."""
        ns = state.copy()
        if not self.target_spell_name:
            return ns

        # Find the target spell on the stack
        target_idx = None
        for i, spell in enumerate(ns.stack):
            if spell.name == self.target_spell_name:
                target_idx = i
                break

        if target_idx is None:
            # Target no longer on stack (was countered by something else)
            return ns

        # Check if opponent can pay {1}
        if self.opponent_can_pay(ns, self.target_spell_owner):
            # Opponent pays {1} - spell stays on stack
            ns = ns.pay_generic_mana(self.target_spell_owner, 1)
        else:
            # Counter the spell
            countered = ns.stack.pop(target_idx)
            ns.graveyard[countered.owner].append(countered)

        return ns

    def get_signature_state(self) -> tuple:
        """Include target in signature for proper memoization."""
        return (self.name, self.target_spell_name, self.target_spell_owner)

    def copy(self) -> 'Daze':
        """Create a deep copy."""
        new_card = Daze(self.owner)
        new_card.tapped = self.tapped
        new_card.target_spell_name = self.target_spell_name
        new_card.target_spell_owner = self.target_spell_owner
        return new_card


def create_daze(owner: int) -> Daze:
    """Factory function for Daze."""
    return Daze(owner)
