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
        # 13: Creature Card Implementations

        **Directory:** `simulator/cards/`

        ## Creature Categories

        ### Simple Creatures
        - Dragon Sniper (1/1 vigilance, reach, deathtouch)
        - Old Growth Dryads
        - Scythe Tiger

        ### Level-Up Creatures
        - Student of Warfare (levels 0→7+)

        ### Counter Creatures
        - Stromkirk Noble (+1/+1 on combat damage)
        - Luminarch Aspirant (distribute counters at combat)
        - Heartfire Hero (Valiant trigger, death trigger)

        ### Token Generators
        - Thallid (spore counters → saprolings)

        ### Tokens
        - Urami (5/5 flying Demon from Tomb of Urami)
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
    from simulator.cards.creature import Creature
    return (Creature,)


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Student of Warfare

        **File:** `student_of_warfare.py`

        Level-up creature that auto-levels each turn:

        | Level | Stats | Abilities |
        |-------|-------|-----------|
        | 0-1 | 1/1 | - |
        | 2-6 | 3/3 | First strike |
        | 7+ | 4/4 | Double strike |

        ### Auto-Level
        ```python
        self.auto_level = True
        # In upkeep and before combat:
        if card.auto_level:
            ns = card.do_auto_level(ns)
        ```
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Dragon Sniper

        **File:** `dragon_sniper.py`

        Simple but effective: 1/1 with three keywords
        - Vigilance (doesn't tap to attack)
        - Reach (can block flyers)
        - Deathtouch (any damage is lethal)

        Creates stalemate in mirrors (mutual deathtouch).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Thallid (Token Generator)

        **File:** `thallid.py`

        Creates infinite tokens over time:
        1. Each upkeep: +1 spore counter
        2. At 3 counters: Can create 1/1 Saproling
        3. Eventually overwhelms opponent

        ```python
        def on_upkeep(self, state):
            self.spore_counters += 1
            if self.spore_counters >= 3:
                # Can create token
        ```

        Wins vs static creatures, loses to growing creatures.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Stromkirk Noble

        **File:** `stromkirk_noble.py`

        Grows on combat damage to player:
        ```python
        def on_deal_combat_damage_to_player(self, state):
            self.plus_counters += 1
        ```

        Can't be blocked by Humans (evasion).
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Luminarch Aspirant

        **File:** `luminarch_aspirant.py`

        At beginning of combat, put +1/+1 counter on target creature:
        ```python
        # In combat_attack phase:
        if not self.combat_trigger_used:
            # Put +1/+1 on any creature you control
            target.plus_counters += 1
            self.combat_trigger_used = True
        ```

        **Memoization:** Caps `plus_counters` at 30 in signature.

        Deck: `aspirant` = Remote Farm + Luminarch Aspirant
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Heartfire Hero

        **File:** `heartfire_hero.py`

        Two triggers:
        1. **Valiant** - When targeted, gets +1/+1 until end of turn
        2. **Death** - Deals damage equal to power to opponent

        ```python
        def on_become_target(self, state):
            self.eot_power_boost += 1
            self.eot_toughness_boost += 1

        def on_death(self, state):
            opponent = 1 - self.owner
            ns.life[opponent] -= self.current_power
        ```

        Deck: `hero` = Hammerheim + Heartfire Hero
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Sleep-Cursed Faerie

        **File:** `sleep_cursed_faerie.py`

        Enters with stun counters:
        - Can't untap normally while stunned
        - Remove 1 stun counter instead of untapping
        - Cheap 3/3 flyer with downside
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        """
        ---
        ## Creature Mechanics Summary

        | Mechanic | Creatures | Effect |
        |----------|-----------|--------|
        | Level-up | Student | Stats improve with levels |
        | +1/+1 counters | Stromkirk, Aspirant | Permanent stat boost |
        | Spore counters | Thallid | Generate tokens |
        | Stun counters | SCF | Delayed untap |
        | Deathtouch | Sniper | 1 damage = lethal |
        | Vigilance | Sniper | Attack without tapping |

        Each creature has unique `get_signature_state()` to include
        its special counters/levels in memoization.
        """
    )
    return


if __name__ == "__main__":
    app.run()
