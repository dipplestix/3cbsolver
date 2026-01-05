import marimo

__generated_with = "0.10.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # 04: Helpers Module

        **File:** `simulator/helpers.py`

        Utility functions for calculating creature stats and checking keywords.
        These helpers handle the complexity of creatures with:
        - Dynamic power/toughness (levels, counters)
        - End-of-turn boosts
        - Multiple keyword sources (properties vs lists)

        ## Functions
        | Function | Purpose |
        |----------|---------|
        | `get_creature_power(card)` | Get current power including all modifiers |
        | `get_creature_toughness(card)` | Get current toughness including all modifiers |
        | `has_first_strike(card)` | Check for first strike keyword |
        | `has_double_strike(card)` | Check for double strike keyword |
        | `has_deathtouch(card)` | Check for deathtouch keyword |
        | `is_lethal_damage(damage, toughness, deathtouch)` | Check if damage kills |
        """
    )
    return


@app.cell
def _():
    # Setup: Add parent directory to path for imports
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent if "__file__" in dir() else Path.cwd().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return Path, project_root, sys


@app.cell
def _():
    from simulator.helpers import (
        get_creature_power,
        get_creature_toughness,
        has_first_strike,
        has_double_strike,
        has_deathtouch,
        is_lethal_damage
    )
    return (
        get_creature_power,
        get_creature_toughness,
        has_deathtouch,
        has_double_strike,
        has_first_strike,
        is_lethal_damage,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Power/Toughness Calculation

        Creatures can have power/toughness from multiple sources:

        1. **Base stats** - `card.power` / `card.toughness`
        2. **Level-based** - `card.current_power` / `card.current_toughness` (Student of Warfare)
        3. **+1/+1 counters** - Implicit in `current_power/toughness`
        4. **End-of-turn boosts** - `card.eot_power_boost` / `card.eot_toughness_boost`

        The helpers check for `current_power`/`current_toughness` first (for level-up creatures),
        then fall back to base `power`/`toughness`.
        """
    )
    return


@app.cell
def _(get_creature_power, get_creature_toughness):
    # Create test creatures with different stat sources

    class BasicCreature:
        """Simple creature with base stats."""
        power = 2
        toughness = 3

    class LevelCreature:
        """Creature with level-based stats (like Student of Warfare)."""
        power = 1
        toughness = 1

        @property
        def current_power(self):
            return 3  # At level 2+

        @property
        def current_toughness(self):
            return 3  # At level 2+

    class BoostedCreature:
        """Creature with end-of-turn boost."""
        power = 2
        toughness = 2
        eot_power_boost = 2
        eot_toughness_boost = 1

    basic = BasicCreature()
    leveled = LevelCreature()
    boosted = BoostedCreature()

    print("Power/Toughness calculations:")
    print(f"  Basic (2/3): {get_creature_power(basic)}/{get_creature_toughness(basic)}")
    print(f"  Leveled (3/3 from current_*): {get_creature_power(leveled)}/{get_creature_toughness(leveled)}")
    print(f"  Boosted (2+2/2+1): {get_creature_power(boosted)}/{get_creature_toughness(boosted)}")
    return (
        BasicCreature,
        BoostedCreature,
        LevelCreature,
        basic,
        boosted,
        leveled,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Keyword Checking

        Keywords can be defined two ways:
        1. **Property methods** - `card.has_first_strike`, `card.has_deathtouch`
        2. **Keywords list** - `'first_strike' in card.keywords`

        The helpers check both, with property taking precedence.
        """
    )
    return


@app.cell
def _(has_deathtouch, has_double_strike, has_first_strike):
    # Creatures with keywords in different ways

    class PropertyKeywords:
        """Creature with keyword properties."""
        has_first_strike = True
        has_double_strike = False
        has_deathtouch = True

    class ListKeywords:
        """Creature with keywords list."""
        keywords = ['first_strike', 'deathtouch']

    class MixedKeywords:
        """Creature with both."""
        keywords = ['vigilance']
        has_first_strike = False  # Property overrides even if in list

    prop_creature = PropertyKeywords()
    list_creature = ListKeywords()
    mixed_creature = MixedKeywords()

    print("Keyword checking:")
    print(f"\nProperty-based creature:")
    print(f"  first_strike: {has_first_strike(prop_creature)}")
    print(f"  double_strike: {has_double_strike(prop_creature)}")
    print(f"  deathtouch: {has_deathtouch(prop_creature)}")

    print(f"\nList-based creature:")
    print(f"  first_strike: {has_first_strike(list_creature)}")
    print(f"  double_strike: {has_double_strike(list_creature)}")
    print(f"  deathtouch: {has_deathtouch(list_creature)}")

    print(f"\nMixed (property False overrides):")
    print(f"  first_strike: {has_first_strike(mixed_creature)}")
    return (
        ListKeywords,
        MixedKeywords,
        PropertyKeywords,
        list_creature,
        mixed_creature,
        prop_creature,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Lethal Damage

        `is_lethal_damage()` determines if damage kills a creature, considering:
        - Normal damage: lethal if `damage >= toughness`
        - Deathtouch: lethal if `damage > 0`
        """
    )
    return


@app.cell
def _(is_lethal_damage):
    print("Lethal damage examples:")
    print(f"\n3 damage to 3 toughness (no deathtouch):")
    print(f"  Lethal: {is_lethal_damage(3, 3, False)}")

    print(f"\n2 damage to 3 toughness (no deathtouch):")
    print(f"  Lethal: {is_lethal_damage(2, 3, False)}")

    print(f"\n1 damage to 5 toughness (WITH deathtouch):")
    print(f"  Lethal: {is_lethal_damage(1, 5, True)}")

    print(f"\n0 damage to 1 toughness (WITH deathtouch):")
    print(f"  Lethal: {is_lethal_damage(0, 1, True)}")
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Usage in Combat

        These helpers are used in `combat.py` to resolve damage:

        ```python
        # In resolve_combat_damage():
        attacker_power = get_creature_power(attacker)
        blocker_toughness = get_creature_toughness(blocker)
        attacker_deathtouch = has_deathtouch(attacker)

        if is_lethal_damage(attacker_power, blocker_toughness, attacker_deathtouch):
            # Blocker dies
        ```

        The level-based stats are important for Student of Warfare:
        - Level 0-1: 1/1
        - Level 2-6: 3/3 first strike
        - Level 7+: 4/4 double strike
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        The helpers module provides:
        1. **Unified stat access** - Handles levels, counters, boosts
        2. **Keyword polymorphism** - Works with properties or lists
        3. **Damage calculation** - Deathtouch-aware lethality

        This abstraction keeps combat logic clean and handles the
        complexity of different creature implementations.
        """
    )
    return


if __name__ == "__main__":
    app.run()
