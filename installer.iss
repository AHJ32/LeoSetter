; ─────────────────────────────────────────────────────────────────────────────
; LeoSetter – Inno Setup Installer Script
; Compile with Inno Setup 6.x  https://jrsoftware.org/isinfo.php
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

; Installation directory
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=no

; ── Output ────────────────────────────────────────────────────────────────────
OutputDir=installer_output
OutputBaseFilename=LeoSetterSetup
SetupIconFile={#AppIcon}

; ── Wizard appearance ─────────────────────────────────────────────────────────
WizardStyle=modern
WizardSizePercent=120

; ── Compression ───────────────────────────────────────────────────────────────
Compression=lzma2/ultra64
SolidCompression=yes

; ── System requirements ───────────────────────────────────────────────────────
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; ── Privileges ────────────────────────────────────────────────────────────────
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; ── Uninstaller ───────────────────────────────────────────────────────────────
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

; ── Welcome page text ─────────────────────────────────────────────────────────
; (Inno Setup uses WizardSmallImageFile / WizardImageFile for branding,
;  and the built-in welcome text is set via the [Messages] or [CustomMessages] section.)

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%nLeoSetter is a dark-themed desktop application for batch editing image metadata. Everything you need — including Python, all libraries, and ExifTool — is bundled inside this installer.%n%nClick Next to continue.

[Tasks]
; Both shortcuts are checked by default
Name: "desktopicon";   Description: "Create a &desktop shortcut";     GroupDescription: "Additional shortcuts:"; Flags: checkedonce
Name: "startmenuicon"; Description: "Add to &Start Menu folder";      GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
; The single self-contained EXE produced by PyInstaller
Source: "dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcuts
Name: "{group}\{#AppName}";               Filename: "{app}\{#AppExeName}"; Tasks: startmenuicon
Name: "{group}\Uninstall {#AppName}";     Filename: "{uninstallexe}";      Tasks: startmenuicon
; Desktop shortcut
Name: "{autodesktop}\{#AppName}";         Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Offer to launch immediately after installation
Filename: "{app}\{#AppExeName}"; \
  Description: "Launch {#AppName} now"; \
  Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove any per-user settings or cache the app wrote during use
Type: filesandordirs; Name: "{localappdata}\{#AppName}"

[Code]
// ── Progress feedback during extraction ────────────────────────────────────
// Shows a status label on the Installing page while PyInstaller's bootloader
// unpacks the embedded archive in the background.
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
  begin
    WizardForm.StatusLabel.Caption := 'Preparing LeoSetter — this may take a moment...';
  end;
end;
