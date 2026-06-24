#!/usr/bin/env python3
"""Tests für Supporter-Key-Validierung und Edition-Unlock."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.edition_keys import (  # noqa: E402
    edition_for_supporter_key,
    generate_supporter_key,
)
from config.editions import (  # noqa: E402
    SETTING_EDITION_UNLOCK,
    apply_supporter_key,
    clear_edition_unlock,
    effective_edition,
    has_feature,
)
from database.database import Database  # noqa: E402


def test_roundtrip_keys():
    for edition in ("crew", "orga"):
        key = generate_supporter_key(edition)
        assert edition_for_supporter_key(key) == edition
        assert edition_for_supporter_key(key.replace("-", " ")) == edition
    assert edition_for_supporter_key("CREW-INVALID-KEY") is None
    print("OK  key roundtrip")


def test_apply_unlock():
    db = Database()
    key = generate_supporter_key("crew")
    ok, _message = apply_supporter_key(db, key)
    assert ok
    assert db.settings.get_app_setting(SETTING_EDITION_UNLOCK) == "crew"
    assert effective_edition(db) == "crew"
    assert has_feature("network.crew_edition", db)
    clear_edition_unlock(db)
    assert db.settings.get_app_setting(SETTING_EDITION_UNLOCK) == ""
    assert effective_edition(db) == "solo"
    assert not has_feature("network.crew_edition", db)
    print("OK  apply/clear unlock")


def main() -> int:
    test_roundtrip_keys()
    test_apply_unlock()
    print("\nAlle Edition-Key-Tests bestanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
