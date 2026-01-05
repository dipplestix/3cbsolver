"""Mental Misstep implementation."""
from typing import List, Optional, TYPE_CHECKING

from .base import Action, Card
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
        self.target_spell_name: Optional[str] = None  # Name of spell we're targeting

    def get_mana_value(self) -> int:
        """Mental Misstep has MV 1 (the Phyrexian mana counts)."""
        return 1

    def get_valid_targets(self, state: 'GameState') -> List[Card]:
        """Get all spells on the stack with MV 1 that we can counter."""
        targets = []
        for spell in state.stack:
            if spell.get_mana_value() == 1:
                targets.append(spell)
        return targets

    def has_valid_target(self, state: 'GameState') -> bool:
        """Check if there's a spell with MV 1 on the stack to counter."""
        return len(self.get_valid_targets(state)) > 0

    def can_pay_with_mana(self, state: 'GameState') -> bool:
        """Check if we can pay with blue mana."""
        available = state.get_available_mana_by_color(self.owner)
        return available.get('U', 0) >= 1

    def can_pay_with_life(self, state: 'GameState') -> bool:
        """Check if we can pay with 2 life (must have > 2 life)."""
        return state.life[self.owner] > 2

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
        targets = self.get_valid_targets(state)
        misstep_name = self.name
        misstep_owner = self.owner

        for target in targets:
            target_name = target.name

            # Option 1: Pay with blue mana
            if self.can_pay_with_mana(state):
                def make_cast_with_mana(tgt_name):
                    def cast_with_mana(s: 'GameState') -> 'GameState':
                        ns = s.copy()
                        # Pay U
                        ns = ns.pay_mana(misstep_owner, 'U', 1)
                        # Remove from hand and put on stack
                        for i, card in enumerate(ns.hands[misstep_owner]):
                            if card.name == misstep_name:
                                misstep = ns.hands[misstep_owner].pop(i)
                                misstep.target_spell_name = tgt_name
                                ns.stack.append(misstep)
                                break
                        # Stay in response phase - opponent can respond to this
                        return ns
                    return cast_with_mana

                actions.append(Action(
                    f"Cast Mental Misstep (pay U) targeting {target_name}",
                    make_cast_with_mana(target_name)
                ))

            # Option 2: Pay with 2 life
            if self.can_pay_with_life(state):
                def make_cast_with_life(tgt_name):
                    def cast_with_life(s: 'GameState') -> 'GameState':
                        ns = s.copy()
                        # Pay 2 life
                        ns.life[misstep_owner] -= 2
                        # Check for death
                        if ns.life[misstep_owner] <= 0:
                            ns.game_over = True
                            ns.winner = 1 - misstep_owner
                            return ns
                        # Remove from hand and put on stack
                        for i, card in enumerate(ns.hands[misstep_owner]):
                            if card.name == misstep_name:
                                misstep = ns.hands[misstep_owner].pop(i)
                                misstep.target_spell_name = tgt_name
                                ns.stack.append(misstep)
                                break
                        # Stay in response phase - opponent can respond to this
                        return ns
                    return cast_with_life

                actions.append(Action(
                    f"Cast Mental Misstep (pay 2 life) targeting {target_name}",
                    make_cast_with_life(target_name)
                ))

        return actions

    def resolve(self, state: 'GameState') -> 'GameState':
        """Counter the targeted spell if it's still on the stack."""
        ns = state.copy()
        if self.target_spell_name:
            # Find and counter the target spell
            for i, spell in enumerate(ns.stack):
                if spell.name == self.target_spell_name:
                    countered = ns.stack.pop(i)
                    ns.graveyard[countered.owner].append(countered)
                    break
        return ns

    def get_signature_state(self) -> tuple:
        """Include target in signature for proper memoization."""
        return (self.name, self.target_spell_name)

    def copy(self) -> 'MentalMisstep':
        """Create a deep copy."""
        new_card = MentalMisstep(self.owner)
        new_card.tapped = self.tapped
        new_card.target_spell_name = self.target_spell_name
        return new_card
