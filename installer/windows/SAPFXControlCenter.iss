#define MyAppName "Atas"
#define MyAppVersion "5.0.0"
#define MyAppPublisher "LORDMANUEL"
#define MyAppURL "https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web"
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
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\Atas
DefaultGroupName=Atas
OutputDir={#OutputDir}
OutputBaseFilename=Atas-V5-Setup-x64
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern
[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Atas"; Filename: "{app}\scripts\windows\start-atas.cmd"; WorkingDir: "{app}"
Name: "{autodesktop}\Atas"; Filename: "{app}\scripts\windows\start-atas.cmd"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{group}\GitHub de LORDMANUEL"; Filename: "https://github.com/LORDMANUEL/tasa-cambio-sap-por-service-layer-web"
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
[Run]
Filename: "{app}\scripts\windows\start-atas.cmd"; Description: "Abrir Atas"; Flags: postinstall nowait skipifsilent
