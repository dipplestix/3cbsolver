import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # 03: Card Type Classes

    **Files:**
    - `simulator/cards/land.py` - Land, CreatureLand
    - `simulator/cards/creature.py` - Creature
    - `simulator/cards/artifact.py` - Artifact
    - `simulator/cards/enchantment.py` - Enchantment
    - `simulator/cards/sorcery.py` - Sorcery
    - `simulator/cards/instant.py` - Instant

    These classes extend the base `Card` class with type-specific behavior.

    ## Inheritance Hierarchy
    ```
    Card (abstract base)
    ├── Land
    │   └── CreatureLand (Mutavault, Dryad Arbor, etc.)
    ├── Creature
    ├── Artifact
    ├── Enchantment
    ├── Sorcery (e.g., Inquisition of Kozilek)
    └── Instant (e.g., Mental Misstep)
    ```
    """)
    return


@app.cell
def _():
    # Setup: Add parent directory to path for imports
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent if "__file__" in dir() else Path.cwd().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return


@app.cell
def _():
    from simulator.cards.land import Land, CreatureLand, create_plains, create_forest
    from simulator.cards.creature import Creature
    from simulator.cards.artifact import Artifact, create_mox_jet, create_mox_pearl
    from simulator.cards.enchantment import Enchantment
    from simulator.cards.sorcery import Sorcery
    from simulator.cards.instant import Instant
    from simulator.cards import create_inquisition_of_kozilek, create_mental_misstep
    from simulator.game_state import GameState
    return (
        Creature,
        CreatureLand,
        Enchantment,
        GameState,
        Land,
        create_forest,
        create_inquisition_of_kozilek,
        create_mental_misstep,
        create_mox_jet,
        create_mox_pearl,
        create_plains,
    )


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Land Class

    Basic lands that produce mana when tapped.

    ### Key Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `mana_produced` | Color code: 'W', 'U', 'B', 'R', 'G' |
    | `entered_this_turn` | Summoning sickness tracking |

    ### Key Methods
    - `get_play_actions()` - Play land (once per turn, main phase only)
    - `get_mana_output()` - Returns 1 for basic lands
    - Landfall trigger: Increments `plus_counters` on creatures
    """)
    return


@app.cell
def _(create_forest, create_plains):
    # Create basic lands
    plains = create_plains(owner=0)
    forest = create_forest(owner=1)

    print("Basic Lands:")
    print(f"  Plains: owner={plains.owner}, mana={plains.mana_produced}")
    print(f"  Forest: owner={forest.owner}, mana={forest.mana_produced}")
    print(f"\nMana output: {plains.get_mana_output()}")
    return


@app.cell
def _(GameState, Land):
    # Test land play action
    test_land = Land("Test Plains", owner=0, mana_produced='W')

    # Create state with land in hand
    land_state = GameState(
        hands=[[test_land], []],
        active_player=0,
        phase="main1",
        land_played_this_turn=False
    )

    actions = test_land.get_play_actions(land_state)
    print(f"Available actions: {[str(a) for a in actions]}")

    # Check that we can't play if land already played
    land_state.land_played_this_turn = True
    actions_after = test_land.get_play_actions(land_state)
    print(f"After playing a land: {[str(a) for a in actions_after]}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## CreatureLand Class

    Lands that can become creatures (e.g., Mutavault).

    ### Key Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `activation_cost` | Mana to become creature |
    | `creature_power/toughness` | Stats when active |
    | `creature_keywords` | Keywords when creature |
    | `_is_creature` | Currently active? |
    | `all_creature_types` | Mutavault special case |

    ### Key Methods
    - `is_creature()` - Only True when `_is_creature` is True
    - `get_battlefield_actions()` - Activation action
    - `can_attack()` / `can_block()` - Combat eligibility
    - `on_end_turn()` - Resets creature status
    """)
    return


@app.cell
def _(CreatureLand):
    # Create a Mutavault-like creature land
    mutavault = CreatureLand(
        name="Mutavault",
        owner=0,
        mana_produced='C',  # Colorless
        activation_cost=1,
        creature_power=2,
        creature_toughness=2,
        creature_keywords=[],
        creature_types=[],
        all_creature_types=True  # Has all creature types
    )

    print("Mutavault (inactive):")
    print(f"  is_creature: {mutavault.is_creature()}")
    print(f"  power: {mutavault.power}")
    print(f"  toughness: {mutavault.toughness}")

    # Activate it
    mutavault._is_creature = True

    print("\nMutavault (active):")
    print(f"  is_creature: {mutavault.is_creature()}")
    print(f"  power: {mutavault.power}")
    print(f"  toughness: {mutavault.toughness}")
    print(f"  all_creature_types: {mutavault.all_creature_types}")
    return (mutavault,)


@app.cell
def _(mutavault):
    # Test combat eligibility
    mutavault._is_creature = True
    mutavault.entered_this_turn = False
    mutavault.tapped = False

    print("Combat eligibility (active, untapped, no summoning sickness):")
    print(f"  can_attack: {mutavault.can_attack()}")

    # With summoning sickness
    mutavault.entered_this_turn = True
    print("\nWith summoning sickness:")
    print(f"  can_attack: {mutavault.can_attack()}")

    # Reset
    mutavault.entered_this_turn = False
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Creature Class

    Standard creature cards with power, toughness, and combat abilities.

    ### Mana Cost System
    - `color_costs`: Dict of colored mana, e.g., `{'W': 1}` for {W}
    - `generic_cost`: Amount of generic mana (any color)

    ### Combat Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `power` / `toughness` | Combat stats |
    | `damage` | Current damage taken |
    | `attacking` | Currently attacking? |
    | `keywords` | Special abilities |
    | `creature_types` | For blocking restrictions |

    ### Key Methods
    - `is_alive` - toughness > damage
    - `can_attack()` - Not tapped, no summoning sickness
    - `can_block(attacker)` - Handles flying, reach, restrictions
    """)
    return


