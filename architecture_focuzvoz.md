# Arquitectura del Sistema - FocuzVoz 0.2

Este documento describe de manera formal y detallada la arquitectura lógica y física de **FocuzVoz 0.2**. Explica técnicamente cómo interactúan, se comunican y se coordinan las diferentes herramientas, APIs, bibliotecas de simulación de hardware, filtros y motores de bases de datos relacionales locales del sistema.

---

## 1. Diagrama de Arquitectura (Mermaid.js)

El siguiente gráfico de arquitectura representa la estructura de 5 capas de FocuzVoz 0.2 con un flujo horizontal (**graph LR**). Todos los nodos del gráfico, subtítulos y líneas de conexión se presentan con un **tamaño mínimo de letra de 18pt (18px)** para garantizar su perfecta visibilidad en cualquier formato de presentación. Las líneas explican detalladamente la técnica, protocolo, verbo técnico o patrón de comunicación utilizado en la conexión entre capas.

```mermaid
graph LR
    %% =========================================================================
    %% DEFINICIÓN DE ESTILOS DE ALTO CONTRASTE Y FUENTE MÍNIMA DE 18PX (18PT)
    %% =========================================================================
    classDef default font-size:18px,font-family:Inter,sans-serif;
    classDef capaEstilo fill:#ffffff,stroke:#333333,stroke-width:1.2px,stroke-dasharray: 4 4,color:#000000,font-size:18px,font-weight:bold;
    classDef nodoPremium fill:#f8f9fa,stroke:#111111,stroke-width:2px,color:#000000,font-size:18px,font-weight:bold;
    classDef nodoSecundario fill:#ffffff,stroke:#1e1e1e,stroke-width:1.5px,color:#000000,font-size:18px;
    classDef nodoDetalle fill:#f4f4f5,stroke:#a1a1aa,stroke-width:1px,color:#000000,font-size:18px;

    %% =========================================================================
    %% 1. CAPA DE ENTRADA (INPUTS)
    %% =========================================================================
    subgraph Capa_1 ["<span style='font-size: 20px; font-weight: bold; color: #111;'>1. CAPA DE ENTRADA</span>"]
        direction TB
        Webcam["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 32px;'>📷</span><br/><b>Cámara Web</b><br/><span style='font-size: 18px;'>Video en tiempo real<br/>(30/60 FPS)</span></div>"]
        Mic["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 32px;'>🎤</span><br/><b>Micrófono</b><br/><span style='font-size: 18px;'>Flujo de audio continuo</span></div>"]
    end

    %% =========================================================================
    %% 2. CAPA DE PROCESAMIENTO (CORE MACHINE LEARNING)
    %% =========================================================================
    subgraph Capa_2 ["<span style='font-size: 20px; font-weight: bold; color: #111;'>2. CAPA DE PROCESAMIENTO</span>"]
        direction TB
        subgraph Mod_Vision ["<span style='font-size: 18px; font-weight: bold; color: #000;'>Módulo de Visión: MediaPipe</span>"]
            direction LR
            Nose["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>👃</span><br/><b>Extractor Rastreo</b><br/><span style='font-size: 18px;'>Landmark de la nariz<br/>Coordenadas (X, Y)</span></div>"]
            Filter["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>⏱️</span><br/><b>1 Euro Filter</b><br/><span style='font-size: 18px;'>Algoritmo de estabilización<br/>Suprime el Jitter</span></div>"]
            Blend["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>🔲</span><br/><b>Extractor Blendshapes</b><br/><span style='font-size: 18px;'>Identifica 52<br/>expresiones faciales</span></div>"]
        end
        
        subgraph Mod_Voz ["<span style='font-size: 18px; font-weight: bold; color: #000;'>Módulo de Voz: SpeechRecognition</span>"]
            direction LR
            Acoustic["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>🦆</span><br/><b>Motor Acústico</b><br/><span style='font-size: 18px;'>Procesamiento y<br/>reducción de ruido</span></div>"]
            Wake["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>🔑</span><br/><b>Trigger Wake Word</b><br/><span style='font-size: 18px;'>Escucha permanente:<br/>Palabra clave ('focuz')</span></div>"]
        end
    end

    %% =========================================================================
    %% 3. CAPA DE CONTROL (LOGICA DE NEGOCIO Y HILOS)
    %% =========================================================================
    subgraph Capa_3 ["<span style='font-size: 20px; font-weight: bold; color: #111;'>3. CAPA DE CONTROL</span>"]
        direction TB
        Mouse["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>🖱️</span><br/><b>Mouse Controller</b><br/><span style='font-size: 18px;'>Transforma coordenadas<br/>vía pyautogui</span></div>"]
        Keybinder["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>⌨️</span><br/><b>Keybinder</b><br/><span style='font-size: 18px;'>Valida gesto deliberado<br/>(Evita Midas Touch) y clic</span></div>"]
        VoiceCtrl["<div style='font-size: 18px; padding: 10px; text-align: center;'><span style='font-size: 24px;'>🗣️</span><br/><b>Voice Controller</b><br/><span style='font-size: 18px;'>Traduce voz a texto e<br/>inyecta en Windows</span></div>"]
    end

    %% =========================================================================
    %% 5. CAPA DE PRESENTACIÓN & 4. CAPA DE PERSISTENCIA
    %% =========================================================================
    subgraph Capa_5 ["<span style='font-size: 20px; font-weight: bold; color: #111;'>5. CAPA DE PRESENTACIÓN</span>"]
        GUI["<div style='font-size: 18px; padding: 10px; text-align: center;'><img src='https://simpleicons.org/icons/python.svg' width='32' height='32' /><br/><b>CustomTkinter GUI</b><br/><br/><ul style='text-align: left; font-size: 18px;'><li>Panel de control principal</li><li>Feedback Visual Micrófono (Escuchando / Apagado)</li></ul></div>"]
    end

    subgraph Capa_4 ["<span style='font-size: 20px; font-weight: bold; color: #111;'>4. CAPA DE PERSISTENCIA</span>"]
        DB[("<div style='font-size: 18px; padding: 10px; text-align: center;'><img src='https://simpleicons.org/icons/sqlite.svg' width='32' height='32' /><br/><b>SQLite3 Local DB</b><br/><br/><ul style='text-align: left; font-size: 18px;'><li>Perfiles (Calibración)</li><li>Mapeo de Gestos</li><li>Analíticas de Usabilidad</li></ul></div>")]
    end

    %% =========================================================================
    %% FLUJOS Y ENLACES DIRECTOS CON EXPLICACIÓN TÉCNICA E HILADO DE LOGICA (18PX)
    %% =========================================================================
    Webcam -->|<div style='font-size: 18px; color: #004d40; font-weight: bold;'>Captura y decodificación RGB en numpy.ndarray vía OpenCV</div>| Nose
    Webcam -->|<div style='font-size: 18px; color: #004d40; font-weight: bold;'>Inyección de frames en clase mp.Image en LIVE_STREAM mode</div>| Blend
    Mic -->|<div style='font-size: 18px; color: #1a237e; font-weight: bold;'>Muestreo de audio por hardware en sr.Microphone (PyAudio)</div>| Acoustic
    
    Nose -->|<div style='font-size: 18px; color: #004d40; font-weight: bold;'>Frecuencia de corte adaptativa en OneEuroFilter2D</div>| Filter
    Filter -->|<div style='font-size: 18px; color: #004d40; font-weight: bold;'>Traspaso de coordenadas adaptativas 2D filtradas</div>| Mouse
    Blend -->|<div style='font-size: 18px; color: #004d40; font-weight: bold;'>Callback asíncrono con scores continuos de 52 Blendshapes</div>| Keybinder
    
    Acoustic -->|<div style='font-size: 18px; color: #1a237e; font-weight: bold;'>Petición cifrada HTTPS (Puerto 443) a Google Speech API</div>| Wake
    Wake -->|<div style='font-size: 18px; color: #1a237e; font-weight: bold;'>Validación léxica de comandos en español y auto-escritura</div>| VoiceCtrl
    
    Mouse -->|<div style='font-size: 18px; color: #b71c1c; font-weight: bold;'>Movimiento del puntero relativo mediante pyautogui.move</div>| GUI
    Keybinder -->|<div style='font-size: 18px; color: #b71c1c; font-weight: bold;'>Clics y teclas DirectInput de bajo nivel vía PyDirectInput</div>| GUI
    VoiceCtrl -->|<div style='font-size: 18px; color: #b71c1c; font-weight: bold;'>Auto-escritura carácter por carácter vía pynput.keyboard</div>| GUI
    
    GUI <-->|<div style='font-size: 18px; color: #2e7d32; font-weight: bold;'>Consultas SQL preparadas en configs/focuzvoz.db (sqlite3)</div>| DB

    %% =========================================================================
    %% ASIGNACIÓN DE CLASES
    %% =========================================================================
    class Capa_1,Capa_2,Capa_3,Capa_4,Capa_5 capaEstilo;
    class GUI,DB nodoPremium;
    class Webcam,Mic,Mouse,Keybinder,VoiceCtrl,Filter,Wake nodoSecundario;
    class Nose,Blend,Acoustic nodoDetalle;
```

