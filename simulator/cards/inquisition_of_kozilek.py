"""Inquisition of Kozilek implementation."""
from typing import List, Optional, TYPE_CHECKING

from .base import Action
from .sorcery import Sorcery

if TYPE_CHECKING:
    from ..game_state import GameState


class InquisitionOfKozilek(Sorcery):
    """Inquisition of Kozilek - {B} Sorcery

    Target player reveals their hand. You choose a nonland card from it
    with mana value 3 or less. That player discards that card.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Inquisition of Kozilek",
            owner=owner,
            color_costs={'B': 1}
        )
        # Target card name to discard (set when casting)
        self.target_card_name: Optional[str] = None

    def get_valid_targets(self, state: 'GameState') -> List[str]:
        """Get names of valid discard targets in opponent's hand."""
        opponent = 1 - self.owner
        targets = []
        for card in state.hands[opponent]:
            # Must be nonland with MV <= 3
            if not card.is_land() and card.get_mana_value() <= 3:
                targets.append(card.name)
        return targets

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        """Get actions to cast this sorcery."""
        if not self.can_cast(state):
            return []

        # Check for valid targets
        valid_targets = self.get_valid_targets(state)
        if not valid_targets:
            return []

        actions = []
        for target_name in valid_targets:
            # Create a separate action for each possible discard choice
            def make_cast_action(target: str):
                def cast(s: 'GameState') -> 'GameState':
                    ns = self.pay_costs(s)

                    # Find and remove this card from hand
                    for i, card in enumerate(ns.hands[self.owner]):
                        if card.name == self.name:
                            spell = ns.hands[self.owner].pop(i)
                            # Set the target
                            spell.target_card_name = target
                            # Put on stack
                            ns.stack.append(spell)
                            break

                    # Move to response phase
                    ns.phase = "response"
                    return ns
                return cast

            actions.append(Action(
                f"Cast Inquisition (discard {target_name})",
                make_cast_action(target_name)
            ))

        return actions

    def resolve(self, state: 'GameState') -> 'GameState':
        """Resolve: opponent discards the targeted card."""
        ns = state.copy()
        opponent = 1 - self.owner

        if self.target_card_name:
            # Find and discard the target card
            for i, card in enumerate(ns.hands[opponent]):
                if card.name == self.target_card_name:
                    discarded = ns.hands[opponent].pop(i)
                    ns.graveyard[opponent].append(discarded)
                    break

        return ns

    def copy(self) -> 'InquisitionOfKozilek':
        """Create a deep copy."""
        new_card = InquisitionOfKozilek(self.owner)
        new_card.tapped = self.tapped
        new_card.target_card_name = self.target_card_name
        return new_card

    def get_signature_state(self) -> tuple:
        """Include target in signature."""
        return (self.name, self.target_card_name)
