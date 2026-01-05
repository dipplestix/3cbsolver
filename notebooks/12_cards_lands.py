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
        # 12: Land Card Implementations

        **Directory:** `simulator/cards/`

        ## Basic Lands
        - Plains (W), Island (U), Forest (G), Swamp (B), Mountain (R)

        ## Special Lands
        - Hammerheim (targets for Valiant), Undiscovered Paradise, Crystal Vein
        - Bottomless Vault (storage counters for black mana)
        - Tomb of Urami (creates 5/5 Demon token)
        - Remote Farm (depletion land, produces WW)

        ## Creature Lands
        - Mutavault (all types, 2/2)
        - Dryad Arbor (always creature)
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
    from simulator.cards.land import (
        Land, CreatureLand,
        create_plains, create_forest, create_island, create_swamp
    )
    return (
        CreatureLand,
        Land,
        create_forest,
        create_island,
        create_plains,
        create_swamp,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Basic Lands

        Each basic land:
        - Costs nothing to play
        - Produces 1 mana of its color
        - One land per turn limit
        """
    )
    return


@app.cell
def _(create_forest, create_island, create_plains, create_swamp):
    # Create basic lands
    lands = [
        create_plains(0),
        create_island(0),
        create_forest(0),
        create_swamp(0),
    ]

    print("Basic Lands:")
    for land in lands:
        print(f"  {land.name}: produces {land.mana_produced}, output={land.get_mana_output()}")
    return (lands,)


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Creature Lands

        Lands that can become creatures by paying activation cost.

        | Land | Cost | Stats | Special |
        |------|------|-------|---------|
        | Mutavault | 1 | 2/2 | All creature types |
        | Dryad Arbor | - | 1/1 | Always a creature |

        ### State Machine
        - `_is_creature = False` → Land only
        - Activate → `_is_creature = True`
        - End of turn → Reset to False
        """
    )
    return


@app.cell
def _(CreatureLand):
    # Create Mutavault
    mutavault = CreatureLand(
        name="Mutavault",
        owner=0,
        mana_produced='C',
        activation_cost=1,
        creature_power=2,
        creature_toughness=2,
        creature_keywords=[],
        creature_types=[],
        all_creature_types=True
    )

    print("Mutavault:")
    print(f"  As land: is_creature={mutavault.is_creature()}, power={mutavault.power}")

    mutavault._is_creature = True
    print(f"  Activated: is_creature={mutavault.is_creature()}, power={mutavault.power}")
    print(f"  All types: {mutavault.all_creature_types}")
    return (mutavault,)


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Storage Lands: Bottomless Vault

        Accumulates mana over time with storage counters:

        ```python
        # Enters tapped, stay_tapped=True
        # Each upkeep while tapped: +1 storage counter
        # "Prepare to release" sets stay_tapped=False
        # Next untap: vault untaps
        # Tap to release: converts all counters to black mana
        ```

        Used with Tomb of Urami (needs 4B to activate).

        **Memoization:** Caps `storage_counters` at 5 in signature (enough for Urami).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Tomb of Urami

        Legendary land that creates a 5/5 flying Demon Spirit token.

        **Activation:** `2BB, T, Sacrifice all lands → Create Urami`

        The Urami token:
        - 5/5 Demon Spirit with flying
        - Enters with summoning sickness
        - Goldfish kill: Turn 10

        Deck: `urami` = Bottomless Vault + Tomb of Urami
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Depletion Lands: Remote Farm

        Enters tapped with depletion counters. Produces extra mana but runs out.

        ```python
        depletion_counters = 2  # Starts with 2
        # Tap: Remove 1 counter, add WW
        # If no counters remain: sacrifice
        ```

        Used with Luminarch Aspirant for early double-white mana.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Landfall Triggers

        When a land enters, creatures with `plus_counters` get +1/+1:

        ```python
        def play_land(s):
            ns = s.copy()
            # ... move land to battlefield ...
            # Trigger landfall
            for card in ns.battlefield[self.owner]:
                if hasattr(card, 'plus_counters'):
                    card.plus_counters += 1
            return ns
        ```

        Affects: Heartfire Hero, etc.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Summary

        | Type | Zone | Mana | Combat |
        |------|------|------|--------|
        | Basic Land | battlefield | 1 colored | No |
        | Creature Land | battlefield | 1 (colorless) | When activated |
        | Dryad Arbor | battlefield | 1 G | Always |

        Lands are fundamental - every deck needs mana sources.
        """
    )
    return


if __name__ == "__main__":
    app.run()