---

## 2. Descripción Técnica de las Capas y Comunicación entre Herramientas

FocuzVoz 0.2 separa rigurosamente las responsabilidades del sistema en **5 capas lógicas**. A continuación se expone cómo se comunican y trabajan las herramientas en cada capa de forma técnica:

### 1. CAPA DE ENTRADA (INPUTS)
Esta capa es responsable de capturar los flujos físicos analógicos y convertirlos en representaciones digitales legibles para el resto del pipeline del software.
*   **Cámara Web (OpenCV)**: El sistema inicializa la cámara física del usuario a través de la biblioteca **OpenCV** empleando `cv2.VideoCapture`. Esta operación corre en un bucle continuo de adquisición que captura fotogramas (frames) a tasas de 30 o 60 cuadros por segundo (FPS). Cada cuadro es decodificado como una matriz de píxeles unidimensional/bidimensional en formato `numpy.ndarray` con espacio de color RGB/BGR.
*   **Micrófono de Hardware (SpeechRecognition)**: El micrófono del sistema se administra mediante la biblioteca **SpeechRecognition** (`speech_recognition`). Utiliza `sr.Microphone()` para abrir un flujo de audio PCM nativo mediante wrappers de la tarjeta de sonido local (generalmente empleando la biblioteca `PyAudio` bajo el capó).

