; Script de Inno Setup para FocuzVoz (Optimizado para Accesibilidad)
[Setup]
AppId={{C1B79E10-6C2D-4EBD-8B39-44F4E4EF4AC4}}
AppName=FocuzVoz
AppVersion=3.0
AppPublisher=Dario7-ux
DefaultDirName={localappdata}\FocuzVoz
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=Instalador_FocuzVoz_3.0
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "startup"; Description: "Ejecutar FocuzVoz al iniciar Windows"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FocuzVoz"; Filename: "{app}\FocuzVoz.exe"
Name: "{autodesktop}\FocuzVoz"; Filename: "{app}\FocuzVoz.exe"; Tasks: desktopicon
Name: "{userstartup}\FocuzVoz"; Filename: "{app}\FocuzVoz.exe"; Tasks: startup

[Run]
Filename: "{app}\FocuzVoz.exe"; Description: "{cm:LaunchProgram,FocuzVoz}"; Flags: nowait postinstall skipifsilent