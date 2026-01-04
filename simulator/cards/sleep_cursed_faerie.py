"""Sleep-Cursed Faerie card for the 3CB simulator.

Scryfall Oracle Text:
---------------------
Sleep-Cursed Faerie {U}
Creature — Faerie Wizard

Flying, ward {2}
This creature enters tapped with three stun counters on it.
(If it would become untapped, remove a stun counter from it instead.)
{1}{U}: Untap this creature.

3/3

Implementation Notes:
- Ward {2} is not implemented (no targeting in this simulator)
- {1}{U} untap ability is not implemented (would add branching)
- Stun counters correctly replace untapping in the untap phase
"""
from typing import List, TYPE_CHECKING

from .base import Action
from .creature import Creature

if TYPE_CHECKING:
    from ..solver import GameState


class SleepCursedFaerie(Creature):
    """Sleep-Cursed Faerie - a 3/3 flyer that enters tapped with stun counters."""

    def __init__(self, owner: int):
        super().__init__(
            name="Sleep-Cursed Faerie",
            owner=owner,
            power=3,
            toughness=3,
            color_costs={'U': 1},
            keywords=['flying']
        )
        self.stun_counters = 3

    def __repr__(self):
        tap_str = " (T)" if self.tapped else ""
        stun_str = f" [{self.stun_counters} stun]" if self.stun_counters > 0 else ""
        return f"{self.name}{tap_str}{stun_str}"

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        available = state.get_available_mana_by_color(self.owner)
        if available.get('U', 0) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            # Pay 1 blue mana
            ns = s.pay_mana(self.owner, 'U', 1)
            # Move faerie from hand to battlefield
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    faerie = ns.hands[self.owner].pop(i)
                    faerie.tapped = True
                    faerie.stun_counters = 3
                    faerie.entered_this_turn = True
                    ns.battlefield[self.owner].append(faerie)
                    break
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def get_signature_state(self) -> tuple:
        """Return faerie-specific state including stun counters."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
            True,  # is_creature
            self.attacking,
            self.damage,
            self.stun_counters,
        )

    def can_attack(self) -> bool:
        return not self.tapped and self.stun_counters == 0 and not self.entered_this_turn

    def can_block(self, attacker) -> bool:
        if self.tapped or self.stun_counters > 0:
            return False
        if hasattr(attacker, 'has_flying') and attacker.has_flying:
            if not self.has_flying and 'reach' not in self.keywords:
                return False
        return True

    def on_upkeep(self, state: 'GameState') -> 'GameState':
        return state

    def copy(self) -> 'SleepCursedFaerie':
        new_faerie = SleepCursedFaerie(self.owner)
        new_faerie.tapped = self.tapped
        new_faerie.damage = self.damage
        new_faerie.attacking = self.attacking
        new_faerie.stun_counters = self.stun_counters
        new_faerie.entered_this_turn = self.entered_this_turn
        return new_faerie


def create_sleep_cursed_faerie(owner: int) -> SleepCursedFaerie:
    return SleepCursedFaerie(owner)
