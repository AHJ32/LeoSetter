; ─────────────────────────────────────────────────────────────────────────────
; LeoSetter – Inno Setup Installer Script
; Compile with Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "LeoSetter"
#define AppVersion   "1.0.0"
#define AppPublisher "AHJ32"
#define AppURL       "https://github.com/AHJ32/LeoSetter"
#define AppExeName   "LeoSetter.exe"
#define AppIcon      "assets\LeoSetter.ico"

[Setup]
AppId={{E5A3B2C1-1234-5678-ABCD-9F0E1D2C3B4A}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=no
; Output
OutputDir=installer_output
OutputBaseFilename=LeoSetterSetup
SetupIconFile={#AppIcon}
WizardStyle=modern
WizardSizePercent=120
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Require Windows 10 or newer
MinVersion=10.0
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
; Uninstaller
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
; Both tasks are checked by default
Name: "desktopicon";   Description: "Create a &desktop shortcut";  GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "startmenuicon"; Description: "Add to &Start Menu folder";   GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; The single-file EXE produced by PyInstaller
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut (created only if task selected)
Name: "{group}\{#AppName}";                         Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon
Name: "{group}\Uninstall {#AppName}";               Filename: "{uninstallexe}";      Tasks: startmenuicon
; Desktop shortcut (created only if task selected)
Name: "{autodesktop}\{#AppName}";                   Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch the app immediately after installation
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove any settings / cache written by the app during use
Type: filesandordirs; Name: "{localappdata}\{#AppName}"
