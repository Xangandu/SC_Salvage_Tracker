"""Update-Paket — Persistenz und Verwaltung der Update-Prüfung.

HINWEIS (Cursor Cloud):
Dieses Paket wurde rekonstruiert, weil das ursprüngliche ``update``-Paket
nicht ins Repository eingecheckt wurde. ``ui/main_window.py`` und
``ui/admin_page.py`` importieren ``update.service`` bzw.
``ui/update_manager.py``; ohne diese Dateien lässt sich die Anwendung nicht
starten. Die Implementierung ist bewusst minimal gehalten (kein Netzwerk-
Zugriff) und persistiert lediglich die bereits vorhandenen App-Einstellungen
``update_auto_check`` und ``update_last_check``.
"""
