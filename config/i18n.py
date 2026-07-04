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
        "language.dialog.hint": (
            "You can change this later under Settings → Language."
        ),
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
            "Choose the username and password for everyday sign-in."
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
        "setup.welcome.info.solo": (
            "Set up Salvage Tracker for yourself.\n\n"
            "First you secure the emergency backup account, "
            "then you create your everyday sign-in account.\n\n"
            "For normal use, sign in with your user account — "
            "not the emergency account."
        ),
        "setup.step.admin.solo": "YOUR ACCOUNT",
        "setup.emergency.info.solo": (
            "This account already exists and is only for emergencies "
            "(forgotten password, recovery if something goes wrong).\n\n"
            "Choose a strong password and write down the credentials. "
            "You will need them only if something goes wrong later."
        ),
        "setup.emergency.note_checkbox.solo": (
            "I have written down the emergency access credentials"
        ),
        "setup.admin.title.solo": "Your sign-in account",
        "setup.admin.hint.solo": (
            "Choose the username and password you will use every time "
            "you open the tracker."
        ),
        "setup.admin.button.solo": "CREATE ACCOUNT",
        "setup.finish.message.solo": (
            "Your sign-in account \"{username}\" was created.\n\n"
            "Click \"Finish\" and sign in with the new account."
        ),
        "setup.complete.message.solo": (
            "Initial setup is complete.\n\n"
            "Sign in now with \"{username}\"."
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
            "The application will restart now to reload the database."
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
        "nav.storage": "Storage",
        "nav.sales": "Sales",
        "nav.payout": "Payout",
        "nav.history": "History",
        "nav.settings": "Settings",
        "nav.version_info": "Version Info",
        "nav.logout": "Sign Out",
        "nav.language.title": "Language",
        "admin.language": "Language",
        "admin.language.restart_now": (
            "Language saved. The application will restart now and "
            "sign you in automatically."
        ),
        "common.yes": "Yes",
        "common.no": "No",
        "common.preview": "Preview",
        "common.edit": "Edit",
        "common.choose": "Choose",
        "common.reset": "Reset",
        "common.close": "Close",
        "common.minimize": "Minimize",
        "common.maximize": "Maximize",
        "common.restore": "Restore",
        "admin.title": "SETTINGS",
        "admin.subtitle": "◆ SYSTEM & ORG ADMINISTRATION",
        "admin.tab.users": "Users",
        "admin.tab.roles": "Roles",
        "admin.tab.design": "Design",
        "admin.tab.network": "Networking",
        "admin.tab.support": "Support",
        "admin.tab.system": "System",
        "admin.tab.language": "Language",
        "admin.language.section": "◆ INTERFACE LANGUAGE",
        "admin.language.tab_hint": (
            "Choose the interface language and click Save. The application "
            "restarts automatically and signs you in again."
        ),
        "admin.users.section": "◆ USER OVERVIEW",
        "admin.users.col.username": "Username",
        "admin.users.col.display_name": "Display name",
        "admin.users.col.role": "Role",
        "admin.users.col.active": "Active",
        "admin.users.col.created": "Created",
        "admin.users.empty": "No users yet.",
        "admin.users.edit_display_name": "Change display name",
        "admin.users.reset_password": "Reset password",
        "admin.users.assign_role": "Assign role",
        "admin.users.toggle_active": "Active / Inactive",
        "admin.users.delete": "Delete user",
        "admin.users.create.section": "◆ CREATE USER",
        "admin.users.placeholder.username": "Username",
        "admin.users.placeholder.display_name": "Display name (optional)",
        "admin.users.placeholder.password": "Password",
        "admin.users.label.username": "Username",
        "admin.users.label.display_name": "Display name",
        "admin.users.label.password": "Password",
        "admin.users.label.role": "Role",
        "admin.users.create.button": "Create user",
        "admin.users.dialog.title": "Users",
        "admin.users.msg.username_required": "Please enter a username.",
        "admin.users.msg.password_required": "Please enter a password.",
        "admin.users.msg.role_required": (
            "Please create and assign a role first."
        ),
        "admin.users.msg.create_failed": (
            "Could not create user. The name may already exist."
        ),
        "admin.users.msg.created": "User was created.",
        "admin.users.msg.select_user": "Please select a user.",
        "admin.users.msg.display_name_title": "Display name",
        "admin.users.msg.display_name_prompt": "New display name:",
        "admin.users.msg.reset_password_title": "Reset password",
        "admin.users.msg.reset_password_prompt": "New password:",
        "admin.users.msg.password_reset": "Password was reset.",
        "admin.users.msg.no_assignable_roles": "No assignable roles available.",
        "admin.users.msg.assign_role_title": "Assign role",
        "admin.users.msg.assign_role_prompt": "Role:",
        "admin.users.msg.role_updated": (
            "Your role was updated. Navigation and permissions are adjusted."
        ),
        "admin.users.msg.delete_title": "Delete user",
        "admin.users.msg.delete_confirm": "Really delete this user?",
        "admin.roles.hint": (
            "Only the \"Administrator\" role is predefined. "
            "Create more roles and assign permissions — "
            "e.g. Officer, Member or Guest for your org."
        ),
        "admin.roles.section": "◆ ROLE OVERVIEW",
        "admin.roles.col.name": "Role name",
        "admin.roles.col.description": "Description",
        "admin.roles.col.permissions": "Permissions",
        "admin.roles.col.users": "Users",
        "admin.roles.empty": (
            "No roles yet. Click \"New role\" to create the first role "
            "for your org."
        ),
        "admin.roles.new": "New role",
        "admin.roles.edit": "Edit",
        "admin.roles.assign_permissions": "Assign permissions",
        "admin.roles.view_permissions": "View permissions",
        "admin.roles.delete": "Delete role",
        "admin.roles.dialog.title": "Roles",
        "admin.roles.msg.create_failed": "Could not create role:\n{error}",
        "admin.roles.msg.created": "Role \"{name}\" was created.",
        "admin.roles.msg.select_role": "Please select a role.",
        "admin.roles.msg.admin_locked": (
            "The Administrator role is system-defined and cannot be edited."
        ),
        "admin.roles.msg.save_failed": "Could not save role:\n{error}",
        "admin.roles.msg.permissions_reloaded": (
            "Your permissions were reloaded from the database."
        ),
        "admin.roles.msg.delete_title": "Delete role",
        "admin.roles.msg.delete_confirm": (
            "Really delete role \"{name}\"?"
        ),
        "admin.design.tab.appearance": "Appearance",
        "admin.design.tab.density": "Density",
        "admin.design.tab.colors": "Colors",
        "admin.design.tab.typography": "Fonts",
        "admin.design.tab.dashboard": "Dashboard",
        "admin.design.tab.organization": "Organization",
        "admin.design.section.appearance": "◆ APPEARANCE",
        "admin.design.section.density": "◆ DENSITY & TRANSPARENCY",
        "admin.design.section.colors": "◆ COLOR PALETTE",
        "admin.design.section.dashboard": "◆ DASHBOARD",
        "admin.design.section.organization": "◆ APP DEFAULT (ORGANIZATION)",
        "admin.design.section.typography": "◆ FONTS",
        "admin.design.hint.typography": (
            "Each category controls matching text across the app. The active "
            "theme is the default until you save — then your choices override "
            "the theme. Save stores your font theme as the new reset baseline."
        ),
        "typography.group.hierarchy": "Page & sections",
        "typography.group.forms": "Forms",
        "typography.group.data": "Data & KPIs",
        "typography.group.hints": "Hints & empty states",
        "typography.group.tables": "Tables",
        "typography.group.navigation": "Navigation",
        "typography.group.dashboard": "Dashboard",
        "typography.group.dialogs": "Dialogs & window",
        "typography.field.family": "Font family",
        "typography.field.size": "Size (px)",
        "typography.field.weight": "Font weight",
        "typography.field.letter_spacing": "Letter spacing (px)",
        "typography.field.color": "Color",
        "typography.family.inherit": "Inherit global font",
        "typography.weight.normal": "Normal",
        "typography.weight.semibold": "Semi-bold",
        "typography.weight.bold": "Bold",
        "typography.italic": "Italic",
        "typography.preview_label": "Preview",
        "typography.reset_role": "Reset this text style",
        "typography.reset_all": "Reset all fonts",
        "typography.color_dialog_title": "Pick text color",
        "typography.category.page_heading": "Page headings",
        "typography.category.page_heading.desc": (
            "Page names (Refinery, Storage, …) and large dashboard titles "
            "(◆ SESSION, ◆ REFINERY, …)."
        ),
        "typography.category.section_heading": "Section headings",
        "typography.category.section_heading.desc": (
            "Orange ◆ lines, subsection titles, navigation section labels "
            "(USER, LANGUAGE, …)."
        ),
        "typography.category.body": "Body text & labels",
        "typography.category.body.desc": (
            "Form labels, hints, read-only values, card subtitles, timeline "
            "text, and window title bar."
        ),
        "typography.category.data": "Numbers & highlights",
        "typography.category.data.desc": (
            "KPI values, statistics, and large dashboard numbers."
        ),
        "typography.category.profit": "Profit & earnings",
        "typography.category.profit.desc": (
            "Profit lines (e.g. “Profit: … aUEC”) and highlighted earnings "
            "on sales and finance summaries."
        ),
        "typography.category.button": "Buttons",
        "typography.category.button.desc": (
            "Primary and secondary actions, navigation buttons, and dashboard "
            "controls."
        ),
        "typography.category.table_header": "Table column headers",
        "typography.category.table_header.desc": (
            "Column titles in all data tables (Location, Material, Status, …)."
        ),
        "typography.category.table_cell": "Table cell text",
        "typography.category.table_cell.desc": (
            "Text inside table rows — values and entries in all data tables."
        ),
        "typography.category.input": "Input fields",
        "typography.category.input.desc": (
            "Text fields, dropdowns, spin boxes, and multi-line inputs."
        ),
        "typography.category.status": "Status messages",
        "typography.category.status.desc": (
            "Empty states, dialog messages, and warning banners."
        ),
        "typography.category.tooltip": "Tooltips",
        "typography.category.tooltip.desc": (
            "Short help text shown when hovering controls."
        ),
        "typography.preview.page_heading": "REFINERY",
        "typography.preview.section_heading": "◆ AVAILABLE MATERIAL",
        "typography.preview.body": "Refinery method",
        "typography.preview.data": "12.4 SCU",
        "typography.preview.profit": "Profit: 18,200 aUEC",
        "typography.preview.button": "SAVE",
        "typography.preview.table_header": "Location",
        "typography.preview.table_cell": "Terra Gateway",
        "typography.preview.input": "Search location…",
        "typography.preview.status": "No refinery jobs yet.",
        "typography.preview.tooltip": "Sorted by location.",
        "typography.role.page_title": "Page title",
        "typography.role.section_accent": "Section heading (◆ …)",
        "typography.role.subsection_title": "Subsection heading",
        "typography.role.form_label": "Form label",
        "typography.role.display_value": "Read-only field value",
        "typography.role.card_title": "Card / KPI title",
        "typography.role.card_value": "Card / KPI value",
        "typography.role.stat_label": "Statistics label",
        "typography.role.stat_value": "Statistics value",
        "typography.role.profit_label": "Profit highlight",
        "typography.role.muted_label": "Hint / secondary text",
        "typography.role.hint_label": "Small hint",
        "typography.role.empty_info": "Empty state message",
        "typography.role.table_header": "Table column header",
        "typography.role.table_cell": "Table cell text",
        "typography.role.nav_title_primary": "Navigation app title",
        "typography.role.nav_user_name": "Navigation username",
        "typography.role.nav_section_heading": "Navigation section heading",
        "typography.role.dashboard_context_title": "Dashboard context title",
        "typography.role.dashboard_timeline_when": "Dashboard timeline time",
        "typography.role.window_title": "Window title bar",
        "typography.role.dialog_info_value": "Dialog message text",
        "typography.preview.page_title": "REFINERY",
        "typography.preview.section_accent": "◆ AVAILABLE MATERIAL",
        "typography.preview.subsection_title": "◆ CREATE REFINERY JOB",
        "typography.preview.form_label": "Refinery method",
        "typography.preview.display_value": "Aegis Reclaimer",
        "typography.preview.card_title": "STATUS",
        "typography.preview.card_value": "12.4 SCU",
        "typography.preview.stat_label": "Mission costs",
        "typography.preview.stat_value": "24,500 aUEC",
        "typography.preview.profit_label": "+18,200 aUEC",
        "typography.preview.muted_label": "No active session.",
        "typography.preview.hint_label": "Sorted by location.",
        "typography.preview.empty_info": "No refinery jobs yet.",
        "typography.preview.table_header": "Location",
        "typography.preview.table_cell": "Terra Gateway",
        "typography.preview.nav_title_primary": "SALVAGE",
        "typography.preview.nav_user_name": "Xangandu",
        "typography.preview.nav_section_heading": "USER",
        "typography.preview.dashboard_context_title": "SESSION",
        "typography.preview.dashboard_timeline_when": "Today 14:32",
        "typography.preview.window_title": "SC SALVAGE TRACKER",
        "typography.preview.dialog_info_value": "Settings saved.",
        "admin.design.label.theme": "Theme",
        "admin.design.label.font_size": "Font size",
        "admin.design.label.font_family": "Font",
        "admin.design.label.animations": "Animations",
        "admin.design.label.nav_width": "Navigation width",
        "admin.design.label.table_density": "Table density",
        "admin.design.label.window_transparency": "Window transparency",
        "admin.design.label.panel_transparency": "Panel transparency",
        "admin.design.label.dashboard_layout": "Dashboard layout",
        "admin.design.label.dashboard_widgets": "Widgets (KPI & panels)",
        "admin.design.label.dashboard_title": "Heading (SALVAGE OVERVIEW)",
        "admin.design.label.dashboard_buttons": "Header buttons",
        "admin.design.label.default_theme": "Default theme",
        "admin.design.hint.appearance": (
            "Basic app appearance. Colors are set in the \"Colors\" tab. "
            "Window position and size are saved automatically on exit "
            "(including on a second monitor)."
        ),
        "admin.design.hint.density": (
            "Table density controls row height and padding. "
            "Window transparency affects background and navigation. "
            "Panel transparency applies in 5% steps to content and info panels."
        ),
        "admin.design.hint.colors": (
            "Empty fields use theme defaults. "
            "The accent color replaces highlight colors in the UI. "
            "Click the color swatch to open the color picker."
        ),
        "admin.design.hint.dashboard": (
            "Layout and font sizes can be scaled independently."
        ),
        "admin.design.hint.organization": (
            "Applies to all users without their own design settings. "
            "Administrators only."
        ),
        "admin.design.color.accent": "Accent color",
        "admin.design.color.label": "Label color",
        "admin.design.color.primary": "Primary button",
        "admin.design.color.secondary": "Secondary button",
        "admin.design.color.default_accent": "Default (theme accent)",
        "admin.design.color.default_label": "Default (theme label)",
        "admin.design.color.default_primary": "Default (theme primary)",
        "admin.design.color.default_secondary": "Default (theme secondary)",
        "admin.design.color.pick_accent": "Choose accent color",
        "admin.design.color.pick_label": "Choose label color",
        "admin.design.color.pick_primary": "Choose primary button",
        "admin.design.color.pick_secondary": "Choose secondary button",
        "admin.design.color.pick_tooltip": "Choose color",
        "admin.design.color.reset_tooltip": "Reset",
        "admin.design.save_app_defaults": "Save app default",
        "admin.design.dialog.title": "Design",
        "admin.design.msg.preview": (
            "Preview applied. Use \"Save\" to keep permanently."
        ),
        "admin.design.msg.saved": (
            "Your design settings were saved."
        ),
        "admin.design.msg.no_app_defaults_permission": (
            "No permission for app defaults."
        ),
        "admin.design.msg.app_defaults_saved": "App default was saved.",
        "admin.dashboard.dialog.title": "Dashboard",
        "admin.dashboard.msg.preview": (
            "Preview applied. Switch to the dashboard to see layout and "
            "font size. Use \"Save\" to keep permanently."
        ),
        "admin.dashboard.msg.saved": "Your dashboard settings were saved.",
        "theme.font_size.small": "Small",
        "theme.font_size.normal": "Normal",
        "theme.font_size.large": "Large",
        "theme.nav_width.narrow": "Narrow",
        "theme.nav_width.normal": "Normal",
        "theme.nav_width.wide": "Wide",
        "theme.animation.off": "Off",
        "theme.animation.reduced": "Reduced",
        "theme.animation.full": "Full",
        "theme.palette.dark": "Dark",
        "theme.palette.star_citizen": "Star Citizen",
        "theme.palette.light": "Light",
        "theme.table_density.compact": "Compact",
        "theme.table_density.normal": "Normal",
        "theme.table_density.spacious": "Spacious",
        "admin.network.section": "◆ CREW",
        "admin.network.hint": (
            "Host crew: copy and share the code. "
            "Join crew: enter the host's code. "
            "That's all you need."
        ),
        "admin.network.host_crew": "Host crew",
        "admin.network.join_crew": "Join crew",
        "admin.network.join_code": "Join code",
        "admin.network.copy_code": "Copy code",
        "admin.network.mode": "Mode",
        "admin.network.status": "Status",
        "admin.network.connected_crew": "Connected crew",
        "admin.network.advanced": "Advanced (optional)",
        "admin.network.relay_register": "Register at Salvage Relay",
        "admin.network.upnp": "Open internet (UPnP)",
        "admin.network.start_host": "Start host manually",
        "admin.network.stop_host": "Stop host",
        "admin.network.dialog.title": "Networking",
        "admin.network.msg.connected": "Connected to host.",
        "admin.network.code.dialog.title": "Code",
        "admin.network.msg.no_code": (
            "No code — click \"Host crew\" first."
        ),
        "admin.network.relay.dialog.title": "Salvage Relay",
        "admin.network.msg.relay_failed": (
            "Relay registration failed. "
            "Check network and relay settings."
        ),
        "admin.network.upnp.dialog.title": "UPnP",
        "admin.network.host.dialog.title": "Host",
        "admin.network.msg.host_running": "Host server is already running.",
        "admin.network.msg.host_start_failed": "Host server could not be started.",
        "admin.support.section.project": "◆ PROJECT",
        "admin.support.intro": (
            "{tagline}\n\n"
            "The SOLO edition is free — for solo players with the full "
            "salvage workflow (sessions, refinery, sales, dashboard).\n\n"
            "The CREW edition adds host/client networking: shared database, "
            "join code, crew plays together.\n\n"
            "The ORGA edition (roadmap) is for organizations and multiple teams."
        ),
        "admin.support.section.edition": "◆ YOUR EDITION",
        "admin.support.label.installation": "Installation",
        "admin.support.label.unlock": "Supporter unlock",
        "admin.support.label.active": "Active",
        "admin.support.section.key": "◆ SUPPORTER KEY",
        "admin.support.key.hint": (
            "A supporter key unlocks CREW or ORGA on this installation — "
            "without replacing the SOLO edition. Keys are stored per installation."
        ),
        "admin.support.label.key": "Key",
        "admin.support.placeholder.key": "e.g. CREW-ABCD-EFGH-XXXXXXXX",
        "admin.support.unlock": "Unlock",
        "admin.support.clear_unlock": "Remove unlock",
        "admin.support.section.donate": "◆ DONATE",
        "admin.support.donate.hint": (
            "If the tracker helps you, you can support development. "
            "The SOLO edition stays free."
        ),
        "admin.support.donate.button": "Support project",
        "admin.support.donate.tooltip_pending": (
            "Donation link will be added with the beta release."
        ),
        "admin.support.key.dialog.title": "Supporter key",
        "admin.support.msg.admin_only": "Only administrators can redeem keys.",
        "admin.support.msg.key_required": "Please enter a key.",
        "admin.support.msg.clear_title": "Remove unlock",
        "admin.support.msg.clear_confirm": (
            "Really remove supporter unlock?\n\n"
            "Networking will be locked again if only SOLO is active."
        ),
        "admin.support.msg.cleared_title": "Unlock removed",
        "admin.support.msg.cleared": "Supporter unlock was removed.",
        "admin.system.section.updates": "◆ UPDATES",
        "admin.system.section.login_history": "◆ LOGIN HISTORY",
        "admin.system.section.backup": "◆ DATA BACKUP",
        "admin.system.updates.installed": "Installed version: {version}",
        "admin.system.updates.last_check": "Last check: {datetime}",
        "admin.system.updates.no_check": "No update check performed yet.",
        "admin.system.updates.available": (
            "New update available: {version} (Build {build})\n{status}"
        ),
        "admin.system.updates.auto_check": "Check for updates on startup",
        "admin.system.updates.check_button": "Check for updates",
        "admin.system.updates.hint": (
            "Updates are provided via GitHub Releases. "
            "Checksum is verified before installation."
        ),
        "admin.system.updates.dialog.title": "Updates",
        "admin.system.updates.msg.not_ready": "Update service is not ready yet.",
        "admin.system.updates.checking": "Checking for updates…",
        "admin.system.history.col.id": "ID",
        "admin.system.history.col.user": "User",
        "admin.system.history.col.login": "Login",
        "admin.system.history.col.logout": "Logout",
        "admin.system.history.empty": "No logins recorded yet.",
        "admin.system.backup.create": "Create backup now",
        "admin.system.backup.restore": "Restore backup",
        "admin.system.backup.open_folder": "Open backup folder",
        "admin.system.backup.col.created": "Created",
        "admin.system.backup.col.size": "Size",
        "admin.system.backup.empty": "No backups yet.",
        "admin.system.backup.delete": "Delete backup",
        "admin.system.backup.danger_zone": "Danger zone",
        "admin.system.backup.danger_hint": (
            "Deletes all sessions, jobs, sales and users "
            "(except default admin). A backup is created automatically first."
        ),
        "admin.system.backup.reinitialize": "Delete all tracker data",
        "admin.system.backup.advanced": "Advanced (support)",
        "admin.system.backup.verify": "Verify database",
        "admin.system.backup.migrate": "Update database",
        "admin.system.backup.retention": "How many backups to keep?",
        "admin.system.backup.retention_hint": (
            "Oldest backups are deleted when the limit is reached. "
            "Automatic backup before delete and restore."
        ),
        "admin.system.backup.status.load_failed": "Could not load status",
        "admin.system.backup.status.needs_check": "Database should be checked",
        "admin.system.backup.status.ok": "All good",
        "admin.system.backup.summary": (
            "Program version: {version}<br>"
            "Stored backups: {count} "
            "<span style='color:#D9F4FF;'>(max. {max_count})</span><br>"
            "Latest backup: {latest}"
        ),
        "admin.system.backup.advanced_status": (
            "Build: {build}\n"
            "Schema: {schema} (target: {target_schema})\n"
            "Database path:\n{db_path}\n"
            "Backup folder:\n{backup_dir}"
        ),
        "admin.system.settings.dialog.title": "Settings",
        "admin.system.settings.msg.save_failed": "Save failed:\n{error}",
        "admin.system.settings.msg.saved": "Settings saved.",
        "admin.system.backup.dialog.title": "Backup",
        "admin.system.backup.msg.create_failed": "Backup failed:\n{error}",
        "admin.system.backup.msg.created": "Backup created ({created_at}).",
        "admin.system.restore.dialog.title": "Restore backup",
        "admin.system.restore.msg.select_first": (
            "Please select a backup from the list first."
        ),
        "admin.system.restore.msg.confirm_title": "Restore backup",
        "admin.system.restore.msg.confirm": (
            "Current state will be replaced by this backup "
            "({label}).\n\nContinue?"
        ),
        "admin.system.restore.msg.failed": "Restore failed:\n{error}",
        "admin.system.restore.msg.success": "State restored: {label}",
        "admin.system.backup_folder.dialog.title": "Backup folder",
        "admin.system.backup_folder.msg.unknown": "Backup folder is unknown.",
        "admin.system.backup_folder.msg.open_failed": (
            "Could not open folder:\n{folder}"
        ),
        "admin.system.backup_delete.dialog.title": "Delete backup",
        "admin.system.backup_delete.msg.select_first": (
            "Please select a backup from the list first."
        ),
        "admin.system.backup_delete.msg.confirm": (
            "Delete this backup permanently?\n\n{label}"
        ),
        "admin.system.backup_delete.msg.failed": "Delete failed:\n{error}",
        "admin.system.backup_delete.msg.success": "Backup deleted: {label}",
        "admin.system.verify.dialog.title": "Verify database",
        "admin.system.verify.msg.ok": "Database is in good shape.",
        "admin.system.verify.msg.needs_update": (
            "Database should be updated.\n\n{details}"
        ),
        "admin.system.migrate.dialog.title": "Update database",
        "admin.system.migrate.msg.confirm": (
            "Database will be updated to the current program version. "
            "A backup is created automatically.\n\nContinue?"
        ),
        "admin.system.migrate.msg.failed": "Update failed:\n{error}",
        "admin.system.migrate.msg.success": "Database was updated.",
        "admin.system.reinitialize.dialog.title": "Delete all tracker data",
        "admin.system.reinitialize.msg.confirm": (
            "Delete all sessions, jobs, sales and users "
            "(except default admin)?\n\n"
            "A backup is created automatically first."
        ),
        "admin.system.reinitialize.msg.failed": "Delete failed:\n{error}",
        "admin.system.reinitialize.msg.error": "Error:\n{error}",
        "admin.system.reinitialize.msg.success": "All tracker data was deleted.",
        "admin.roles.msg.admin_locked_short": (
            "The Administrator role is system-defined."
        ),
        "admin.network.msg.settings_saved": "Network settings saved.",
        "admin.network.msg.host_mode_active": (
            "Crew mode active.\nCode copied — share with your crew."
        ),
        "admin.network.msg.code_copied": "Code copied.",
        "admin.network.mode.standalone": "Standalone (local)",
        "admin.network.mode.host": "Host",
        "admin.network.mode.client": "Client",
        "admin.network.status.running": "Running · Code {code}{relay}",
        "admin.network.status.relay_active": " · Relay active",
        "admin.network.status.none": "None",
        "admin.network.status.inactive": "Inactive",
        "admin.network.relay.check_hint": (
            "Check relay address and whether the relay server is running."
        ),
        "admin.network.upnp.progress": "UPnP…",
        "admin.network.msg.client_connected": (
            "Connected to host. The session page was switched to client mode."
        ),
        "admin.network.msg.host_saved": (
            "Host mode saved. Start the server under Networking when the crew joins."
        ),
        "admin.system.backup.msg.removed_note": (
            "\n\n{count} older backups were removed (retention limit)."
        ),
        "admin.system.restore.msg.confirm_long": (
            "Current state will be replaced by this backup:\n\n{label}\n\n"
            "The current state will be backed up first.\n\n"
            "All unsaved changes will be lost.\n\nContinue?"
        ),
        "admin.system.restore.msg.safety_note": (
            "\n\nThe previous state was backed up first."
        ),
        "admin.system.restore.msg.relogin": (
            "Please sign out and sign in again."
        ),
        "admin.system.backup_delete.msg.select_first": (
            "Please select a backup from the list first."
        ),
        "admin.system.verify.msg.update_action": (
            "Please run \"Update database\"."
        ),
        "admin.system.migrate.msg.confirm_long": (
            "The database will be updated to the current program version. "
            "Your data will be preserved.\n\nContinue?"
        ),
        "admin.system.reinitialize.msg.confirm_long": (
            "All sessions, jobs, sales and users "
            "(except default admin) will be permanently deleted.\n\n"
            "A backup will be created automatically first.\n\nContinue?"
        ),
        "admin.system.reinitialize.msg.confirm_input": (
            "Enter RESET to confirm:"
        ),
        "admin.system.reinitialize.msg.backup_note": (
            "\n\nA backup was created first."
        ),
        "admin.system.reinitialize.msg.login_hint": (
            "The application will now restart. "
            "You can sign in again afterward."
        ),
        "status.ACTIVE": "ACTIVE",
        "permission.users.manage": "Manage users",
        "permission.roles.manage": "Manage roles",
        "permission.settings.manage": "Change system settings",
        "permission.database.reset": "Reset database",
        "permission.sessions.manage": "Manage all sessions",
        "permission.sessions.manage_own": "Manage own sessions",
        "permission.crew.manage": "Manage crew",
        "permission.refinery.manage": "Manage refinery",
        "permission.sales.manage": "Process sales",
        "permission.payouts.manage": "Create payouts",
        "permission.payouts.approve": "Approve payouts",
        "permission.payouts.view_own": "View own payouts",
        "permission.history.view": "View history",
        "permission.statistics.view": "View statistics / payout",
        "permission.dashboard.view": "Use dashboard",
        "permission.group.users_system": "Users & system",
        "permission.group.sessions_crew": "Sessions & crew",
        "permission.group.operations": "Operations",
        "permission.group.payouts": "Payout",
        "permission.group.views": "Views",
        "role.dialog.edit": "Edit role",
        "role.dialog.new": "New role",
        "role.dialog.view": "Role: {name}",
        "role.dialog.placeholder.name": "e.g. Officer",
        "role.dialog.placeholder.description": "Optional",
        "role.dialog.label.name": "Role name",
        "role.dialog.label.description": "Description",
        "role.dialog.section.permissions": "◆ PERMISSIONS",
        "role.dialog.select_all": "Select all",
        "role.dialog.select_none": "Select none",
        "role.dialog.select_except_db": "All except database",
        "role.dialog.scroll_hint": (
            "More permissions below — use scrollbar or mouse wheel over the list."
        ),
        "role.dialog.limit_hint": (
            "Grayed-out permissions you don't have — "
            "you cannot grant or remove them."
        ),
        "role.dialog.tooltip.assigned_locked": (
            "Assigned to role — you may not change this permission."
        ),
        "role.dialog.tooltip.not_grantable": (
            "You don't have this permission and cannot grant it."
        ),
        "role.dialog.msg.title": "Role",
        "role.dialog.msg.name_required": "Please enter a role name.",
        "role.dialog.msg.admin_reserved": (
            "The name \"Administrator\" is reserved by the system."
        ),
        "status.ACTIVE": "ACTIVE",
        "status.WAITING_FOR_REFINERY": "WAITING FOR REFINERY",
        "status.WAITING_FOR_SALE": "READY FOR SALE",
        "status.WAITING_FOR_PAYOUT": "PAYOUT",
        "status.REFINERY_COMPLETED": "READY FOR SALE",
        "status.SOLD": "SOLD",
        "status.IDLE": "IDLE",
        "dashboard.status.cycle_complete": "COMPLETE",
        "common.error": "Error",
        "common.hint": "Note",
        "common.not_possible": "Not possible",
        "common.success": "Success",
        "login.error.failed_title": "Sign-in failed",
        "login.error.invalid_credentials": "Invalid username or password.",
        "login.error.blocked_title": "Sign-in not allowed",
        "login.error.blocked_setup": (
            "During initial setup, only the super administrator can sign in."
        ),
        "main.login.blocked.title": "Sign-in not allowed",
        "main.login.blocked.message": "This user cannot sign in at the moment.",
        "main.superadmin.title": "Super Administrator",
        "main.superadmin.message": (
            "The super administrator is only for initial setup and emergencies.\n\n"
            "Please sign in with an organization user."
        ),
        "main.host.title": "Host Server",
        "main.host.start_failed": "The host server could not be started.",
        "main.start.error.title": "Startup Error",
        "main.start.error.message": (
            "The main window could not be loaded:\n\n{error}"
        ),
        "splash.initializing": "INITIALIZING SALVAGE TRACKER...",
        "splash.db_preparing": "PREPARING DATABASE...",
        "splash.db_step": "DATABASE: {name} ({current}/{total})",
        "splash.fonts_loading": "LOADING FONT PACKAGES...",
        "splash.ui_preparing": "PREPARING INTERFACE...",
        "splash.complete": "SYSTEM CHECK COMPLETE",
        "splash.created_by": "Created by {name} · {alias}",
        "nav.user": "◆  USER",
        "nav.badge.update": "◆ UPDATE · {version}",
        "nav.badge.update_available": "◆ UPDATE AVAILABLE",
        "nav.network.client": "◆ CLIENT · {host}:{port}",
        "nav.network.host": (
            "◆ HOST · {addresses}:{port}\n"
            "Code: {code} · {clients} client(s)"
        ),
        "nav.network.host_inactive": "◆ HOST · inactive",
        "nav.network.host_fallback": "Host",
        "dates.error.empty": "Please enter a date.",
        "dates.error.invalid_date": (
            "Invalid date. Please use DD.MM.YYYY."
        ),
        "dates.error.invalid_timestamp": "Invalid timestamp.",
        "dates.error.invalid_datetime": "Invalid date or time.",
        "dates.month_year": "{month} {year}",
        "dates.month.1": "January",
        "dates.month.2": "February",
        "dates.month.3": "March",
        "dates.month.4": "April",
        "dates.month.5": "May",
        "dates.month.6": "June",
        "dates.month.7": "July",
        "dates.month.8": "August",
        "dates.month.9": "September",
        "dates.month.10": "October",
        "dates.month.11": "November",
        "dates.month.12": "December",
        "error.session.not_found": "Session not found.",
        "error.session.ship_not_found": (
            "Could not resolve the session ship. "
            "Start the session with a known salvage ship."
        ),
        "error.session.has_refinery_jobs": (
            "Session has refinery jobs. "
            "Please cancel the jobs first."
        ),
        "error.session.has_sales": (
            "Session is linked to sales. "
            "Please void the sales first."
        ),
        "error.refinery.not_found": "Refinery job not found.",
        "error.refinery.cancel.only_active": (
            "Only running or ready-for-pickup jobs can be cancelled."
        ),
        "error.refinery.delete.only_completed": (
            "Only completed jobs can be deleted here. "
            "Please cancel running jobs instead."
        ),
        "error.refinery.delete.already_sold": (
            "The refined material has already been sold. "
            "Please void the sale first."
        ),
        "error.sale.has_payout_void": (
            "A payout already exists for this sale. "
            "Please void the payout first."
        ),
        "error.sale.not_found": "Sale not found.",
        "error.payout.not_found": "Payout not found.",
        "error.refinery.batch_required": (
            "At least one material batch is required."
        ),
        "error.refinery.input_must_be_positive": (
            "Input quantity must be greater than 0."
        ),
        "error.refinery.batch_not_raw": (
            "Batch #{batch_id} is not raw material for the refinery."
        ),
        "error.refinery.insufficient_batch": (
            "Not enough material in batch #{batch_id} ({label}). "
            "Available: {available} SCU, requested: {requested} SCU."
        ),
        "error.refinery.pool_not_raw": (
            "{material} is not raw material for the refinery."
        ),
        "error.refinery.insufficient_pool": (
            "Not enough {material} at this location. "
            "Available: {available} SCU, requested: {requested} SCU."
        ),
        "error.refinery.cost_payer_required": (
            "Please specify who paid the refinery costs."
        ),
        "error.refinery.output_must_be_positive": (
            "Output quantity must be greater than 0."
        ),
        "error.refinery.already_completed": "Job is already completed.",
        "error.refinery.no_items": "Job contains no line items.",
        "error.refinery.invalid_input_quantity": (
            "Invalid input quantity in job."
        ),
        "error.material.batch_not_found": "Material batch not found.",
        "error.material.capture_in_use": (
            "This capture can no longer be reversed "
            "(material already used in refinery or sale)."
        ),
        "error.material.capture_in_refinery": (
            "This capture is reserved for an active refinery job."
        ),
        "error.cost.not_found": "Cost entry not found.",
        "error.cost.not_mission": "Only mission costs can be removed here.",
        "error.cost.session_locked": (
            "Mission costs can only be removed while the session "
            "is active or waiting for refinery."
        ),
        "error.correction.capture_not_reversible": (
            "This capture entry cannot be reversed."
        ),
        "error.correction.already_reverted": (
            "This entry has already been reversed."
        ),
        "error.correction.event_not_reversible": (
            "This history entry cannot be reversed "
            "(older transfers may lack restore data)."
        ),
        "error.session.reopen.not_waiting": (
            "Only sessions waiting for refinery can be reopened."
        ),
        "error.session.reopen.active_exists": (
            "End or delete the current active session first."
        ),
        "error.material.insufficient_batch": (
            "Not enough material in batch ({available} SCU available)."
        ),
        "error.material.insufficient_batches": (
            "Not enough {material} in open batches. "
            "Available: {available} SCU, requested: {requested} SCU."
        ),
        "error.material.storage_changed": (
            "Stock level has changed. Please try again."
        ),
        "error.sale.line_required": (
            "At least one sale line item is required."
        ),
        "error.sale.quantity_must_be_positive": (
            "Sale quantity must be greater than 0."
        ),
        "error.sale.price_not_negative": (
            "Sale price must not be negative."
        ),
        "error.sale.material_not_sellable": (
            "{material_code} is not a sellable material. "
            "Raw material must be refined first."
        ),
        "error.sale.insufficient_stock": (
            "Not enough stock for {material_code}. "
            "Short by {remaining} SCU."
        ),
        "error.payout.already_exists": (
            "A payout already exists for this sale."
        ),
        "error.payout.items_required": (
            "At least one payout line item is required."
        ),
        "error.payout.member_empty": "Crew member must not be empty.",
        "error.payout.amount_not_negative": (
            "Payout amount must not be negative."
        ),
        "error.payout.no_sessions_trace": (
            "No sessions assignable via inventory trace."
        ),
        "error.payout.select_cost_payer": (
            "Cost refunds are assigned to {labels}. "
            "Please select the payer."
        ),
        "error.backup.invalid_file": "Invalid backup file.",
        "error.backup.not_found": "Backup not found.",
        "error.database.not_found": "Database file not found.",
        "error.cost.unknown_schema": "Unknown cost schema.",
        "error.cost.payers_required": (
            "Old and new payer must both be specified."
        ),
        "error.dashboard.max_presets": (
            "Maximum of {max} custom presets allowed."
        ),
        "error.role.name_required": "Role name is required.",
        "error.role.name_admin_reserved": (
            "The name \"Administrator\" is reserved by the system."
        ),
        "error.role.name_super_admin_reserved": (
            "The name \"Super Administrator\" is reserved by the system."
        ),
        "error.role.admin_cannot_rename": (
            "The Administrator role cannot be renamed."
        ),
        "error.role.super_admin_cannot_rename": (
            "The Super Administrator role cannot be renamed."
        ),
        "error.role.not_found": "Role not found.",
        "error.role.admin_perms_immutable": (
            "Administrator permissions cannot be changed."
        ),
        "error.role.super_admin_perms_immutable": (
            "Super Administrator permissions cannot be changed."
        ),
        "error.role.forbidden_permissions": (
            "You may not grant or revoke the following permissions:"
        ),
        "error.role.only_admin_can_assign_admin": (
            "Only an administrator may assign the Administrator role."
        ),
        "error.role.exceeds_actor_permissions": (
            "This role includes permissions you do not have. "
            "You may not assign it to anyone — including yourself."
        ),
        "error.role.admin_cannot_delete": (
            "The Administrator role cannot be deleted."
        ),
        "error.role.super_admin_cannot_delete": (
            "The Super Administrator role cannot be deleted."
        ),
        "error.role.still_assigned": (
            "Role is still assigned to users."
        ),
        "error.user.not_found": "User not found.",
        "error.user.system_immutable": (
            "System users cannot be changed."
        ),
        "error.user.system_cannot_manage": (
            "System users cannot be managed."
        ),
        "error.user.super_admin_cannot_manage": (
            "The Super Administrator cannot be managed."
        ),
        "error.user.admin_only_manages_admin": (
            "The Administrator account may only be managed "
            "by an administrator."
        ),
        "error.password.no_permission_other_user": (
            "No permission to change another user's password."
        ),
        "error.setup.superadmin_after_complete": (
            "The Super Administrator password cannot be set here "
            "after initial setup."
        ),
        "error.setup.superadmin_not_found": (
            "Super Administrator was not found."
        ),
        "error.setup.default_password_forbidden": (
            "Please choose a password other than the default."
        ),
        "session.title": "SESSION",
        "session.section.manage": "◆ SHIP, CREW & LOOT",
        "session.section.new": "◆ START SESSION",
        "session.section.network": "◆ NETWORK SESSION",
        "session.section.active": "◆ RUNNING SESSION",
        "session.section.missions": "◆ MISSION COSTS",
        "session.section.materials": "◆ RECORD LOOT",
        "session.label.ship": "Ship",
        "session.label.crew": "Players (one name per line)",
        "session.label.status": "Status",
        "session.label.not_started": "No session started yet",
        "session.label.active_session": "Active session",
        "session.label.mission_cost": "Mission cost (aUEC)",
        "session.label.paid_by": "Paid by",
        "session.label.deletable_session": "Incorrect session:",
        "session.hint.start": (
            "Record mission costs during the active session — one entry per accepted "
            "mission. Until the cargo hold is full, multiple missions and material "
            "runs can belong to the same session."
        ),
        "session.hint.archived": (
            "Completed sessions including mission costs are listed under History. "
            "Start your next session here."
        ),
        "session.hint.client": (
            "Select the host's running session. Material fields adjust automatically "
            "to that session's ship."
        ),
        "session.hint.mission": (
            "Record the cost for each accepted mission. "
            "All missions in a session are summed."
        ),
        "session.hint.material_default": (
            "Material fields follow the ship of the active session."
        ),
        "session.hint.material_ship": (
            "With {ship}: {materials}"
        ),
        "session.crew.placeholder": (
            "One name per line\n\n"
            "Example:\n"
            "Xangandu\n"
            "Pilot2\n"
            "Pilot3"
        ),
        "session.placeholder.mission_cost": "Cost of this mission in aUEC",
        "session.placeholder.quantity": "Amount in SCU",
        "session.button.start": "Start session",
        "session.button.save_run": "Save materials",
        "session.button.end": "Complete session",
        "session.button.delete": "Delete session",
        "session.button.reopen": "Reopen session",
        "session.button.undo_capture": "Undo",
        "session.button.delete_mission": "Remove",
        "session.button.add_mission": "Enter costs",
        "session.client.empty": (
            "No active session on the host.\n"
            "The host must start a session first."
        ),
        "session.mission.paid_by.placeholder": "— Please select —",
        "session.mission.costs_total": (
            "Mission costs: {mission_total} aUEC · "
            "Session total: {session_total} aUEC"
        ),
        "session.mission.line": "Mission {index}: {amount} aUEC ({paid_by})",
        "session.mission.none": "No missions recorded yet.",
        "session.section.captures": "◆ RECORDED LOOT (CORRECTIONS)",
        "session.hint.captures": (
            "Wrong amount or material? Undo individual entries here."
        ),
        "session.table.capture_material": "Material",
        "session.table.capture_quantity": "SCU",
        "session.table.capture_time": "Recorded",
        "session.table.capture_action": "Action",
        "session.table.mission_amount": "Amount (aUEC)",
        "session.table.mission_payer": "Paid by",
        "session.table.mission_action": "Action",
        "session.msg.capture_undo_confirm.title": "Undo capture",
        "session.msg.capture_undo_confirm.message": (
            "Remove {quantity} SCU {material} from this session?"
        ),
        "session.msg.capture_undone": "Capture reversed.",
        "session.msg.mission_delete_confirm.title": "Remove mission cost",
        "session.msg.mission_delete_confirm.message": (
            "Remove mission cost of {amount} aUEC ({paid_by})?"
        ),
        "session.msg.mission_deleted": "Mission cost removed.",
        "session.msg.reopen_confirm.title": "Reopen session",
        "session.msg.reopen_confirm.message": (
            "Reopen session #{session_id}? "
            "You can record more loot and mission costs."
        ),
        "session.msg.reopened.title": "Session reopened",
        "session.msg.reopened.message": (
            "Session #{session_id} is active again."
        ),
        "session.section.refinery_costs": "◆ REFINERY (COSTS)",
        "session.refinery.costs_total": (
            "Refinery costs: {refinery_total} aUEC · "
            "Session total: {session_total} aUEC"
        ),
        "session.refinery.line": (
            "Job #{job_id}: {amount} aUEC ({station} · {paid_by})"
        ),
        "session.refinery.none": "No refinery costs recorded yet.",
        "session.msg.no_session": (
            "No active session — please start a session first."
        ),
        "session.msg.paid_by_required": (
            "Please specify who paid the mission costs."
        ),
        "session.msg.invalid_mission_cost": "Please enter valid mission costs.",
        "session.msg.amount_positive": "Please enter an amount greater than 0.",
        "session.msg.mission_added.title": "Mission recorded",
        "session.msg.mission_added.message": (
            "Mission cost {amount} aUEC was added to the session."
        ),
        "session.msg.no_deletable": "No deletable session selected.",
        "session.msg.delete_confirm.title": "Delete session",
        "session.msg.delete_confirm.message": (
            "Really delete session #{session_id}?\n\n"
            "Material, costs, and crew entries for this session will be removed. "
            "Only possible without refinery and sales."
        ),
        "session.msg.delete_failed": "Delete failed:\n\n{error}",
        "session.msg.deleted.title": "Deleted",
        "session.msg.deleted.message": "Session #{session_id} was deleted.",
        "session.msg.no_crew": "Please enter at least one crew member.",
        "session.msg.started.title": "Session started",
        "session.msg.started.message": (
            "The salvage session was started.\n\n"
            "Record each accepted mission under “Mission Costs”."
        ),
        "session.msg.start_failed": (
            "Session could not be started:\n\n{error}"
        ),
        "session.msg.no_active_selected": "No active session selected.",
        "session.msg.invalid_numbers": "Please enter valid numbers.",
        "session.msg.material_required": (
            "Please enter at least one material with quantity > 0."
        ),
        "session.msg.material_not_allowed": (
            "{material} cannot be recorded with {ship}.\n\n"
            "Allowed: {allowed}"
        ),
        "session.msg.material_saved.title": "Success",
        "session.msg.material_saved.message": "Materials saved.",
        "session.msg.no_active_found": "No active session found.",
        "session.msg.ended.title": "Session ended",
        "session.msg.ended.message": (
            "The session is now waiting for the refinery."
        ),
        "session.ship.unnamed": "this ship",
        "refinery.title": "REFINERY",
        "refinery.section.batches": "◆ AVAILABLE MATERIAL",
        "refinery.section.create": "◆ CREATE REFINERY JOB",
        "refinery.section.active": "◆ ACTIVE JOBS",
        "refinery.section.history": "◆ REFINERY HISTORY",
        "refinery.table.batch": "Batch",
        "refinery.table.location": "Location",
        "refinery.table.material": "Material",
        "refinery.table.available_scu": "Available (SCU)",
        "refinery.table.original_scu": "Original (SCU)",
        "refinery.table.session": "Session",
        "refinery.history.no": "No.",
        "refinery.history.station": "Station",
        "refinery.history.method": "Method",
        "refinery.history.status": "Status",
        "refinery.history.input": "Input",
        "refinery.history.cm_output": "CM Raf Output",
        "refinery.history.yield": "Yield",
        "refinery.history.cost": "Cost",
        "refinery.history.created_by": "Created by",
        "refinery.label.station": "Refinery / Station",
        "refinery.label.method": "Refinery method",
        "refinery.label.cost": "Cost (aUEC)",
        "refinery.label.paid_by": "Paid by",
        "refinery.label.batch": "Material batch",
        "refinery.label.material_source": "Material source",
        "refinery.label.input_scu": "Input (SCU)",
        "refinery.label.input_cscu": "Input (cSCU) — terminal",
        "refinery.label.hours": "Hours",
        "refinery.label.minutes": "Minutes",
        "refinery.label.notes": "Note",
        "refinery.placeholder.station": "Select or type station",
        "refinery.placeholder.cost": "Cost in aUEC (when creating)",
        "refinery.placeholder.input_scu": "Input quantity in SCU",
        "refinery.placeholder.input_cscu": "Quantity at refinery terminal (cSCU)",
        "refinery.hint.cscu_formula": "1000 cSCU = 10 SCU · 100 cSCU = 1 SCU",
        "refinery.hint.scu_from_cscu": "→ {scu} SCU in tracker ({cscu} cSCU terminal)",
        "refinery.hint.cscu": "Terminal: {cscu} cSCU ({scu} SCU)",
        "location.placeholder.custom": "Select or type location",
        "location.placeholder.select": "— Select location —",
        "location.label.system": "System",
        "location.label.station": "Space station",
        "location.label.city": "City / landing zone",
        "location.label.place": "Location (station or city)",
        "location.placeholder.system": "— Select system —",
        "location.placeholder.station": "— Select station —",
        "location.placeholder.city": "— Select city —",
        "location.group.stations": "— Space stations —",
        "location.group.cities": "— Cities / landing zones —",
        "error.location.not_selected": "Please select a station or city from the list.",
        "refinery.placeholder.hours": "Hours",
        "refinery.placeholder.minutes": "Minutes",
        "refinery.placeholder.notes": "Note (optional)",
        "refinery.method.placeholder": "— Select method —",
        "refinery.button.create": "Create job",
        "refinery.button.delete": "Delete job",
        "refinery.button.cancel": "Cancel",
        "refinery.button.complete": "COMPLETE",
        "refinery.status.panel": (
            "● REFINERY STATUS\n\n"
            "Ready at:\n{ready_at}\n\n"
            "Remaining:\n{remaining}\n\n"
            "Status:\n{status}"
        ),
        "refinery.status.waiting_input": "WAITING FOR INPUT",
        "refinery.status.in_progress": "IN PROGRESS",
        "refinery.status.ready_for_pickup": "READY FOR PICKUP",
        "refinery.status.final_phase": "FINAL PHASE",
        "refinery.status.finished": "Done",
        "refinery.status.remaining_min": "{minutes} min",
        "refinery.status.remaining_hm": "{hours}h {minutes}m",
        "refinery.active.empty": "No active refinery jobs.",
        "refinery.job.detail": "Job #{job_id} | {name}",
        "refinery.job.method": "Method: {method}",
        "refinery.job.cost": "Cost: {cost} aUEC",
        "refinery.job.cost_paid": "Cost: {cost} aUEC · paid by {payer}",
        "refinery.job.created_by": "Created by: {name}",
        "refinery.job.batch_line": (
            "Batch #{batch_id} | {material} | "
            "Input: {quantity} SCU"
        ),
        "refinery.job.ready_at": "Ready: {time}",
        "refinery.job.remaining": "Remaining: {remaining}",
        "refinery.job.countdown": "Countdown: {countdown}",
        "refinery.job.progress": "Progress: {percent}%",
        "refinery.banner.ready_one": (
            "Job #{job_id} at {station} is ready for pickup!"
        ),
        "refinery.banner.ready_many": (
            "{count} refinery jobs are ready for pickup!"
        ),
        "refinery.batch.combo": "#{batch_id} | {material} | {remaining} SCU",
        "refinery.pool.combo": (
            "{location} · {material} · {quantity} SCU"
        ),
        "refinery.history.input_line": (
            "{quantity} SCU {material} (Batch #{batch_id})"
        ),
        "refinery.history.output_line": "{quantity} SCU {material}",
        "refinery.history.yield_pct": "{yield_pct} %",
        "refinery.complete.dialog.title": "Complete refinery job",
        "refinery.complete.dialog.field": "CM Raf Output (cSCU)",
        "refinery.complete.dialog.tooltip": (
            "Quantity shown at the refinery terminal in cSCU "
            "(1000 cSCU = 10 SCU in the tracker)."
        ),
        "refinery.complete.hint": (
            "Your average yield for {material}: {efficiency} % "
            "({job_count} jobs)"
        ),
        "refinery.msg.no_batch": "No material batch available.",
        "refinery.msg.no_pool": "No material available at ship or storage.",
        "refinery.msg.no_station": "Please enter a refinery/station.",
        "refinery.msg.invalid_values": "Please enter valid values.",
        "refinery.msg.negative_cost": "Cost cannot be negative.",
        "refinery.msg.paid_by_required": (
            "Please specify who paid the refinery costs."
        ),
        "refinery.msg.create_failed": (
            "Job could not be created:\n\n{error}"
        ),
        "refinery.msg.complete_failed": (
            "Completion failed:\n\n{error}"
        ),
        "refinery.msg.completed.title": "Completed",
        "refinery.msg.completed.message": (
            "{quantity} SCU {material} added to inventory "
            "(yield: {yield_pct} %)."
        ),
        "refinery.msg.cancel_confirm.title": "Cancel job",
        "refinery.msg.cancel_confirm.message": (
            "Cancel refinery job #{job_id}?\n\n"
            "Reserved material will be returned to the batch."
        ),
        "refinery.msg.cancel_failed": (
            "Cancellation failed:\n\n{error}"
        ),
        "refinery.msg.cancelled.title": "Cancelled",
        "refinery.msg.cancelled.message": "Job #{job_id} was cancelled.",
        "refinery.msg.no_selection": (
            "Please select a job in the history first."
        ),
        "refinery.msg.delete_confirm.title": "Delete job",
        "refinery.msg.delete_confirm.message": (
            "Delete completed job #{job_id}?\n\n"
            "CM will be removed from inventory and raw material "
            "returned to batches. Only possible if the CM was not sold."
        ),
        "refinery.msg.delete_failed": "Delete failed:\n\n{error}",
        "refinery.msg.deleted.title": "Deleted",
        "refinery.msg.deleted.message": "Job #{job_id} was deleted.",
        "refinery.job_status.RUNNING": "RUNNING",
        "refinery.job_status.READY": "READY",
        "refinery.job_status.COMPLETED": "COMPLETED",
        "refinery.job_status.CANCELLED": "CANCELLED",
        "storage.title": "STORAGE / LOCATIONS",
        "storage.section.list": "◆ MATERIAL BY LOCATION",
        "storage.section.add": "◆ STORE MATERIAL",
        "storage.section.history": "◆ LOG",
        "storage.section.totals": "◆ TOTAL STOCK BY MATERIAL",
        "storage.table.location": "Location",
        "storage.table.material": "Material",
        "storage.table.quantity": "Quantity (SCU)",
        "storage.table.status": "Status",
        "storage.table.ship": "Ship",
        "storage.table.activity": "Last activity",
        "storage.table.reserve": "Reserve",
        "storage.table.notes": "Note",
        "storage.label.location_type": "Where is it?",
        "storage.label.location": "Location",
        "storage.label.ship": "Ship",
        "storage.label.material": "Material",
        "storage.label.quantity": "Quantity (SCU)",
        "storage.label.reserve": "Reserve tag",
        "storage.label.notes": "Note",
        "storage.label.sort": "Sort list by",
        "storage.location_type.station": "Station / city",
        "storage.location_type.ship": "In ship",
        "storage.location.ship": "Ship · {ship}",
        "storage.event.session_salvage": "Salvage run",
        "storage.event.from_ship": "From ship",
        "storage.event.to_refinery": "To refinery · {station}",
        "storage.event.refinery_cancelled": "Refinery cancelled",
        "storage.status.IN_SHIP": "In ship",
        "storage.status.STORED": "Stored",
        "storage.status.IN_REFINERY": "In refinery",
        "storage.status.READY_PICKUP": "Ready for pickup",
        "storage.status.RESERVED": "Reserve",
        "storage.sort.location": "Location (A–Z)",
        "storage.sort.material": "Material type",
        "storage.sort.age": "Last activity (oldest first)",
        "storage.placeholder.reserve": "e.g. Reserve — no warning",
        "storage.placeholder.notes": "Note (optional)",
        "storage.empty": "No stored material recorded yet.",
        "storage.totals.line": "{material}: {quantity} SCU",
        "storage.totals.none": "No stock totals.",
        "storage.button.save": "Store",
        "storage.button.delete": "Delete entry",
        "storage.button.delete_event": "Delete history entry",
        "storage.button.revert_event": "Undo movement",
        "storage.event.reverted_note": "Reversed",
        "storage.msg.revert_event_confirm.title": "Undo movement",
        "storage.msg.revert_event_confirm.message": (
            "Reverse this stock movement? "
            "Quantities will be restored accordingly."
        ),
        "storage.msg.reverted": "Movement reversed.",
        "storage.button.reminded": "Warning read",
        "storage.button.set_reserve": "Set reserve tag",
        "storage.button.clear_reserve": "Remove reserve tag",
        "storage.button.moved": "Mark as moved",
        "storage.button.transfer": "Move material",
        "storage.transfer.title": "Move material",
        "storage.transfer.hint": "Select source, quantity, and destination. Material is deducted from the source row and credited at the target location.",
        "storage.transfer.pool_hint": (
            "Sources are grouped by location and material type. "
            "The quantity is taken from the total (FIFO across underlying rows)."
        ),
        "storage.transfer.pool_option": (
            "{location} · {material} · {quantity} SCU"
        ),
        "storage.transfer.label.source": "Source",
        "storage.transfer.label.destination_type": "Destination type",
        "storage.transfer.confirm": "Move",
        "storage.transfer.source_option": "{location} · {material} · {quantity} SCU",
        "storage.transfer.msg.no_source": "Please select a source stock entry.",
        "storage.msg.transferred": "Material moved successfully.",
        "storage.event.from_location": "From location stock",
        "storage.event.inbound_transfer": "Inbound transfer",
        "storage.event.withdrawn": "Withdrawn from stock",
        "storage.history.type.TRANSFER": "Transfer",
        "storage.history.type.WITHDRAW": "Withdrawal",
        "error.storage.insufficient_at_location": "Not enough material at locations ({available} SCU {material} available).",
        "error.storage.insufficient_at_source": "Not enough material at source ({available} SCU {material} available).",
        "error.storage.transfer_same_location": "Source and destination are the same.",
        "error.storage.transfer_invalid_source": "This stock entry cannot be used as a transfer source.",
        "error.storage.transfer_material_mismatch": "Material does not match the selected source.",
        "error.storage.transfer_failed": "Transfer failed — no suitable source found.",
        "error.storage.insufficient_pool": (
            "Not enough {material} at this location. "
            "Available: {available} SCU, requested: {requested} SCU."
        ),
        "error.storage.insufficient_ship_pool": (
            "Not enough {material} on ship. "
            "Available: {available} SCU, requested: {requested} SCU."
        ),
        "error.storage.insufficient_stored_pool": (
            "Not enough {material} in storage. "
            "Available: {available} SCU, requested: {requested} SCU."
        ),
        "storage.filter.warnings_only": "Warnings only",
        "storage.idle.banner.title": (
            "{count} stockpile(s) idle for more than {days} days"
        ),
        "storage.idle.banner.hint": (
            "Select an entry below and acknowledge the warning, "
            "mark it as reserve, or mark it as moved."
        ),
        "storage.idle.banner.collapse": "Hide",
        "storage.idle.banner.expand": "Show",
        "storage.activity.today": "Today",
        "storage.activity.yesterday": "Yesterday",
        "storage.activity.days_ago": "{days} days ago",
        "storage.activity.warning_prefix": "⚠ ",
        "storage.msg.reminded": "Warning acknowledged.",
        "storage.msg.reserve_set": "Reserve tag saved.",
        "storage.msg.reserve_cleared": "Reserve tag removed.",
        "storage.msg.reserve_clear_confirm.title": "Remove reserve tag",
        "storage.msg.reserve_clear_confirm.message": "Remove the reserve tag from this stockpile? Idle warnings may apply again.",
        "error.storage.reserve_not_set": "This stockpile has no reserve tag.",
        "storage.msg.moved": "Material withdrawn from stock.",
        "storage.msg.reserve_prompt.title": "Reserve tag",
        "storage.msg.reserve_prompt.label": "Tag for this stockpile",
        "nav.badge.storage_idle": "◆ {count} IDLE",
        "error.storage.reserve_required": "Please enter a reserve tag.",
        "storage.history.type.DEPOSIT": "Deposit",
        "storage.history.type.UPDATE": "Update",
        "storage.history.type.DELETE": "Delete",
        "storage.history.type.IDLE_REMINDED": "Idle reminder",
        "storage.history.type.TAG_SET": "Reserve tag",
        "storage.history.type.TAG_CLEAR": "Reserve removed",
        "storage.history.type.ACTIVITY": "Activity",
        "storage.history.type": "Type",
        "storage.history.delta": "Change",
        "storage.history.when": "When",
        "storage.msg.saved": "Material stored.",
        "storage.msg.deleted": "Storage entry deleted.",
        "storage.msg.no_selection": "Please select an entry.",
        "storage.msg.delete_confirm.title": "Delete entry",
        "storage.msg.delete_confirm.message": (
            "Delete this storage entry?\n\n{location} · {material} · {quantity} SCU"
        ),
        "storage.msg.delete_event_confirm.title": "Delete history entry",
        "storage.msg.delete_event_confirm.message": (
            "Remove this history entry permanently?"
        ),
        "error.storage.not_available": "Storage module is not available.",
        "error.storage.not_found": "Storage entry not found.",
        "error.storage.event_not_found": "History entry not found.",
        "error.storage.quantity_positive": "Quantity must be greater than zero.",
        "error.storage.location_required": "Please enter a location.",
        "error.storage.ship_required": "Please select a ship.",
        "error.storage.insufficient_global": (
            "Not enough unassigned material available "
            "({available} SCU {material}). "
            "Record salvage in the session first, or reduce the quantity."
        ),
        "error.storage.insufficient_on_ship": (
            "Not enough material on ships "
            "({available} SCU {material}). "
            "Record salvage in the session first, or reduce the quantity."
        ),
        "sales.title": "SALES",
        "sales.section.inventory": "◆ AVAILABLE INVENTORY",
        "sales.section.new": "◆ NEW SALE",
        "sales.section.finance": "◆ FINANCIAL OVERVIEW",
        "sales.section.history": "◆ SALES HISTORY",
        "sales.table.material": "Material",
        "sales.table.available_scu": "Available (SCU)",
        "sales.inventory.empty": "No sellable material in inventory.",
        "sales.label.location": "Sale location",
        "sales.label.date": "Date",
        "sales.label.material": "Material",
        "sales.label.quantity": "Quantity (SCU)",
        "sales.label.unit_price": "Unit price (aUEC)",
        "sales.label.notes": "Note",
        "sales.placeholder.location": "Select or type location",
        "sales.placeholder.date": "DD.MM.YYYY",
        "sales.placeholder.quantity": "Quantity in SCU",
        "sales.placeholder.unit_price": "Price per SCU (aUEC)",
        "sales.placeholder.notes": "Note (optional)",
        "sales.button.save": "Save sale",
        "sales.button.void": "Void sale",
        "sales.line_total": "Total: {total} aUEC",
        "sales.line_total.invalid": "Total: — aUEC",
        "sales.summary.revenue": "Total revenue (all sales): {amount} aUEC",
        "sales.summary.costs": "Total costs: {amount} aUEC",
        "sales.summary.profit": "Profit: {amount} aUEC",
        "sales.history.no": "No.",
        "sales.history.date": "Date",
        "sales.history.location": "Location",
        "sales.history.materials": "Materials",
        "sales.history.revenue": "Revenue",
        "sales.history.seller": "Seller",
        "sales.material.combo": "{material} — {quantity} SCU",
        "sales.history.item_line": "{quantity} SCU {material}",
        "sales.msg.no_location": "Please enter a sale location.",
        "sales.msg.no_material": "No material available in inventory.",
        "sales.msg.invalid_quantity_price": (
            "Please enter valid quantity and price."
        ),
        "sales.msg.quantity_positive": (
            "Sale quantity must be greater than 0."
        ),
        "sales.msg.not_possible.title": "Sale not possible",
        "sales.msg.save_failed": (
            "Sale could not be saved:\n\n{error}"
        ),
        "sales.msg.saved.title": "Sale saved",
        "sales.msg.saved.message": "The sale was recorded in inventory.",
        "sales.msg.no_selection": (
            "Please select a sale in the history first."
        ),
        "sales.msg.void_confirm.title": "Void sale",
        "sales.msg.void_confirm.message": (
            "Really void sale #{sale_id}?\n\n"
            "The sold quantity will be returned to inventory. "
            "Not possible if already paid out."
        ),
        "sales.msg.void_failed": "Void failed:\n\n{error}",
        "sales.msg.voided.title": "Voided",
        "sales.msg.voided.message": "Sale #{sale_id} was voided.",
        "payout.title": "PROFIT DISTRIBUTION",
        "payout.section.main": "◆ CREW PAYOUT & STATISTICS",
        "payout.section.summary": "◆ OVERVIEW",
        "payout.section.unpaid": "◆ OPEN SALES (NOT YET PAID OUT)",
        "payout.section.calculate": "◆ CALCULATE PAYOUT",
        "payout.section.crew_totals": "◆ CREW TOTAL PAYOUTS",
        "payout.section.history": "◆ PAYOUT HISTORY",
        "payout.summary": (
            "Pending sales: {count} | Total paid out: {total} aUEC"
        ),
        "payout.table.no": "No.",
        "payout.table.date": "Date",
        "payout.table.location": "Location",
        "payout.table.revenue": "Revenue",
        "payout.table.seller": "Seller",
        "payout.table.sale": "Sale",
        "payout.table.paid_out": "Paid out",
        "payout.table.created_by": "Created by",
        "payout.table.crew_member": "Crew member",
        "payout.table.amount": "Amount (aUEC)",
        "payout.table.total_received": "Total received (aUEC)",
        "payout.table.date_or_crew": "Date / Crew member",
        "payout.unpaid.empty": (
            "No open sales — all sales have been paid out."
        ),
        "payout.calc.placeholder": (
            "Select a sale to load the proposal."
        ),
        "payout.label.sale": "Sale",
        "payout.label.notes": "Note",
        "payout.label.cost_payer": "Cost reimbursement to crew member:",
        "payout.placeholder.notes": "Note (optional)",
        "payout.sale.placeholder": "— Select sale —",
        "payout.button.save": "Save payout",
        "payout.button.void": "Void payout",
        "payout.crew.empty": "No crew payouts recorded yet.",
        "payout.history.empty": "No payouts saved yet.",
        "payout.sale.combo": (
            "#{sale_id} | {location} | {amount} aUEC"
        ),
        "payout.proposal.detail": (
            "Sale #{sale_id} | Revenue: {revenue} aUEC\n"
            "Sessions: {sessions}\n"
            "Session costs: {session_costs} aUEC\n"
            "Refinery costs: {refinery_costs} aUEC\n"
            "Total costs: {total_costs} aUEC\n"
            "Cost reimbursements: {refunds}\n"
            "Profit share per crew: {equal_share} aUEC\n"
            "Total distributed: {distributed_total} aUEC"
        ),
        "payout.proposal.cost_settled": (
            "\nSession costs already settled (sessions {sessions})"
        ),
        "payout.proposal.refinery_settled": (
            "\nRefinery costs already settled (jobs {jobs})"
        ),
        "payout.proposal.refund_line": "{name}: {amount} aUEC",
        "payout.proposal.refunds_none": "none",
        "payout.msg.select_sale": "Please select a sale first.",
        "payout.msg.calc_failed": "Calculation failed:\n\n{error}",
        "payout.msg.cost_payer.title": "Cost reimbursement",
        "payout.msg.cost_payer_required": (
            "Please select which crew member paid the mission costs."
        ),
        "payout.msg.invalid_amount": "Invalid amount for {member}.",
        "payout.msg.system_costs": (
            "SYSTEM costs must be assigned to a crew member."
        ),
        "payout.msg.no_items": "No payout line items present.",
        "payout.msg.save_failed": "Payout failed:\n\n{error}",
        "payout.msg.saved.title": "Saved",
        "payout.msg.saved.message": "Payout #{payout_id} was saved.",
        "payout.msg.no_selection": (
            "Please select a payout in the history first."
        ),
        "payout.msg.void_confirm.title": "Void payout",
        "payout.msg.void_confirm.message": (
            "Really void payout #{payout_id}?\n\n"
            "The sale will appear as open again and can be recalculated."
        ),
        "payout.msg.void_failed": "Void failed:\n\n{error}",
        "payout.msg.voided.title": "Voided",
        "payout.msg.voided.message": "Payout #{payout_id} was voided.",
        "dashboard.title": "SALVAGE OVERVIEW",
        "dashboard.subtitle": "◆ OPERATIONS OVERVIEW",
        "dashboard.window.title": "MobiGlas Salvage Overview",
        "dashboard.button.presets": "Presets",
        "dashboard.button.customize": "Customize dashboard",
        "dashboard.button.customize_dirty": "Customize dashboard ●",
        "dashboard.button.save": "Save",
        "dashboard.button.cancel": "Cancel",
        "dashboard.nav.detached": "Overview ●",
        "dashboard.nav.embedded": "Overview ⧉",
        "dashboard.widget.status": "STATUS",
        "dashboard.widget.crew": "CREW",
        "dashboard.widget.session_crew": "CREW (session)",
        "dashboard.widget.refinery_jobs": "REFINERY",
        "dashboard.widget.active_sessions": "ACTIVE",
        "dashboard.widget.total_sessions": "SESSIONS",
        "dashboard.widget.sold_sessions": "SALES",
        "dashboard.widget.ready_sessions": "STORAGE (SCU)",
        "dashboard.widget.total_sales": "REVENUE",
        "dashboard.widget.total_profit": "PROFIT",
        "dashboard.widget.session": "◆ ACTIVE SESSION",
        "dashboard.widget.refinery_stats": "◆ REFINERY STATISTICS",
        "dashboard.operations.title": "OPEN ACTIONS",
        "dashboard.alert.show": "Show",
        "dashboard.context.pin": "Pin",
        "dashboard.context.unpin": "Unpin",
        "dashboard.context.mode_follow": "Mode: Follow navigation",
        "dashboard.context.mode_pinned": "Mode: Pinned",
        "dashboard.context.nav_pinned": "Nav: {nav} (pinned)",
        "dashboard.context.overview.title": "◆ OVERVIEW",
        "dashboard.context.overview.subtitle": "All areas · Next actions",
        "dashboard.context.session.title": "◆ SESSION",
        "dashboard.context.session.subtitle": "Active session · Materials & flow",
        "dashboard.context.refinery.title": "◆ REFINERY",
        "dashboard.context.refinery.subtitle": "Open jobs · Pickup & efficiency",
        "dashboard.context.storage.title": "◆ STORAGE",
        "dashboard.context.storage.subtitle": "Stock · Locations · Idle warnings",
        "dashboard.context.sales.title": "◆ SALES",
        "dashboard.context.sales.subtitle": "Ready to sell · Open sales",
        "dashboard.context.payout.title": "◆ PAYOUT",
        "dashboard.context.payout.subtitle": "Open payouts · Session mapping",
        "dashboard.context.history.title": "◆ HISTORY",
        "dashboard.context.history.subtitle": "Timeline · Statistics · Trends",
        "dashboard.context.session_scu": "SESSION SCU",
        "dashboard.context.mission_costs_subtotal": (
            "Mission costs: {mission_total} aUEC"
        ),
        "dashboard.context.refinery_costs_subtotal": (
            "Refinery costs: {refinery_total} aUEC"
        ),
        "dashboard.context.session_costs_total": (
            "Session total costs: {session_total} aUEC"
        ),
        "dashboard.context.locations": "LOCATIONS",
        "dashboard.context.processes": "CURRENT PROCESSES",
        "dashboard.context.no_locations": "No material locations recorded.",
        "dashboard.context.no_processes": "No active processes.",
        "dashboard.context.open": "OPEN",
        "dashboard.context.avg_efficiency": "AVG EFFICIENCY",
        "dashboard.context.active_jobs": "ACTIVE JOBS",
        "dashboard.context.total": "TOTAL",
        "dashboard.context.by_location": "BY LOCATION",
        "dashboard.context.inventory": "STOCK",
        "dashboard.context.storage_inventory_detail": (
            "{material} · {quantity} · from {source} · {location} · "
            "stored {stored_since}"
        ),
        "dashboard.context.no_inventory": "No stored material recorded.",
        "dashboard.context.recent_moves": "RECENT MOVEMENTS",
        "dashboard.context.pending": "OPEN SALES",
        "dashboard.context.pending_amount": "OPEN (aUEC)",
        "dashboard.context.sale_items": "READY TO SELL",
        "dashboard.context.open_payouts": "OPEN PAYOUTS",
        "dashboard.context.open_total": "TOTAL OPEN",
        "dashboard.context.revenue_trend": "MONTHLY REVENUE",
        "dashboard.context.revenue_trend_hint": (
            "Sales revenue per month (last 6 months). "
            "With multiple months, bar length compares to the best month."
        ),
        "dashboard.context.revenue_peak_month": "Best month",
        "dashboard.context.revenue_vs_peak": "{pct} % of best month",
        "dashboard.context.revenue_trend_empty": "No sales recorded yet.",
        "dashboard.context.recent_events": "RECENT EVENTS",
        "dashboard.context.refinery_station": "Refinery · {station}",
        "dashboard.context.refinery_job_detail": "Job #{job_id} · {status} · {scu} SCU",
        "dashboard.context.session_batches": "Session batches",
        "dashboard.context.session_materials": "Unassigned material",
        "dashboard.context.process_pickup": "Pickup at {station} · Job #{job_id}",
        "dashboard.context.process_running": "Running at {station} · Job #{job_id}",
        "dashboard.context.process_status": "Session workflow status",
        "dashboard.context.storage_event": "Stock event",
        "dashboard.context.storage_event_detail": "{material} {delta} SCU · {location}",
        "dashboard.context.storage_deposit_event_detail": (
            "{material} {delta} SCU · from {source} · {location}"
        ),
        "dashboard.context.history_sale": "Sale completed",
        "dashboard.context.history_sale_detail": "{location} · {amount} aUEC · {materials}",
        "dashboard.context.materials_sellable": "SELLABLE MATERIALS",
        "dashboard.context.materials_raw": "RAW MATERIALS",
        "dashboard.context.overview.help": (
            "Cross-domain summary: urgent actions sorted by priority, "
            "plus revenue, profit, open refinery jobs and sellable storage."
        ),
        "dashboard.context.session.help": (
            "Your current or latest session at a glance: workflow status, "
            "crew, mission and refinery costs, collected materials "
            "(sellable vs. raw), where stock is located, and what happens next."
        ),
        "dashboard.context.refinery.help": (
            "Active refinery jobs (running or ready for pickup), total "
            "input/output SCU, and average efficiency by material from "
            "completed jobs."
        ),
        "dashboard.context.storage.help": (
            "All stored materials with deposit time, pickup source, "
            "current location and storage age, plus recent moves."
        ),
        "dashboard.context.sales.help": (
            "Materials ready to sell by location, open sales awaiting payout, "
            "and total sellable SCU in storage and stockpiles."
        ),
        "dashboard.context.payout.help": (
            "Sales completed but not yet paid out — grouped by session with "
            "material, quantity, amount and location."
        ),
        "dashboard.context.history.help": (
            "Completed sales over time, session counts, total revenue, "
            "monthly trend and the latest sale events."
        ),
        "dashboard.operations.hint": (
            "Sorted by urgency — payout first, then pickup and sales."
        ),
        "dashboard.operations.empty": (
            "No open actions. Start a session or add stock in Storage."
        ),
        "dashboard.operations.col.status": "Status",
        "dashboard.operations.col.material": "Material",
        "dashboard.operations.col.quantity": "Quantity",
        "dashboard.operations.col.context": "Location / session",
        "dashboard.operations.col.detail": "Details",
        "dashboard.operations.summary.idle": "Idle warnings",
        "dashboard.next_action.all_clear": (
            "No urgent actions — you're up to date."
        ),
        "dashboard.next_action.payout": (
            "Payout pending — {material} ({session})"
        ),
        "dashboard.next_action.refinery_ready": (
            "Refinery ready for pickup — {station}"
        ),
        "dashboard.next_action.sale": (
            "Ready to sell — {material} · {location} · {when}"
        ),
        "dashboard.next_action.refinery_input": (
            "Ready for refinery — {material} · {location}"
        ),
        "dashboard.next_action.storage_idle": (
            "Stock idle for more than {days} days"
        ),
        "dashboard.action.payout_pending": "Payout pending",
        "dashboard.action.refinery_ready": "Ready for pickup",
        "dashboard.action.refinery_running": "Refinery running",
        "dashboard.action.refinery_material": "Refinery input",
        "dashboard.action.sale_ready": "Ready to sell",
        "dashboard.action.refinery_input_ready": "Ready for refinery",
        "dashboard.readiness.line": "{material} · {status}",
        "dashboard.readiness.none": "No material ready for sale or refinery.",
        "dashboard.readiness.separator": "  |  ",
        "dashboard.action.storage_idle": "Idle stock",
        "dashboard.action.session": "Active session",
        "dashboard.action.legacy_storage": "Global storage",
        "dashboard.action.detail.session": "Session · {session}",
        "dashboard.action.detail.job": "Job #{job_id}",
        "dashboard.action.detail.legacy": "Legacy inventory",
        "dashboard.action.detail.idle": "Check Storage page",
        "dashboard.session.none": "NO SESSION",
        "dashboard.session.active": "ACTIVE SESSION",
        "dashboard.session.materials": "MATERIALS",
        "dashboard.label.ship": "Ship",
        "dashboard.label.crew": "Crew",
        "dashboard.label.status": "Status",
        "dashboard.label.refinery": "Refinery",
        "dashboard.refinery_stats.title": "REFINERY STATISTICS",
        "dashboard.refinery_stats.empty": (
            "No completed refinery jobs yet."
        ),
        "dashboard.refinery_stats.empty_short": (
            "No completed jobs yet."
        ),
        "dashboard.refinery_stats.jobs": "Jobs: {count}",
        "dashboard.refinery_stats.io": (
            "Input: {input_scu} SCU · Output: {output_scu} SCU"
        ),
        "dashboard.refinery_stats.efficiency": "Avg efficiency: {value}",
        "dashboard.refinery_stats.by_material": "By material:",
        "dashboard.refinery_stats.by_method": "By method:",
        "dashboard.refinery_stats.detail_line": (
            "  {label}: {efficiency} ({count}×)"
        ),
        "dashboard.refinery.open_suffix": " open",
        "dashboard.catalog.title": "◆ WIDGET CATALOG",
        "dashboard.catalog.hint": (
            "Drag widgets onto the dashboard.\n"
            "Remove: × or drag back here."
        ),
        "dashboard.catalog.drop": "Drop zone — release widget to remove",
        "dashboard.msg.no_user": "No user signed in.",
        "dashboard.msg.layout_saved": "Dashboard layout was saved.",
        "dashboard.font_preview.section": "◆ PREVIEW",
        "dashboard.font_preview.demo_title": "STATUS",
        "dashboard.font_preview.demo_value": "128 SCU",
        "dashboard.font_preview.hint": (
            "100 % = default size. All dashboard text scales uniformly."
        ),
        "dashboard.preset.title": "DASHBOARD PRESETS",
        "dashboard.preset.window_title": "Dashboard Presets",
        "dashboard.preset.section.system": "◆ SYSTEM TEMPLATE",
        "dashboard.preset.section.custom": "◆ CUSTOM PRESETS",
        "dashboard.preset.label.template": "Template",
        "dashboard.preset.button.load_template": "Load template",
        "dashboard.preset.hint.max": (
            "Maximum {max} custom presets per user."
        ),
        "dashboard.preset.label.name": "Preset name",
        "dashboard.preset.placeholder.name": "Name for new preset",
        "dashboard.preset.button.save_current": "Save current",
        "dashboard.preset.button.load_selected": "Load selected",
        "dashboard.preset.button.delete": "Delete",
        "dashboard.preset.button.close": "Close",
        "dashboard.preset.blank.label": "Blank",
        "dashboard.preset.blank.description": "No widgets — empty dashboard",
        "dashboard.preset.classic.label": "Classic",
        "dashboard.preset.classic.description": "All areas equally weighted",
        "dashboard.preset.operations.label": "Operations",
        "dashboard.preset.operations.description": (
            "Focus: active session, crew, materials"
        ),
        "dashboard.preset.refinery.label": "Refinery",
        "dashboard.preset.refinery.description": (
            "Focus: refinery jobs and raw materials"
        ),
        "dashboard.preset.storage.label": "Storage",
        "dashboard.preset.storage.description": (
            "Focus: inventory, sales, profit"
        ),
        "dashboard.preset.msg.title": "Preset",
        "dashboard.preset.msg.name_required": "Please enter a preset name.",
        "dashboard.preset.msg.no_layout": "No layout available to save.",
        "dashboard.preset.msg.saved": "Preset \"{name}\" was saved.",
        "dashboard.preset.msg.select": "Please select a preset.",
        "dashboard.preset.msg.load_failed": "Preset could not be loaded.",
        "dashboard.preset.msg.delete_confirm.title": "Delete preset",
        "dashboard.preset.msg.delete_confirm": (
            "Really delete preset \"{name}\"?"
        ),
        "history.title": "HISTORY",
        "history.section.sessions": "◆ COMPLETED SESSIONS",
        "history.section.sales": "◆ ALL SALES",
        "history.section.all_payouts": "◆ ALL PAYOUTS",
        "history.empty": "No sales recorded yet.",
        "history.sessions.empty": (
            "No completed sessions yet. "
            "Mission costs appear here after refinery/sale workflow."
        ),
        "history.session.no": "No.",
        "history.session.ship": "Ship",
        "history.session.status": "Status",
        "history.session.ended": "Ended",
        "history.session.mission_costs": "Mission costs",
        "history.session.total_costs": "Total costs",
        "history.session.mission_line": (
            "{amount} aUEC ({paid_by})"
        ),
        "history.session.no_missions": "No mission costs",
        "history.session.costs_total": (
            "Mission: {mission_total} aUEC · Total: {session_total} aUEC"
        ),
        "common.ok": "OK",
        "common.cancel": "Cancel",
        "common.back": "Back",
        "common.continue": "Continue",
        "common.logout": "Sign out",
        "common.connecting": "Connecting…",
        "common.save": "Save",
        "password.change.title": "Change password",
        "password.required.window_title": (
            "First sign-in — new password required"
        ),
        "password.required.frame_title": "First sign-in — new password",
        "password.required.banner_title": "FIRST SIGN-IN",
        "password.required.banner": (
            "You signed in with the default password.\n\n"
            "Before you can use the app, you must set your own password now.\n\n"
            "Signed in as: {username}"
        ),
        "password.required.step": (
            "Step 1 of 1 — choose a new password (at least 6 characters)"
        ),
        "password.label.new": "New password",
        "password.placeholder.new": "Enter new password",
        "password.label.confirm": "Confirm password",
        "password.placeholder.confirm": "Repeat password",
        "password.button.set_and_continue": (
            "Set new password and continue"
        ),
        "password.msg.blocked.title": "First sign-in",
        "password.msg.blocked": (
            "The app cannot start without a new password.\n\n"
            "Please set a password."
        ),
        "password.msg.title": "Password",
        "password.msg.length": (
            "The password must be at least 6 characters long."
        ),
        "password.msg.mismatch": "The passwords do not match.",
        "password.msg.required_success.title": "First sign-in complete",
        "password.msg.required_success": (
            "Your password was saved.\n\nThe app will start now."
        ),
        "password.msg.changed": "The password was changed.",
        "input.msg.title": "Input",
        "input.msg.quantity_required": "Please enter a valid quantity.",
        "input.msg.number_required": "Please enter a valid number.",
        "input.msg.range": (
            "Quantity must be between {minimum} and {maximum} SCU."
        ),
        "network.assistant.title": "NETWORKING",
        "network.assistant.window_title": "Networking",
        "network.assistant.subtitle": (
            "Play solo, host a crew, or join with a code."
        ),
        "network.assistant.mode.standalone": "Play solo",
        "network.assistant.mode.host": "Host crew",
        "network.assistant.mode.client": "Join crew",
        "network.assistant.section.local": "◆ LOCAL",
        "network.assistant.local.info": (
            "All data stays on this computer. No crew connection needed."
        ),
        "network.assistant.section.host": "◆ INVITE CREW",
        "network.assistant.host.info": (
            "Share this code with your crew. They only need the "
            "Salvage Tracker and the code — no IP, router, or extra software."
        ),
        "network.assistant.button.copy_code": "Copy code",
        "network.assistant.copy.message": (
            "Code copied — e.g. paste in Discord."
        ),
        "network.assistant.section.client": "◆ JOIN CREW",
        "network.assistant.client.info": (
            "Enter the host's code — or paste the invitation."
        ),
        "network.assistant.placeholder.code": "6-digit code",
        "network.assistant.placeholder.name": "Your name (optional)",
        "network.assistant.label.code": "Join code",
        "network.assistant.label.display_name": "Display name",
        "network.assistant.button.join": "Join",
        "network.assistant.msg.join_title": "Join",
        "network.assistant.msg.code_required": (
            "Please enter a join code."
        ),
        "network.quick_join.title": "JOIN CREW",
        "network.quick_join.window_title": "Join crew",
        "network.quick_join.hint": (
            "Enter the host's 6-digit code — or paste the invitation."
        ),
        "network.quick_join.placeholder.code": "e.g. K7M2XP",
        "network.quick_join.placeholder.name": (
            "Your name in the crew (optional)"
        ),
        "network.quick_join.label.code": "Join code",
        "network.quick_join.label.display_name": "Display name",
        "network.quick_join.button.join": "Join",
        "network.scenario.title.client": "◆ WHERE ARE YOU PLAYING?",
        "network.scenario.title.host": "◆ HOW DO CLIENTS CONNECT?",
        "network.scenario.label.type": "Connection type",
        "network.scenario.label.invite_address": "Address for invitation",
        "network.scenario.label.relay_address": "Relay address",
        "network.scenario.label.relay_port": "Relay port",
        "network.scenario.lan.label": "Same Wi‑Fi / LAN",
        "network.scenario.relay.label": "Internet — Salvage Relay (code only)",
        "network.scenario.internet.label": "Internet — crew invite (address + code)",
        "network.scenario.router.label": "Internet — manual router (fallback)",
        "network.scenario.client_hint.lan": (
            "You are on the same network. Enter the host PC's LAN IP "
            "(e.g. 192.168.x.x — shown on the host under Settings → Networking)."
        ),
        "network.scenario.client_hint.relay": (
            "Only Salvage Tracker required — no extra software, no IP from the host. "
            "Enter the relay address (shared by the host) and the join code. "
            "The host must be registered at the relay (Settings → Networking)."
        ),
        "network.scenario.client_hint.internet": (
            "The host sends you an invitation (address + join code). "
            "Enter both — no extra software required."
        ),
        "network.scenario.client_hint.router": (
            "Fallback: the host forwarded port 47890 on the router. "
            "Enter the external internet address (not 192.168.x.x)."
        ),
        "network.scenario.host_hint.lan": (
            "Clients on the same Wi‑Fi connect using a LAN address of this PC "
            "and the join code. Test on the same PC: 127.0.0.1."
        ),
        "network.scenario.host_hint.relay": (
            "Start the host server and enable \"Register at Salvage Relay\". "
            "Share only relay address and join code with the crew — no IP needed. "
            "For tests: start relay locally (scripts/start_relay_server.py)."
        ),
        "network.scenario.host_hint.internet": (
            "Copy the invitation for your crew. Optional: \"Open internet (UPnP)\" "
            "for automatic port forwarding on the router."
        ),
        "network.scenario.host_hint.router": (
            "Forward TCP port 47890 on the router to this PC. "
            "Fetch external IP and share it with the code."
        ),
        "network.scenario.placeholder.lan": "Host LAN IP, e.g. 192.168.1.10",
        "network.scenario.placeholder.relay": "Relay address, e.g. relay.example.com",
        "network.scenario.placeholder.internet": "Address from the host invitation",
        "network.scenario.placeholder.router": "Host external IP, e.g. 85.123.45.67",
        "network.scenario.host_placeholder.lan": "LAN IP for the crew",
        "network.scenario.host_placeholder.relay": (
            "Salvage relay, e.g. relay.example.com"
        ),
        "network.scenario.host_placeholder.internet": (
            "Reachable address for the invitation "
            "(external IP or LAN IP)"
        ),
        "network.scenario.host_placeholder.router": (
            "External IP — use \"Fetch external IP\" or from your provider"
        ),
        "network.scenario.button.fetch_ip": "Fetch external IP",
        "network.scenario.button.fetch_ip_progress": "Fetching…",
        "network.scenario.button.copy_invite": "Copy invitation",
        "network.scenario.msg.fetch_ip_title": "External IP",
        "network.scenario.msg.fetch_ip_failed": (
            "Could not fetch the external IP.\n"
            "Check your internet connection or enter the IP manually "
            "(router status page or provider)."
        ),
        "network.scenario.msg.invite_title": "Invitation",
        "network.scenario.msg.relay_address_required": (
            "Please enter the relay address first."
        ),
        "network.scenario.msg.address_required": (
            "Please enter or fetch an address first."
        ),
        "network.scenario.msg.join_code_missing": (
            "Join code missing — start the host or generate a code."
        ),
        "network.scenario.msg.invite_copied": (
            "Invitation text copied.\n"
            "Send it to your crew (chat, Discord, …)."
        ),
        "network.error.connect_title": "Connection",
        "network.error.relay_address_required": "Please enter a relay address.",
        "network.error.host_address_required": "Please enter a host address.",
        "network.error.guest_code_required": (
            "A join code is required for guest access."
        ),
        "network.error.credentials_required": (
            "Username and password are required."
        ),
        "network.error.connection_failed": "Connection failed",
        "network.error.connect_error": "Connection error",
        "network.error.host_refused_hint": (
            "The host server is not running or not listening on this port. "
            "Start the host and sign in until ◆ HOST appears in the bar."
        ),
        "network.error.relay_failed": "Relay connection failed",
        "network.error.relay_invalid_response": "Invalid relay response",
        "network.error.protocol_incompatible": "Incompatible protocol version",
        "network.error.auth_failed": "Authentication failed",
        "network.error.invalid_join_code": "Invalid join code",
        "network.error.login_failed": "Sign-in failed",
        "network.error.not_authenticated": "Not authenticated",
        "network.error.rpc_failed": "RPC failed",
        "network.error.rpc_path_denied": "RPC path not allowed: {path}",
        "network.error.guest_no_permission": (
            "Guest accounts do not have permission for this action."
        ),
        "network.error.no_permission": "No permission.",
        "network.error.write_not_allowed": "Write access not permitted.",
        "network.guest.username": "Guest",
        "network.guest.role_name": "Guest (network)",
        "admin.network.upnp.msg.lib_missing": (
            "UPnP library not installed.\n\n"
            "Current Python version: {version}\n"
        ),
        "admin.network.upnp.msg.lib_missing_py314": (
            "There is no ready-made miniupnpc wheel for Python 3.14 yet.\n"
            "Optional: install Python 3.12/3.13 and run "
            "'pip install miniupnpc' there,\n"
            "or configure port forwarding on your router manually."
        ),
        "admin.network.upnp.msg.install_pip": "Install with: pip install miniupnpc",
        "admin.network.upnp.msg.no_router": (
            "No UPnP router found on the network."
        ),
        "admin.network.upnp.msg.success": (
            "Port {port} was forwarded via UPnP to {host}."
        ),
        "admin.network.upnp.msg.failed": "UPnP failed: {error}",
        "recovery.title": "EMERGENCY MAINTENANCE",
        "recovery.window_title": "Emergency maintenance",
        "recovery.subtitle": (
            "The super administrator has no access to normal tracker "
            "operation. Here you can repair users and administrators."
        ),
        "recovery.section.options": "Options",
        "recovery.status.admins": (
            "Active organization administrators: {count}\n\n"
            "Choose a maintenance action:"
        ),
        "recovery.button.create_admin": "Create organization administrator",
        "recovery.button.reset_password": "Reset user password",
        "recovery.section.create_admin": "Create administrator",
        "recovery.section.reset_password": "Reset password",
        "recovery.create.hint": (
            "Role: {role} (fixed)\n"
            "The user must set their own password on first sign-in."
        ),
        "recovery.reset.hint": (
            "Resets an organization user's password. "
            "A new password must be chosen on next sign-in."
        ),
        "recovery.button.create": "Create administrator",
        "recovery.button.reset": "Reset password",
        "recovery.msg.title": "Emergency maintenance",
        "recovery.msg.admin_created": (
            "Administrator \"{username}\" was created."
        ),
        "recovery.msg.password_reset": (
            "Password for \"{username}\" was reset."
        ),
        "recovery.msg.create_failed": (
            "The administrator could not be created."
        ),
        "recovery.msg.admin_created_detail": (
            "Administrator \"{username}\" was created.\n\n"
            "Sign in with this user afterward."
        ),
        "recovery.msg.password_reset_detail": (
            "Password for \"{username}\" was reset.\n\n"
            "A new password must be set on next sign-in."
        ),
        "recovery.msg.superadmin_password_locked": (
            "You can only change the super administrator password "
            "via \"Change password\" after sign-in — not here."
        ),
        "recovery.msg.user_not_found": "User \"{username}\" not found.",
        "recovery.msg.user_create_failed": (
            "The user could not be created. "
            "The name may already exist."
        ),
        "update.available.title": "Update available",
        "update.available.page_title": "UPDATE AVAILABLE",
        "update.available.installed": "Currently installed: {version}",
        "update.available.download": (
            "Download: {filename} ({size})"
        ),
        "update.available.version_line": (
            "{version} · Build {build} · {codename}"
        ),
        "update.available.notes_empty": "No release notes available.",
        "update.tab.de": "German",
        "update.tab.en": "English",
        "update.button.install": "Install now",
        "update.button.later": "Later",
        "update.button.skip": "Skip this version",
        "update.download.title": "Downloading update",
        "update.download.page_title": "DOWNLOAD",
        "update.download.status": "{filename} is downloading …",
        "update.download.indeterminate": "{mb} MB downloaded …",
        "update.download.progress": "{received} / {total} ({percent} %)",
        "update.manager.dialog.title": "Updates",
        "update.manager.check_running": "An update check is already running.",
        "update.manager.check_failed": "Update check failed:\n\n{error}",
        "update.manager.manifest_failed": "Could not read update manifest.",
        "update.manager.up_to_date": (
            "You are already using the latest version.\n\n{version}"
        ),
        "update.manager.notify.title": "New update available",
        "update.manager.notify.message": (
            "Version {version} (Build {build}) is available on GitHub.\n\n"
            "Show update details?"
        ),
        "update.manager.installer_unavailable": (
            "Automatic installation is only available in the "
            "installed Windows version.\n\n"
            "Download the update manually:\n{url}"
        ),
        "update.manager.network_active.title": "Network active",
        "update.manager.network_active.continue": (
            "{warning}\n\nContinue anyway?"
        ),
        "update.manager.install_confirm.title": "Install update",
        "update.manager.install_confirm.message": (
            "The update will be downloaded first.\n\n"
            "Install location:\n{install_dir}\n\n"
            "Detected via: {source_label}\n\n"
            "Continue?"
        ),
        "update.manager.install_ready.title": "Ready to install",
        "update.manager.install_ready.message": (
            "The update has been downloaded successfully.\n\n"
            "Version: {version} (Build {build})\n"
            "Install location:\n{install_dir}\n\n"
            "Detected via: {source_label}\n\n"
            "The app will close and the setup wizard will install "
            "the update visibly. The updated app will start "
            "automatically when installation finishes."
        ),
        "update.manager.install_path.unknown": (
            "No existing installation was found. The default path "
            "will be used:\n{install_dir}"
        ),
        "update.install_path.source.explicit": "Manual selection",
        "update.install_path.source.registry": "Windows registry",
        "update.install_path.source.manifest": "Installation manifest",
        "update.install_path.source.running_exe": "Running application",
        "update.install_path.source.default": "Default path",
        "update.download.install_path": (
            "Install location: {install_dir} ({source_label})"
        ),
        "update.manager.download.title": "Download",
        "update.manager.download.failed": (
            "The update could not be downloaded:\n\n{error}"
        ),
        "update.manager.install.title": "Installation",
        "update.warning.host_active": (
            "Host mode is active. Clients should disconnect "
            "before installing an update."
        ),
        "update.warning.client_connected": (
            "You are connected to a host as a client. "
            "Disconnect before installing the update."
        ),
        "update.error.download_failed": "Download failed: {error}",
        "update.error.checksum_failed": (
            "The downloaded file is corrupted "
            "(SHA256 checksum mismatch)."
        ),
        "update.error.installer_frozen_only": (
            "Updates can only be installed automatically in the "
            "installed Windows app."
        ),
        "changelog.title": "Changelog",
        "changelog.page_title": "{app_name} – PATCHNOTES & ROADMAP",
        "changelog.tab.patchnotes": "Patch notes",
        "changelog.tab.roadmap": "Roadmap",
        "edition.locked.title": "{edition} required",
        "edition.teaser.badge": "◆ SC SALVAGE TRACKER - {edition}",
        "edition.button.learn_more": "More about {edition}",
        "edition.info.footer": (
            "The SOLO edition remains free for solo players. "
            "CREW and ORGA expand the app with multiplayer "
            "and organization features — without removing solo features.\n\n"
            "You can redeem supporter keys under Settings → Support."
        ),
        "edition.feature.network.host": "Host crew session",
        "edition.feature.network.client": "Join crew session",
        "edition.feature.network.crew_edition": "Networking (CREW Edition)",
        "edition.feature.org.module": "Organization management",
        "edition.teaser.crew": (
            "Track salvage with friends: one host starts the session, "
            "the crew joins via code — everyone shares one database. "
            "Available in SC Salvage Tracker - CREW Edition."
        ),
        "edition.teaser.orga": (
            "Organizations, multiple teams and advanced administration — "
            "planned for SC Salvage Tracker - ORGA Edition."
        ),
        "edition.teaser.fallback": (
            "Available in SC Salvage Tracker - {edition}."
        ),
        "edition.key.invalid": "The supporter key is invalid.",
        "edition.key.unlocked": (
            "Unlocked: {edition}. Networking is now available."
        ),
        "edition.key.stored_ceiling": (
            "Key stored ({edition}), this installation remains at {ceiling}."
        ),
        "common.discard": "Discard",
        "common.apply": "Apply",
        "common.retry": "Retry",
        "common.ignore": "Ignore",
        "common.abort": "Abort",
    },
    "de": {
        "language.dialog.title": "Sprache wählen",
        "language.dialog.subtitle": "Wähle deine Oberflächensprache",
        "language.dialog.hint": (
            "Du kannst das später unter Einstellungen → Sprache ändern."
        ),
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
            "Lege Benutzername und Passwort für die tägliche Anmeldung fest."
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
        "setup.welcome.info.solo": (
            "Richte den Salvage Tracker für dich ein.\n\n"
            "Zuerst sicherst du den Notfall-Zugang, "
            "danach legst du dein Benutzerkonto für die tägliche Anmeldung an.\n\n"
            "Für den normalen Betrieb meldest du dich mit deinem "
            "Benutzerkonto an — nicht mit dem Notfall-Zugang."
        ),
        "setup.step.admin.solo": "DEIN KONTO",
        "setup.emergency.info.solo": (
            "Dieses Konto existiert bereits und ist nur für Notfälle "
            "gedacht (Passwort vergessen, Wiederherstellung bei Problemen).\n\n"
            "Wähle ein sicheres Passwort und schreib dir die Zugangsdaten auf. "
            "Du brauchst sie nur, wenn später etwas schiefgeht."
        ),
        "setup.emergency.note_checkbox.solo": (
            "Ich habe die Zugangsdaten für den Notfall-Zugang notiert"
        ),
        "setup.admin.title.solo": "Dein Benutzerkonto",
        "setup.admin.hint.solo": (
            "Lege Benutzername und Passwort für die tägliche Anmeldung fest."
        ),
        "setup.admin.button.solo": "KONTO ANLEGEN",
        "setup.finish.message.solo": (
            "Dein Benutzerkonto „{username}“ wurde angelegt.\n\n"
            "Klicke auf „Fertig“ und melde dich danach mit dem neuen Konto an."
        ),
        "setup.complete.message.solo": (
            "Die Erstinstallation ist abgeschlossen.\n\n"
            "Melde dich jetzt als „{username}“ an."
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
            "Die Anwendung startet jetzt neu, um die Datenbank erneut zu laden."
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
        "nav.storage": "Lager",
        "nav.sales": "Verkäufe",
        "nav.payout": "Auszahlung",
        "nav.history": "Historie",
        "nav.settings": "Einstellungen",
        "nav.version_info": "Version Info",
        "nav.logout": "Abmelden",
        "nav.language.title": "Sprache",
        "admin.language": "Sprache",
        "admin.language.restart_now": (
            "Sprache gespeichert. Das Programm startet jetzt neu und "
            "meldet dich automatisch wieder an."
        ),
        "common.yes": "Ja",
        "common.no": "Nein",
        "common.preview": "Vorschau",
        "common.edit": "Bearbeiten",
        "common.choose": "Wählen",
        "common.reset": "Zurücksetzen",
        "common.close": "Schließen",
        "common.minimize": "Minimieren",
        "common.maximize": "Maximieren",
        "common.restore": "Wiederherstellen",
        "admin.title": "EINSTELLUNGEN",
        "admin.subtitle": "◆ SYSTEM & ORGA-VERWALTUNG",
        "admin.tab.users": "Benutzer",
        "admin.tab.roles": "Rollen",
        "admin.tab.design": "Design",
        "admin.tab.network": "Vernetzung",
        "admin.tab.support": "Unterstützen",
        "admin.tab.system": "System",
        "admin.tab.language": "Sprache",
        "admin.language.section": "◆ OBERFLÄCHENSSPRACHE",
        "admin.language.tab_hint": (
            "Wähle die Sprache der Oberfläche und klicke auf Speichern. "
            "Danach startet die Anwendung automatisch neu und meldet "
            "dich wieder an."
        ),
        "admin.users.section": "◆ BENUTZERÜBERSICHT",
        "admin.users.col.username": "Benutzername",
        "admin.users.col.display_name": "Anzeigename",
        "admin.users.col.role": "Rolle",
        "admin.users.col.active": "Aktiv",
        "admin.users.col.created": "Erstellt am",
        "admin.users.empty": "Keine Benutzer vorhanden.",
        "admin.users.edit_display_name": "Anzeigename ändern",
        "admin.users.reset_password": "Passwort zurücksetzen",
        "admin.users.assign_role": "Rolle zuweisen",
        "admin.users.toggle_active": "Aktiv / Inaktiv",
        "admin.users.delete": "Benutzer löschen",
        "admin.users.create.section": "◆ NEUEN BENUTZER ANLEGEN",
        "admin.users.placeholder.username": "Benutzername",
        "admin.users.placeholder.display_name": "Anzeigename (optional)",
        "admin.users.placeholder.password": "Passwort",
        "admin.users.label.username": "Benutzername",
        "admin.users.label.display_name": "Anzeigename",
        "admin.users.label.password": "Passwort",
        "admin.users.label.role": "Rolle",
        "admin.users.create.button": "Benutzer anlegen",
        "admin.users.dialog.title": "Benutzer",
        "admin.users.msg.username_required": "Bitte Benutzername eingeben.",
        "admin.users.msg.password_required": "Bitte Passwort eingeben.",
        "admin.users.msg.role_required": (
            "Bitte zuerst eine Rolle anlegen und zuweisen."
        ),
        "admin.users.msg.create_failed": (
            "Benutzer konnte nicht angelegt werden. "
            "Der Name existiert möglicherweise bereits."
        ),
        "admin.users.msg.created": "Benutzer wurde angelegt.",
        "admin.users.msg.select_user": "Bitte einen Benutzer auswählen.",
        "admin.users.msg.display_name_title": "Anzeigename",
        "admin.users.msg.display_name_prompt": "Neuer Anzeigename:",
        "admin.users.msg.reset_password_title": "Passwort zurücksetzen",
        "admin.users.msg.reset_password_prompt": "Neues Passwort:",
        "admin.users.msg.password_reset": "Passwort wurde zurückgesetzt.",
        "admin.users.msg.no_assignable_roles": (
            "Keine zuweisbaren Rollen vorhanden."
        ),
        "admin.users.msg.assign_role_title": "Rolle zuweisen",
        "admin.users.msg.assign_role_prompt": "Rolle:",
        "admin.users.msg.role_updated": (
            "Deine Rolle wurde aktualisiert. "
            "Navigation und Rechte sind angepasst."
        ),
        "admin.users.msg.delete_title": "Benutzer löschen",
        "admin.users.msg.delete_confirm": "Benutzer wirklich löschen?",
        "admin.roles.hint": (
            "Nur die Rolle „Administrator“ ist vordefiniert. "
            "Lege weitere Rollen an und weise Rechte zu — "
            "z. B. Officer, Member oder Guest für deine ORGA."
        ),
        "admin.roles.section": "◆ ROLLENÜBERSICHT",
        "admin.roles.col.name": "Rollenname",
        "admin.roles.col.description": "Beschreibung",
        "admin.roles.col.permissions": "Rechte",
        "admin.roles.col.users": "Benutzer",
        "admin.roles.empty": (
            "Noch keine Rollen angelegt. "
            "Klicke auf „Neue Rolle“, um die erste Rolle "
            "für deine ORGA zu erstellen."
        ),
        "admin.roles.new": "Neue Rolle",
        "admin.roles.edit": "Bearbeiten",
        "admin.roles.assign_permissions": "Rechte zuweisen",
        "admin.roles.view_permissions": "Rechte anzeigen",
        "admin.roles.delete": "Rolle löschen",
        "admin.roles.dialog.title": "Rolle",
        "admin.roles.msg.create_failed": (
            "Rolle konnte nicht angelegt werden:\n{error}"
        ),
        "admin.roles.msg.created": "Rolle „{name}“ wurde angelegt.",
        "admin.roles.msg.select_role": "Bitte eine Rolle auswählen.",
        "admin.roles.msg.admin_locked": (
            "Die Administrator-Rolle ist "
            "systemseitig vordefiniert und kann nicht bearbeitet werden."
        ),
        "admin.roles.msg.save_failed": (
            "Rolle konnte nicht gespeichert werden:\n{error}"
        ),
        "admin.roles.msg.permissions_reloaded": (
            "Deine Rechte wurden aus der Datenbank "
            "neu geladen."
        ),
        "admin.roles.msg.delete_title": "Rolle löschen",
        "admin.roles.msg.delete_confirm": (
            "Rolle „{name}“ wirklich löschen?"
        ),
        "admin.design.tab.appearance": "Erscheinungsbild",
        "admin.design.tab.density": "Dichte",
        "admin.design.tab.colors": "Farben",
        "admin.design.tab.typography": "Schriften",
        "admin.design.tab.dashboard": "Dashboard",
        "admin.design.tab.organization": "Organisation",
        "admin.design.section.appearance": "◆ ERSCHEINUNGSBILD",
        "admin.design.section.density": "◆ DICHTE & TRANSPARENZ",
        "admin.design.section.colors": "◆ FARBPALETTE",
        "admin.design.section.dashboard": "◆ DASHBOARD",
        "admin.design.section.organization": "◆ APP-STANDARD (ORGANISATION)",
        "admin.design.section.typography": "◆ SCHRIFTEN",
        "admin.design.hint.typography": (
            "Pro Kategorie ein Stil für alle passenden Texte. Das aktive Theme "
            "ist der Standard, bis du speicherst — dann überschreiben deine "
            "Werte das Theme. Speichern legt dein Schrift-Theme als neuen "
            "Zurücksetzen-Standard fest."
        ),
        "typography.group.hierarchy": "Seiten & Bereiche",
        "typography.group.forms": "Formulare & Eingaben",
        "typography.group.data": "Zahlen & Werte",
        "typography.group.hints": "Hinweise & Meldungen",
        "typography.group.tables": "Tabellen",
        "typography.group.navigation": "Linke Leiste",
        "typography.group.dashboard": "Dashboard",
        "typography.group.dialogs": "Fenster & Dialoge",
        "typography.field.family": "Schriftart",
        "typography.field.size": "Größe (Pixel)",
        "typography.field.weight": "Schriftstärke",
        "typography.field.letter_spacing": "Abstand zwischen Buchstaben",
        "typography.field.color": "Farbe",
        "typography.family.inherit": "Wie unter „Erscheinungsbild“",
        "typography.weight.normal": "Normal",
        "typography.weight.semibold": "Halbfett",
        "typography.weight.bold": "Fett",
        "typography.italic": "Kursiv",
        "typography.preview_label": "So sieht es aus",
        "typography.reset_role": "Diese Schrift zurücksetzen",
        "typography.reset_all": "Alle Schriften zurücksetzen",
        "typography.color_dialog_title": "Textfarbe wählen",
        "typography.category.page_heading": "Seitenüberschriften",
        "typography.category.page_heading.desc": (
            "Seitennamen (Raffinerie, Lager, …) und große Dashboard-Titel "
            "(◆ SESSION, ◆ RAFFINERIE, …)."
        ),
        "typography.category.section_heading": "Abschnittsüberschriften",
        "typography.category.section_heading.desc": (
            "Orange ◆-Zeilen, kleinere Überschriften, Navigations-Bereiche "
            "(USER, SPRACHE, …)."
        ),
        "typography.category.body": "Standardtexte & Labels",
        "typography.category.body.desc": (
            "Beschriftungen, Hinweise, Anzeigewerte, Karten-Untertitel, "
            "Zeitstempel und Fensterleiste."
        ),
        "typography.category.data": "Zahlen & Hervorhebungen",
        "typography.category.data.desc": (
            "KPI-Werte, Statistiken und große Dashboard-Zahlen."
        ),
        "typography.category.profit": "Gewinn & Erlöse",
        "typography.category.profit.desc": (
            "Gewinn-Zeilen (z. B. „Gewinn: … aUEC“) und hervorgehobene "
            "Erlöse in Verkauf und Finanzübersicht."
        ),
        "typography.category.button": "Buttons",
        "typography.category.button.desc": (
            "Haupt- und Nebenaktionen, Navigations-Buttons und "
            "Dashboard-Steuerung."
        ),
        "typography.category.table_header": "Tabellen-Spaltenüberschriften",
        "typography.category.table_header.desc": (
            "Spaltennamen in allen Datentabellen (Standort, Material, Status, …)."
        ),
        "typography.category.table_cell": "Tabellen-Zelltext",
        "typography.category.table_cell.desc": (
            "Text in den Tabellenzeilen — Werte und Einträge in allen "
            "Datentabellen."
        ),
        "typography.category.input": "Eingabefelder",
        "typography.category.input.desc": (
            "Textfelder, Dropdowns, Zahlenfelder und mehrzeilige Eingaben."
        ),
        "typography.category.status": "Statusmeldungen",
        "typography.category.status.desc": (
            "Leere Zustände, Dialog-Texte und Warn-Banner."
        ),
        "typography.category.tooltip": "Tooltips",
        "typography.category.tooltip.desc": (
            "Kurze Hilfe beim Überfahren von Elementen mit der Maus."
        ),
        "typography.preview.page_heading": "RAFFINERIE",
        "typography.preview.section_heading": "◆ VERFÜGBARES MATERIAL",
        "typography.preview.body": "Raffinerie-Methode",
        "typography.preview.data": "12,4 SCU",
        "typography.preview.profit": "Gewinn: 18.200 aUEC",
        "typography.preview.button": "SPEICHERN",
        "typography.preview.table_header": "Standort",
        "typography.preview.table_cell": "Terra Gateway",
        "typography.preview.input": "Standort suchen…",
        "typography.preview.status": "Noch keine Raffinerieaufträge.",
        "typography.preview.tooltip": "Sortiert nach Standort.",
        "typography.role.page_title": "Seitenname (z. B. RAFFINERIE)",
        "typography.role.section_accent": "Orange Zeile mit ◆",
        "typography.role.subsection_title": "Kleinere Überschrift im Bereich",
        "typography.role.form_label": "Text über Eingabefeldern",
        "typography.role.display_value": "Angezeigter Wert (nur lesen)",
        "typography.role.card_title": "Kleine Überschrift in Karten",
        "typography.role.card_value": "Große Zahl in Karten",
        "typography.role.stat_label": "Text neben Statistik-Zahlen",
        "typography.role.stat_value": "Statistik-Zahlen",
        "typography.role.profit_label": "Gewinn (hervorgehoben)",
        "typography.role.muted_label": "Grauer Hinweistext",
        "typography.role.hint_label": "Kleiner Zusatz-Hinweis",
        "typography.role.empty_info": "Text wenn nichts eingetragen ist",
        "typography.role.table_header": "Spaltenname in Tabellen (z. B. Standort)",
        "typography.role.table_cell": "Text in Tabellenzellen",
        "typography.role.nav_title_primary": "App-Name links (SALVAGE)",
        "typography.role.nav_user_name": "Dein Name in der Leiste",
        "typography.role.nav_section_heading": "Kleine Überschrift (z. B. USER)",
        "typography.role.dashboard_context_title": "Großer Titel im Dashboard",
        "typography.role.dashboard_timeline_when": "Uhrzeit in „Letzte Bewegungen“",
        "typography.role.window_title": "Text oben in der Fensterleiste",
        "typography.role.dialog_info_value": "Text in Hinweis-Fenstern",
        "typography.preview.page_title": "RAFFINERIE",
        "typography.preview.section_accent": "◆ VERFÜGBARES MATERIAL",
        "typography.preview.subsection_title": "◆ RAFFINERIE-AUFTRAG ANLEGEN",
        "typography.preview.form_label": "Raffinerie-Methode",
        "typography.preview.display_value": "Aegis Reclaimer",
        "typography.preview.card_title": "STATUS",
        "typography.preview.card_value": "12,4 SCU",
        "typography.preview.stat_label": "Missionskosten",
        "typography.preview.stat_value": "24.500 aUEC",
        "typography.preview.profit_label": "+18.200 aUEC",
        "typography.preview.muted_label": "Keine aktive Sitzung.",
        "typography.preview.hint_label": "Sortiert nach Standort.",
        "typography.preview.empty_info": "Noch keine Raffinerieaufträge.",
        "typography.preview.table_header": "Standort",
        "typography.preview.table_cell": "Terra Gateway",
        "typography.preview.nav_title_primary": "SALVAGE",
        "typography.preview.nav_user_name": "Xangandu",
        "typography.preview.nav_section_heading": "USER",
        "typography.preview.dashboard_context_title": "SITZUNG",
        "typography.preview.dashboard_timeline_when": "Heute 14:32",
        "typography.preview.window_title": "SC SALVAGE TRACKER",
        "typography.preview.dialog_info_value": "Einstellungen gespeichert.",
        "admin.design.label.theme": "Theme",
        "admin.design.label.font_size": "Schriftgröße",
        "admin.design.label.font_family": "Schriftart",
        "admin.design.label.animations": "Animationen",
        "admin.design.label.nav_width": "Navigationsbreite",
        "admin.design.label.table_density": "Tabellen-Dichte",
        "admin.design.label.window_transparency": "Fenster-Transparenz",
        "admin.design.label.panel_transparency": "Panel-Transparenz",
        "admin.design.label.dashboard_layout": "Dashboard-Layout",
        "admin.design.label.dashboard_widgets": "Widgets (KPI & Panels)",
        "admin.design.label.dashboard_title": "Überschrift (SALVAGE-ÜBERSICHT)",
        "admin.design.label.dashboard_buttons": "Header-Buttons",
        "admin.design.label.default_theme": "Standard-Theme",
        "admin.design.hint.appearance": (
            "Grundlegende Darstellung der App. Farben werden "
            "im Tab „Farben“ eingestellt. Position und Größe "
            "des Fensters werden beim Beenden automatisch "
            "gespeichert (auch Monitor 2)."
        ),
        "admin.design.hint.density": (
            "Tabellen-Dichte steuert Zeilenhöhe und Innenabstände. "
            "Fenster-Transparenz betrifft Hintergrund und Navigation. "
            "Panel-Transparenz wirkt feiner (5-%-Schritte) auf "
            "Inhalts- und Info-Panels."
        ),
        "admin.design.hint.colors": (
            "Leere Felder übernehmen Theme-Standardwerte. "
            "Die Akzentfarbe ersetzt Highlight-Farben "
            "in der Oberfläche. "
            "Klick auf die Farbfläche öffnet den Farbwähler."
        ),
        "admin.design.hint.dashboard": (
            "Layout und Schriftgrößen lassen sich unabhängig "
            "voneinander skalieren."
        ),
        "admin.design.hint.organization": (
            "Gilt für alle Benutzer ohne eigene Design-Einstellungen. "
            "Nur für Administratoren."
        ),
        "admin.design.color.accent": "Akzentfarbe",
        "admin.design.color.label": "Label-Farbe",
        "admin.design.color.primary": "Primär-Button",
        "admin.design.color.secondary": "Sekundär-Button",
        "admin.design.color.default_accent": "Standard (Theme-Akzent)",
        "admin.design.color.default_label": "Standard (Theme-Label)",
        "admin.design.color.default_primary": "Standard (Theme-Primär)",
        "admin.design.color.default_secondary": "Standard (Theme-Sekundär)",
        "admin.design.color.pick_accent": "Akzentfarbe wählen",
        "admin.design.color.pick_label": "Label-Farbe wählen",
        "admin.design.color.pick_primary": "Primär-Button wählen",
        "admin.design.color.pick_secondary": "Sekundär-Button wählen",
        "admin.design.color.pick_tooltip": "Farbe wählen",
        "admin.design.color.reset_tooltip": "Zurücksetzen",
        "admin.design.save_app_defaults": "App-Standard speichern",
        "admin.design.dialog.title": "Design",
        "admin.design.msg.preview": (
            "Vorschau angewendet. "
            "Mit „Speichern“ dauerhaft übernehmen."
        ),
        "admin.design.msg.saved": (
            "Deine Design-Einstellungen wurden gespeichert."
        ),
        "admin.design.msg.no_app_defaults_permission": (
            "Keine Berechtigung für App-Standards."
        ),
        "admin.design.msg.app_defaults_saved": "App-Standard wurde gespeichert.",
        "admin.dashboard.dialog.title": "Dashboard",
        "admin.dashboard.msg.preview": (
            "Vorschau angewendet. "
            "Wechsle zum Dashboard, um Layout und Schriftgröße "
            "zu sehen. Mit „Speichern“ dauerhaft übernehmen."
        ),
        "admin.dashboard.msg.saved": (
            "Deine Dashboard-Einstellungen wurden gespeichert."
        ),
        "theme.font_size.small": "Klein",
        "theme.font_size.normal": "Normal",
        "theme.font_size.large": "Groß",
        "theme.nav_width.narrow": "Schmal",
        "theme.nav_width.normal": "Normal",
        "theme.nav_width.wide": "Breit",
        "theme.animation.off": "Aus",
        "theme.animation.reduced": "Reduziert",
        "theme.animation.full": "Voll",
        "theme.palette.dark": "Dark",
        "theme.palette.star_citizen": "Star Citizen",
        "theme.palette.light": "Light",
        "theme.table_density.compact": "Kompakt",
        "theme.table_density.normal": "Normal",
        "theme.table_density.spacious": "Geräumig",
        "admin.network.section": "◆ CREW",
        "admin.network.hint": (
            "Crew hosten: Code kopieren und teilen. "
            "Crew beitreten: Code vom Host eingeben. "
            "Mehr ist nicht nötig."
        ),
        "admin.network.host_crew": "Crew hosten",
        "admin.network.join_crew": "Crew beitreten",
        "admin.network.join_code": "Beitrittscode",
        "admin.network.copy_code": "Code kopieren",
        "admin.network.mode": "Modus",
        "admin.network.status": "Status",
        "admin.network.connected_crew": "Verbundene Crew",
        "admin.network.advanced": "Erweitert (optional)",
        "admin.network.relay_register": "Am Salvage-Relay registrieren",
        "admin.network.upnp": "Internet freigeben (UPnP)",
        "admin.network.start_host": "Host manuell starten",
        "admin.network.stop_host": "Host stoppen",
        "admin.network.dialog.title": "Vernetzung",
        "admin.network.msg.connected": "Mit Host verbunden.",
        "admin.network.code.dialog.title": "Code",
        "admin.network.msg.no_code": (
            "Kein Code — zuerst „Crew hosten“ klicken."
        ),
        "admin.network.relay.dialog.title": "Salvage-Relay",
        "admin.network.msg.relay_failed": (
            "Relay-Registrierung fehlgeschlagen. "
            "Netzwerk und Relay-Einstellungen prüfen."
        ),
        "admin.network.upnp.dialog.title": "UPnP",
        "admin.network.host.dialog.title": "Host",
        "admin.network.msg.host_running": "Der Host-Server läuft bereits.",
        "admin.network.msg.host_start_failed": (
            "Host-Server konnte nicht gestartet werden."
        ),
        "admin.support.section.project": "◆ PROJEKT",
        "admin.support.intro": (
            "{tagline}\n\n"
            "Die SOLO Version ist kostenlos — für Einzelspieler mit vollem "
            "Salvage-Workflow (Sitzungen, Raffinerie, Verkäufe, Dashboard).\n\n"
            "Die CREW Version erweitert um Host/Client-Vernetzung: gemeinsame "
            "Datenbank, Beitrittscode, Crew spielt zusammen.\n\n"
            "Die ORGA Version (Roadmap) kommt für Organisationen und "
            "mehrere Teams."
        ),
        "admin.support.section.edition": "◆ DEINE EDITION",
        "admin.support.label.installation": "Installation",
        "admin.support.label.unlock": "Supporter-Freischaltung",
        "admin.support.label.active": "Aktiv",
        "admin.support.section.key": "◆ SUPPORTER-KEY",
        "admin.support.key.hint": (
            "Mit einem Supporter-Key schaltest du CREW oder ORGA auf dieser "
            "Installation frei — ohne die SOLO Version zu ersetzen. "
            "Keys werden pro Installation gespeichert."
        ),
        "admin.support.label.key": "Key",
        "admin.support.placeholder.key": "z. B. CREW-ABCD-EFGH-XXXXXXXX",
        "admin.support.unlock": "Freischalten",
        "admin.support.clear_unlock": "Freischaltung entfernen",
        "admin.support.section.donate": "◆ SPENDEN",
        "admin.support.donate.hint": (
            "Wenn dir der Tracker hilft, kannst du die Weiterentwicklung "
            "unterstützen. Die SOLO Version bleibt dabei kostenlos."
        ),
        "admin.support.donate.button": "Projekt unterstützen",
        "admin.support.donate.tooltip_pending": (
            "Spenden-Link wird mit der Beta-Veröffentlichung ergänzt."
        ),
        "admin.support.key.dialog.title": "Supporter-Key",
        "admin.support.msg.admin_only": (
            "Nur Administratoren können Keys einlösen."
        ),
        "admin.support.msg.key_required": "Bitte einen Key eingeben.",
        "admin.support.msg.clear_title": "Freischaltung entfernen",
        "admin.support.msg.clear_confirm": (
            "Supporter-Freischaltung wirklich entfernen?\n\n"
            "Vernetzung wird wieder gesperrt, wenn nur SOLO aktiv ist."
        ),
        "admin.support.msg.cleared_title": "Freischaltung entfernt",
        "admin.support.msg.cleared": (
            "Die Supporter-Freischaltung wurde entfernt."
        ),
        "admin.system.section.updates": "◆ UPDATES",
        "admin.system.section.login_history": "◆ LOGIN-HISTORIE",
        "admin.system.section.backup": "◆ DATENSICHERUNG",
        "admin.system.updates.installed": (
            "Installierte Version: {version}"
        ),
        "admin.system.updates.last_check": "Letzte Prüfung: {datetime}",
        "admin.system.updates.no_check": (
            "Noch keine Update-Prüfung durchgeführt."
        ),
        "admin.system.updates.available": (
            "Neues Update verfügbar: {version} (Build {build})\n{status}"
        ),
        "admin.system.updates.auto_check": (
            "Beim Start automatisch nach Updates suchen"
        ),
        "admin.system.updates.check_button": "Nach Updates suchen",
        "admin.system.updates.hint": (
            "Updates werden über GitHub Releases bereitgestellt. "
            "Die Prüfsumme wird vor der Installation verifiziert."
        ),
        "admin.system.updates.dialog.title": "Updates",
        "admin.system.updates.msg.not_ready": (
            "Update-Dienst ist noch nicht bereit."
        ),
        "admin.system.updates.checking": "Update-Prüfung läuft …",
        "admin.system.history.col.id": "ID",
        "admin.system.history.col.user": "Benutzer",
        "admin.system.history.col.login": "Anmeldung",
        "admin.system.history.col.logout": "Abmeldung",
        "admin.system.history.empty": "Noch keine Anmeldungen protokolliert.",
        "admin.system.backup.create": "Jetzt Sicherung erstellen",
        "admin.system.backup.restore": "Stand wiederherstellen",
        "admin.system.backup.open_folder": "Backup-Ordner öffnen",
        "admin.system.backup.col.created": "Erstellt",
        "admin.system.backup.col.size": "Größe",
        "admin.system.backup.empty": "Noch keine Sicherungen vorhanden.",
        "admin.system.backup.delete": "Sicherung löschen",
        "admin.system.backup.danger_zone": "Gefahrenzone",
        "admin.system.backup.danger_hint": (
            "Löscht alle Sessions, Jobs, Verkäufe und Benutzer "
            "(außer Standard-Admin). Vorher wird automatisch eine "
            "Sicherung erstellt."
        ),
        "admin.system.backup.reinitialize": "Alle Tracker-Daten löschen",
        "admin.system.backup.advanced": "Erweitert (Support)",
        "admin.system.backup.verify": "Speicherstand prüfen",
        "admin.system.backup.migrate": "Datenbank aktualisieren",
        "admin.system.backup.retention": "Wie viele Sicherungen behalten?",
        "admin.system.backup.retention_hint": (
            "Älteste Sicherungen werden gelöscht, wenn das Limit "
            "erreicht ist. Vor dem Löschen und Zurückladen wird "
            "automatisch gesichert."
        ),
        "admin.system.backup.status.load_failed": (
            "Status konnte nicht geladen werden"
        ),
        "admin.system.backup.status.needs_check": (
            "Speicherstand sollte geprüft werden"
        ),
        "admin.system.backup.status.ok": "Alles in Ordnung",
        "admin.system.backup.summary": (
            "Programmversion: {version}<br>"
            "Gespeicherte Sicherungen: {count} "
            "<span style='color:#D9F4FF;'>(max. {max_count})</span><br>"
            "Letzte Sicherung: {latest}"
        ),
        "admin.system.backup.advanced_status": (
            "Build: {build}\n"
            "Datenstand: {schema} (Ziel: {target_schema})\n"
            "Datenbankpfad:\n{db_path}\n"
            "Sicherungsordner:\n{backup_dir}"
        ),
        "admin.system.settings.dialog.title": "Einstellungen",
        "admin.system.settings.msg.save_failed": (
            "Speichern fehlgeschlagen:\n{error}"
        ),
        "admin.system.settings.msg.saved": "Einstellungen gespeichert.",
        "admin.system.backup.dialog.title": "Sicherung",
        "admin.system.backup.msg.create_failed": (
            "Sicherung fehlgeschlagen:\n{error}"
        ),
        "admin.system.backup.msg.created": (
            "Sicherung erstellt ({created_at})."
        ),
        "admin.system.restore.dialog.title": "Wiederherstellen",
        "admin.system.restore.msg.select_first": (
            "Bitte zuerst eine Sicherung aus der Liste wählen."
        ),
        "admin.system.restore.msg.confirm_title": "Stand wiederherstellen",
        "admin.system.restore.msg.confirm": (
            "Der aktuelle Stand wird durch diese Sicherung "
            "({label}) ersetzt.\n\nFortfahren?"
        ),
        "admin.system.restore.msg.failed": (
            "Wiederherstellung fehlgeschlagen:\n{error}"
        ),
        "admin.system.restore.msg.success": (
            "Stand wiederhergestellt: {label}"
        ),
        "admin.system.backup_folder.dialog.title": "Backup-Ordner",
        "admin.system.backup_folder.msg.unknown": (
            "Backup-Ordner ist nicht bekannt."
        ),
        "admin.system.backup_folder.msg.open_failed": (
            "Ordner konnte nicht geöffnet werden:\n{folder}"
        ),
        "admin.system.backup_delete.dialog.title": "Sicherung löschen",
        "admin.system.backup_delete.msg.select_first": (
            "Bitte zuerst eine Sicherung aus der Liste wählen."
        ),
        "admin.system.backup_delete.msg.confirm": (
            "Diese Sicherung unwiderruflich löschen?\n\n{label}"
        ),
        "admin.system.backup_delete.msg.failed": (
            "Löschen fehlgeschlagen:\n{error}"
        ),
        "admin.system.backup_delete.msg.success": (
            "Sicherung gelöscht: {label}"
        ),
        "admin.system.verify.dialog.title": "Speicherstand prüfen",
        "admin.system.verify.msg.ok": (
            "Der Speicherstand ist in Ordnung."
        ),
        "admin.system.verify.msg.needs_update": (
            "Der Speicherstand sollte aktualisiert werden.\n\n{details}"
        ),
        "admin.system.migrate.dialog.title": "Datenbank aktualisieren",
        "admin.system.migrate.msg.confirm": (
            "Der Speicherstand wird an die aktuelle Programmversion "
            "angepasst. Dabei wird automatisch gesichert.\n\nFortfahren?"
        ),
        "admin.system.migrate.msg.failed": (
            "Aktualisierung fehlgeschlagen:\n{error}"
        ),
        "admin.system.migrate.msg.success": (
            "Speicherstand wurde aktualisiert."
        ),
        "admin.system.reinitialize.dialog.title": (
            "Alle Tracker-Daten löschen"
        ),
        "admin.system.reinitialize.msg.confirm": (
            "Alle Sessions, Jobs, Verkäufe und Benutzer "
            "(außer Standard-Admin) löschen?\n\n"
            "Vorher wird automatisch gesichert."
        ),
        "admin.system.reinitialize.msg.failed": (
            "Löschen fehlgeschlagen:\n{error}"
        ),
        "admin.system.reinitialize.msg.error": "Fehler:\n{error}",
        "admin.system.reinitialize.msg.success": (
            "Alle Tracker-Daten wurden gelöscht."
        ),
        "admin.roles.msg.admin_locked_short": (
            "Die Administrator-Rolle ist systemseitig festgelegt."
        ),
        "admin.network.msg.settings_saved": (
            "Vernetzungseinstellungen gespeichert."
        ),
        "admin.network.msg.host_mode_active": (
            "Crew-Modus aktiv.\n"
            "Code kopiert — an die Crew schicken."
        ),
        "admin.network.msg.code_copied": "Code kopiert.",
        "admin.network.mode.standalone": "Standalone (lokal)",
        "admin.network.mode.host": "Host",
        "admin.network.mode.client": "Client",
        "admin.network.status.running": "Läuft · Code {code}{relay}",
        "admin.network.status.relay_active": " · Relay aktiv",
        "admin.network.status.none": "Keine",
        "admin.network.status.inactive": "Nicht aktiv",
        "admin.network.relay.check_hint": (
            "Prüfe Relay-Adresse und ob der Relay-Server läuft."
        ),
        "admin.network.upnp.progress": "UPnP…",
        "admin.network.msg.client_connected": (
            "Mit Host verbunden. Die Sitzungs-Seite "
            "wurde in den Client-Modus umgeschaltet."
        ),
        "admin.network.msg.host_saved": (
            "Host-Modus gespeichert. Starte den Server "
            "unter Vernetzung, wenn die Crew beitritt."
        ),
        "admin.system.backup.msg.removed_note": (
            "\n\n{count} ältere Sicherungen wurden entfernt "
            "(Aufbewahrungslimit)."
        ),
        "admin.system.restore.msg.confirm_long": (
            "Der aktuelle Stand wird durch diese Sicherung "
            "ersetzt:\n\n{label}\n\n"
            "Vorher wird automatisch der jetzige Stand "
            "gesichert.\n\n"
            "Alle nicht gesicherten Änderungen gehen verloren.\n\n"
            "Fortfahren?"
        ),
        "admin.system.restore.msg.safety_note": (
            "\n\nDer bisherige Stand wurde vorher gesichert."
        ),
        "admin.system.restore.msg.relogin": (
            "Bitte abmelden und erneut anmelden."
        ),
        "admin.system.backup_delete.msg.select_first": (
            "Bitte zuerst eine Sicherung aus der Liste wählen."
        ),
        "admin.system.verify.msg.update_action": (
            "Bitte „Datenbank aktualisieren“ ausführen."
        ),
        "admin.system.migrate.msg.confirm_long": (
            "Der Speicherstand wird an die aktuelle Programmversion "
            "angepasst. Ihre Daten bleiben erhalten.\n\n"
            "Fortfahren?"
        ),
        "admin.system.reinitialize.msg.confirm_long": (
            "Alle Sessions, Jobs, Verkäufe und Benutzer "
            "(außer Standard-Admin) werden unwiderruflich "
            "gelöscht.\n\n"
            "Vorher wird automatisch eine Sicherung erstellt.\n\n"
            "Fortfahren?"
        ),
        "admin.system.reinitialize.msg.confirm_input": (
            "Zur Bestätigung bitte RESET eingeben:"
        ),
        "admin.system.reinitialize.msg.backup_note": (
            "\n\nEine Sicherung wurde vorher erstellt."
        ),
        "admin.system.reinitialize.msg.login_hint": (
            "Das Programm wird jetzt neu gestartet. "
            "Du kannst dich danach wieder anmelden."
        ),
        "permission.users.manage": "Benutzer verwalten",
        "permission.roles.manage": "Rollen verwalten",
        "permission.settings.manage": "Systemeinstellungen ändern",
        "permission.database.reset": "Datenbank zurücksetzen",
        "permission.sessions.manage": "Alle Sitzungen verwalten",
        "permission.sessions.manage_own": "Eigene Sitzungen verwalten",
        "permission.crew.manage": "Crew verwalten",
        "permission.refinery.manage": "Raffinerie verwalten",
        "permission.sales.manage": "Verkäufe durchführen",
        "permission.payouts.manage": "Auszahlungen erstellen",
        "permission.payouts.approve": "Auszahlungen freigeben",
        "permission.payouts.view_own": "Eigene Auszahlungen ansehen",
        "permission.history.view": "Historie ansehen",
        "permission.statistics.view": "Statistiken / Auszahlung ansehen",
        "permission.dashboard.view": "Dashboard nutzen",
        "permission.group.users_system": "Benutzer & System",
        "permission.group.sessions_crew": "Sitzungen & Crew",
        "permission.group.operations": "Operationen",
        "permission.group.payouts": "Auszahlung",
        "permission.group.views": "Ansicht",
        "role.dialog.edit": "Rolle bearbeiten",
        "role.dialog.new": "Neue Rolle",
        "role.dialog.view": "Rolle: {name}",
        "role.dialog.placeholder.name": "z. B. Officer",
        "role.dialog.placeholder.description": "Optional",
        "role.dialog.label.name": "Rollenname",
        "role.dialog.label.description": "Beschreibung",
        "role.dialog.section.permissions": "◆ RECHTE",
        "role.dialog.select_all": "Alle auswählen",
        "role.dialog.select_none": "Alle abwählen",
        "role.dialog.select_except_db": "Alle außer Datenbank",
        "role.dialog.scroll_hint": (
            "Weitere Rechte unten — Scrollbalken oder "
            "Mausrad über der Liste nutzen."
        ),
        "role.dialog.limit_hint": (
            "Ausgegraute Rechte hast du selbst nicht — "
            "du kannst sie weder vergeben noch entfernen."
        ),
        "role.dialog.tooltip.assigned_locked": (
            "Der Rolle zugewiesen — du darfst "
            "dieses Recht nicht ändern."
        ),
        "role.dialog.tooltip.not_grantable": (
            "Du hast dieses Recht selbst nicht "
            "und kannst es nicht vergeben."
        ),
        "role.dialog.msg.title": "Rolle",
        "role.dialog.msg.name_required": (
            "Bitte einen Rollennamen eingeben."
        ),
        "role.dialog.msg.admin_reserved": (
            "Der Name „Administrator“ ist "
            "systemseitig reserviert."
        ),
        "status.ACTIVE": "AKTIV",
        "status.WAITING_FOR_REFINERY": "WARTET AUF RAFFINERIE",
        "status.WAITING_FOR_SALE": "VERKAUFSBEREIT",
        "status.WAITING_FOR_PAYOUT": "AUSZAHLUNG",
        "status.REFINERY_COMPLETED": "VERKAUFSBEREIT",
        "status.SOLD": "VERKAUFT",
        "status.IDLE": "LEERLAUF",
        "dashboard.status.cycle_complete": "ABGESCHLOSSEN",
        "common.error": "Fehler",
        "common.hint": "Hinweis",
        "common.not_possible": "Nicht möglich",
        "common.success": "Erfolg",
        "login.error.failed_title": "Anmeldung fehlgeschlagen",
        "login.error.invalid_credentials": (
            "Benutzername oder Passwort ist ungültig."
        ),
        "login.error.blocked_title": "Anmeldung nicht möglich",
        "login.error.blocked_setup": (
            "Während der Erstinstallation kann sich nur der "
            "Super-Administrator anmelden."
        ),
        "main.login.blocked.title": "Anmeldung nicht möglich",
        "main.login.blocked.message": (
            "Dieser Benutzer darf sich derzeit nicht anmelden."
        ),
        "main.superadmin.title": "Super-Administrator",
        "main.superadmin.message": (
            "Der Super-Administrator ist nur für die "
            "Erstinstallation und Notfälle gedacht.\n\n"
            "Bitte melde dich mit einem Organisations-Benutzer an."
        ),
        "main.host.title": "Host-Server",
        "main.host.start_failed": (
            "Der Host-Server konnte nicht gestartet werden."
        ),
        "main.start.error.title": "Startfehler",
        "main.start.error.message": (
            "Das Hauptfenster konnte nicht geladen werden:\n\n{error}"
        ),
        "splash.initializing": "INITIALISIERE SALVAGE TRACKER...",
        "splash.db_preparing": "DATENBANK WIRD VORBEREITET...",
        "splash.db_step": "DATENBANK: {name} ({current}/{total})",
        "splash.fonts_loading": "SCHRIFTPAKETE WERDEN GELADEN...",
        "splash.ui_preparing": "OBERFLÄCHE WIRD VORBEREITET...",
        "splash.complete": "SYSTEMCHECK ABGESCHLOSSEN",
        "splash.created_by": "Created by {name} · {alias}",
        "nav.user": "◆  BENUTZER",
        "nav.badge.update": "◆ UPDATE · {version}",
        "nav.badge.update_available": "◆ UPDATE VERFÜGBAR",
        "nav.network.client": "◆ CLIENT · {host}:{port}",
        "nav.network.host": (
            "◆ HOST · {addresses}:{port}\n"
            "Code: {code} · {clients} Client(s)"
        ),
        "nav.network.host_inactive": "◆ HOST · nicht aktiv",
        "nav.network.host_fallback": "Host",
        "dates.error.empty": "Bitte ein Datum angeben.",
        "dates.error.invalid_date": (
            "Ungültiges Datum. Bitte TT.MM.JJJJ verwenden."
        ),
        "dates.error.invalid_timestamp": "Ungültiger Zeitstempel.",
        "dates.error.invalid_datetime": (
            "Ungültiges Datum oder Uhrzeit."
        ),
        "dates.month_year": "{month} {year}",
        "dates.month.1": "Januar",
        "dates.month.2": "Februar",
        "dates.month.3": "März",
        "dates.month.4": "April",
        "dates.month.5": "Mai",
        "dates.month.6": "Juni",
        "dates.month.7": "Juli",
        "dates.month.8": "August",
        "dates.month.9": "September",
        "dates.month.10": "Oktober",
        "dates.month.11": "November",
        "dates.month.12": "Dezember",
        "error.session.not_found": "Sitzung nicht gefunden.",
        "error.session.ship_not_found": (
            "Session-Schiff konnte nicht ermittelt werden. "
            "Sitzung mit einem bekannten Salvage-Schiff starten."
        ),
        "error.session.has_refinery_jobs": (
            "Sitzung hat Raffinerieaufträge. "
            "Bitte zuerst die Aufträge stornieren."
        ),
        "error.session.has_sales": (
            "Sitzung ist mit Verkäufen verknüpft. "
            "Bitte zuerst die Verkäufe stornieren."
        ),
        "error.refinery.not_found": "Raffinerieauftrag nicht gefunden.",
        "error.refinery.cancel.only_active": (
            "Nur laufende oder abholbereite "
            "Aufträge können storniert werden."
        ),
        "error.refinery.delete.only_completed": (
            "Nur abgeschlossene Aufträge können "
            "hier gelöscht werden. "
            "Laufende Aufträge bitte stornieren."
        ),
        "error.refinery.delete.already_sold": (
            "Das raffinierte Material wurde "
            "bereits verkauft. "
            "Bitte zuerst den Verkauf stornieren."
        ),
        "error.sale.has_payout_void": (
            "Für diesen Verkauf existiert "
            "bereits eine Auszahlung. "
            "Bitte zuerst die Auszahlung stornieren."
        ),
        "error.sale.not_found": "Verkauf nicht gefunden.",
        "error.payout.not_found": "Auszahlung nicht gefunden.",
        "error.refinery.batch_required": (
            "Mindestens ein Material-Batch "
            "ist erforderlich."
        ),
        "error.refinery.input_must_be_positive": (
            "Eingabemenge muss größer "
            "als 0 sein."
        ),
        "error.refinery.batch_not_raw": (
            "Batch #{batch_id} ist kein "
            "Rohmaterial für die Raffinerie."
        ),
        "error.refinery.insufficient_batch": (
            "Nicht genug Material in Batch "
            "#{batch_id} ({label}). "
            "Verfügbar: {available} SCU, "
            "angefordert: {requested} SCU."
        ),
        "error.refinery.pool_not_raw": (
            "{material} ist kein Rohmaterial für die Raffinerie."
        ),
        "error.refinery.insufficient_pool": (
            "Nicht genug {material} an diesem Ort. "
            "Verfügbar: {available} SCU, "
            "angefordert: {requested} SCU."
        ),
        "error.refinery.cost_payer_required": (
            "Bitte angeben, wer die "
            "Raffinerie-Kosten bezahlt hat."
        ),
        "error.refinery.output_must_be_positive": (
            "Ausgabemenge muss größer als 0 sein."
        ),
        "error.refinery.already_completed": (
            "Auftrag ist bereits abgeschlossen."
        ),
        "error.refinery.no_items": (
            "Auftrag enthält keine Positionen."
        ),
        "error.refinery.invalid_input_quantity": (
            "Ungültige Eingabemenge im Auftrag."
        ),
        "error.material.batch_not_found": "Material-Batch nicht gefunden.",
        "error.material.capture_in_use": (
            "Diese Erfassung kann nicht mehr rückgängig gemacht werden "
            "(Material bereits in Raffinerie oder Verkauf)."
        ),
        "error.material.capture_in_refinery": (
            "Diese Erfassung ist für einen aktiven Raffinerie-Auftrag reserviert."
        ),
        "error.cost.not_found": "Kosten-Eintrag nicht gefunden.",
        "error.cost.not_mission": "Hier können nur Missionskosten entfernt werden.",
        "error.cost.session_locked": (
            "Missionskosten können nur entfernt werden, solange die Sitzung "
            "aktiv ist oder auf Raffinerie wartet."
        ),
        "error.correction.capture_not_reversible": (
            "Diese Erfassung kann nicht rückgängig gemacht werden."
        ),
        "error.correction.already_reverted": (
            "Dieser Eintrag wurde bereits rückgängig gemacht."
        ),
        "error.correction.event_not_reversible": (
            "Dieser Historie-Eintrag kann nicht rückgängig gemacht werden "
            "(ältere Verschiebungen ohne Wiederherstellungsdaten)."
        ),
        "error.session.reopen.not_waiting": (
            "Nur Sitzungen mit Status „Wartet auf Raffinerie“ können wieder geöffnet werden."
        ),
        "error.session.reopen.active_exists": (
            "Beende oder lösche zuerst die aktuelle aktive Sitzung."
        ),
        "error.material.insufficient_batch": (
            "Nicht genug Material im Batch "
            "({available} SCU verfügbar)."
        ),
        "error.material.insufficient_batches": (
            "Nicht genug {material} in offenen Batches. "
            "Verfügbar: {available} SCU, "
            "angefordert: {requested} SCU."
        ),
        "error.material.storage_changed": (
            "Lagerbestand hat sich geändert. "
            "Bitte erneut versuchen."
        ),
        "error.sale.line_required": (
            "Mindestens eine Verkaufsposition "
            "ist erforderlich."
        ),
        "error.sale.quantity_must_be_positive": (
            "Verkaufsmenge muss größer "
            "als 0 sein."
        ),
        "error.sale.price_not_negative": (
            "Verkaufspreis darf nicht "
            "negativ sein."
        ),
        "error.sale.material_not_sellable": (
            "{material_code} ist kein "
            "verkaufbares Material. "
            "Rohmaterial muss zuerst "
            "raffiniert werden."
        ),
        "error.sale.insufficient_stock": (
            "Nicht genug Lagerbestand für "
            "{material_code}. "
            "Es fehlen {remaining} SCU."
        ),
        "error.payout.already_exists": (
            "Für diesen Verkauf existiert "
            "bereits eine Auszahlung."
        ),
        "error.payout.items_required": (
            "Mindestens eine Auszahlungsposition "
            "ist erforderlich."
        ),
        "error.payout.member_empty": (
            "Crew-Mitglied darf nicht leer sein."
        ),
        "error.payout.amount_not_negative": (
            "Auszahlungsbetrag darf nicht "
            "negativ sein."
        ),
        "error.payout.no_sessions_trace": (
            "Keine Sitzungen über Lager-Trace "
            "zuordenbar."
        ),
        "error.payout.select_cost_payer": (
            "Kostenerstattungen sind "
            "{labels} zugeordnet. "
            "Bitte den Zahler auswählen."
        ),
        "error.backup.invalid_file": "Ungültige Backup-Datei.",
        "error.backup.not_found": "Backup nicht gefunden.",
        "error.database.not_found": "Datenbankdatei nicht gefunden.",
        "error.cost.unknown_schema": "Unbekanntes Kosten-Schema",
        "error.cost.payers_required": (
            "Alter und neuer Zahler müssen "
            "angegeben werden."
        ),
        "error.dashboard.max_presets": (
            "Maximal {max} eigene Presets erlaubt."
        ),
        "error.role.name_required": "Rollenname erforderlich.",
        "error.role.name_admin_reserved": (
            "Der Name „Administrator“ ist "
            "systemseitig reserviert."
        ),
        "error.role.name_super_admin_reserved": (
            "Der Name „Super-Administrator“ ist "
            "systemseitig reserviert."
        ),
        "error.role.admin_cannot_rename": (
            "Die Administrator-Rolle kann nicht "
            "umbenannt werden."
        ),
        "error.role.super_admin_cannot_rename": (
            "Die Super-Administrator-Rolle kann nicht "
            "umbenannt werden."
        ),
        "error.role.not_found": "Rolle nicht gefunden.",
        "error.role.admin_perms_immutable": (
            "Administrator-Rechte können nicht "
            "geändert werden."
        ),
        "error.role.super_admin_perms_immutable": (
            "Super-Administrator-Rechte können nicht "
            "geändert werden."
        ),
        "error.role.forbidden_permissions": (
            "Du darfst folgende Rechte nicht vergeben "
            "oder entziehen:"
        ),
        "error.role.only_admin_can_assign_admin": (
            "Nur ein Administrator darf die "
            "Administrator-Rolle zuweisen."
        ),
        "error.role.exceeds_actor_permissions": (
            "Diese Rolle enthält Rechte, die du "
            "selbst nicht hast. Du darfst sie "
            "niemandem zuweisen — auch nicht dir."
        ),
        "error.role.admin_cannot_delete": (
            "Die Administrator-Rolle kann nicht "
            "gelöscht werden."
        ),
        "error.role.super_admin_cannot_delete": (
            "Die Super-Administrator-Rolle kann nicht "
            "gelöscht werden."
        ),
        "error.role.still_assigned": (
            "Rolle ist noch Benutzern zugewiesen."
        ),
        "error.user.not_found": "Benutzer nicht gefunden.",
        "error.user.system_immutable": (
            "System-Benutzer können nicht geändert werden."
        ),
        "error.user.system_cannot_manage": (
            "System-Benutzer können nicht "
            "verwaltet werden."
        ),
        "error.user.super_admin_cannot_manage": (
            "Der Super-Administrator kann nicht "
            "verwaltet werden."
        ),
        "error.user.admin_only_manages_admin": (
            "Der Administrator-Account darf nur von "
            "einem Administrator verwaltet werden."
        ),
        "error.password.no_permission_other_user": (
            "Keine Berechtigung, das Passwort "
            "eines anderen Benutzers zu ändern."
        ),
        "error.setup.superadmin_after_complete": (
            "Das Super-Administrator-Passwort kann nach der "
            "Erstinstallation hier nicht mehr gesetzt werden."
        ),
        "error.setup.superadmin_not_found": (
            "Der Super-Administrator wurde nicht gefunden."
        ),
        "error.setup.default_password_forbidden": (
            "Bitte ein anderes Passwort als das "
            "Standard-Passwort wählen."
        ),
        "session.title": "SITZUNG",
        "session.section.manage": "◆ SCHIFF, CREW & BEUTE",
        "session.section.new": "◆ SITZUNG STARTEN",
        "session.section.network": "◆ NETZWERK-SITZUNG",
        "session.section.active": "◆ LAUFENDE SITZUNG",
        "session.section.missions": "◆ MISSIONSKOSTEN",
        "session.section.materials": "◆ BEUTE EINTRAGEN",
        "session.label.ship": "Schiff",
        "session.label.crew": "Mitspieler (ein Name pro Zeile)",
        "session.label.status": "Status",
        "session.label.not_started": "Noch keine Sitzung gestartet",
        "session.label.active_session": "Aktive Sitzung",
        "session.label.mission_cost": "Missionskosten (aUEC)",
        "session.label.paid_by": "Bezahlt von",
        "session.label.deletable_session": "Fehlerhafte Sitzung:",
        "session.hint.start": (
            "Missionskosten werden während der laufenden Sitzung "
            "erfasst — pro angenommener Mission einzeln. "
            "Bis der Laderaum voll ist, können mehrere Missionen "
            "und Material-Einsätze zur gleichen Sitzung gehören."
        ),
        "session.hint.archived": (
            "Abgeschlossene Sitzungen inkl. Missionskosten findest du "
            "unter Historie. Hier startest du die nächste Sitzung."
        ),
        "session.hint.client": (
            "Wähle die laufende Sitzung des Hosts. "
            "Die Materialfelder richten sich automatisch "
            "nach dem Schiff dieser Sitzung."
        ),
        "session.hint.mission": (
            "Pro angenommener Mission die Kosten erfassen. "
            "Alle Missionen einer Sitzung werden summiert."
        ),
        "session.hint.material_default": (
            "Materialfelder richten sich nach dem Schiff "
            "der aktiven Sitzung."
        ),
        "session.hint.material_ship": (
            "Mit {ship}: {materials}"
        ),
        "session.crew.placeholder": (
            "Ein Name pro Zeile\n\n"
            "Beispiel:\n"
            "Xangandu\n"
            "Pilot2\n"
            "Pilot3"
        ),
        "session.placeholder.mission_cost": "Kosten dieser Mission in aUEC",
        "session.placeholder.quantity": "Menge in SCU",
        "session.button.start": "Sitzung starten",
        "session.button.save_run": "Material speichern",
        "session.button.end": "Sitzung abschließen",
        "session.button.delete": "Sitzung löschen",
        "session.button.reopen": "Sitzung wieder öffnen",
        "session.button.undo_capture": "Rückgängig",
        "session.button.delete_mission": "Entfernen",
        "session.button.add_mission": "Kosten eintragen",
        "session.client.empty": (
            "Keine aktive Sitzung auf dem Host.\n"
            "Der Host muss zuerst eine Sitzung starten."
        ),
        "session.mission.paid_by.placeholder": "— Bitte wählen —",
        "session.mission.costs_total": (
            "Missionskosten: {mission_total} aUEC · "
            "Gesamtkosten Sitzung: {session_total} aUEC"
        ),
        "session.mission.line": (
            "Mission {index}: {amount} aUEC ({paid_by})"
        ),
        "session.mission.none": "Noch keine Missionen erfasst.",
        "session.section.captures": "◆ ERFASSTE BEUTE (KORREKTUR)",
        "session.hint.captures": (
            "Falsche Menge oder Material? Einzelne Erfassungen hier rückgängig machen."
        ),
        "session.table.capture_material": "Material",
        "session.table.capture_quantity": "SCU",
        "session.table.capture_time": "Erfasst",
        "session.table.capture_action": "Aktion",
        "session.table.mission_amount": "Betrag (aUEC)",
        "session.table.mission_payer": "Bezahlt von",
        "session.table.mission_action": "Aktion",
        "session.msg.capture_undo_confirm.title": "Erfassung rückgängig",
        "session.msg.capture_undo_confirm.message": (
            "{quantity} SCU {material} aus dieser Sitzung entfernen?"
        ),
        "session.msg.capture_undone": "Erfassung rückgängig gemacht.",
        "session.msg.mission_delete_confirm.title": "Missionskosten entfernen",
        "session.msg.mission_delete_confirm.message": (
            "Missionskosten {amount} aUEC ({paid_by}) entfernen?"
        ),
        "session.msg.mission_deleted": "Missionskosten entfernt.",
        "session.msg.reopen_confirm.title": "Sitzung wieder öffnen",
        "session.msg.reopen_confirm.message": (
            "Sitzung #{session_id} wieder öffnen? "
            "Du kannst dann weiter Beute und Missionskosten erfassen."
        ),
        "session.msg.reopened.title": "Sitzung wieder geöffnet",
        "session.msg.reopened.message": (
            "Sitzung #{session_id} ist wieder aktiv."
        ),
        "session.section.refinery_costs": "◆ RAFFINERIE (KOSTEN)",
        "session.refinery.costs_total": (
            "Raffineriekosten: {refinery_total} aUEC · "
            "Gesamtkosten Sitzung: {session_total} aUEC"
        ),
        "session.refinery.line": (
            "Job #{job_id}: {amount} aUEC ({station} · {paid_by})"
        ),
        "session.refinery.none": "Noch keine Raffineriekosten erfasst.",
        "session.msg.no_session": (
            "Keine aktive Sitzung — bitte zuerst eine Sitzung starten."
        ),
        "session.msg.paid_by_required": (
            "Bitte angeben, wer die Missionskosten bezahlt hat."
        ),
        "session.msg.invalid_mission_cost": (
            "Bitte gültige Missionskosten eingeben."
        ),
        "session.msg.amount_positive": (
            "Bitte einen Betrag größer als 0 eingeben."
        ),
        "session.msg.mission_added.title": "Mission erfasst",
        "session.msg.mission_added.message": (
            "Missionskosten {amount} aUEC wurden zur Sitzung hinzugefügt."
        ),
        "session.msg.no_deletable": "Keine löschbare Sitzung ausgewählt.",
        "session.msg.delete_confirm.title": "Sitzung löschen",
        "session.msg.delete_confirm.message": (
            "Sitzung #{session_id} wirklich löschen?\n\n"
            "Material, Kosten und Crew-Einträge dieser Sitzung werden entfernt. "
            "Nur möglich ohne Raffinerie und Verkauf."
        ),
        "session.msg.delete_failed": "Löschen fehlgeschlagen:\n\n{error}",
        "session.msg.deleted.title": "Gelöscht",
        "session.msg.deleted.message": "Sitzung #{session_id} wurde gelöscht.",
        "session.msg.no_crew": (
            "Bitte mindestens ein Crew-Mitglied angeben."
        ),
        "session.msg.started.title": "Sitzung gestartet",
        "session.msg.started.message": (
            "Die Salvage-Sitzung wurde gestartet.\n\n"
            "Erfasse unter „Missionskosten“ jede angenommene Mission einzeln."
        ),
        "session.msg.start_failed": (
            "Sitzung konnte nicht gestartet werden:\n\n{error}"
        ),
        "session.msg.no_active_selected": "Keine aktive Sitzung ausgewählt.",
        "session.msg.invalid_numbers": "Bitte gültige Zahlen eingeben.",
        "session.msg.material_required": (
            "Bitte mindestens ein Material mit Menge > 0 eingeben."
        ),
        "session.msg.material_not_allowed": (
            "{material} kann mit {ship} nicht erfasst werden.\n\n"
            "Erlaubt: {allowed}"
        ),
        "session.msg.material_saved.title": "Erfolg",
        "session.msg.material_saved.message": "Material gespeichert.",
        "session.msg.no_active_found": "Keine aktive Sitzung gefunden.",
        "session.msg.ended.title": "Sitzung beendet",
        "session.msg.ended.message": (
            "Die Sitzung wartet nun auf die Raffinerie."
        ),
        "session.ship.unnamed": "diesem Schiff",
        "refinery.title": "RAFFINERIE",
        "refinery.section.batches": "◆ VERFÜGBARES MATERIAL",
        "refinery.section.create": "◆ RAFFINERIEAUFTRAG ANLEGEN",
        "refinery.section.active": "◆ AKTIVE AUFTRÄGE",
        "refinery.section.history": "◆ RAFFINERIE-HISTORIE",
        "refinery.table.batch": "Batch",
        "refinery.table.location": "Standort",
        "refinery.table.material": "Material",
        "refinery.table.available_scu": "Verfügbar (SCU)",
        "refinery.table.original_scu": "Original (SCU)",
        "refinery.table.session": "Sitzung",
        "refinery.history.no": "Nr.",
        "refinery.history.station": "Station",
        "refinery.history.method": "Methode",
        "refinery.history.status": "Status",
        "refinery.history.input": "Input",
        "refinery.history.cm_output": "CM Raf Output",
        "refinery.history.yield": "Ausbeute",
        "refinery.history.cost": "Kosten",
        "refinery.history.created_by": "Erstellt von",
        "refinery.label.station": "Raffinerie / Station",
        "refinery.label.method": "Raffinerie-Methode",
        "refinery.label.cost": "Kosten (aUEC)",
        "refinery.label.paid_by": "Bezahlt von",
        "refinery.label.batch": "Material-Batch",
        "refinery.label.material_source": "Material-Quelle",
        "refinery.label.input_scu": "Eingabe (SCU)",
        "refinery.label.input_cscu": "Eingabe (cSCU) — Terminal",
        "refinery.label.hours": "Stunden",
        "refinery.label.minutes": "Minuten",
        "refinery.label.notes": "Notiz",
        "refinery.placeholder.station": "Station wählen oder eingeben",
        "refinery.placeholder.cost": "Kosten in aUEC (beim Anlegen)",
        "refinery.placeholder.input_scu": "Eingabemenge in SCU",
        "refinery.placeholder.input_cscu": "Menge am Raffinerie-Terminal (cSCU)",
        "refinery.hint.cscu_formula": "1000 cSCU = 10 SCU · 100 cSCU = 1 SCU",
        "refinery.hint.scu_from_cscu": "→ {scu} SCU im Tracker ({cscu} cSCU Terminal)",
        "refinery.hint.cscu": "Terminal: {cscu} cSCU ({scu} SCU)",
        "location.placeholder.custom": "Ort wählen oder eingeben",
        "location.placeholder.select": "— Standort wählen —",
        "location.label.system": "System",
        "location.label.station": "Weltraum-Station",
        "location.label.city": "Stadt / Landeplatz",
        "location.label.place": "Standort (Station oder Stadt)",
        "location.placeholder.system": "— System wählen —",
        "location.placeholder.station": "— Station wählen —",
        "location.placeholder.city": "— Stadt wählen —",
        "location.group.stations": "— Weltraum-Stationen —",
        "location.group.cities": "— Städte / Landeplätze —",
        "error.location.not_selected": "Bitte eine Station oder Stadt aus der Liste wählen.",
        "refinery.placeholder.hours": "Stunden",
        "refinery.placeholder.minutes": "Minuten",
        "refinery.placeholder.notes": "Notiz (optional)",
        "refinery.method.placeholder": "— Methode wählen —",
        "refinery.button.create": "Auftrag erstellen",
        "refinery.button.delete": "Auftrag löschen",
        "refinery.button.cancel": "Stornieren",
        "refinery.button.complete": "ABSCHLIESSEN",
        "refinery.status.panel": (
            "● RAFFINERIE STATUS\n\n"
            "Fertig am:\n{ready_at}\n\n"
            "Verbleibend:\n{remaining}\n\n"
            "Status:\n{status}"
        ),
        "refinery.status.waiting_input": "WARTET AUF EINGABE",
        "refinery.status.in_progress": "IN BEARBEITUNG",
        "refinery.status.ready_for_pickup": "ABHOLBEREIT",
        "refinery.status.final_phase": "ENDPHASE",
        "refinery.status.finished": "Fertig",
        "refinery.status.remaining_min": "{minutes} Min",
        "refinery.status.remaining_hm": "{hours}h {minutes}m",
        "refinery.active.empty": "Keine aktiven Raffinerieaufträge.",
        "refinery.job.detail": "Auftrag #{job_id} | {name}",
        "refinery.job.method": "Methode: {method}",
        "refinery.job.cost": "Kosten: {cost} aUEC",
        "refinery.job.cost_paid": "Kosten: {cost} aUEC · bezahlt von {payer}",
        "refinery.job.created_by": "Erstellt von: {name}",
        "refinery.job.batch_line": (
            "Batch #{batch_id} | {material} | "
            "Input: {quantity} SCU"
        ),
        "refinery.job.ready_at": "Fertig: {time}",
        "refinery.job.remaining": "Verbleibend: {remaining}",
        "refinery.job.countdown": "Countdown: {countdown}",
        "refinery.job.progress": "Fortschritt: {percent} %",
        "refinery.banner.ready_one": (
            "Auftrag #{job_id} in {station} ist abholbereit!"
        ),
        "refinery.banner.ready_many": (
            "{count} Raffinerie-Aufträge sind abholbereit!"
        ),
        "refinery.batch.combo": "#{batch_id} | {material} | {remaining} SCU",
        "refinery.pool.combo": (
            "{location} · {material} · {quantity} SCU"
        ),
        "refinery.history.input_line": (
            "{quantity} SCU {material} (Batch #{batch_id})"
        ),
        "refinery.history.output_line": "{quantity} SCU {material}",
        "refinery.history.yield_pct": "{yield_pct} %",
        "refinery.complete.dialog.title": "Raffinerie abschließen",
        "refinery.complete.dialog.field": "CM Raf Output (cSCU)",
        "refinery.complete.dialog.tooltip": (
            "Menge laut Raffinerie-Terminal in cSCU "
            "(1000 cSCU = 10 SCU im Tracker)."
        ),
        "refinery.complete.hint": (
            "Dein bisheriger Durchschnitt für {material}: {efficiency} % "
            "({job_count} Aufträge)"
        ),
        "refinery.msg.no_batch": "Kein Material-Batch verfügbar.",
        "refinery.msg.no_pool": (
            "Kein Material am Schiff oder im Lager verfügbar."
        ),
        "refinery.msg.no_station": "Bitte Raffinerie/Station angeben.",
        "refinery.msg.invalid_values": "Bitte gültige Werte eingeben.",
        "refinery.msg.negative_cost": "Kosten dürfen nicht negativ sein.",
        "refinery.msg.paid_by_required": (
            "Bitte angeben, wer die Raffinerie-Kosten bezahlt hat."
        ),
        "refinery.msg.create_failed": (
            "Auftrag konnte nicht erstellt werden:\n\n{error}"
        ),
        "refinery.msg.complete_failed": (
            "Abschluss fehlgeschlagen:\n\n{error}"
        ),
        "refinery.msg.completed.title": "Abgeschlossen",
        "refinery.msg.completed.message": (
            "{quantity} SCU {material} ins Lager gebucht "
            "(Ausbeute: {yield_pct} %)."
        ),
        "refinery.msg.cancel_confirm.title": "Auftrag stornieren",
        "refinery.msg.cancel_confirm.message": (
            "Raffinerieauftrag #{job_id} stornieren?\n\n"
            "Reserviertes Material wird wieder dem Batch gutgeschrieben."
        ),
        "refinery.msg.cancel_failed": (
            "Stornierung fehlgeschlagen:\n\n{error}"
        ),
        "refinery.msg.cancelled.title": "Storniert",
        "refinery.msg.cancelled.message": "Auftrag #{job_id} wurde storniert.",
        "refinery.msg.no_selection": (
            "Bitte zuerst einen Auftrag in der Historie auswählen."
        ),
        "refinery.msg.delete_confirm.title": "Auftrag löschen",
        "refinery.msg.delete_confirm.message": (
            "Abgeschlossenen Auftrag #{job_id} löschen?\n\n"
            "CM wird aus dem Lager entfernt und Rohmaterial den Batches "
            "zurückgebucht. Nur möglich, wenn das CM nicht verkauft wurde."
        ),
        "refinery.msg.delete_failed": "Löschen fehlgeschlagen:\n\n{error}",
        "refinery.msg.deleted.title": "Gelöscht",
        "refinery.msg.deleted.message": "Auftrag #{job_id} wurde gelöscht.",
        "refinery.job_status.RUNNING": "LAUFEND",
        "refinery.job_status.READY": "ABHOLBEREIT",
        "refinery.job_status.COMPLETED": "ABGESCHLOSSEN",
        "refinery.job_status.CANCELLED": "STORNIERT",
        "storage.title": "LAGER / STANDORTE",
        "storage.section.list": "◆ MATERIAL JE STANDORT",
        "storage.section.add": "◆ MATERIAL EINLAGERN",
        "storage.section.history": "◆ VERLAUF",
        "storage.section.totals": "◆ GESAMTBESTAND PRO MATERIAL",
        "storage.table.location": "Standort",
        "storage.table.material": "Material",
        "storage.table.quantity": "Menge (SCU)",
        "storage.table.status": "Status",
        "storage.table.ship": "Schiff",
        "storage.table.activity": "Letzte Aktivität",
        "storage.table.reserve": "Reserve",
        "storage.table.notes": "Notiz",
        "storage.label.location_type": "Wo liegt es?",
        "storage.label.location": "Standort",
        "storage.label.ship": "Schiff",
        "storage.label.material": "Material",
        "storage.label.quantity": "Menge (SCU)",
        "storage.label.reserve": "Reserve-Tag",
        "storage.label.notes": "Notiz",
        "storage.label.sort": "Liste sortieren nach",
        "storage.location_type.station": "Station / Stadt",
        "storage.location_type.ship": "Im Schiff",
        "storage.location.ship": "Schiff · {ship}",
        "storage.event.session_salvage": "Einsatz",
        "storage.event.from_ship": "Vom Schiff",
        "storage.event.to_refinery": "Zur Raffinerie · {station}",
        "storage.event.refinery_cancelled": "Raffinerie abgebrochen",
        "storage.status.IN_SHIP": "Im Schiff",
        "storage.status.STORED": "Eingelagert",
        "storage.status.IN_REFINERY": "In Raffinerie",
        "storage.status.READY_PICKUP": "Abholbereit",
        "storage.status.RESERVED": "Reserve",
        "storage.sort.location": "Standort (A–Z)",
        "storage.sort.material": "Material",
        "storage.sort.age": "Zuletzt bewegt (älteste zuerst)",
        "storage.placeholder.reserve": "z.B. Reserve — keine Warnung",
        "storage.placeholder.notes": "Notiz (optional)",
        "storage.empty": "Noch kein Material an Standorten erfasst.",
        "storage.totals.line": "{material}: {quantity} SCU",
        "storage.totals.none": "Keine Bestandssummen.",
        "storage.button.save": "Einlagern",
        "storage.button.delete": "Eintrag löschen",
        "storage.button.delete_event": "Historie-Eintrag löschen",
        "storage.button.revert_event": "Bewegung rückgängig",
        "storage.event.reverted_note": "Rückgängig gemacht",
        "storage.msg.revert_event_confirm.title": "Bewegung rückgängig",
        "storage.msg.revert_event_confirm.message": (
            "Diese Lagerbewegung rückgängig machen? "
            "Der Bestand wird entsprechend zurückgebucht."
        ),
        "storage.msg.reverted": "Bewegung rückgängig gemacht.",
        "storage.button.reminded": "Warnung gelesen",
        "storage.button.set_reserve": "Reserve setzen",
        "storage.button.clear_reserve": "Reserve entfernen",
        "storage.button.moved": "Als bewegt markieren",
        "storage.button.transfer": "Material verschieben",
        "storage.transfer.title": "Material verschieben",
        "storage.transfer.hint": "Quelle, Menge und Ziel wählen. Die Menge wird von der Quell-Zeile abgezogen und am Zielort gutgeschrieben.",
        "storage.transfer.pool_hint": (
            "Quellen sind nach Standort und Materialtyp zusammengefasst. "
            "Die Menge wird aus der Gesamtsumme entnommen (FIFO über die Einzelzeilen)."
        ),
        "storage.transfer.pool_option": (
            "{location} · {material} · {quantity} SCU"
        ),
        "storage.transfer.label.source": "Quelle",
        "storage.transfer.label.destination_type": "Ziel-Typ",
        "storage.transfer.confirm": "Verschieben",
        "storage.transfer.source_option": "{location} · {material} · {quantity} SCU",
        "storage.transfer.msg.no_source": "Bitte einen Quell-Bestand wählen.",
        "storage.msg.transferred": "Material erfolgreich verschoben.",
        "storage.event.from_location": "Vom Standort-Lager",
        "storage.event.inbound_transfer": "Eingehende Umlagerung",
        "storage.event.withdrawn": "Aus Lager entnommen",
        "storage.history.type.TRANSFER": "Verschiebung",
        "storage.history.type.WITHDRAW": "Entnahme",
        "error.storage.insufficient_at_location": "Nicht genug Material an Standorten ({available} SCU {material} verfügbar).",
        "error.storage.insufficient_at_source": "Nicht genug Material an der Quelle ({available} SCU {material} verfügbar).",
        "error.storage.transfer_same_location": "Quelle und Ziel sind identisch.",
        "error.storage.transfer_invalid_source": "Dieser Bestand kann nicht als Quelle verwendet werden.",
        "error.storage.transfer_material_mismatch": "Material passt nicht zur gewählten Quelle.",
        "error.storage.transfer_failed": "Verschieben fehlgeschlagen — keine passende Quelle gefunden.",
        "error.storage.insufficient_pool": (
            "Nicht genug {material} an diesem Ort. "
            "Verfügbar: {available} SCU, "
            "angefordert: {requested} SCU."
        ),
        "error.storage.insufficient_ship_pool": (
            "Nicht genug {material} am Schiff. "
            "Verfügbar: {available} SCU, "
            "angefordert: {requested} SCU."
        ),
        "error.storage.insufficient_stored_pool": (
            "Nicht genug {material} im Lager. "
            "Verfügbar: {available} SCU, "
            "angefordert: {requested} SCU."
        ),
        "storage.filter.warnings_only": "Nur Warnungen",
        "storage.idle.banner.title": (
            "{count} Bestand/Bestände seit über {days} Tagen ohne Bewegung"
        ),
        "storage.idle.banner.hint": (
            "Eintrag in der Liste wählen und Warnung bestätigen, "
            "als Reserve markieren oder als bewegt markieren."
        ),
        "storage.idle.banner.collapse": "Ausblenden",
        "storage.idle.banner.expand": "Anzeigen",
        "storage.activity.today": "Heute",
        "storage.activity.yesterday": "Gestern",
        "storage.activity.days_ago": "vor {days} Tagen",
        "storage.activity.warning_prefix": "⚠ ",
        "storage.msg.reminded": "Warnung bestätigt.",
        "storage.msg.reserve_set": "Reserve-Tag gespeichert.",
        "storage.msg.reserve_cleared": "Reserve-Tag entfernt.",
        "storage.msg.reserve_clear_confirm.title": "Reserve-Tag entfernen",
        "storage.msg.reserve_clear_confirm.message": "Reserve-Tag von diesem Bestand entfernen? Idle-Warnungen können wieder erscheinen.",
        "error.storage.reserve_not_set": "Dieser Bestand hat keinen Reserve-Tag.",
        "storage.msg.moved": "Material aus dem Lager entnommen.",
        "storage.msg.reserve_prompt.title": "Reserve-Tag",
        "storage.msg.reserve_prompt.label": "Tag für diesen Bestand",
        "nav.badge.storage_idle": "◆ {count} INAKTIV",
        "error.storage.reserve_required": "Bitte einen Reserve-Tag eingeben.",
        "storage.history.type.DEPOSIT": "Einlagerung",
        "storage.history.type.UPDATE": "Änderung",
        "storage.history.type.DELETE": "Löschung",
        "storage.history.type.IDLE_REMINDED": "Idle-Erinnerung",
        "storage.history.type.TAG_SET": "Reserve-Tag",
        "storage.history.type.TAG_CLEAR": "Reserve entfernt",
        "storage.history.type.ACTIVITY": "Aktivität",
        "storage.history.type": "Typ",
        "storage.history.delta": "Änderung",
        "storage.history.when": "Zeitpunkt",
        "storage.msg.saved": "Material eingelagert.",
        "storage.msg.deleted": "Lager-Eintrag gelöscht.",
        "storage.msg.no_selection": "Bitte einen Eintrag auswählen.",
        "storage.msg.delete_confirm.title": "Eintrag löschen",
        "storage.msg.delete_confirm.message": (
            "Diesen Lager-Eintrag löschen?\n\n{location} · {material} · {quantity} SCU"
        ),
        "storage.msg.delete_event_confirm.title": "Historie-Eintrag löschen",
        "storage.msg.delete_event_confirm.message": (
            "Diesen Historie-Eintrag wirklich entfernen?"
        ),
        "error.storage.not_available": "Lager-Modul ist nicht verfügbar.",
        "error.storage.not_found": "Lager-Eintrag nicht gefunden.",
        "error.storage.event_not_found": "Historie-Eintrag nicht gefunden.",
        "error.storage.quantity_positive": "Menge muss größer als null sein.",
        "error.storage.location_required": "Bitte einen Standort angeben.",
        "error.storage.ship_required": "Bitte ein Schiff auswählen.",
        "error.storage.insufficient_global": (
            "Nicht genug unzugeordnetes Material verfügbar "
            "({available} SCU {material}). "
            "Bitte zuerst in der Session erfassen oder die Menge reduzieren."
        ),
        "error.storage.insufficient_on_ship": (
            "Nicht genug Material auf Schiffen "
            "({available} SCU {material}). "
            "Bitte zuerst in der Session erfassen oder die Menge reduzieren."
        ),
        "sales.title": "VERKÄUFE",
        "sales.section.inventory": "◆ VERFÜGBARER LAGERBESTAND",
        "sales.section.new": "◆ NEUER VERKAUF",
        "sales.section.finance": "◆ FINANZÜBERSICHT",
        "sales.section.history": "◆ VERKAUFSHISTORIE",
        "sales.table.material": "Material",
        "sales.table.available_scu": "Verfügbar (SCU)",
        "sales.inventory.empty": "Kein verkaufbares Material im Lager.",
        "sales.label.location": "Verkaufsort",
        "sales.label.date": "Datum",
        "sales.label.material": "Material",
        "sales.label.quantity": "Menge (SCU)",
        "sales.label.unit_price": "Stückpreis (aUEC)",
        "sales.label.notes": "Notiz",
        "sales.placeholder.location": "Ort wählen oder eingeben",
        "sales.placeholder.date": "TT.MM.JJJJ",
        "sales.placeholder.quantity": "Menge in SCU",
        "sales.placeholder.unit_price": "Preis pro SCU (aUEC)",
        "sales.placeholder.notes": "Notiz (optional)",
        "sales.button.save": "Verkauf speichern",
        "sales.button.void": "Verkauf stornieren",
        "sales.line_total": "Gesamt: {total} aUEC",
        "sales.line_total.invalid": "Gesamt: — aUEC",
        "sales.summary.revenue": (
            "Gesamtumsatz (alle Verkäufe): {amount} aUEC"
        ),
        "sales.summary.costs": "Gesamtkosten: {amount} aUEC",
        "sales.summary.profit": "Gewinn: {amount} aUEC",
        "sales.history.no": "Nr.",
        "sales.history.date": "Datum",
        "sales.history.location": "Ort",
        "sales.history.materials": "Materialien",
        "sales.history.revenue": "Umsatz",
        "sales.history.seller": "Verkäufer",
        "sales.material.combo": "{material} — {quantity} SCU",
        "sales.history.item_line": "{quantity} SCU {material}",
        "sales.msg.no_location": "Bitte einen Verkaufsort angeben.",
        "sales.msg.no_material": "Kein Material im Lager verfügbar.",
        "sales.msg.invalid_quantity_price": (
            "Bitte gültige Menge und Preis eingeben."
        ),
        "sales.msg.quantity_positive": (
            "Die Verkaufsmenge muss größer als 0 sein."
        ),
        "sales.msg.not_possible.title": "Verkauf nicht möglich",
        "sales.msg.save_failed": (
            "Verkauf konnte nicht gespeichert werden:\n\n{error}"
        ),
        "sales.msg.saved.title": "Verkauf gespeichert",
        "sales.msg.saved.message": "Der Verkauf wurde im Lager verbucht.",
        "sales.msg.no_selection": (
            "Bitte zuerst einen Verkauf in der Historie auswählen."
        ),
        "sales.msg.void_confirm.title": "Verkauf stornieren",
        "sales.msg.void_confirm.message": (
            "Verkauf #{sale_id} wirklich stornieren?\n\n"
            "Die verkaufte Menge wird dem Lager zurückgebucht. "
            "Nicht möglich, wenn bereits ausgezahlt."
        ),
        "sales.msg.void_failed": "Stornierung fehlgeschlagen:\n\n{error}",
        "sales.msg.voided.title": "Storniert",
        "sales.msg.voided.message": "Verkauf #{sale_id} wurde storniert.",
        "payout.title": "GEWINNVERTEILUNG",
        "payout.section.main": "◆ CREW-AUSZAHLUNG & STATISTIK",
        "payout.section.summary": "◆ ÜBERSICHT",
        "payout.section.unpaid": "◆ OFFENE VERKÄUFE (NOCH NICHT AUSGEZAHLT)",
        "payout.section.calculate": "◆ AUSZAHLUNG BERECHNEN",
        "payout.section.crew_totals": "◆ CREW-GESAMTAUSZAHLUNGEN",
        "payout.section.history": "◆ AUSZAHLUNGS-HISTORIE",
        "payout.summary": (
            "Ausstehende Verkäufe: {count} | "
            "Ausgezahlt gesamt: {total} aUEC"
        ),
        "payout.table.no": "Nr.",
        "payout.table.date": "Datum",
        "payout.table.location": "Ort",
        "payout.table.revenue": "Umsatz",
        "payout.table.seller": "Verkäufer",
        "payout.table.sale": "Verkauf",
        "payout.table.paid_out": "Ausgezahlt",
        "payout.table.created_by": "Erstellt von",
        "payout.table.crew_member": "Crew-Mitglied",
        "payout.table.amount": "Betrag (aUEC)",
        "payout.table.total_received": "Gesamt erhalten (aUEC)",
        "payout.table.date_or_crew": "Datum / Crew-Mitglied",
        "payout.unpaid.empty": (
            "Keine offenen Verkäufe — alle Verkäufe sind ausgezahlt."
        ),
        "payout.calc.placeholder": (
            "Verkauf wählen, um Vorschlag zu laden."
        ),
        "payout.label.sale": "Verkauf",
        "payout.label.notes": "Notiz",
        "payout.label.cost_payer": "Kostenerstattung an Crew-Mitglied:",
        "payout.placeholder.notes": "Notiz (optional)",
        "payout.sale.placeholder": "— Verkauf wählen —",
        "payout.button.save": "Auszahlung speichern",
        "payout.button.void": "Auszahlung stornieren",
        "payout.crew.empty": "Noch keine Crew-Auszahlungen erfasst.",
        "payout.history.empty": "Noch keine Auszahlungen gespeichert.",
        "payout.sale.combo": (
            "#{sale_id} | {location} | {amount} aUEC"
        ),
        "payout.proposal.detail": (
            "Verkauf #{sale_id} | Umsatz: {revenue} aUEC\n"
            "Sitzungen: {sessions}\n"
            "Sitzungskosten: {session_costs} aUEC\n"
            "Raffineriekosten: {refinery_costs} aUEC\n"
            "Kosten gesamt: {total_costs} aUEC\n"
            "Kostenerstattungen: {refunds}\n"
            "Gewinnanteil je Crew: {equal_share} aUEC\n"
            "Verteilt gesamt: {distributed_total} aUEC"
        ),
        "payout.proposal.cost_settled": (
            "\nSitzungskosten bereits abgerechnet (Sitzungen {sessions})"
        ),
        "payout.proposal.refinery_settled": (
            "\nRaffineriekosten bereits abgerechnet (Aufträge {jobs})"
        ),
        "payout.proposal.refund_line": "{name}: {amount} aUEC",
        "payout.proposal.refunds_none": "keine",
        "payout.msg.select_sale": "Bitte zuerst einen Verkauf wählen.",
        "payout.msg.calc_failed": (
            "Berechnung fehlgeschlagen:\n\n{error}"
        ),
        "payout.msg.cost_payer.title": "Kostenerstattung",
        "payout.msg.cost_payer_required": (
            "Bitte wählen, welches Crew-Mitglied "
            "die Missionskosten bezahlt hat."
        ),
        "payout.msg.invalid_amount": "Ungültiger Betrag für {member}.",
        "payout.msg.system_costs": (
            "SYSTEM-Kosten müssen einem Crew-Mitglied zugeordnet werden."
        ),
        "payout.msg.no_items": "Keine Auszahlungspositionen vorhanden.",
        "payout.msg.save_failed": "Auszahlung fehlgeschlagen:\n\n{error}",
        "payout.msg.saved.title": "Gespeichert",
        "payout.msg.saved.message": (
            "Auszahlung #{payout_id} wurde gespeichert."
        ),
        "payout.msg.no_selection": (
            "Bitte zuerst eine Auszahlung in der Historie auswählen."
        ),
        "payout.msg.void_confirm.title": "Auszahlung stornieren",
        "payout.msg.void_confirm.message": (
            "Auszahlung #{payout_id} wirklich stornieren?\n\n"
            "Der Verkauf erscheint wieder als offen "
            "und kann neu berechnet werden."
        ),
        "payout.msg.void_failed": (
            "Stornierung fehlgeschlagen:\n\n{error}"
        ),
        "payout.msg.voided.title": "Storniert",
        "payout.msg.voided.message": (
            "Auszahlung #{payout_id} wurde storniert."
        ),
        "dashboard.title": "SALVAGE-ÜBERSICHT",
        "dashboard.subtitle": "◆ BETRIEBSÜBERSICHT",
        "dashboard.window.title": "MobiGlas Salvage-Übersicht",
        "dashboard.button.presets": "Presets",
        "dashboard.button.customize": "Dashboard anpassen",
        "dashboard.button.customize_dirty": "Dashboard anpassen ●",
        "dashboard.button.save": "Speichern",
        "dashboard.button.cancel": "Abbrechen",
        "dashboard.nav.detached": "Übersicht ●",
        "dashboard.nav.embedded": "Übersicht ⧉",
        "dashboard.widget.status": "STATUS",
        "dashboard.widget.crew": "CREW",
        "dashboard.widget.session_crew": "CREW (Sitzung)",
        "dashboard.widget.refinery_jobs": "RAFFINERIE",
        "dashboard.widget.active_sessions": "AKTIV",
        "dashboard.widget.total_sessions": "SITZUNGEN",
        "dashboard.widget.sold_sessions": "VERKÄUFE",
        "dashboard.widget.ready_sessions": "LAGER (SCU)",
        "dashboard.widget.total_sales": "UMSATZ",
        "dashboard.widget.total_profit": "GEWINN",
        "dashboard.widget.session": "◆ AKTIVE SITZUNG",
        "dashboard.widget.refinery_stats": "◆ RAFFINERIE-STATISTIK",
        "dashboard.operations.title": "OFFENE AKTIONEN",
        "dashboard.alert.show": "Anzeigen",
        "dashboard.context.pin": "Anheften",
        "dashboard.context.unpin": "Loslösen",
        "dashboard.context.mode_follow": "Modus: Folgt Navigation",
        "dashboard.context.mode_pinned": "Modus: Angeheftet",
        "dashboard.context.nav_pinned": "Nav: {nav} (angeheftet)",
        "dashboard.context.overview.title": "◆ ÜBERSICHT",
        "dashboard.context.overview.subtitle": "Alle Bereiche · Nächste Aktionen",
        "dashboard.context.session.title": "◆ SESSION",
        "dashboard.context.session.subtitle": "Aktive Sitzung · Material & Fluss",
        "dashboard.context.refinery.title": "◆ RAFFINERIE",
        "dashboard.context.refinery.subtitle": "Offene Jobs · Abholung & Effizienz",
        "dashboard.context.storage.title": "◆ LAGER",
        "dashboard.context.storage.subtitle": "Bestand · Standorte · Inaktiv-Warnungen",
        "dashboard.context.sales.title": "◆ VERKAUF",
        "dashboard.context.sales.subtitle": "Verkaufsbereit · Offene Verkäufe",
        "dashboard.context.payout.title": "◆ AUSZAHLUNG",
        "dashboard.context.payout.subtitle": "Offene Payouts · Session-Zuordnung",
        "dashboard.context.history.title": "◆ HISTORIE",
        "dashboard.context.history.subtitle": "Verlauf · Statistik · Trends",
        "dashboard.context.session_scu": "SESSION-SCU",
        "dashboard.context.mission_costs_subtotal": (
            "Missionskosten: {mission_total} aUEC"
        ),
        "dashboard.context.refinery_costs_subtotal": (
            "Raffineriekosten: {refinery_total} aUEC"
        ),
        "dashboard.context.session_costs_total": (
            "Gesamtkosten Sitzung: {session_total} aUEC"
        ),
        "dashboard.context.locations": "STANDORTE",
        "dashboard.context.processes": "AKTUELLE PROZESSE",
        "dashboard.context.no_locations": "Keine Material-Standorte erfasst.",
        "dashboard.context.no_processes": "Keine aktiven Prozesse.",
        "dashboard.context.open": "OFFEN",
        "dashboard.context.avg_efficiency": "Ø EFFIZIENZ",
        "dashboard.context.active_jobs": "AKTIVE JOBS",
        "dashboard.context.total": "GESAMT",
        "dashboard.context.by_location": "NACH STANDORT",
        "dashboard.context.inventory": "BESTAND",
        "dashboard.context.storage_inventory_detail": (
            "{material} · {quantity} · von {source} · {location} · "
            "gelagert {stored_since}"
        ),
        "dashboard.context.no_inventory": "Kein Lagerbestand erfasst.",
        "dashboard.context.recent_moves": "LETZTE BEWEGUNGEN",
        "dashboard.context.pending": "OFFENE VERKÄUFE",
        "dashboard.context.pending_amount": "OFFEN (aUEC)",
        "dashboard.context.sale_items": "VERKAUFSBEREIT",
        "dashboard.context.open_payouts": "OFFENE PAYOUTS",
        "dashboard.context.open_total": "SUMME OFFEN",
        "dashboard.context.revenue_trend": "UMSATZ PRO MONAT",
        "dashboard.context.revenue_trend_hint": (
            "Verkaufserlös je Monat (letzte 6 Monate). "
            "Bei mehreren Monaten: Balkenlänge im Vergleich zum besten Monat."
        ),
        "dashboard.context.revenue_peak_month": "Bester Monat",
        "dashboard.context.revenue_vs_peak": "{pct} % vom besten Monat",
        "dashboard.context.revenue_trend_empty": "Noch keine Verkäufe erfasst.",
        "dashboard.context.recent_events": "LETZTE EREIGNISSE",
        "dashboard.context.refinery_station": "Raffinerie · {station}",
        "dashboard.context.refinery_job_detail": "Job #{job_id} · {status} · {scu} SCU",
        "dashboard.context.session_batches": "Session-Batches",
        "dashboard.context.session_materials": "Noch nicht zugeordnet",
        "dashboard.context.process_pickup": "Abholung · {station} · Job #{job_id}",
        "dashboard.context.process_running": "Läuft · {station} · Job #{job_id}",
        "dashboard.context.process_status": "Session-Workflow-Status",
        "dashboard.context.storage_event": "Lager-Ereignis",
        "dashboard.context.storage_event_detail": "{material} {delta} SCU · {location}",
        "dashboard.context.storage_deposit_event_detail": (
            "{material} {delta} SCU · von {source} · {location}"
        ),
        "dashboard.context.history_sale": "Verkauf abgeschlossen",
        "dashboard.context.history_sale_detail": "{location} · {amount} aUEC · {materials}",
        "dashboard.context.materials_sellable": "VERKAUFSFÄHIG",
        "dashboard.context.materials_raw": "ROHSTOFFE",
        "dashboard.context.overview.help": (
            "App-weite Zusammenfassung: dringende Aktionen nach Priorität, "
            "dazu Umsatz, Gewinn, offene Raffinerie-Jobs und verkaufbares Lager."
        ),
        "dashboard.context.session.help": (
            "Deine aktuelle oder letzte Sitzung: Workflow-Status, Crew, "
            "Missions- und Raffineriekosten, gesammeltes Material "
            "(verkaufsfähig vs. Rohstoff), Standorte und nächste Schritte."
        ),
        "dashboard.context.refinery.help": (
            "Laufende und abholbereite Raffinerie-Jobs, Input/Output in SCU "
            "sowie durchschnittliche Effizienz nach Material (abgeschlossene Jobs)."
        ),
        "dashboard.context.storage.help": (
            "Alle gelagerten Materialien mit Einlagerungszeit, "
            "Abholquelle, aktuellem Standort und Lagerdauer, "
            "dazu letzte Bewegungen."
        ),
        "dashboard.context.sales.help": (
            "Verkaufsbereites Material nach Standort, offene Verkäufe ohne "
            "Auszahlung und gesamt verkaufbare SCU."
        ),
        "dashboard.context.payout.help": (
            "Abgeschlossene Verkäufe ohne Auszahlung — nach Session mit Material, "
            "Menge, Betrag und Ort."
        ),
        "dashboard.context.history.help": (
            "Abgeschlossene Verkäufe im Zeitverlauf, Session-Zahlen, Gesamtumsatz, "
            "Monats-Trend und letzte Verkäufe."
        ),
        "dashboard.operations.hint": (
            "Nach Dringlichkeit sortiert — zuerst Auszahlung, "
            "dann Abholung und Verkauf."
        ),
        "dashboard.operations.empty": (
            "Keine offenen Aktionen. Session starten oder "
            "Bestand im Lager erfassen."
        ),
        "dashboard.operations.col.status": "Status",
        "dashboard.operations.col.material": "Material",
        "dashboard.operations.col.quantity": "Menge",
        "dashboard.operations.col.context": "Ort / Session",
        "dashboard.operations.col.detail": "Details",
        "dashboard.operations.summary.idle": "Inaktiv-Warnungen",
        "dashboard.next_action.all_clear": (
            "Keine dringenden Aktionen — alles erledigt."
        ),
        "dashboard.next_action.payout": (
            "Auszahlung offen — {material} ({session})"
        ),
        "dashboard.next_action.refinery_ready": (
            "Raffinerie abholbereit — {station}"
        ),
        "dashboard.next_action.sale": (
            "Verkaufsbereit — {material} · {location} · {when}"
        ),
        "dashboard.next_action.refinery_input": (
            "Bereit für Raffinerie — {material} · {location}"
        ),
        "dashboard.next_action.storage_idle": (
            "Bestand seit über {days} Tagen ohne Bewegung"
        ),
        "dashboard.action.payout_pending": "Auszahlung offen",
        "dashboard.action.refinery_ready": "Abholbereit",
        "dashboard.action.refinery_running": "Raffinerie läuft",
        "dashboard.action.refinery_material": "Raffinerie-Input",
        "dashboard.action.sale_ready": "Verkaufsbereit",
        "dashboard.action.refinery_input_ready": "Bereit für Raffinerie",
        "dashboard.readiness.line": "{material} · {status}",
        "dashboard.readiness.none": (
            "Kein Material verkaufs- oder raffineriebereit."
        ),
        "dashboard.readiness.separator": "  |  ",
        "dashboard.action.storage_idle": "Inaktiver Bestand",
        "dashboard.action.session": "Aktive Session",
        "dashboard.action.legacy_storage": "Globales Lager",
        "dashboard.action.detail.session": "Session · {session}",
        "dashboard.action.detail.job": "Job #{job_id}",
        "dashboard.action.detail.legacy": "Legacy-Bestand",
        "dashboard.action.detail.idle": "Lager prüfen",
        "dashboard.session.none": "KEINE SITZUNG",
        "dashboard.session.active": "AKTIVE SITZUNG",
        "dashboard.session.materials": "MATERIALIEN",
        "dashboard.label.ship": "Schiff",
        "dashboard.label.crew": "Crew",
        "dashboard.label.status": "Status",
        "dashboard.label.refinery": "Raffinerie",
        "dashboard.refinery_stats.title": "RAFFINERIE-STATISTIK",
        "dashboard.refinery_stats.empty": (
            "Noch keine abgeschlossenen Raffinerieaufträge."
        ),
        "dashboard.refinery_stats.empty_short": (
            "Noch keine abgeschlossenen Aufträge."
        ),
        "dashboard.refinery_stats.jobs": "Aufträge: {count}",
        "dashboard.refinery_stats.io": (
            "Input: {input_scu} SCU · Output: {output_scu} SCU"
        ),
        "dashboard.refinery_stats.efficiency": "Ø Effizienz: {value}",
        "dashboard.refinery_stats.by_material": "Nach Material:",
        "dashboard.refinery_stats.by_method": "Nach Methode:",
        "dashboard.refinery_stats.detail_line": (
            "  {label}: {efficiency} ({count}×)"
        ),
        "dashboard.refinery.open_suffix": " offen",
        "dashboard.catalog.title": "◆ WIDGET-KATALOG",
        "dashboard.catalog.hint": (
            "Widgets auf das Dashboard ziehen.\n"
            "Entfernen: × oder zurück hierher ziehen."
        ),
        "dashboard.catalog.drop": (
            "Ablage — Widget ablegen zum Entfernen"
        ),
        "dashboard.msg.no_user": "Kein Benutzer angemeldet.",
        "dashboard.msg.layout_saved": (
            "Dashboard-Layout wurde gespeichert."
        ),
        "dashboard.font_preview.section": "◆ VORSCHAU",
        "dashboard.font_preview.demo_title": "STATUS",
        "dashboard.font_preview.demo_value": "128 SCU",
        "dashboard.font_preview.hint": (
            "100 % = Standardgröße. Alle Dashboard-Texte skalieren einheitlich."
        ),
        "dashboard.preset.title": "DASHBOARD-PRESETS",
        "dashboard.preset.window_title": "Dashboard-Presets",
        "dashboard.preset.section.system": "◆ SYSTEM-VORLAGE",
        "dashboard.preset.section.custom": "◆ EIGENE PRESETS",
        "dashboard.preset.label.template": "Vorlage",
        "dashboard.preset.button.load_template": "Vorlage laden",
        "dashboard.preset.hint.max": (
            "Maximal {max} eigene Presets pro Benutzer."
        ),
        "dashboard.preset.label.name": "Preset-Name",
        "dashboard.preset.placeholder.name": "Name für neues Preset",
        "dashboard.preset.button.save_current": "Aktuelles speichern",
        "dashboard.preset.button.load_selected": "Auswahl laden",
        "dashboard.preset.button.delete": "Löschen",
        "dashboard.preset.button.close": "Schließen",
        "dashboard.preset.blank.label": "Leer",
        "dashboard.preset.blank.description": (
            "Keine Widgets — leeres Dashboard"
        ),
        "dashboard.preset.classic.label": "Classic",
        "dashboard.preset.classic.description": (
            "Alle Bereiche gleich gewichtet"
        ),
        "dashboard.preset.operations.label": "Operations",
        "dashboard.preset.operations.description": (
            "Fokus: aktive Session, Crew, Material"
        ),
        "dashboard.preset.refinery.label": "Refinery",
        "dashboard.preset.refinery.description": (
            "Fokus: Raffinerie-Jobs und Rohmaterial"
        ),
        "dashboard.preset.storage.label": "Storage",
        "dashboard.preset.storage.description": (
            "Fokus: Lager, Verkäufe, Gewinn"
        ),
        "dashboard.preset.msg.title": "Preset",
        "dashboard.preset.msg.name_required": (
            "Bitte einen Preset-Namen eingeben."
        ),
        "dashboard.preset.msg.no_layout": (
            "Kein Layout zum Speichern vorhanden."
        ),
        "dashboard.preset.msg.saved": "Preset „{name}“ wurde gespeichert.",
        "dashboard.preset.msg.select": "Bitte ein Preset auswählen.",
        "dashboard.preset.msg.load_failed": (
            "Preset konnte nicht geladen werden."
        ),
        "dashboard.preset.msg.delete_confirm.title": "Preset löschen",
        "dashboard.preset.msg.delete_confirm": (
            "Preset „{name}“ wirklich löschen?"
        ),
        "history.title": "HISTORIE",
        "history.section.sessions": "◆ ABGESCHLOSSENE SITZUNGEN",
        "history.section.sales": "◆ ALLE VERKÄUFE",
        "history.section.all_payouts": "◆ ALLE AUSZAHLUNGEN",
        "history.empty": "Noch keine Verkäufe erfasst.",
        "history.sessions.empty": (
            "Noch keine abgeschlossenen Sitzungen. "
            "Missionskosten erscheinen hier nach Raffinerie/Verkauf."
        ),
        "history.session.no": "Nr.",
        "history.session.ship": "Schiff",
        "history.session.status": "Status",
        "history.session.ended": "Beendet",
        "history.session.mission_costs": "Missionskosten",
        "history.session.total_costs": "Gesamtkosten",
        "history.session.mission_line": (
            "{amount} aUEC ({paid_by})"
        ),
        "history.session.no_missions": "Keine Missionskosten",
        "history.session.costs_total": (
            "Mission: {mission_total} aUEC · Gesamt: {session_total} aUEC"
        ),
        "common.ok": "OK",
        "common.cancel": "Abbrechen",
        "common.back": "Zurück",
        "common.continue": "Weiter",
        "common.logout": "Abmelden",
        "common.connecting": "Verbinde…",
        "common.save": "Speichern",
        "password.change.title": "Passwort ändern",
        "password.required.window_title": (
            "Erstanmeldung — Neues Passwort erforderlich"
        ),
        "password.required.frame_title": (
            "Erstanmeldung — Neues Passwort"
        ),
        "password.required.banner_title": "ERSTANMELDUNG",
        "password.required.banner": (
            "Du hast dich mit dem Standardpasswort angemeldet.\n\n"
            "Bevor du das Programm nutzen kannst, musst du "
            "jetzt ein eigenes Passwort setzen.\n\n"
            "Angemeldet als: {username}"
        ),
        "password.required.step": (
            "Schritt 1 von 1 — Neues Passwort wählen "
            "(mindestens 6 Zeichen)"
        ),
        "password.label.new": "Neues Passwort",
        "password.placeholder.new": "Neues Passwort eingeben",
        "password.label.confirm": "Passwort bestätigen",
        "password.placeholder.confirm": "Passwort wiederholen",
        "password.button.set_and_continue": (
            "Neues Passwort setzen und fortfahren"
        ),
        "password.msg.blocked.title": "Erstanmeldung",
        "password.msg.blocked": (
            "Ohne neues Passwort kann das Programm "
            "nicht gestartet werden.\n\n"
            "Bitte ein Passwort setzen."
        ),
        "password.msg.title": "Passwort",
        "password.msg.length": (
            "Das Passwort muss mindestens 6 Zeichen lang sein."
        ),
        "password.msg.mismatch": (
            "Die Passwörter stimmen nicht überein."
        ),
        "password.msg.required_success.title": (
            "Erstanmeldung abgeschlossen"
        ),
        "password.msg.required_success": (
            "Dein Passwort wurde gespeichert.\n\n"
            "Das Programm startet jetzt."
        ),
        "password.msg.changed": "Das Passwort wurde geändert.",
        "input.msg.title": "Eingabe",
        "input.msg.quantity_required": (
            "Bitte eine gültige Menge eingeben."
        ),
        "input.msg.number_required": (
            "Bitte eine gültige Zahl eingeben."
        ),
        "input.msg.range": (
            "Die Menge muss zwischen {minimum} und {maximum} SCU liegen."
        ),
        "network.assistant.title": "VERNETZUNG",
        "network.assistant.window_title": "Vernetzung",
        "network.assistant.subtitle": (
            "Allein spielen, als Host eine Crew einladen, "
            "oder mit einem Code beitreten."
        ),
        "network.assistant.mode.standalone": "Allein spielen",
        "network.assistant.mode.host": "Crew hosten",
        "network.assistant.mode.client": "Crew beitreten",
        "network.assistant.section.local": "◆ LOKAL",
        "network.assistant.local.info": (
            "Alle Daten bleiben auf diesem Rechner. "
            "Keine Crew-Verbindung nötig."
        ),
        "network.assistant.section.host": "◆ CREW EINLADEN",
        "network.assistant.host.info": (
            "Teile diesen Code mit deiner Crew. "
            "Sie brauchen nur den Salvage Tracker und den Code — "
            "keine IP, kein Router, keine Extra-Software."
        ),
        "network.assistant.button.copy_code": "Code kopieren",
        "network.assistant.copy.message": (
            "Code kopiert — z. B. in Discord schicken."
        ),
        "network.assistant.section.client": "◆ CREW BEITRETEN",
        "network.assistant.client.info": (
            "Code vom Host eingeben — oder die Einladung einfügen."
        ),
        "network.assistant.placeholder.code": "6-stelliger Code",
        "network.assistant.placeholder.name": "Dein Name (optional)",
        "network.assistant.label.code": "Beitrittscode",
        "network.assistant.label.display_name": "Anzeigename",
        "network.assistant.button.join": "Beitreten",
        "network.assistant.msg.join_title": "Beitritt",
        "network.assistant.msg.code_required": (
            "Bitte Beitrittscode eingeben."
        ),
        "network.quick_join.title": "CREW BEITRETEN",
        "network.quick_join.window_title": "Crew beitreten",
        "network.quick_join.hint": (
            "Gib den 6-stelligen Code vom Host ein — "
            "oder füge die Einladung ein."
        ),
        "network.quick_join.placeholder.code": "z. B. K7M2XP",
        "network.quick_join.placeholder.name": (
            "Dein Name in der Crew (optional)"
        ),
        "network.quick_join.label.code": "Beitrittscode",
        "network.quick_join.label.display_name": "Anzeigename",
        "network.quick_join.button.join": "Beitreten",
        "network.scenario.title.client": "◆ WO SPIELT IHR?",
        "network.scenario.title.host": "◆ WIE VERBINDEN SICH CLIENTS?",
        "network.scenario.label.type": "Verbindungsart",
        "network.scenario.label.invite_address": "Adresse für Einladung",
        "network.scenario.label.relay_address": "Relay-Adresse",
        "network.scenario.label.relay_port": "Relay-Port",
        "network.scenario.lan.label": "Gleiches WLAN / LAN",
        "network.scenario.relay.label": "Internet — Salvage-Relay (nur Code)",
        "network.scenario.internet.label": (
            "Internet — Crew-Einladung (Adresse + Code)"
        ),
        "network.scenario.router.label": (
            "Internet — Router manuell (Fallback)"
        ),
        "network.scenario.client_hint.lan": (
            "Ihr seid im gleichen Netzwerk. Trage die LAN-IP des Host-Rechners ein "
            "(z. B. 192.168.x.x — steht auf dem Host unter Einstellungen → Vernetzung)."
        ),
        "network.scenario.client_hint.relay": (
            "Nur Salvage Tracker nötig — keine extra Software, keine IP vom Host. "
            "Trage die Relay-Adresse (vom Host mitgeteilt) und den Beitrittscode ein. "
            "Der Host muss am Relay registriert sein (Einstellungen → Vernetzung)."
        ),
        "network.scenario.client_hint.internet": (
            "Der Host sendet dir eine Einladung (Adresse + Beitrittscode). "
            "Trage beides ein — kein Zusatzprogramm nötig."
        ),
        "network.scenario.client_hint.router": (
            "Fallback: Host hat Port 47890 am Router weitergeleitet. "
            "Externe Internet-Adresse eintragen (nicht 192.168.x.x)."
        ),
        "network.scenario.host_hint.lan": (
            "Clients im gleichen WLAN verbinden sich mit einer LAN-Adresse dieses "
            "Rechners und dem Beitrittscode. Test auf demselben PC: 127.0.0.1."
        ),
        "network.scenario.host_hint.relay": (
            "Host-Server starten und „Am Salvage-Relay registrieren“ aktivieren. "
            "Teile der Crew nur Relay-Adresse und Beitrittscode — keine IP nötig. "
            "Für Tests: Relay lokal starten (scripts/start_relay_server.py)."
        ),
        "network.scenario.host_hint.internet": (
            "Kopiere die Einladung an deine Crew. Optional: „Internet freigeben (UPnP)“ "
            "für automatische Portweiterleitung am Router."
        ),
        "network.scenario.host_hint.router": (
            "Am Router TCP-Port 47890 auf diesen PC weiterleiten. "
            "Externe IP abrufen und mit Code teilen."
        ),
        "network.scenario.placeholder.lan": "LAN-IP des Hosts, z. B. 192.168.1.10",
        "network.scenario.placeholder.relay": (
            "Relay-Adresse, z. B. relay.example.com"
        ),
        "network.scenario.placeholder.internet": (
            "Adresse aus der Host-Einladung"
        ),
        "network.scenario.placeholder.router": (
            "Externe IP des Hosts, z. B. 85.123.45.67"
        ),
        "network.scenario.host_placeholder.lan": "LAN-IP für die Crew",
        "network.scenario.host_placeholder.relay": (
            "Salvage-Relay, z. B. relay.example.com"
        ),
        "network.scenario.host_placeholder.internet": (
            "Erreichbare Adresse für die Einladung "
            "(externe IP oder LAN-IP)"
        ),
        "network.scenario.host_placeholder.router": (
            "Externe IP — „Externe IP abrufen“ oder vom Provider"
        ),
        "network.scenario.button.fetch_ip": "Externe IP abrufen",
        "network.scenario.button.fetch_ip_progress": "Rufe ab…",
        "network.scenario.button.copy_invite": "Einladung kopieren",
        "network.scenario.msg.fetch_ip_title": "Externe IP",
        "network.scenario.msg.fetch_ip_failed": (
            "Die externe IP konnte nicht abgerufen werden.\n"
            "Prüfe die Internetverbindung oder trage die IP "
            "manuell ein (Router-Statusseite oder Anbieter)."
        ),
        "network.scenario.msg.invite_title": "Einladung",
        "network.scenario.msg.relay_address_required": (
            "Bitte zuerst die Relay-Adresse eintragen."
        ),
        "network.scenario.msg.address_required": (
            "Bitte zuerst eine Adresse eintragen oder abrufen."
        ),
        "network.scenario.msg.join_code_missing": (
            "Beitrittscode fehlt — Host starten oder Code erzeugen."
        ),
        "network.scenario.msg.invite_copied": (
            "Einladungstext wurde kopiert.\n"
            "Sende ihn an deine Crew (Chat, Discord, …)."
        ),
        "network.error.connect_title": "Verbindung",
        "network.error.relay_address_required": (
            "Bitte Relay-Adresse eingeben."
        ),
        "network.error.host_address_required": (
            "Bitte Host-Adresse eingeben."
        ),
        "network.error.guest_code_required": (
            "Als Gast ist der Beitrittscode erforderlich."
        ),
        "network.error.credentials_required": (
            "Benutzername und Passwort erforderlich."
        ),
        "network.error.connection_failed": "Verbindung fehlgeschlagen",
        "network.error.connect_error": "Verbindungsfehler",
        "network.error.host_refused_hint": (
            "Der Host-Server läuft nicht oder lauscht "
            "nicht auf diesem Port. "
            "Host zuerst starten und einloggen, bis "
            "◆ HOST in der Leiste erscheint."
        ),
        "network.error.relay_failed": "Relay-Verbindung fehlgeschlagen",
        "network.error.relay_invalid_response": "Ungültige Relay-Antwort",
        "network.error.protocol_incompatible": "Protokollversion inkompatibel",
        "network.error.auth_failed": "Authentifizierung fehlgeschlagen",
        "network.error.invalid_join_code": "Ungültiger Beitrittscode",
        "network.error.login_failed": "Anmeldung fehlgeschlagen",
        "network.error.not_authenticated": "Nicht authentifiziert",
        "network.error.rpc_failed": "RPC fehlgeschlagen",
        "network.error.rpc_path_denied": "RPC-Pfad nicht erlaubt: {path}",
        "network.error.guest_no_permission": (
            "Gast hat keine Berechtigung für diese Aktion"
        ),
        "network.error.no_permission": "Keine Berechtigung",
        "network.error.write_not_allowed": (
            "Schreibzugriff nicht freigegeben"
        ),
        "network.guest.username": "Gast",
        "network.guest.role_name": "Gast (Netzwerk)",
        "admin.network.upnp.msg.lib_missing": (
            "UPnP-Bibliothek nicht installiert.\n\n"
            "Aktuelle Python-Version: {version}\n"
        ),
        "admin.network.upnp.msg.lib_missing_py314": (
            "Unter Python 3.14 gibt es noch kein fertiges "
            "miniupnpc-Wheel.\n"
            "Optional: Python 3.12/3.13 installieren und dort "
            "'pip install miniupnpc' ausführen,\n"
            "oder UPnP manuell am Router einrichten."
        ),
        "admin.network.upnp.msg.install_pip": (
            "Installation: pip install miniupnpc"
        ),
        "admin.network.upnp.msg.no_router": (
            "Kein UPnP-Router im Netzwerk gefunden."
        ),
        "admin.network.upnp.msg.success": (
            "Port {port} wurde per UPnP auf {host} weitergeleitet."
        ),
        "admin.network.upnp.msg.failed": "UPnP fehlgeschlagen: {error}",
        "recovery.title": "NOTFALL-WARTUNG",
        "recovery.window_title": "Notfall-Wartung",
        "recovery.subtitle": (
            "Der Super-Administrator hat keinen Zugriff auf "
            "den normalen Tracker-Betrieb. Hier kannst du "
            "Benutzer und Administratoren reparieren."
        ),
        "recovery.section.options": "Optionen",
        "recovery.status.admins": (
            "Aktive Organisations-Administratoren: {count}\n\n"
            "Wähle eine Wartungsaktion:"
        ),
        "recovery.button.create_admin": (
            "Organisations-Administrator anlegen"
        ),
        "recovery.button.reset_password": "Benutzer-Passwort zurücksetzen",
        "recovery.section.create_admin": "Administrator anlegen",
        "recovery.section.reset_password": "Passwort zurücksetzen",
        "recovery.create.hint": (
            "Rolle: {role} (fest)\n"
            "Der Benutzer muss sich beim ersten Login ein "
            "eigenes Passwort setzen."
        ),
        "recovery.reset.hint": (
            "Setzt das Passwort eines Organisations-Benutzers "
            "zurück. Beim nächsten Login muss ein neues Passwort "
            "gewählt werden."
        ),
        "recovery.button.create": "Administrator anlegen",
        "recovery.button.reset": "Passwort zurücksetzen",
        "recovery.msg.title": "Notfall-Wartung",
        "recovery.msg.admin_created": (
            "Administrator „{username}“ wurde angelegt."
        ),
        "recovery.msg.password_reset": (
            "Passwort für „{username}“ wurde zurückgesetzt."
        ),
        "recovery.msg.create_failed": (
            "Der Administrator konnte nicht angelegt werden."
        ),
        "recovery.msg.admin_created_detail": (
            "Administrator „{username}“ wurde angelegt.\n\n"
            "Melde dich danach mit diesem Benutzer an."
        ),
        "recovery.msg.password_reset_detail": (
            "Das Passwort für „{username}“ wurde zurückgesetzt.\n\n"
            "Beim nächsten Login muss ein neues Passwort "
            "gesetzt werden."
        ),
        "recovery.msg.superadmin_password_locked": (
            "Das Super-Administrator-Passwort kannst du "
            "nur über „Passwort ändern“ nach dem Login "
            "ändern — nicht hier."
        ),
        "recovery.msg.user_not_found": (
            "Benutzer „{username}“ nicht gefunden."
        ),
        "recovery.msg.user_create_failed": (
            "Der Benutzer konnte nicht angelegt werden. "
            "Der Name existiert möglicherweise bereits."
        ),
        "update.available.title": "Update verfügbar",
        "update.available.page_title": "UPDATE VERFÜGBAR",
        "update.available.installed": (
            "Aktuell installiert: {version}"
        ),
        "update.available.download": (
            "Download: {filename} ({size})"
        ),
        "update.available.version_line": (
            "{version} · Build {build} · {codename}"
        ),
        "update.available.notes_empty": (
            "Keine Release Notes verfügbar."
        ),
        "update.tab.de": "Deutsch",
        "update.tab.en": "English",
        "update.button.install": "Jetzt installieren",
        "update.button.later": "Später",
        "update.button.skip": "Diese Version überspringen",
        "update.download.title": "Update wird heruntergeladen",
        "update.download.page_title": "DOWNLOAD",
        "update.download.status": "{filename} wird geladen …",
        "update.download.indeterminate": "{mb} MB heruntergeladen …",
        "update.download.progress": "{received} / {total} ({percent} %)",
        "update.manager.dialog.title": "Updates",
        "update.manager.check_running": (
            "Es läuft bereits eine Update-Prüfung."
        ),
        "update.manager.check_failed": (
            "Update-Prüfung fehlgeschlagen:\n\n{error}"
        ),
        "update.manager.manifest_failed": (
            "Update-Manifest konnte nicht gelesen werden."
        ),
        "update.manager.up_to_date": (
            "Sie verwenden bereits die neueste Version.\n\n{version}"
        ),
        "update.manager.notify.title": "Neues Update verfügbar",
        "update.manager.notify.message": (
            "Version {version} (Build {build}) ist auf GitHub "
            "verfügbar.\n\n"
            "Möchten Sie die Update-Details anzeigen?"
        ),
        "update.manager.installer_unavailable": (
            "Die automatische Installation ist nur in der "
            "installierten Windows-Version verfügbar.\n\n"
            "Laden Sie das Update manuell herunter:\n{url}"
        ),
        "update.manager.network_active.title": "Netzwerk aktiv",
        "update.manager.network_active.continue": (
            "{warning}\n\nTrotzdem fortfahren?"
        ),
        "update.manager.install_confirm.title": "Update installieren",
        "update.manager.install_confirm.message": (
            "Das Update wird zuerst heruntergeladen.\n\n"
            "Installationsordner:\n{install_dir}\n\n"
            "Erkannt über: {source_label}\n\n"
            "Fortfahren?"
        ),
        "update.manager.install_ready.title": "Bereit zur Installation",
        "update.manager.install_ready.message": (
            "Das Update wurde erfolgreich heruntergeladen.\n\n"
            "Version: {version} (Build {build})\n"
            "Installationsordner:\n{install_dir}\n\n"
            "Erkannt über: {source_label}\n\n"
            "Die App wird geschlossen und der Setup-Assistent "
            "installiert das Update sichtbar. "
            "Die aktualisierte Version startet danach automatisch."
        ),
        "update.manager.install_path.unknown": (
            "Keine bestehende Installation gefunden. "
            "Es wird der Standardpfad verwendet:\n{install_dir}"
        ),
        "update.install_path.source.explicit": "Manuelle Auswahl",
        "update.install_path.source.registry": "Windows-Registry",
        "update.install_path.source.manifest": "Installations-Manifest",
        "update.install_path.source.running_exe": "Laufende Anwendung",
        "update.install_path.source.default": "Standardpfad",
        "update.download.install_path": (
            "Installationsordner: {install_dir} ({source_label})"
        ),
        "update.manager.download.title": "Download",
        "update.manager.download.failed": (
            "Das Update konnte nicht heruntergeladen werden:\n\n{error}"
        ),
        "update.manager.install.title": "Installation",
        "update.warning.host_active": (
            "Der Host-Modus ist aktiv. Clients sollten die Verbindung "
            "trennen, bevor ein Update installiert wird."
        ),
        "update.warning.client_connected": (
            "Sie sind als Client mit einem Host verbunden. "
            "Trennen Sie die Verbindung vor dem Update."
        ),
        "update.error.download_failed": "Download fehlgeschlagen: {error}",
        "update.error.checksum_failed": (
            "Die heruntergeladene Datei ist beschädigt "
            "(SHA256-Prüfsumme stimmt nicht)."
        ),
        "update.error.installer_frozen_only": (
            "Updates können nur in der installierten Windows-App "
            "automatisch installiert werden."
        ),
        "changelog.title": "Änderungsprotokoll",
        "changelog.page_title": "{app_name} – PATCHNOTES & ROADMAP",
        "changelog.tab.patchnotes": "Patchnotes",
        "changelog.tab.roadmap": "Roadmap",
        "edition.locked.title": "{edition} erforderlich",
        "edition.teaser.badge": "◆ SC SALVAGE TRACKER - {edition}",
        "edition.button.learn_more": "Mehr zur {edition}",
        "edition.info.footer": (
            "Die SOLO Version bleibt für Einzelspieler kostenlos. "
            "CREW und ORGA erweitern das Programm um Mehrspieler "
            "und Organisation — ohne Solo-Features zu entfernen.\n\n"
            "Supporter-Keys kannst du unter Einstellungen → "
            "Unterstützen einlösen."
        ),
        "edition.feature.network.host": "Crew hosten",
        "edition.feature.network.client": "Crew beitreten",
        "edition.feature.network.crew_edition": "Vernetzung (CREW Edition)",
        "edition.feature.org.module": "Organisations-Verwaltung",
        "edition.teaser.crew": (
            "Mit Freunden Salvage tracken: ein Host startet die Session, "
            "die Crew tritt per Code bei — alle arbeiten an einer "
            "gemeinsamen Datenbank. Verfügbar in der "
            "SC Salvage Tracker - CREW Version."
        ),
        "edition.teaser.orga": (
            "Organisationen, mehrere Teams und erweiterte Verwaltung — "
            "geplant für die SC Salvage Tracker - ORGA Version."
        ),
        "edition.teaser.fallback": (
            "Verfügbar in der SC Salvage Tracker - {edition}."
        ),
        "edition.key.invalid": "Der Supporter-Key ist ungültig.",
        "edition.key.unlocked": (
            "Freigeschaltet: {edition}. "
            "Vernetzung ist jetzt verfügbar."
        ),
        "edition.key.stored_ceiling": (
            "Key gespeichert ({edition}), "
            "diese Installation bleibt bei {ceiling}."
        ),
        "common.discard": "Verwerfen",
        "common.apply": "Anwenden",
        "common.retry": "Wiederholen",
        "common.ignore": "Ignorieren",
        "common.abort": "Abbrechen",
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


def _has_translation(key: str) -> bool:
    lang = _current_language
    table = _TRANSLATIONS.get(lang, _TRANSLATIONS[DEFAULT_LANGUAGE])
    if key in table:
        return True
    return key in _TRANSLATIONS[DEFAULT_LANGUAGE]


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


def tr_setup(key: str, *, db=None, **kwargs) -> str:
    """Setup copy for the active edition (SOLO uses ``{key}.solo`` when defined)."""
    from config.editions import EDITION_SOLO, effective_edition

    if effective_edition(db) == EDITION_SOLO:
        solo_key = f"{key}.solo"
        if _has_translation(solo_key):
            return tr(solo_key, **kwargs)
    return tr(key, **kwargs)


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


def format_scu(value) -> str:
    """SCU ohne Nachkommastellen (3 SCU statt 3,0 SCU)."""
    return f"{format_number(value, 0)} SCU"


def format_scu_delta(value) -> str:
    """SCU-Delta mit Vorzeichen, ohne Nachkommastellen."""
    amount = float(value or 0)
    if amount > 0:
        return f"+{format_number(amount, 0)}"
    return format_number(amount, 0)


def status_label(status: str) -> str:
    key = f"status.{status}"
    translated = tr(key, default=status)
    return translated


def theme_option_label(category: str, key: str, fallback: str = "") -> str:
    return tr(f"theme.{category}.{key}", default=fallback)


def feature_label(feature_id: str) -> str:
    from config.editions import FEATURE_LABELS

    return tr(
        f"edition.feature.{feature_id}",
        default=FEATURE_LABELS.get(feature_id, feature_id),
    )


def permission_label(perm: str) -> str:
    from config.permissions import PERMISSION_LABELS

    return tr(f"permission.{perm}", default=PERMISSION_LABELS.get(perm, perm))


def permission_group_label(group_key: str) -> str:
    return tr(f"permission.group.{group_key}")
