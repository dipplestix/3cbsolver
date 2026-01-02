"""Helper functions for creature stats and keywords."""


def get_creature_power(card) -> int:
    """Get a creature's current power (including +1/+1 counters, levels, eot boosts, etc)."""
    if hasattr(card, 'current_power'):
        base = card.current_power
    else:
        base = card.power if hasattr(card, 'power') else 0
    return base + getattr(card, 'eot_power_boost', 0)


def get_creature_toughness(card) -> int:
    """Get a creature's current toughness (including +1/+1 counters, levels, eot boosts, etc)."""
    if hasattr(card, 'current_toughness'):
        base = card.current_toughness
    else:
        base = card.toughness if hasattr(card, 'toughness') else 0
    return base + getattr(card, 'eot_toughness_boost', 0)


def has_first_strike(card) -> bool:
    """Check if creature has first strike."""
    if hasattr(card, 'has_first_strike'):
        return card.has_first_strike
    if hasattr(card, 'keywords'):
        return 'first_strike' in card.keywords
    return False


def has_double_strike(card) -> bool:
    """Check if creature has double strike."""
    if hasattr(card, 'has_double_strike'):
        return card.has_double_strike
    if hasattr(card, 'keywords'):
        return 'double_strike' in card.keywords
    return False


def has_deathtouch(card) -> bool:
    """Check if creature has deathtouch."""
    if hasattr(card, 'has_deathtouch'):
        return card.has_deathtouch
    if hasattr(card, 'keywords'):
        return 'deathtouch' in card.keywords
    return False


def is_lethal_damage(damage: int, toughness: int, attacker_has_deathtouch: bool) -> bool:
    """Check if damage is lethal (considering deathtouch)."""
    if attacker_has_deathtouch and damage > 0:
        return True
    return damage >= toughness