### 2. CAPA DE PROCESAMIENTO (INTELIGENCIA ARTIFICIAL & ML)
Es el núcleo cognitivo del software. Traduce los datos en bruto de la Capa de Entrada en eventos y métricas estructuradas empleando modelos entrenados de redes neuronales y algoritmos de procesamiento digital de señales.
*   **Módulo de Visión (MediaPipe Face Landmarker)**:
    *   **MediaPipe Face Landmarker**: Recibe de forma asíncrona cada fotograma de OpenCV convertido a la clase interna `mp.Image`. Ejecuta de forma local el modelo neuronal optimizado `face_landmarker_with_blendshapes.task` en modo de transmisión en vivo (`RunningMode.LIVE_STREAM`). Este modelo produce dos salidas en un callback seguro para subprocesos (`mp_callback`):
        1.  Una malla facial tridimensional (Face Mesh) compuesta por **478 puntos de coordenadas normalizadas (X, Y, Z)**.
        2.  Un conjunto de **52 coeficientes de expresión facial (Blendshapes)** que representan la intensidad de activación (de `0.0` a `1.0`) de músculos faciales (p. ej., pestañeo, guiños, apertura de boca, cejas).
    *   **Extractor de Landmark de Nariz**: Extrae las coordenadas espaciales `(X, Y)` de la nariz (Landmarks específicos parametrizados en la configuración, o calculados a través de SVD sobre la matriz de transformación de cabeza en 3D) para ser utilizados como puntero del ratón en pantalla.
    *   **Filtro 1 Euro (One Euro Filter 2D)**: Las coordenadas de la nariz crudas presentan vibraciones musculares naturales denominadas *Jitter*. Para evitar esto sin inducir latencia (lag), FocuzVoz procesa las coordenadas a través de una clase especializada `OneEuroFilter2D` (`src/utils/one_euro_filter.py`). Este filtro adaptativo utiliza una frecuencia de corte variable de primer orden; si la velocidad de movimiento es baja, aumenta el filtrado (suprime Jitter para clics de precisión); si la velocidad es alta, disminuye el filtrado (evita lag en desplazamientos rápidos).
