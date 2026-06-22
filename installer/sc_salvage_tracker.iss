; SC Salvage Tracker — Custom Setup (Launcher Polish · Inno Setup 6.7+)
; Build: powershell -ExecutionPolicy Bypass -File installer\build_installer.ps1

#ifndef MyAppVersion
  #define MyAppVersion "0.14.1 Alpha"
#endif

#ifndef MyAppVersionFile
  #define MyAppVersionFile "0.14.1"
#endif

#ifndef MyAppVersionInfo
  #define MyAppVersionInfo "0.14.1.0"
#endif

#ifndef MyAppBuild
  #define MyAppBuild "2026.06"
#endif

#ifndef MyAppCodename
  #define MyAppCodename "Launcher Polish"
#endif

#ifndef InstallerOutputDir
  #define InstallerOutputDir "..\..\..\Release\installer"
#endif

#define MyAppName "SC Salvage Tracker"
#define MyAppPublisher "Christian · Xan-Gan-Du"
#define MyAppExeName "SC_Salvage_Tracker.exe"
#define MyAppURL "https://github.com/"

[Setup]
AppId={{A7C3E9F1-2B4D-4E8A-9F1C-6D5E8A2B4C7F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir={#InstallerOutputDir}
OutputBaseFilename=SC_Salvage_Tracker_Setup_{#MyAppVersionFile}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=classic dark hidebevels includetitlebar
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
MinVersion=10.0
ShowLanguageDialog=no
DisableWelcomePage=no
DisableFinishedPage=no
DisableReadyPage=no
SetupLogging=yes
SetupIconFile=assets\app_icon.ico
VersionInfoVersion={#MyAppVersionInfo}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=SC Salvage Tracker — Custom Setup
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersionInfo}

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[CustomMessages]
german.WelcomeLabel2=Willkommen beim SC Salvage Tracker Setup.
german.SelectDirLabel3=Der Salvage Tracker wird in folgenden Ordner installiert:
german.SelectDirBrowseLabel=Klicke auf Weiter, um fortzufahren — oder auf Durchsuchen, um einen anderen Ordner zu wählen.
german.DiskSpaceMBLabel=Mindestens [mb] MB freier Speicherplatz erforderlich.
german.ButtonBrowse=DURCHSUCHEN …
german.ReadyLabel1=Der Salvage Tracker ist bereit zur Installation.
german.ReadyLabel2a=Klicke auf Installieren, um fortzufahren — oder auf Zurück, um Einstellungen zu prüfen.
german.ReadyLabel2b=Klicke auf Installieren, um fortzufahren.
german.InstallingLabel=Bitte warten — der Salvage Tracker wird installiert …
german.FinishedLabel=Der Salvage Tracker wurde installiert. Starte die Anwendung über das Startmenü oder die Desktop-Verknüpfung.
german.SelectTasksLabel2=Wähle optionale Verknüpfungen und den Start nach der Installation.
german.BrowseDialogTitle=Installationsordner wählen
german.BrowseDialogLabel=Wähle einen Ordner und klicke auf OK.
german.ClickNext=Klicke auf Weiter, um fortzufahren — oder auf Abbrechen, um das Setup zu beenden.

[Tasks]
Name: "desktopicon"; Description: "Desktop-Verknüpfung erstellen"; GroupDescription: "Zusätzliche Optionen:"; Flags: unchecked
Name: "launchapp"; Description: "SC Salvage Tracker nach der Installation starten"; GroupDescription: "Nach der Installation:"; Flags: checkedonce

[Files]
Source: "..\..\..\Release\app\SC_Salvage_Tracker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\install_bg.png"; Flags: dontcopy

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Comment: "SC Salvage Tracker — Salvage-Operationen"
Name: "{group}\{#MyAppName} deinstallieren"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{#MyAppName} starten"; Flags: nowait postinstall skipifsilent; Tasks: launchapp

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\SC Salvage Tracker\logs"

[Code]
#include "mobiglas_wizard.inc"
