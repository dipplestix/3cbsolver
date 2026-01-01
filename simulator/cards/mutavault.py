"""Mutavault card for the 3CB simulator."""
from .land import CreatureLand


def create_mutavault(owner: int) -> CreatureLand:
    """Mutavault - becomes a 2/2 with all creature types."""
    return CreatureLand(
        name="Mutavault",
        owner=owner,
        mana_produced='1',
        activation_cost=1,
        creature_power=2,
        creature_toughness=2,
        creature_keywords=[],
        creature_types=[],  # Empty list, but all_creature_types=True means it has all
        all_creature_types=True  # Has all creature types (including Human)
    )