*   **Módulo de Voz (Google Speech API & PyTTSx3)**:
    *   **Google Speech Recognition API**: FocuzVoz toma la grabación de audio en buffer gestionada por el micrófono. Primero aplica dinámicamente un filtrado y ajuste del umbral de energía de ruido ambiental (`recognizer.adjust_for_ambient_noise`) durante un lapso de 0.5s para mitigar interferencias de fondo. Posteriormente, empaqueta el audio y lo transmite de forma asíncrona a través de una conexión HTTPS segura (Puerto 443) a la API de reconocimiento de voz en la nube de **Google** utilizando la función `recognizer.recognize_google`. La API retorna un objeto JSON con el texto transcrito y el nivel de confianza asociado.
    *   **PyTTSx3 (Text-to-Speech)**: Proporciona retroalimentación acústica asíncrona a través de una biblioteca de síntesis de voz que utiliza el motor local del sistema operativo de Windows (SAPI5). Al alternar modos de control, lanza un subproceso asíncrono para notificar auditivamente comandos como *"Control facial activado"* o *"Escritura desactivada"*.

### 3. CAPA DE CONTROL (LOGICA DE NEGOCIO Y SUBPROCESOS)
La capa de control actúa como despachador de eventos (Dispatcher) y traductor de lógica de negocio, procesando los datos normalizados de la Capa de Procesamiento y convirtiéndolos en comandos del sistema operativo.
*   **Mouse Controller (PyAutoGUI)**:
    *   Esta clase singleton (`MouseController` en `src/controllers/mouse_controller.py`) corre en un hilo de fondo dedicado (`threading.Thread` provisto por un `concurrent.futures.ThreadPoolExecutor` de un solo trabajador) para evitar congelar el bucle principal de la GUI.
    *   Recibe las coordenadas en píxeles estabilizadas por el filtro 1 Euro, calcula el diferencial de movimiento con respecto a la posición previa (`prev_x`, `prev_y`), aplica una escala asimétrica dependiente de la dirección (los coeficientes `spd_up`, `spd_down`, `spd_left`, `spd_right` almacenados en SQLite) y, opcionalmente, una curva de aceleración sigmoidea (`SigmoidAccel`).
    *   Finalmente, ejecuta el movimiento físico del puntero en Windows invocando llamadas nativas a la biblioteca **PyAutoGUI** (`pyautogui.move`), la cual desactiva las pausas de seguridad predeterminadas (`pyautogui.PAUSE = 0`) para lograr respuesta inmediata.
*   **Gestor de Eventos contra Toque de Midas (FacialEventManager)**:
    *   El parpadeo involuntario o los gestos faciales expresivos naturales pueden provocar clics o teclas accidentales. Para solucionar esto (fenómeno del *Toque de Midas*), el componente `FacialEventManager` de FocuzVoz filtra los 52 blendshapes del Face Landmarker aplicando:
        1.  **Dwell Time (Tiempo de permanencia)**: Exige que el coeficiente del blendshape (p. ej. guiño ocular `eyeBlinkLeft`) supere su umbral configurado (p. ej. `0.65`) de forma continua durante al menos 150 ms para considerarlo una acción intencionada.
        2.  **Cooldown (Enfriamiento)**: Una vez que un gesto se activa, bloquea disparos repetitivos del mismo gesto durante 350 ms para evitar dobles clics o dobles pulsaciones involuntarias.
        3.  **Filtro de estabilidad por fotogramas**: Implementa un buffer de persistencia de estados; un gesto requiere cruzar el umbral en al menos 2 frames consecutivos para ingresar en estado activo, y mantenerse por debajo en 3 frames consecutivos para volver al estado inactivo.