@app.cell
def _(Creature):
    # Create a simple creature
    soldier = Creature(
        name="Soldier",
        owner=0,
        power=2,
        toughness=2,
        color_costs={'W': 1},
        generic_cost=1,  # Total cost: 1W
        keywords=['first strike'],
        creature_types=['Human', 'Soldier']
    )

    print("Soldier creature:")
    print(f"  Power/Toughness: {soldier.power}/{soldier.toughness}")
    print(f"  Keywords: {soldier.keywords}")
    print(f"  Creature types: {soldier.creature_types}")
    print(f"  is_creature: {soldier.is_creature()}")
    print(f"  is_alive: {soldier.is_alive}")
    return (soldier,)


@app.cell
def _(Creature):
    # Create a flying creature
    flyer = Creature(
        name="Bird",
        owner=1,
        power=1,
        toughness=1,
        color_costs={'U': 1},
        keywords=['flying']
    )

    # Create a ground creature with reach
    archer = Creature(
        name="Archer",
        owner=0,
        power=1,
        toughness=2,
        color_costs={'G': 1},
        keywords=['reach']
    )

    # Create a ground creature without reach
    bear = Creature(
        name="Bear",
        owner=0,
        power=2,
        toughness=2,
        color_costs={'G': 1},
        keywords=[]
    )

    print("Blocking flying creatures:")
    print(f"  Bird has flying: {flyer.has_flying}")
    print(f"  Archer can block Bird: {archer.can_block(flyer)}")
    print(f"  Bear can block Bird: {bear.can_block(flyer)}")
    return


@app.cell
def _(Creature, GameState, Land):
    # Test creature casting
    test_creature = Creature(
        name="Test Creature",
        owner=0,
        power=2,
        toughness=2,
        color_costs={'W': 1},
        generic_cost=1
    )

    # State with creature in hand and 2 lands
    creature_state = GameState(
        hands=[[test_creature], []],
        battlefield=[
            [Land("Plains", 0, 'W'), Land("Forest", 0, 'G')],
            []
        ],
        active_player=0,
        phase="main1"
    )

    print("Casting requirements:")
    print(f"  Color costs: {test_creature.color_costs}")
    print(f"  Generic cost: {test_creature.generic_cost}")
    print(f"\nAvailable mana:")
    print(f"  Total: {creature_state.get_available_mana(0)}")
    print(f"  By color: {creature_state.get_available_mana_by_color(0)}")

    cast_actions = test_creature.get_play_actions(creature_state)
    print(f"\nCan cast: {len(cast_actions) > 0}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Artifact Class

    Non-creature artifacts, primarily mana rocks (Moxen).

    ### Key Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `mana_cost` | Cost to play (0 for Moxen) |
    | `mana_produced` | Color of mana produced |

    ### Behavior
    - Artifacts go to `artifacts` zone, not `battlefield`
    - No summoning sickness (can tap immediately)
    - Simpler than creatures (no combat)
    """)
    return


@app.cell
def _(create_mox_jet, create_mox_pearl):
    # Create Moxen
    mox_pearl = create_mox_pearl(owner=0)
    mox_jet = create_mox_jet(owner=1)

    print("Moxen:")
    print(f"  Mox Pearl: cost={mox_pearl.mana_cost}, produces={mox_pearl.mana_produced}")
    print(f"  Mox Jet: cost={mox_jet.mana_cost}, produces={mox_jet.mana_produced}")
    return (mox_pearl,)


@app.cell
def _(GameState, mox_pearl):
    # Test artifact play
    artifact_state = GameState(
        hands=[[mox_pearl], []],
        active_player=0,
        phase="main1"
    )

    # Mox costs 0, should always be playable
    mox_actions = mox_pearl.get_play_actions(artifact_state)
    print(f"Mox Pearl play actions: {[str(a) for a in mox_actions]}")

    # Execute the play action
    if mox_actions:
        after_play = mox_actions[0].execute(artifact_state)
        print(f"\nAfter playing Mox Pearl:")
        print(f"  Hand: {[c.name for c in after_play.hands[0]]}")
        print(f"  Artifacts: {[c.name for c in after_play.artifacts[0]]}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Enchantment Class

    Global enchantments with ongoing effects.

    ### Key Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `color_costs` | Colored mana requirements |
    | `generic_cost` | Generic mana requirement |

    ### Key Methods
    - `get_play_actions()` - Cast from hand
    - `on_opponent_upkeep()` - Hook for effects like Shrieking Affliction

    ### Behavior
    - Goes to `enchantments` zone
    - Typically no activated abilities
    - Override `on_opponent_upkeep()` for trigger effects
    """)
    return


