"""
Produkt-Editionen: SOLO, CREW, ORGA.

Edition = welche Fähigkeiten diese Installation hat (Build + optionaler Unlock).
Rollen/Rechte (Administrator, Operator, …) bleiben davon getrennt.
"""

from __future__ import annotations

from config.version import APP_EDITION, EDITION_TITLES
from config.paths import is_frozen

EDITION_SOLO = "solo"
EDITION_CREW = "crew"
EDITION_ORGA = "orga"

EDITION_ORDER = (EDITION_SOLO, EDITION_CREW, EDITION_ORGA)

SETTING_EDITION_UNLOCK = "edition_unlock"

EDITION_SHORT = {
    EDITION_SOLO: "SOLO",
    EDITION_CREW: "CREW",
    EDITION_ORGA: "ORGA",
}

EDITION_GLOW_RGB: dict[str, tuple[int, int, int]] = {
    EDITION_SOLO: (0, 217, 255),
    EDITION_CREW: (65, 209, 122),
    EDITION_ORGA: (155, 122, 255),
}


def edition_short_label(db=None) -> str:
    return EDITION_SHORT.get(effective_edition(db), "SOLO")

# Feature-ID → mindestens erforderliche Edition
FEATURE_MIN_EDITION: dict[str, str] = {
    "network.host": EDITION_CREW,
    "network.client": EDITION_CREW,
    "network.crew_edition": EDITION_CREW,
    "org.module": EDITION_ORGA,
}

FEATURE_LABELS: dict[str, str] = {
    "network.host": "Crew hosten",
    "network.client": "Crew beitreten",
    "network.crew_edition": "Vernetzung (CREW Edition)",
    "org.module": "Organisations-Verwaltung",
}

TEASER_TEXT: dict[str, str] = {
    EDITION_CREW: (
        "Mit Freunden Salvage tracken: ein Host startet die Session, "
        "die Crew tritt per Code bei — alle arbeiten an einer gemeinsamen "
        "Datenbank. Verfügbar in der SC Salvage Tracker - CREW Version."
    ),
    EDITION_ORGA: (
        "Organisationen, mehrere Teams und erweiterte Verwaltung — "
        "geplant für die SC Salvage Tracker - ORGA Version."
    ),
}


def _edition_rank(edition: str) -> int:
    try:
        return EDITION_ORDER.index(edition)
    except ValueError:
        return 0


def max_edition(*editions: str) -> str:
    best = EDITION_SOLO
    best_rank = -1
    for edition in editions:
        rank = _edition_rank(edition)
        if rank > best_rank:
            best = edition
            best_rank = rank
    return best


def build_edition() -> str:
    """Edition aus dem Build (config/version.py), optional Dev-Override."""
    base = APP_EDITION if APP_EDITION in EDITION_ORDER else EDITION_SOLO
    if not is_frozen():
        import os

        env = (os.environ.get("SST_EDITION") or "").strip().lower()
        if env in EDITION_ORDER:
            return max_edition(base, env)
    return base


def unlocked_edition(db) -> str | None:
    if db is None:
        return None
    raw = db.settings.get_app_setting(SETTING_EDITION_UNLOCK, "") or ""
    raw = raw.strip().lower()
    if raw in EDITION_ORDER:
        return raw
    return None


def effective_edition(db=None) -> str:
    """Höchste gültige Edition: Build-Obergrenze ∩ optionaler Unlock."""
    ceiling = build_edition()
    unlock = unlocked_edition(db)
    if unlock is None:
        return ceiling
    return max_edition(ceiling, unlock)


def edition_title(edition_key: str | None = None) -> str:
    key = edition_key or EDITION_SOLO
    return EDITION_TITLES.get(key, EDITION_TITLES[EDITION_SOLO])


def resolve_app_name(db=None) -> str:
    return f"SC Salvage Tracker - {edition_title(effective_edition(db))}"


def required_edition(feature_id: str) -> str:
    return FEATURE_MIN_EDITION.get(feature_id, EDITION_SOLO)


def has_feature(feature_id: str, db=None) -> bool:
    needed = _edition_rank(required_edition(feature_id))
    current = _edition_rank(effective_edition(db))
    return current >= needed


def feature_teaser_text(feature_id: str) -> str:
    from config.i18n import tr

    needed = required_edition(feature_id)
    fallback = TEASER_TEXT.get(
        needed,
        f"Verfügbar in der SC Salvage Tracker - "
        f"{edition_title(needed)}.",
    )
    return tr(f"edition.teaser.{needed}", default=fallback)


def enforce_standalone_network(db) -> None:
    """SOLO-Edition: gespeicherten Netzwerkmodus auf Standalone zurücksetzen."""
    if has_feature("network.crew_edition", db):
        return
    from network.constants import NETWORK_MODE_STANDALONE
    from network.network_state import get_network_state

    db.settings.set_app_setting("network_mode", NETWORK_MODE_STANDALONE)
    get_network_state().mode = NETWORK_MODE_STANDALONE


def apply_supporter_key(db, raw_key: str) -> tuple[bool, str]:
    """Supporter-Key prüfen und edition_unlock speichern."""
    from config.edition_keys import edition_for_supporter_key
    from config.i18n import tr

    edition = edition_for_supporter_key(raw_key)
    if edition is None:
        return False, tr("edition.key.invalid")

    ceiling = build_edition()
    unlocked = max_edition(ceiling, edition)
    db.settings.set_app_setting(SETTING_EDITION_UNLOCK, edition)

    if unlocked == edition:
        message = tr(
            "edition.key.unlocked",
            edition=edition_title(edition),
        )
    else:
        message = tr(
            "edition.key.stored_ceiling",
            edition=edition_title(edition),
            ceiling=edition_title(ceiling),
        )

    return True, message


def clear_edition_unlock(db) -> None:
    db.settings.set_app_setting(SETTING_EDITION_UNLOCK, "")
    enforce_standalone_network(db)


def edition_unlock_label(db=None) -> str:
    unlock = unlocked_edition(db)
    if unlock is None:
        return "—"
    return edition_title(unlock)


def edition_status_lines(db=None) -> tuple[str, str, str]:
    """Build-Edition, optionaler Unlock und effektive Edition für die UI."""
    build = edition_title(build_edition())
    unlock = edition_unlock_label(db)
    effective = edition_title(effective_edition(db))
    return build, unlock, effective