*   **Keybinder (PyDirectInput & Win32API)**:
    *   Traduce los gestos validados y aprobados por el `FacialEventManager` en acciones físicas en el sistema operativo.
    *   En lugar de simular pulsaciones convencionales mediante APIs de alto nivel que suelen fallar en videojuegos o aplicaciones de pantalla completa, utiliza la biblioteca **PyDirectInput**. Esta biblioteca envía eventos a nivel de controlador de entrada DirectInput de DirectX en Windows (`pydirectinput.click`, `pydirectinput.mouseDown`, `pydirectinput.mouseUp`), simulando señales de hardware directo.
    *   Se comunica con **Win32API** para enumerar las pantallas instaladas (`win32api.EnumDisplayMonitors`) y rastrear el monitor activo del usuario, facilitando acciones especiales como "reiniciar puntero al centro" o "pasar cursor recursivamente al monitor adyacente" (acción `cycle`).
*   **Voice Controller (Pynput & Parsing de Comandos)**:
    *   Monitorea las transcripciones provenientes de la Capa de Procesamiento. Evalúa lexicográficamente cadenas en español mediante coincidencia de patrones (regex/substrings).
    *   **Control del Sistema**: Comandos específicos ("mover", "quieto", "escribir", "silencio", "focuzvoz go", "focuzvoz finish") se traducen en llamadas directas a las APIs singleton de `MouseController` (habilitar/deshabilitar rastreo) y a la clase principal de la interfaz para iniciar/finalizar grabaciones de telemetría.
    *   **Auto-escritura (Dictado)**: Cuando el modo auto-escritura está activo, inyecta el texto transcrito de forma exacta y carácter por carácter en el campo de texto que tenga el foco del sistema operativo mediante la simulación de teclado por hardware provista por la biblioteca **Pynput** (`pynput.keyboard.Controller()`).
    *   **Edición y Corrección por Voz**: Si se detecta un comando de borrado ("borrar", "eliminar", "corregir", "deshacer"), la clase calcula la longitud del último segmento inyectado (`last_typed_len`) y simula ráfagas ultrarrápidas de la tecla `Backspace` mediante Pynput para eliminar exactamente la cadena errónea, o bien simula `Ctrl + A` y `Backspace` en el comando "borrar todo".

### 4. CAPA DE PERSISTENCIA (DATOS RELACIONALES)
Esta capa es responsable del almacenamiento permanente de configuraciones, perfiles individuales y, de forma crítica, de la adquisición de datos científicos durante las sesiones de evaluación de usabilidad.
*   **SQLite3 Local Database**:
    *   El sistema utiliza la base de datos SQL relacional e integrada **SQLite3** (`sqlite3` en Python), almacenada en el archivo local `configs/focuzvoz.db`. La base de datos está inicializada bajo el patrón de diseño Singleton a través de la clase `DatabaseManager` (`src/utils/database.py`).
    *   La base de datos habilita la integridad referencial y eliminaciones/actualizaciones en cascada mediante la instrucción `PRAGMA foreign_keys = ON;`.
    *   **Esquema de Tablas e Intercambio de Datos**:
        *   `profiles`: Almacena los perfiles del usuario que diferencian parámetros de calibración.
        *   `cursor_config`: Almacena la configuración de suavizado del filtro 1 Euro (Beta, Min Cutoff, D Cutoff), velocidades de cursor de ratón, aceleración y resolución en una cadena de texto JSON persistente.
        *   `bindings`: Mapea relacionalmente cada gesto (Blendshape) a su respectiva acción (tecla o ratón), estableciendo el umbral de disparo, tipo de pulsación (`single` o `hold`) y perfil asignado.
        *   `voice_config`: Guarda en formato JSON configuraciones de voz (retroalimentación, sensibilidad, idioma configurado como `'es-ES'`).
        *   `research_sessions` y `research_events`: Las clases singleton de control (`MouseController`, `Keybinder`, `VoiceController`) interactúan directamente con la base de datos a través de llamadas asíncronas a `DatabaseManager().log_research_event()`. Cuando se activa una sesión científica, el sistema registra cada micro-evento (marca de tiempo exacta en formato ISO 8601, tipo de evento, posición física del cursor X/Y en píxeles, valor float del blendshape causante del evento y la cadena de voz detectada junto con su factor de confianza), permitiendo extraer análisis estadísticos completos de la interacción.

