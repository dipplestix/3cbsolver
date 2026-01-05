"""Durkwood Baloth - A 5/5 Beast with Suspend 5—{G}."""
from .suspend_creature import SuspendCreature


class DurkwoodBaloth(SuspendCreature):
    """Durkwood Baloth - 5/5 Beast with Suspend 5.

    Mana cost: {4}{G}{G}
    Suspend 5—{G} (pay G to exile with 5 time counters)

    In 3CB, will typically be suspended on turn 1 and enter on turn 6.
    Goldfish kill: Turn 7 (suspend T1, enter T6, attack T7).
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Durkwood Baloth",
            owner=owner,
            power=5,
            toughness=5,
            color_costs={'G': 2},
            generic_cost=4,
            suspend_counters=5,
            suspend_color='G',
            keywords=[],
            creature_types=['Beast']
        )


def create_durkwood_baloth(owner: int) -> DurkwoodBaloth:
    """Factory function for Durkwood Baloth."""
    return DurkwoodBaloth(owner)
