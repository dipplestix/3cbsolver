"""Mountain basic land."""
from .land import Land


class Mountain(Land):
    """Basic land that produces red mana."""

    def __init__(self, owner: int):
        super().__init__("Mountain", owner, mana_produced='R')


def create_mountain(owner: int) -> Mountain:
    """Factory function for Mountain."""
    return Mountain(owner)
