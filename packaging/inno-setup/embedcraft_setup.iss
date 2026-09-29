; Inno Setup 6 Script for EmbedCraft RAG Studio
; Provides clean user-level Windows installation without admin privileges requirement.

#define MyAppName "EmbedCraft RAG Studio"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "David Caro"
#define MyAppURL "https://github.com/davidcaroo/embedcraft-rag-studio"
#define MyAppExeName "EmbedCraft.exe"
#define MyCliExeName "embedcraft.exe"

[Setup]
AppId={{9F82A0E3-55D4-4B4B-91E2-A23F7E3B5C91}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={localappdata}\Programs\EmbedCraft
DisableProgramGroupPage=yes
LicenseFile=..\..\LICENSE
PrivilegesRequired=lowest
OutputBaseFilename=EmbedCraft-RAG-Studio-Setup-v{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
ChangesEnvironment=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "addtopath"; Description: "Añadir la CLI embedcraft al PATH de usuario"; GroupDescription: "Configuración del Sistema:"

[Files]
; Copy all files from PyInstaller dist/EmbedCraft-Studio directory
Source: "..\..\dist\EmbedCraft-Studio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\EmbedCraft CLI"; Filename: "{cmd}"; Parameters: "/K ""{app}\{#MyCliExeName}"" --help"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Add application directory to user PATH if task is selected
Root: HKCU; Subkey: "Environment"; \
    ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; \
    Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Code]
function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', OrigPath)
  then begin
    Result := True;
    exit;
  end;
  { Look for the path with leading and trailing semicolons }
  Result := Pos(';' + Param + ';', ';' + OrigPath + ';') = 0;
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
