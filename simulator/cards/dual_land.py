"""Dual Lands for the 3CB simulator.

Scryfall Oracle Text (Original Dual Lands):
--------------------------------------------
Underground Sea - Land - Island Swamp
({T}: Add {U} or {B}.)

Volcanic Island - Land - Island Mountain
({T}: Add {U} or {R}.)

Tundra - Land - Plains Island
({T}: Add {W} or {U}.)

Tropical Island - Land - Forest Island
({T}: Add {G} or {U}.)

Savannah - Land - Forest Plains
({T}: Add {G} or {W}.)

Scrubland - Land - Plains Swamp
({T}: Add {W} or {B}.)

Badlands - Land - Swamp Mountain
({T}: Add {B} or {R}.)

Taiga - Land - Mountain Forest
({T}: Add {R} or {G}.)

Plateau - Land - Mountain Plains
({T}: Add {R} or {W}.)

Bayou - Land - Swamp Forest
({T}: Add {B} or {G}.)
"""
from typing import List, TYPE_CHECKING

from .land import Land
from .base import Action

if TYPE_CHECKING:
    from ..game_state import GameState


class DualLand(Land):
    """A dual land that can produce one of two colors of mana.

    The original dual lands have basic land types (e.g., Island Swamp)
    which matters for effects that care about land types (like Daze).
    """

    def __init__(self, name: str, owner: int, color1: str, color2: str,
                 land_types: List[str]):
        # Store both colors - mana_produced will be used for color identity
        super().__init__(name, owner, mana_produced=f'{color1}{color2}')
        self.color1 = color1
        self.color2 = color2
        self.land_types = land_types  # e.g., ['Island', 'Swamp']

    def get_signature_state(self) -> tuple:
        """Return dual-land-specific state for memoization."""
        return (
            self.name,
            self.tapped,
            self.entered_this_turn,
        )

    def has_land_type(self, land_type: str) -> bool:
        """Check if this land has a specific land type."""
        return land_type in self.land_types

    def copy(self) -> 'DualLand':
        new_land = DualLand(
            self.name, self.owner,
            self.color1, self.color2,
            self.land_types.copy()
        )
        new_land.tapped = self.tapped
        new_land.entered_this_turn = self.entered_this_turn
        return new_land


# =============================================================================
# Factory Functions
# =============================================================================

def create_underground_sea(owner: int) -> DualLand:
    """Create Underground Sea - Island Swamp ({T}: Add {U} or {B}.)"""
    return DualLand("Underground Sea", owner, 'U', 'B', ['Island', 'Swamp'])


def create_volcanic_island(owner: int) -> DualLand:
    """Create Volcanic Island - Island Mountain ({T}: Add {U} or {R}.)"""
    return DualLand("Volcanic Island", owner, 'U', 'R', ['Island', 'Mountain'])


def create_tundra(owner: int) -> DualLand:
    """Create Tundra - Plains Island ({T}: Add {W} or {U}.)"""
    return DualLand("Tundra", owner, 'W', 'U', ['Plains', 'Island'])


def create_tropical_island(owner: int) -> DualLand:
    """Create Tropical Island - Forest Island ({T}: Add {G} or {U}.)"""
    return DualLand("Tropical Island", owner, 'G', 'U', ['Forest', 'Island'])


def create_savannah(owner: int) -> DualLand:
    """Create Savannah - Forest Plains ({T}: Add {G} or {W}.)"""
    return DualLand("Savannah", owner, 'G', 'W', ['Forest', 'Plains'])


def create_scrubland(owner: int) -> DualLand:
    """Create Scrubland - Plains Swamp ({T}: Add {W} or {B}.)"""
    return DualLand("Scrubland", owner, 'W', 'B', ['Plains', 'Swamp'])


def create_badlands(owner: int) -> DualLand:
    """Create Badlands - Swamp Mountain ({T}: Add {B} or {R}.)"""
    return DualLand("Badlands", owner, 'B', 'R', ['Swamp', 'Mountain'])


def create_taiga(owner: int) -> DualLand:
    """Create Taiga - Mountain Forest ({T}: Add {R} or {G}.)"""
    return DualLand("Taiga", owner, 'R', 'G', ['Mountain', 'Forest'])


def create_plateau(owner: int) -> DualLand:
    """Create Plateau - Mountain Plains ({T}: Add {R} or {W}.)"""
    return DualLand("Plateau", owner, 'R', 'W', ['Mountain', 'Plains'])


def create_bayou(owner: int) -> DualLand:
    """Create Bayou - Swamp Forest ({T}: Add {B} or {G}.)"""
    return DualLand("Bayou", owner, 'B', 'G', ['Swamp', 'Forest'])
