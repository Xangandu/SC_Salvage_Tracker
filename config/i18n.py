"""UI-Sprachen: Englisch (Standard) und Deutsch."""

from __future__ import annotations

SUPPORTED_LANGUAGES = ("en", "de")
DEFAULT_LANGUAGE = "en"

SETTING_LANGUAGE = "language"
SETTING_LANGUAGE_CONFIRMED = "language_confirmed"

_current_language = DEFAULT_LANGUAGE

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "language.dialog.title": "Choose Language",
        "language.dialog.subtitle": "Select your interface language",
        "language.dialog.hint": "You can change this later under Settings → Design → Appearance.",
        "language.dialog.continue": "Continue",
        "language.name.en": "English",
        "language.name.de": "Deutsch",
        "login.title": "Sign In",
        "login.tagline": "SALVAGE TRACKER",
        "login.username": "Username",
        "login.password": "Password",
        "login.remember": "Stay signed in",
        "login.button": "SIGN IN",
        "login.first_setup.banner": (
            "INITIAL SETUP\n"
            "User: {username}  ·  Password: {password}\n"
            "After sign-in you must change your password and create an organization administrator."
        ),
        "login.recovery.hint": (
            "EMERGENCY MAINTENANCE\n"
            "Sign in as super administrator ({username}) using the "
            "credentials you set during initial setup."
        ),
        "setup.wizard.title": "Initial Setup",
        "setup.wizard.tagline": "INITIAL SETUP",
        "setup.step.welcome": "WELCOME",
        "setup.step.emergency": "EMERGENCY ACCESS",
        "setup.step.admin": "ADMINISTRATOR",
        "setup.step.finish": "FINISH",
        "setup.step.indicator": "STEP {current} · {total}  —  {name}",
        "setup.welcome.info": (
            "Set up the Salvage Tracker for your organization.\n\n"
            "First you secure the emergency super administrator, "
            "then you create the organization administrator.\n\n"
            "For everyday use, sign in with the organization "
            "administrator — not the super administrator."
        ),
        "setup.emergency.title": "Secure Emergency Access",
        "setup.emergency.banner": (
            "EMERGENCY SUPER ADMINISTRATOR\n"
            "Username: {username}"
        ),
        "setup.emergency.info": (
            "This account already exists and is only for emergencies "
            "(forgotten admin, reset user passwords).\n\n"
            "Choose a strong password and write down the credentials. "
            "You will need them only if something goes wrong later."
        ),
        "setup.emergency.password": "New password",
        "setup.emergency.confirm": "Confirm password",
        "setup.emergency.note_checkbox": (
            "I have written down the super administrator credentials"
        ),
        "setup.emergency.error.note": (
            "Please confirm that you have written down the credentials."
        ),
        "setup.emergency.error.default_password": (
            "Please choose a password other than the default."
        ),
        "setup.emergency.button": "SAVE EMERGENCY ACCESS",
        "setup.admin.title": "Organization Administrator",
        "setup.admin.hint": (
            "Role: {role} (fixed)\n"
            "This user sets their own password on first sign-in."
        ),
        "setup.admin.username": "Username",
        "setup.admin.display_name": "Display name",
        "setup.admin.display_name_optional": "Display name (optional)",
        "setup.admin.password": "Password",
        "setup.admin.password_placeholder": "Password (at least 6 characters)",
        "setup.admin.confirm": "Confirm password",
        "setup.admin.confirm_placeholder": "Repeat password",
        "setup.admin.button": "CREATE ADMINISTRATOR",
        "setup.finish.title": "Ready",
        "setup.finish.success": "Initial setup complete",
        "setup.finish.message": (
            "The organization administrator \"{username}\" was created.\n\n"
            "Click \"Finish\" and sign in with the new administrator."
        ),
        "setup.button.back": "BACK",
        "setup.button.next": "CONTINUE",
        "setup.button.finish": "FINISH",
        "setup.error.title": "Initial Setup",
        "setup.error.username": "Please enter a username.",
        "setup.error.reserved_username": (
            "The username \"{username}\" is reserved for the "
            "super administrator."
        ),
        "setup.error.password_length": (
            "The password must be at least 6 characters long."
        ),
        "setup.error.password_mismatch": "The passwords do not match.",
        "setup.error.role_missing": (
            "The role \"{role}\" was not found. "
            "Please restart the application."
        ),
        "setup.error.create_failed": (
            "The administrator could not be created. "
            "The username may already exist."
        ),
        "setup.close_blocked": (
            "Initial setup must be completed before you can use "
            "the Salvage Tracker."
        ),
        "login.error.empty": "Please enter username and password.",
        "login.error.failed": "Sign-in failed.",
        "login.error.blocked": "This user cannot sign in at the moment.",
        "setup.complete.title": "Initial Setup Complete",
        "setup.complete.message": (
            "Initial setup is complete.\n\n"
            "Sign in now as \"{username}\"."
        ),
        "nav.dashboard": "Overview",
        "nav.session": "Session",
        "nav.refinery": "Refinery",
        "nav.sales": "Sales",
        "nav.payout": "Payout",
        "nav.history": "History",
        "nav.settings": "Settings",
        "nav.logout": "Sign Out",
        "admin.language": "Language",
        "admin.language.restart_hint": (
            "Language saved. Restart the application for all texts to update."
        ),
        "status.ACTIVE": "ACTIVE",
        "status.WAITING_FOR_REFINERY": "WAITING FOR REFINERY",
        "status.WAITING_FOR_SALE": "READY FOR SALE",
        "status.WAITING_FOR_PAYOUT": "PAYOUT",
        "status.REFINERY_COMPLETED": "READY FOR SALE",
        "status.SOLD": "SOLD",
        "status.IDLE": "IDLE",
    },
    "de": {
        "language.dialog.title": "Sprache wählen",
        "language.dialog.subtitle": "Wähle deine Oberflächensprache",
        "language.dialog.hint": "Du kannst das später unter Einstellungen → Design → Erscheinungsbild ändern.",
        "language.dialog.continue": "Weiter",
        "language.name.en": "English",
        "language.name.de": "Deutsch",
        "login.title": "Anmeldung",
        "login.tagline": "BERGUNGS-TRACKER",
        "login.username": "Benutzername",
        "login.password": "Passwort",
        "login.remember": "Angemeldet bleiben",
        "login.button": "ANMELDEN",
        "login.first_setup.banner": (
            "ERSTINSTALLATION\n"
            "Benutzer: {username}  ·  Passwort: {password}\n"
            "Nach der Anmeldung musst du dein Passwort ändern und einen Organisations-Administrator anlegen."
        ),
        "login.recovery.hint": (
            "NOTFALL-WARTUNG\n"
            "Melde dich als Super-Administrator ({username}) mit den "
            "Zugangsdaten an, die du bei der Erstinstallation festgelegt hast."
        ),
        "setup.wizard.title": "Erstinstallation",
        "setup.wizard.tagline": "ERSTINSTALLATION",
        "setup.step.welcome": "WILLKOMMEN",
        "setup.step.emergency": "NOTFALL-ZUGANG",
        "setup.step.admin": "ADMINISTRATOR",
        "setup.step.finish": "ABSCHLUSS",
        "setup.step.indicator": "SCHRITT {current} · {total}  —  {name}",
        "setup.welcome.info": (
            "Richte den Salvage Tracker für deine Organisation ein.\n\n"
            "Zuerst sicherst du den Notfall-Zugang (Super-Administrator), "
            "danach legst du den Organisations-Administrator an.\n\n"
            "Für den normalen Betrieb meldest du dich mit dem "
            "Organisations-Administrator an — nicht mit dem Super-Administrator."
        ),
        "setup.emergency.title": "Notfall-Zugang absichern",
        "setup.emergency.banner": (
            "NOTFALL SUPER-ADMINISTRATOR\n"
            "Benutzername: {username}"
        ),
        "setup.emergency.info": (
            "Dieses Konto existiert bereits und ist nur für Notfälle "
            "gedacht (Admin vergessen, Benutzer-Passwörter zurücksetzen).\n\n"
            "Wähle ein sicheres Passwort und schreib dir die Zugangsdaten auf. "
            "Du brauchst sie nur, wenn später etwas schiefgeht."
        ),
        "setup.emergency.password": "Neues Passwort",
        "setup.emergency.confirm": "Passwort bestätigen",
        "setup.emergency.note_checkbox": (
            "Ich habe die Zugangsdaten des Super-Administrators notiert"
        ),
        "setup.emergency.error.note": (
            "Bitte bestätige, dass du die Zugangsdaten notiert hast."
        ),
        "setup.emergency.error.default_password": (
            "Bitte ein anderes Passwort als das Standard-Passwort wählen."
        ),
        "setup.emergency.button": "NOTFALL-ZUGANG SPEICHERN",
        "setup.admin.title": "Organisations-Administrator",
        "setup.admin.hint": (
            "Rolle: {role} (fest)\n"
            "Der neue Benutzer setzt beim ersten Login ein eigenes Passwort."
        ),
        "setup.admin.username": "Benutzername",
        "setup.admin.display_name": "Anzeigename",
        "setup.admin.display_name_optional": "Anzeigename (optional)",
        "setup.admin.password": "Passwort",
        "setup.admin.password_placeholder": "Passwort (mindestens 6 Zeichen)",
        "setup.admin.confirm": "Passwort bestätigen",
        "setup.admin.confirm_placeholder": "Passwort wiederholen",
        "setup.admin.button": "ADMINISTRATOR ANLEGEN",
        "setup.finish.title": "Bereit",
        "setup.finish.success": "Erstinstallation abgeschlossen",
        "setup.finish.message": (
            "Der Organisations-Administrator „{username}“ wurde angelegt.\n\n"
            "Klicke auf „Fertig“ und melde dich danach mit dem neuen "
            "Administrator an."
        ),
        "setup.button.back": "ZURÜCK",
        "setup.button.next": "WEITER",
        "setup.button.finish": "FERTIG",
        "setup.error.title": "Erstinstallation",
        "setup.error.username": "Bitte einen Benutzernamen eingeben.",
        "setup.error.reserved_username": (
            "Der Benutzername „{username}“ ist für den "
            "Super-Administrator reserviert."
        ),
        "setup.error.password_length": (
            "Das Passwort muss mindestens 6 Zeichen lang sein."
        ),
        "setup.error.password_mismatch": (
            "Die Passwörter stimmen nicht überein."
        ),
        "setup.error.role_missing": (
            "Die Rolle „{role}“ wurde nicht gefunden. "
            "Bitte starte die Anwendung neu."
        ),
        "setup.error.create_failed": (
            "Der Administrator konnte nicht angelegt werden. "
            "Der Benutzername existiert möglicherweise bereits."
        ),
        "setup.close_blocked": (
            "Die Erstinstallation muss abgeschlossen werden, "
            "bevor der Salvage Tracker genutzt werden kann."
        ),
        "login.error.empty": "Bitte Benutzername und Passwort eingeben.",
        "login.error.failed": "Anmeldung fehlgeschlagen.",
        "login.error.blocked": "Dieser Benutzer darf sich derzeit nicht anmelden.",
        "setup.complete.title": "Erstinstallation abgeschlossen",
        "setup.complete.message": (
            "Die Erstinstallation ist abgeschlossen.\n\n"
            "Melde dich jetzt als „{username}“ an."
        ),
        "nav.dashboard": "Übersicht",
        "nav.session": "Sitzung",
        "nav.refinery": "Raffinerie",
        "nav.sales": "Verkäufe",
        "nav.payout": "Auszahlung",
        "nav.history": "Historie",
        "nav.settings": "Einstellungen",
        "nav.logout": "Abmelden",
        "admin.language": "Sprache",
        "admin.language.restart_hint": (
            "Sprache gespeichert. Bitte die Anwendung neu starten, "
            "damit alle Texte aktualisiert werden."
        ),
        "status.ACTIVE": "AKTIV",
        "status.WAITING_FOR_REFINERY": "WARTET AUF RAFFINERIE",
        "status.WAITING_FOR_SALE": "VERKAUFSBEREIT",
        "status.WAITING_FOR_PAYOUT": "AUSZAHLUNG",
        "status.REFINERY_COMPLETED": "VERKAUFSBEREIT",
        "status.SOLD": "VERKAUFT",
        "status.IDLE": "LEERLAUF",
    },
}