@app.cell
def _(Enchantment, GameState, Land):
    # Create a simple enchantment
    test_enchantment = Enchantment(
        name="Test Enchantment",
        owner=0,
        color_costs={'B': 1},
        generic_cost=0
    )

    # State with enchantment in hand and swamp
    ench_state = GameState(
        hands=[[test_enchantment], []],
        battlefield=[[Land("Swamp", 0, 'B')], []],
        active_player=0,
        phase="main1"
    )

    ench_actions = test_enchantment.get_play_actions(ench_state)
    print(f"Enchantment play actions: {[str(a) for a in ench_actions]}")

    # Execute
    if ench_actions:
        after_cast = ench_actions[0].execute(ench_state)
        print(f"\nAfter casting:")
        print(f"  Hand: {[c.name for c in after_cast.hands[0]]}")
        print(f"  Enchantments: {[c.name for c in after_cast.enchantments[0]]}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Sorcery Class

    Spells that resolve once and go to graveyard.

    ### Key Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `color_costs` | Colored mana requirements |
    | `generic_cost` | Generic mana requirement |

    ### Key Methods
    - `get_play_actions()` - Cast from hand (main phase, empty stack)
    - `resolve(state)` - Abstract, implement spell effect
    - `can_cast(state)` - Check mana and timing

    ### Behavior
    - Can only cast during main phase when stack is empty
    - Goes on stack, triggers response phase
    - After resolution, goes to graveyard
    """)
    return


@app.cell
def _(create_inquisition_of_kozilek):
    # Example: Inquisition of Kozilek
    inquisition = create_inquisition_of_kozilek(owner=0)

    print("Inquisition of Kozilek:")
    print(f"  Mana value: {inquisition.get_mana_value()}")
    print(f"  Color costs: {inquisition.color_costs}")
    print(f"  Generic cost: {inquisition.generic_cost}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Instant Class

    Spells that can be cast in response to other spells.

    ### Key Attributes
    | Attribute | Description |
    |-----------|-------------|
    | `color_costs` | Colored mana requirements |
    | `generic_cost` | Generic mana requirement |

    ### Key Methods
    - `get_response_actions(state)` - Cast during response phase
    - `resolve(state)` - Abstract, implement spell effect
    - `can_pay_mana_cost(state)` - Check mana availability

    ### Behavior
    - Cast during response phase (when spell on stack)
    - Effect happens immediately (e.g., counter spell)
    - Goes to graveyard after use
    """)
    return


@app.cell
def _(create_mental_misstep):
    # Example: Mental Misstep
    misstep = create_mental_misstep(owner=1)

    print("Mental Misstep:")
    print(f"  Mana value: {misstep.get_mana_value()}")
    print(f"  Note: Phyrexian mana - can pay {'{U}'} or 2 life")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Signature States

    Each card type includes different state in its signature for memoization:

    | Type | Signature Contents |
    |------|-------------------|
    | Land | name, tapped, entered_this_turn |
    | CreatureLand | + _is_creature, attacking, damage |
    | Creature | + attacking, damage |
    | Artifact | name, tapped |
    | Enchantment | name, tapped |
    | Sorcery | name (+ target if applicable) |
    | Instant | name |
    """)
    return


@app.cell
def _(Land, mutavault, soldier):
    # Compare signatures
    basic_land = Land("Plains", 0, 'W')

    print("Signature comparison:")
    print(f"  Land: {basic_land.get_signature_state()}")
    print(f"  CreatureLand: {mutavault.get_signature_state()}")
    print(f"  Creature: {soldier.get_signature_state()}")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Summary

    ### Card Type Comparison

    | Type | Zone | Combat | Mana |
    |------|------|--------|------|
    | Land | battlefield | No | Produces |
    | CreatureLand | battlefield | When active | Produces |
    | Creature | battlefield | Yes | Costs |
    | Artifact | artifacts | No | May produce |
    | Enchantment | enchantments | No | Costs |
    | Sorcery | stack → graveyard | No | Costs |
    | Instant | stack → graveyard | No | Costs |

    ### Key Design Patterns

    1. **Zone Separation** - Different card types go to different zones
    2. **Action Polymorphism** - Each type overrides action methods appropriately
    3. **State Signatures** - Each type includes its relevant state
    4. **Copy Semantics** - Each type implements deep copy
    5. **Mana System** - Cards can have color + generic costs
    """)
    return


if __name__ == "__main__":
    app.run()
