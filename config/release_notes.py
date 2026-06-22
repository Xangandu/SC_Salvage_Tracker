from config.paths import changelogs_dir


def load_patchnotes():
    path = changelogs_dir() / "PATCHNOTES.txt"

    if path.exists():
        return path.read_text(encoding="utf-8")

    return "Keine Patchnotes gefunden."


def load_roadmap():
    path = changelogs_dir() / "ROADMAP.txt"

    if path.exists():
        return path.read_text(encoding="utf-8")

    return "Keine Roadmap gefunden."


def load_project_summary():
    path = changelogs_dir() / "PROJEKT_ZUSAMMENFASSUNG.txt"

    if path.exists():
        return path.read_text(encoding="utf-8")

    return ""
