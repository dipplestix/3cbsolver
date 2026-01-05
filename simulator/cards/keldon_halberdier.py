"""Keldon Halberdier - A 4/1 Human Warrior with First Strike and Suspend 4—{R}."""
from .suspend_creature import SuspendCreature


class KeldonHalberdier(SuspendCreature):
    """Keldon Halberdier - 4/1 Human Warrior with First Strike and Suspend 4.

    Mana cost: {4}{R}
    First strike
    Suspend 4—{R} (pay R to exile with 4 time counters)

    In 3CB, will typically be suspended on turn 1 and enter on turn 5.
    Goldfish kill: Turn 6 (suspend T1, enter T5, attack T6 for 4, attack T7 for 4,
                          attack T8 for 4, attack T9 for 4, attack T10 for 4 = 20).
    Wait, 4 damage * 5 attacks = 20. So kill on turn 10.
    Actually: T6 attack (4), T7 attack (4), T8 attack (4), T9 attack (4), T10 attack (4) = 20.
    Goldfish kill: Turn 10.
    """

    def __init__(self, owner: int):
        super().__init__(
            name="Keldon Halberdier",
            owner=owner,
            power=4,
            toughness=1,
            color_costs={'R': 1},
            generic_cost=4,
            suspend_counters=4,
            suspend_color='R',
            keywords=['first_strike'],
            creature_types=['Human', 'Warrior']
        )


def create_keldon_halberdier(owner: int) -> KeldonHalberdier:
    """Factory function for Keldon Halberdier."""
    return KeldonHalberdier(owner)