### 5. CAPA DE PRESENTACIÓN (INTERFAZ DE USUARIO)
Esta capa representa la interfaz interactiva con la que opera el usuario.
*   **CustomTkinter GUI**:
    *   Construida sobre la biblioteca **CustomTkinter**, que provee widgets de alto rendimiento visual (esquinas redondeadas, modo oscuro/claro de alto contraste y tipografía premium Inter).
    *   Se comunica de forma bidireccional con las Capas de Control y Persistencia:
        1.  **Hacia la base de datos**: Lee perfiles activos y mapeos relacionales al iniciar, y persiste instantáneamente las modificaciones realizadas por el usuario en las tablas de SQLite3.
        2.  **Hacia los controladores**: El ciclo principal de CustomTkinter corre en el hilo del sistema de ventanas principal (Main Thread). Para evitar congelamiento por operaciones que bloquean hilos (como la escucha de voz o el tracking continuo), la GUI recibe notificaciones y actualiza sus variables indicadoras de estado (p. ej., interruptor de cursor activo, nivel de volumen, palabras reconocidas) utilizando callbacks seguros para hilos (`root.after()` de Tkinter).
        3.  **Hacia el flujo de video**: OpenCV entrega buffers que son convertidos a objetos compatibles de Tkinter (`PIL.Image` e `ImageTk.PhotoImage`) y renderizados en un widget `Label` a alta velocidad en el hilo de la UI, permitiendo dibujar sobre el video la malla facial de 478 puntos de MediaPipe en tiempo real.

---

## 3. Lógica de Interconexión y Conexiones entre Capas

La lógica de interconexión se describe formalmente a través de las siguientes técnicas y canales de comunicación:

1.  **OpenCV numpy.ndarray a MediaPipe**: La comunicación se realiza mediante el paso por referencia en memoria RAM de matrices NumPy que contienen la información de color e intensidad por pixel del frame capturado por la cámara. No hay sockets ni puertos implicados para garantizar latencia cero.
2.  **MediaPipe a FacialEventManager**: Se implementa a través de un **Callback asíncrono**. Cuando MediaPipe termina de procesar de manera asíncrona un cuadro en su hilo interno de C++, dispara el callback registrado `mp_callback`, transmitiendo un objeto `FaceLandmarkerResult` con listas de objetos nativos conteniendo los landmarks e índices de blendshapes.
3.  **SpeechRecognition a Google Speech API**: Se realiza una conexión **HTTPS saliente sobre el puerto TCP 443** (protocolo TLS 1.3). Se empaqueta el fragmento de audio PCM capturado en formato de compresión sin pérdidas FLAC/WAV y se envía como petición POST web. La respuesta JSON retorna con el texto reconocido.
4.  **Controladores (Mouse/Keybinder/Voice) a Sistema Operativo (Windows OS)**: 
    *   **PyAutoGUI** y **PyDirectInput** realizan llamadas a funciones nativas dinámicas enlazadas (DLLs) de la API de Windows (`user32.dll`) utilizando wrappers internos en Python (`ctypes`) para inyectar eventos de bajo nivel a la cola de entrada del Kernel de Windows.
    *   **Pynput** interactúa con el despachador de eventos de teclado del sistema operativo utilizando hooks del sistema de Windows para emular eventos físicos idénticos a los del teclado real.
    *   **Pyttsx3** inicializa y controla la interfaz COM SAPI5 (`Speech API 5.4` de Microsoft en Windows) utilizando interoperabilidad COM para modular las voces del sistema instaladas localmente en el registro.
5.  **Controladores a Base de Datos (SQLite3)**: La comunicación se maneja mediante llamadas locales directas al motor SQLite en disco a través del driver estándar `sqlite3` de Python, empleando transacciones seguras (`BEGIN TRANSACTION`, `COMMIT`) y sentencias SQL preparadas con paso de tuplas de parámetros para evitar la inyección de código SQL y garantizar que la base de datos relacional conserve su integridad.
