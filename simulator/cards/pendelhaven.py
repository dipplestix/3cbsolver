"""Pendelhaven - Legendary land that pumps 1/1 creatures.

Pendelhaven
Legendary Land
T: Add G.
T: Target 1/1 creature gets +1/+2 until end of turn.
"""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action

if TYPE_CHECKING:
    from ..solver import GameState


class Pendelhaven(Land):
    """Pendelhaven - Legendary land that can pump 1/1 creatures."""

    def __init__(self, owner: int):
        super().__init__(
            name="Pendelhaven",
            owner=owner,
            mana_produced='G'
        )

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """T: Target 1/1 creature gets +1/+2 until end of turn."""
        actions = []

        # Only pump during combat_block phase (before blockers are declared)
        if state.phase != "combat_block":
            return actions
        if self.tapped:
            return actions

        # Find all 1/1 creatures we control that could be pumped
        # Dedupe identical tokens - only need to consider one of each type
        # Exception: if a creature is being attacked/blocked, consider it separately
        seen_types = set()
        blocked_creatures = set(state.blocking_assignments.values())

        for i, card in enumerate(state.battlefield[self.owner]):
            if not hasattr(card, 'power'):
                continue

            # Check if creature is currently 1/1
            if hasattr(card, 'current_power'):
                base_power = card.current_power
            else:
                base_power = card.power
            if hasattr(card, 'current_toughness'):
                base_tough = card.current_toughness
            else:
                base_tough = card.toughness

            current_power = base_power + getattr(card, 'eot_power_boost', 0)
            current_tough = base_tough + getattr(card, 'eot_toughness_boost', 0)

            if current_power == 1 and current_tough == 1:
                # Check if this creature is in combat (attacking or blocking)
                is_attacking = getattr(card, 'attacking', False)
                is_blocking = i in blocked_creatures if self.owner != state.active_player else False
                is_in_combat = is_attacking or is_blocking
                if not is_in_combat and card.name in seen_types:
                    continue  # Skip duplicate tokens not in combat
                seen_types.add(card.name)

                def make_pump(target_idx):
                    def pump(s: 'GameState') -> 'GameState':
                        ns = s.copy()
                        # Tap Pendelhaven
                        for c in ns.battlefield[self.owner]:
                            if c.name == "Pendelhaven" and not c.tapped:
                                c.tapped = True
                                break
                        # Apply boost to target
                        target = ns.battlefield[self.owner][target_idx]
                        target.eot_power_boost = getattr(target, 'eot_power_boost', 0) + 1
                        target.eot_toughness_boost = getattr(target, 'eot_toughness_boost', 0) + 2
                        return ns
                    return pump
                actions.append(Action(
                    f"Pendelhaven: +1/+2 to {card.name}",
                    make_pump(i)
                ))

        return actions

    def copy(self) -> 'Pendelhaven':
        p = Pendelhaven(self.owner)
        p.tapped = self.tapped
        p.entered_this_turn = self.entered_this_turn
        return p


def create_pendelhaven(owner: int) -> Pendelhaven:
    """Factory function for Pendelhaven."""
    return Pendelhaven(owner)
