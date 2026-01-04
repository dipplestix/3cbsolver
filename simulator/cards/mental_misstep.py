"""Mental Misstep implementation."""
from typing import List, TYPE_CHECKING

from .base import Action
from .instant import Instant

if TYPE_CHECKING:
    from ..game_state import GameState


class MentalMisstep(Instant):
    """Mental Misstep - {U/P} Instant

    ({U/P} can be paid with either {U} or 2 life.)
    Counter target spell with mana value 1.
    """

    def __init__(self, owner: int):
        # Note: color_costs is empty because we handle Phyrexian mana specially
        super().__init__(
            name="Mental Misstep",
            owner=owner,
            color_costs={},  # Phyrexian mana handled separately
            generic_cost=0
        )

    def get_mana_value(self) -> int:
        """Mental Misstep has MV 1 (the Phyrexian mana counts)."""
        return 1

    def has_valid_target(self, state: 'GameState') -> bool:
        """Check if there's a spell with MV 1 on the stack to counter."""
        if not state.stack:
            return False
        # Check if any spell on stack has MV 1
        # We can only counter the top spell in our simplified model
        top_spell = state.stack[-1]
        return top_spell.get_mana_value() == 1

    def can_pay_with_mana(self, state: 'GameState') -> bool:
        """Check if we can pay with blue mana."""
        available = state.get_available_mana_by_color(self.owner)
        return available.get('U', 0) >= 1

    def can_pay_with_life(self, state: 'GameState') -> bool:
        """Check if we can pay with 2 life (must have > 2 life)."""
        return state.life[self.owner] > 2

    def get_response_actions(self, state: 'GameState') -> List[Action]:
        """Get actions to counter a spell on the stack."""
        # Must be in response phase and be the responding player
        if state.phase != "response":
            return []

        # The responding player is the non-active player
        if self.owner == state.active_player:
            return []

        # Must have valid target
        if not self.has_valid_target(state):
            return []

        actions = []

        # Option 1: Pay with blue mana
        if self.can_pay_with_mana(state):
            def cast_with_mana(s: 'GameState') -> 'GameState':
                ns = s.copy()
                # Pay U
                ns = ns.pay_mana(self.owner, 'U', 1)
                # Remove from hand
                for i, card in enumerate(ns.hands[self.owner]):
                    if card.name == self.name:
                        misstep = ns.hands[self.owner].pop(i)
                        break
                # Counter top spell (remove from stack, put in graveyard)
                countered = ns.stack.pop()
                ns.graveyard[countered.owner].append(countered)
                # Put Mental Misstep in graveyard
                ns.graveyard[self.owner].append(misstep)
                return ns

            actions.append(Action(
                f"Counter with Mental Misstep (pay U)",
                cast_with_mana
            ))

        # Option 2: Pay with 2 life
        if self.can_pay_with_life(state):
            def cast_with_life(s: 'GameState') -> 'GameState':
                ns = s.copy()
                # Pay 2 life
                ns.life[self.owner] -= 2
                # Check for death
                if ns.life[self.owner] <= 0:
                    ns.game_over = True
                    ns.winner = 1 - self.owner
                    return ns
                # Remove from hand
                for i, card in enumerate(ns.hands[self.owner]):
                    if card.name == self.name:
                        misstep = ns.hands[self.owner].pop(i)
                        break
                # Counter top spell
                countered = ns.stack.pop()
                ns.graveyard[countered.owner].append(countered)
                # Put Mental Misstep in graveyard
                ns.graveyard[self.owner].append(misstep)
                return ns

            actions.append(Action(
                f"Counter with Mental Misstep (pay 2 life)",
                cast_with_life
            ))

        return actions

    def resolve(self, state: 'GameState') -> 'GameState':
        """Mental Misstep resolves immediately when cast (counter effect).

        This is handled in get_response_actions, so this is a no-op.
        """
        return state

    def copy(self) -> 'MentalMisstep':
        """Create a deep copy."""
        new_card = MentalMisstep(self.owner)
        new_card.tapped = self.tapped
        return new_card
