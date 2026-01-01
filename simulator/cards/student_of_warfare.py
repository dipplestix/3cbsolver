"""Student of Warfare card for the 3CB simulator."""
from typing import List, TYPE_CHECKING

from .base import Action
from .creature import Creature

if TYPE_CHECKING:
    from ..solver import GameState


class StudentOfWarfare(Creature):
    """
    Student of Warfare - W
    Creature - Human Knight
    1/1
    Level up W (W: Put a level counter on this. Level up only as a sorcery.)
    LEVEL 0-1: 1/1
    LEVEL 2-6: 3/3, First strike
    LEVEL 7+: 4/4, First strike, Double strike
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Student of Warfare",
            owner=owner,
            power=1,
            toughness=1,
            mana_cost=1,
            mana_color='W',
            keywords=[],
            creature_types=['Human', 'Knight']
        )
        self.level = 0
        self.auto_level = True  # Automatically level up when mana available

    @property
    def current_power(self) -> int:
        if self.level >= 7:
            return 4
        elif self.level >= 2:
            return 3
        return 1

    @property
    def current_toughness(self) -> int:
        if self.level >= 7:
            return 4
        elif self.level >= 2:
            return 3
        return 1

    @property
    def has_first_strike(self) -> bool:
        return self.level >= 2

    @property
    def has_double_strike(self) -> bool:
        return self.level >= 7

    def do_auto_level(self, state: 'GameState') -> 'GameState':
        """Automatically level up as much as possible when mana is available."""
        ns = state.copy()

        # Keep leveling while we have mana
        while True:
            available = ns.get_available_mana_by_color(self.owner)
            if available.get('W', 0) < 1:
                break

            # Find this student on the battlefield and level it up
            student_found = False
            for card in ns.battlefield[self.owner]:
                if card.name == self.name and isinstance(card, StudentOfWarfare):
                    card.level += 1
                    student_found = True
                    break

            if not student_found:
                break

            # Tap a white mana source
            mana_tapped = False
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'mana_produced') and card.mana_produced == 'W' and not card.tapped:
                    card.tapped = True
                    mana_tapped = True
                    break

            if not mana_tapped:
                break

        return ns

    def get_play_actions(self, state: 'GameState') -> List[Action]:
        if state.active_player != self.owner:
            return []
        if state.phase != "main1":
            return []

        available = state.get_available_mana_by_color(self.owner)
        if available.get('W', 0) < 1:
            return []

        def cast(s: 'GameState') -> 'GameState':
            ns = s.copy()
            for i, card in enumerate(ns.hands[self.owner]):
                if card.name == self.name:
                    student = ns.hands[self.owner].pop(i)
                    student.entered_this_turn = True
                    ns.battlefield[self.owner].append(student)
                    break
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'mana_produced') and card.mana_produced == 'W' and not card.tapped:
                    card.tapped = True
                    break
            return ns

        return [Action(f"Cast {self.name}", cast)]

    def get_battlefield_actions(self, state: 'GameState') -> List[Action]:
        """Level up is now automatic via do_auto_level, no manual actions needed."""
        return []

    def copy(self) -> 'StudentOfWarfare':
        new_student = StudentOfWarfare(self.owner)
        new_student.tapped = self.tapped
        new_student.damage = self.damage
        new_student.attacking = self.attacking
        new_student.entered_this_turn = self.entered_this_turn
        new_student.level = self.level
        new_student.auto_level = self.auto_level
        return new_student


def create_student_of_warfare(owner: int) -> StudentOfWarfare:
    return StudentOfWarfare(owner)
