; Inno Setup script for NoteApp.
;
; Build on Windows:
;   1. python -m venv .venv && .venv\Scripts\activate
;   2. pip install -r requirements.txt
;   3. pyinstaller packaging\noteapp.spec
;      (produces dist\NoteApp\NoteApp.exe + _internal\)
;   4. Compile this script with Inno Setup:
;        iscc packaging\windows\noteapp.iss
;      or open it in the Inno Setup Compiler GUI and click Compile.
;
; Output: dist\NoteApp-Setup-<version>.exe

#define MyAppName "NoteApp"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Sandeep Biswas"
#define MyAppExeName "NoteApp.exe"
#define MyDistDir "..\..\dist\NoteApp"
#define MyIconFile "..\..\resources\icons\icon.ico"

[Setup]
AppId={{E004FDF0-0723-4AA6-B3CC-D3F090B751B9}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\dist
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile={#MyIconFile}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#MyDistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"