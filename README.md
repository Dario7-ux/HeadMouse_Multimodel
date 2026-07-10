# FocuzVoz: Software bimodal de control computacional mediante gestos y voz offline

**FocuzVoz** es una herramienta avanzada de tecnología de asistencia que permite el control total y bimodal del ordenador de forma alternativa mediante el movimiento de la cabeza, expresiones/gestos faciales y comandos de voz en español totalmente fuera de línea (offline). 

Esta aplicación ha sido diseñada con altos estándares de accesibilidad para ayudar a personas con discapacidades motoras graves o movilidad reducida a utilizar sistemas operativos Windows con total autonomía, privacidad y comodidad.

---

## 🚀 Descarga e Instalación

### Opción 1: Ejecutable Standalone (Instalación Rápida)
Si no deseas configurar un entorno de desarrollo de Python, puedes descargar el instalador compilado que no requiere privilegios de administrador para facilitar el acceso a cualquier usuario:

1. Descarga el instalador desde la [Sección de Releases](https://github.com/Dario7-ux/HeadMouse_Multimodel/releases).
2. Ejecuta `Instalador_FocuzVoz_v3.0.exe`.
3. Sigue los sencillos pasos del asistente. El instalador creará un acceso directo en tu escritorio y ejecutará la aplicación de inmediato al finalizar.

---

### Opción 2: Entorno de Desarrollo (Python)
Para desarrolladores o personalizaciones del código fuente, el sistema funciona sobre entornos Windows y requiere **Python 3.9**.

#### 1. Clonar el repositorio
```bash
git clone https://github.com/Dario7-ux/HeadMouse_Multimodel.git
cd HeadMouse_Multimodel
```

#### 2. Configuración Automatizada de Vosk y Dependencias
El sistema de reconocimiento de voz de FocuzVoz utiliza **Vosk**, lo que permite transcribir voz y ejecutar comandos de forma 100% local, privada y sin conexión a internet. Hemos desarrollado un script automatizado que instala todos los requisitos del sistema y descarga el modelo en español:

```bash
python setup_vosk.py
```

*Este script hará lo siguiente por ti:*
- Instalará todas las librerías necesarias especificadas en `requirements.txt` (incluyendo `customtkinter`, `mediapipe`, `vosk`, `pyaudio`, `pyttsx3`, `pyautogui`, `PyDirectInput` y `pywin32`).
- Descargará de forma segura el modelo acústico en español (`vosk-model-es-0.42`) y lo extraerá automáticamente en la ruta correspondiente (`assets/models/vosk-model-es-0.42/`).
- Validará la integridad de la instalación física.

*(Opcional) Si la descarga automática falla debido a límites de tu red local, puedes descargar el modelo `.zip` manualmente desde la [Página Oficial de Vosk](https://alphacephei.com/vosk/models), buscar `vosk-model-es-0.42` y descomprimirlo en `assets/models/vosk-model-es-0.42/`.*

#### 3. Ejecutar la aplicación
Una vez configurado con éxito, inicia el programa con:
```bash
python run_app.py
```

---

## ✨ Características Principales

FocuzVoz se compone de una arquitectura premium de **5 capas lógicas** que garantizan un rendimiento superior:

1. **Rastreo Facial Ultrapreciso (MediaPipe Face Mesh)**: Utiliza la cámara web nativa (a través de OpenCV a 30/60 FPS) para capturar la malla facial tridimensional del usuario con 478 puntos clave en tiempo real, rastreando las coordenadas `(X, Y)` de la nariz para el guiado del cursor.
2. **Estabilización Inteligente (Filtro 1 Euro)**: Procesa las coordenadas del movimiento facial empleando el algoritmo dinámico adaptativo **One Euro Filter** (`src/utils/one_euro_filter.py`). Si mueves la cabeza lentamente, el filtro suprime por completo el temblor natural (*jitter*) permitiendo clics de precisión milimétrica; si realizas un movimiento rápido, reduce el suavizado para evitar retrasos (*lag*).
3. **Control Anti-Midas Touch (FacialEventManager)**: Previene activaciones o clics involuntarios producidos por gestos cotidianos o pestañeos naturales. Aplica filtros temporales de permanencia (**Dwell Time** ≥ 150 ms) y tiempos de bloqueo preventivo (**Cooldown** = 350 ms) antes de disparar un evento de teclado o ratón.
4. **Reconocimiento de Voz 100% Offline (Vosk)**: Transcribe voz localmente garantizando total privacidad de datos. Permite dictar texto directo carácter por carácter en cualquier campo activo del sistema operativo Windows empleando la simulación por hardware de **Pynput**.
5. **Base de Datos Integrada (SQLite3)**: Centraliza la persistencia relacional en `configs/focuzvoz.db`. Registra automáticamente la telemetría detallada de eventos científicos para análisis de usabilidad (tiempos de uso, marcas temporales exactas, coordenadas de cursor y eficiencia de clics/voz), además de guardar los perfiles de calibración del usuario.

---

## 🗣️ Comandos de Voz Soportados (Español)

El sistema está permanentemente a la escucha del comando de activación o palabra clave (Wake Word): **"focuz"**. Una vez activo, puedes pronunciar los siguientes comandos nativos:

| Categoría | Comando de Voz | Acción Ejecutada |
| :--- | :--- | :--- |
| **Control Facial** | `"mover"` / `"activar cursor"` / `"cursor on"` | Activa el control del puntero mediante el movimiento de la cabeza |
| | `"quieto"` / `"desactivar cursor"` / `"cursor off"` | Pausa el control del puntero en pantalla |
| **Escritura y Dictado** | `"escribir"` / `"activar voz"` / `"voz up"` | Habilita el modo de dictado continuo (inyección de texto en foco activo) |
| | `"silencio"` / `"desactivar voz"` / `"voz off"` | Desactiva el modo de dictado de texto |
| **Edición de Texto** | `"borrar"` / `"eliminar"` / `"deshacer"` | Elimina por teclado simulado el último segmento/palabra escrita |
| | `"borrar todo"` / `"limpiar"` | Realiza un `Ctrl + A` seguido de `Backspace` para limpiar la caja activa |
| **Analítica Científica** | `"focusvoz go"` | Inicia una sesión de telemetría y grabación de usabilidad |
| | `"focusvoz finish"` | Detiene y guarda asíncronamente los logs analíticos en SQLite |

---

## 🛠️ Archivos de Configuración (JSON)

Las configuraciones por defecto del software se definen en el directorio `configs/default/`:

- **[`cursor.json`](configs/default/cursor.json)**:
  Contiene los multiplicadores de velocidad física del ratón en las 4 direcciones (`spd_up`, `spd_down`, `spd_left`, `spd_right`), suavizado del puntero, delays de activación del trigger, habilitación de la aceleración del ratón y el uso de la matriz de transformación.
- **[`mouse_bindings.json`](configs/default/mouse_bindings.json)** y **[`keyboard_bindings.json`](configs/default/keyboard_bindings.json)**:
  Mapean expresiones faciales de la lista de 52 blendshapes faciales a clics de ratón (`left`, `right`, `middle`) o teclas específicas. La estructura sigue este patrón:
  ```json
  "nombre_gesto": ["dispositivo", "accion", "umbral", "tipo_disparo"]
  ```
  *(Por ejemplo, asociar guiño izquierdo a clic de ratón izquierdo con umbral 0.65 de activación).*
- **[`voice.json`](configs/default/voice.json)**:
  Define los parámetros del motor Vosk, ID del micrófono físico activo, sensibilidad de recepción, retroalimentación auditiva interactiva y si la confirmación de comandos es requerida.

---

## 📦 Compilación y Distribución

Si deseas compilar la aplicación para generar un ejecutable redistribuible:

#### 1. PyInstaller standalone
Utiliza el script de empaquetado optimizado para agrupar todas las librerías nativas, modelos de MediaPipe y recursos estáticos:
```bash
pyinstaller build.spec
```
Esto creará el directorio ejecutable portable completo en `dist/FocuzVoz/`.

#### 2. Compilar Instalador Accesible
Abre el archivo **[`installer_setup.iss`](installer_setup.iss)** usando el compilador **Inno Setup** en Windows y compílalo. Generará el instalador autoejecutable ligero `Instalador_FocuzVoz_v2.1.exe` en la carpeta `dist_installer/`.

---

## 🤝 Soporte y Contribuciones

Para reportar problemas técnicos o proponer mejoras de accesibilidad:
1. Revisa el registro en tiempo real de la aplicación en `log.txt`.
2. Asegúrate de ejecutar `setup_vosk.py` antes de iniciar para instalar el modelo de voz.
3. Para cualquier duda, abre un Issue en el repositorio oficial.

*FocuzVoz 2.1 — Diseñado para derribar barreras y potenciar la accesibilidad digital.* 🌟
