"""3CB Combat Simulator"""
from .game_state import GameState
from .solver import (
    solve,
    find_optimal_line,
    get_available_actions,
    minimax,
)
from .tables import (
    lookup_transposition,
    store_transposition,
    check_dominance,
    store_dominance,
)
from .combat import resolve_combat_damage
from .helpers import (
    get_creature_power,
    get_creature_toughness,
    has_first_strike,
    has_double_strike,
    has_deathtouch,
    is_lethal_damage,
)
from .heuristics import (
    evaluate_position,
    evaluate_early_grinding,
    evaluate_max_depth,
)
from .phases import untap, upkeep, end_turn
from .cards import (
    Card, Action, CardType,
    Land, CreatureLand, Creature, Artifact,
    create_island, create_forest, create_plains, create_mountain,
    create_hammerheim,
    create_mox_jet, create_mutavault,
    SleepCursedFaerie, create_sleep_cursed_faerie,
    ScytheTiger, create_scythe_tiger,
    UndiscoveredParadise, create_undiscovered_paradise,
    SazhsChocobo, create_sazhs_chocobo,
    StudentOfWarfare, create_student_of_warfare,
    OldGrowthDryads, create_old_growth_dryads,
    DryadArbor, create_dryad_arbor,
    DragonSniper, create_dragon_sniper,
    Mountain, StromkirkNoble, create_stromkirk_noble,
    Hammerheim, HeartfireHero, create_heartfire_hero,
    BottomlessVault, create_bottomless_vault,
    TombOfUrami, create_tomb_of_urami,
    UramiToken, create_urami_token,
    RemoteFarm, create_remote_farm,
    LuminarchAspirant, create_luminarch_aspirant,
    Thallid, create_thallid,
    SaprolingToken, create_saproling_token,
    Pendelhaven, create_pendelhaven,
)

__all__ = [
    # Solver
    'GameState', 'solve', 'find_optimal_line',
    'get_available_actions', 'minimax',
    # Transposition & Dominance
    'lookup_transposition', 'store_transposition',
    'check_dominance', 'store_dominance',
    # Combat
    'resolve_combat_damage',
    # Helpers
    'get_creature_power', 'get_creature_toughness',
    'has_first_strike', 'has_double_strike', 'has_deathtouch', 'is_lethal_damage',
    # Heuristics
    'evaluate_position', 'evaluate_early_grinding', 'evaluate_max_depth',
    # Phases
    'end_turn', 'upkeep', 'untap',
    # Base classes
    'Card', 'Action', 'CardType',
    'Land', 'CreatureLand', 'Creature', 'Artifact',
    # Factory functions
    'create_island', 'create_forest', 'create_plains', 'create_mountain',
    'create_hammerheim',
    'create_mox_jet', 'create_mutavault',
    'create_sleep_cursed_faerie', 'create_scythe_tiger',
    'create_undiscovered_paradise', 'create_sazhs_chocobo',
    'create_student_of_warfare', 'create_old_growth_dryads',
    'create_dryad_arbor', 'create_dragon_sniper',
    'create_stromkirk_noble', 'create_heartfire_hero',
    'create_bottomless_vault', 'create_tomb_of_urami', 'create_urami_token',
    'create_remote_farm', 'create_luminarch_aspirant',
    'create_thallid', 'create_saproling_token', 'create_pendelhaven',
    # Card classes
    'Mountain', 'Hammerheim', 'SleepCursedFaerie', 'ScytheTiger',
    'UndiscoveredParadise', 'SazhsChocobo', 'StudentOfWarfare',
    'OldGrowthDryads', 'DryadArbor', 'DragonSniper', 'StromkirkNoble',
    'HeartfireHero', 'BottomlessVault', 'TombOfUrami', 'UramiToken',
    'RemoteFarm', 'LuminarchAspirant', 'Thallid', 'SaprolingToken', 'Pendelhaven',
]
