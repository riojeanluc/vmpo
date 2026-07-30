#define MyAppName "Cleaner App"
#define MyAppVersion "0.1.0"
#define MyAppExeName "cleaner_app.exe"

[Setup]
AppId={{6F2B0F1E-2B7B-4C2C-9C2A-6E9C6C2D6B1A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=CleanerAppSetup
OutputDir=output
Compression=lzma
SolidCompression=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Files]
Source: "..\cleaner\dist\cleaner_app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "cleaner_app_scan.cmd"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Analyser (scan)"; Filename: "{app}\cleaner_app_scan.cmd"; WorkingDir: "{app}"
Name: "{group}\Dossier d'installation"; Filename: "{app}"
Name: "{group}\Désinstaller {#MyAppName}"; Filename: "{uninstallexe}"