def normalize_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE
    lang = str(value).strip().lower()[:2]
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return DEFAULT_LANGUAGE


def current_language() -> str:
    return _current_language


def set_language(language: str) -> None:
    global _current_language
    _current_language = normalize_language(language)


def tr(key: str, *, default: str | None = None, **kwargs) -> str:
    lang = _current_language
    table = _TRANSLATIONS.get(lang, _TRANSLATIONS[DEFAULT_LANGUAGE])
    text = table.get(key)
    if text is None:
        text = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key)
    if text is None:
        text = default if default is not None else key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text


def init_language_from_db(db) -> None:
    lang = db.settings.get_app_setting(
        SETTING_LANGUAGE,
        DEFAULT_LANGUAGE,
    )
    set_language(lang)


def is_language_confirmed(db) -> bool:
    return (
        db.settings.get_app_setting(SETTING_LANGUAGE_CONFIRMED, "0")
        == "1"
    )


def save_language_choice(db, language: str) -> None:
    lang = normalize_language(language)
    db.settings.set_app_setting(SETTING_LANGUAGE, lang)
    db.settings.set_app_setting(SETTING_LANGUAGE_CONFIRMED, "1")
    set_language(lang)


def format_number(value, decimals: int = 0) -> str:
    if _current_language == "de":
        from config.strings_de import format_number_de

        return format_number_de(value, decimals)
    formatted = f"{float(value):,.{decimals}f}"
    return formatted


def status_label(status: str) -> str:
    key = f"status.{status}"
    translated = tr(key, default=status)
    return translated
