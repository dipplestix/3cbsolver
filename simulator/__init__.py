"""3CB Combat Simulator"""
from .game_state import GameState
from .solver import (
    solve,
    find_optimal_line,
    minimax,
)
from .actions import get_available_actions
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
    Land, CreatureLand, DualLand, Creature, Artifact, Enchantment, SuspendCreature,
    create_island, create_forest, create_plains, create_swamp, create_mountain,
    create_hammerheim,
    # Dual lands
    create_underground_sea, create_volcanic_island, create_tundra,
    create_tropical_island, create_savannah, create_scrubland,
    create_badlands, create_taiga, create_plateau, create_bayou,
    # Other cards
    create_mox_jet, create_mox_pearl, create_mutavault,
    CrystalVein, create_crystal_vein,
    SoldierToken, create_soldier_token,
    SoldierMilitaryProgram, create_soldier_military_program,
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
    ShriekingAffliction, create_shrieking_affliction,
    DurkwoodBaloth, create_durkwood_baloth,
    KeldonHalberdier, create_keldon_halberdier,
    Daze, create_daze,
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
    'Land', 'CreatureLand', 'DualLand', 'Creature', 'Artifact', 'Enchantment', 'SuspendCreature',
    # Factory functions - Basic lands
    'create_island', 'create_forest', 'create_plains', 'create_swamp', 'create_mountain',
    'create_hammerheim',
    # Factory functions - Dual lands
    'create_underground_sea', 'create_volcanic_island', 'create_tundra',
    'create_tropical_island', 'create_savannah', 'create_scrubland',
    'create_badlands', 'create_taiga', 'create_plateau', 'create_bayou',
    # Factory functions - Other
    'create_mox_jet', 'create_mox_pearl', 'create_mutavault',
    'create_crystal_vein', 'create_soldier_token', 'create_soldier_military_program',
    'create_sleep_cursed_faerie', 'create_scythe_tiger',
    'create_undiscovered_paradise', 'create_sazhs_chocobo',
    'create_student_of_warfare', 'create_old_growth_dryads',
    'create_dryad_arbor', 'create_dragon_sniper',
    'create_stromkirk_noble', 'create_heartfire_hero',
    'create_bottomless_vault', 'create_tomb_of_urami', 'create_urami_token',
    'create_remote_farm', 'create_luminarch_aspirant',
    'create_thallid', 'create_saproling_token', 'create_pendelhaven',
    'create_shrieking_affliction',
    'create_durkwood_baloth', 'create_keldon_halberdier',
    'create_daze',
    # Card classes
    'Mountain', 'Hammerheim', 'SleepCursedFaerie', 'ScytheTiger',
    'UndiscoveredParadise', 'SazhsChocobo', 'StudentOfWarfare',
    'OldGrowthDryads', 'DryadArbor', 'DragonSniper', 'StromkirkNoble',
    'HeartfireHero', 'BottomlessVault', 'TombOfUrami', 'UramiToken',
    'RemoteFarm', 'LuminarchAspirant', 'Thallid', 'SaprolingToken', 'Pendelhaven',
    'ShriekingAffliction', 'CrystalVein', 'SoldierToken', 'SoldierMilitaryProgram',
    'DurkwoodBaloth', 'KeldonHalberdier', 'Daze',
]
