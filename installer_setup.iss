; Script de Inno Setup para FocuzVoz (Optimizado para Accesibilidad)
[Setup]
AppId={{C1B79E10-6C2D-4EBD-8B39-44F4E4EF4AC4}}
AppName=FocuzVoz
AppVersion=2.1
AppPublisher=Dario7-ux
DefaultDirName={localappdata}\FocuzVoz
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=Instalador_FocuzVoz_2.2
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "c:\Servidores\Lectura_FocuzVoz\FocuzVoz2.1\dist\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\FocuzVoz"; Filename: "{app}\run_app.exe"
Name: "{autodesktop}\FocuzVoz"; Filename: "{app}\run_app.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\run_app.exe"; Description: "{cm:LaunchProgram,FocuzVoz}"; Flags: nowait postinstall skipifsilent