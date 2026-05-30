; Script de Inno Setup para FocuzVoz (Optimizado para Accesibilidad)
#define MyAppName "FocuzVoz"
#define MyAppVersion "2.1"
#define MyAppPublisher "Dario7-ux"
#define MyAppExeName "run_app.exe"

[Setup]
AppId={{C1B79E10-6C2D-4EBD-8B39-44F4E4EF4AC4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\{#MyAppName}
DisableProgramGroupPage=yes
; MUY IMPORTANTE: "lowest" evita que pida permisos de Administrador.
; Cualquier persona con discapacidad o baja experiencia podrá instalarlo sin contraseñas de sistema.
PrivilegesRequired=lowest
OutputDir=dist_installer
OutputBaseFilename=Instalador_FocuzVoz_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
; Seleccionamos por defecto crear el acceso directo en el escritorio para que no tengan que configurar nada
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Copia todos los archivos compilados de tu carpeta dist/FocuzVoz
Source: "c:\Servidores\Lectura_FocuzVoz\FocuzVoz2.1\dist\FocuzVoz\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Crea los accesos directos en el menú inicio y en el escritorio
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Ofrece ejecutar la aplicación inmediatamente al terminar de instalar
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
