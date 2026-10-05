#define MyAppName "SAP FX Control Center"
#define MyAppVersion "5.0.0"
#define MyAppPublisher "SAP FX Control Center Community"
#ifndef SourceDir
  #define SourceDir "..\..\dist\windows-package"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist\installer"
#endif
[Setup]
AppId={{F85D1C86-B307-4E9B-8F8B-5F27F13CE5C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\SAPFXControlCenter
DefaultGroupName=SAP FX Control Center
OutputDir={#OutputDir}
OutputBaseFilename=SAP-FX-Control-Center-V5-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\SAP FX Control Center"; Filename: "{app}\scripts\windows\start-v5.cmd"; WorkingDir: "{app}"
Name: "{autodesktop}\SAP FX Control Center"; Filename: "{app}\scripts\windows\start-v5.cmd"; WorkingDir: "{app}"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
[Run]
Filename: "{app}\scripts\windows\start-v5.cmd"; Description: "Abrir SAP FX Control Center"; Flags: postinstall nowait skipifsilent
