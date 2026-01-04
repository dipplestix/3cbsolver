# 3CB Solver

A perfect-play solver for Three Card Blind (3CB), a Magic: The Gathering variant where each player has exactly 3 cards and perfect information.

## What is 3CB?

Three Card Blind is a minimalist MTG format where:
- Each player builds a "deck" of exactly 3 cards
- Both players have perfect information (all cards are revealed)
- The game is solved via minimax search to determine the optimal line of play

## Features

- **Alpha-beta minimax solver** with transposition tables and dominance pruning
- **Modular card system** - each card defines its own actions and triggers
- **Nash equilibrium calculator** using R-NAD (Replicator Neural Annealing Dynamics)
- **CLI interface** for solving matchups, viewing optimal lines, and computing metagame tables

## Installation

```bash
# Clone the repository
git clone https://github.com/dipplestix/3cbsolver.git
cd 3cbsolver

# Install dependencies (using uv)
uv sync
```

## Usage

### Solve a matchup
```bash
python cli.py solve student scf --first 0
```

### Show optimal play line
```bash
python cli.py show student scf --first 0
```

### Test against goldfish (no opponent)
```bash
python cli.py goldfish student --show
```

### Run metagame table with Nash equilibrium
```bash
python cli.py metagame
```

### List available decks
```bash
python cli.py list
```

## Available Decks

| Deck | Cards |
|------|-------|
| `student` | Plains + Student of Warfare |
| `scf` | Island + Sleep-Cursed Faerie |
| `tiger` | Forest + Scythe Tiger |
| `noble` | Mountain + Stromkirk Noble |
| `hero` | Mountain + Hammerheim + Heartfire Hero |
| `sniper` | Mountain + Dragon Sniper |
| `mutavault` | Mutavault |

## Architecture

```
simulator/
├── solver.py        # Minimax search with alpha-beta pruning
├── game_state.py    # GameState dataclass and core methods
├── actions.py       # Action generation by phase
├── combat.py        # Combat damage resolution
├── heuristics.py    # Early termination for grinding games
├── tables.py        # Transposition and dominance tables
├── helpers.py       # Creature stat/keyword queries
├── nash.py          # Nash equilibrium via R-NAD
├── phases/          # Phase handlers (untap, upkeep, end_turn)
└── cards/           # Card implementations
    ├── base.py      # Base classes (Card, Creature, Land, Action)
    └── *.py         # Individual card implementations
```

### Data Flow

```
solve(p1_hand, p2_hand)
  └── minimax(state, player)
        ├── evaluate_position()        [heuristics.py]
        ├── lookup_transposition()     [tables.py]
        ├── check_dominance()          [tables.py]
        ├── get_available_actions()    [actions.py]
        │     └── card.get_play_actions() / get_battlefield_actions()
        ├── action.execute(state) → new GameState
        └── recurse minimax()
```

### Phase Flow

```
end_turn → untap → upkeep → main1 → combat_attack → combat_block → combat_damage ─┐
    ^                                                                              │
    └──────────────────────────────────────────────────────────────────────────────┘
```

**Decision points:** main1, combat_attack, combat_block
**Automatic:** untap, upkeep, combat_damage, end_turn

## License

See [LICENSE](LICENSE) for details.

