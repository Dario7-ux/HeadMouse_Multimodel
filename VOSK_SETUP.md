# Vosk Offline Speech Recognition Setup

FocuzVoz ha sido migrado a usar **Vosk** para reconocimiento de voz offline en español. Esta es una mejora importante que permite:

- ✅ **Funcionamiento sin internet** - Reconocimiento local y privado
- ✅ **Mayor privacidad** - No envía audio a servidores externos
- ✅ **Mejor rendimiento** - Procesamiento más rápido
- ✅ **Independencia** - No depende de API de Google

## Instalación Rápida

### Opción 1: Setup Automático (Recomendado)

```bash
python setup_vosk.py
```

Este script hará todo automáticamente:
1. Instala las dependencias necesarias
2. Descarga el modelo de Vosk para español
3. Valida la instalación

### Opción 2: Instalación Manual

#### Paso 1: Instalar dependencias
```bash
pip install -r requirements.txt
```

Esto instala:
- `vosk==0.3.32` - Engine de reconocimiento offline
- `pyaudio>=0.2.11` - Captura de audio
- `pyttsx3>=2.90` - Síntesis de voz

#### Paso 2: Descargar modelo Vosk

**Opción A: Descarga automática**
```bash
python -m src.utils.vosk_setup
```

**Opción B: Descarga manual**
1. Descarga el modelo desde: https://alphacephei.com/vosk/models
2. Busca: `vosk-model-es-0.42.zip` (modelo en español)
3. Extrae en: `assets/models/vosk-model-es-0.42/`

La estructura final debe ser:
```
assets/models/vosk-model-es-0.42/
├── am/
├── conf/
├── graph/
├── ivector/
└── model
```

## Cambios en el Código

### Imports actualizados
```python
# Antes (Google Speech):
import speech_recognition as sr

# Ahora (Vosk offline):
from vosk import Model, KaldiRecognizer
import pyaudio
```

### Configuración sin cambios
El archivo `configs/default/voice.json` mantiene la misma estructura:
```json
{
    "enabled": true,
    "language": "es-ES",
    "microphone_id": 0,
    "confidence_threshold": 0.5,
    "voice_sensitivity": 50,
    "auto_type": false,
    "confirmation_required": false,
    "pause_during_cursor": true,
    "speech_timeout_ms": 5000,
    "voice_feedback": true
}
```

## Uso

Una vez configurado, el funcionamiento es idéntico:

```bash
python run_app.py
```

### Comandos de voz soportados

La aplicación sigue reconociendo los mismos comandos:

**Escritura:**
- "escribir" / "activar voz" / "voz up" - Activar escritura por voz
- "silencio" / "desactivar voz" / "voz off" - Desactivar escritura

**Control de cursor:**
- "mover" / "activar cursor" / "cursor on" - Activar control facial
- "quieto" / "desactivar cursor" / "cursor off" - Desactivar control facial

**Sesiones de grabación:**
- "focusvoz go" - Iniciar sesión
- "focusvoz finish" - Finalizar sesión

**Edición:**
- "borrar" / "eliminar" / "deshacer" - Borrar último segmento
- "borrar todo" / "limpiar" - Borrar todo el texto

## Solución de Problemas

### El modelo no se descarga
```bash
# Intenta descargarlo manualmente:
python -m src.utils.vosk_setup
```

### Error: "PyAudio not found"
En Windows, PyAudio requiere compilación. Instala pre-compilado:
```bash
pip install pipwin
pipwin install pyaudio
```

O descarga desde: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### El reconocimiento no funciona
1. Verifica que el micrófono esté conectado y funcione
2. Comprueba que el modelo está en `assets/models/vosk-model-es-0.42/`
3. Revisa los logs en `log.txt` para más detalles

### Precisión del reconocimiento
Vosk tiene menos precisión que Google Speech, especialmente con:
- Acentos poco claros
- Ruido ambiental fuerte
- Velocidad de habla muy rápida o lenta

Mejoras para aumentar precisión:
- Habla claramente y a ritmo normal
- Reduce ruido de fondo
- Acércate al micrófono

## Comparación: Google Speech vs Vosk

| Aspecto | Google Speech | Vosk |
|---------|--------------|------|
| Requiere Internet | Sí | No |
| Privacidad | Menor | Mayor |
| Precisión | Mayor | Buena |
| Velocidad | Depende conexión | Rápido |
| Costo | Gratis | Gratis |
| Configuración | Simple | Requiere modelo |
| Idiomas | Múltiples | 20+ idiomas |

## Cambios a requirements.txt

```diff
  flatbuffers==2.0.0
  matplotlib>=3.7.1,<3.9.0
  opencv-contrib-python>=4.8.0.0
  psutil>=5.9.4
  pyautogui>=0.9.53
  customtkinter>=5.2.0
  PyDirectInput>=1.0.4
  pywin32>=306
  mediapipe>=0.10.11
  numpy>=1.24.0,<2.0.0
- speech_recognition>=3.10.0
+ vosk==0.3.32
+ pyaudio>=0.2.11
+ pyttsx3>=2.90
+ requests>=2.28.0
```

## Archivos Modificados

- ✅ `requirements.txt` - Dependencias actualizadas
- ✅ `src/controllers/voice_controller.py` - Usa Vosk en lugar de Google Speech
- ✅ `src/utils/vosk_setup.py` - Nuevo: descarga automática del modelo
- ✅ `setup_vosk.py` - Nuevo: script de instalación
- ✅ `assets/models/` - Nuevo directorio para el modelo

## Archivos Sin Cambios

- 📋 `configs/default/voice.json` - Configuración idéntica
- 📋 `run_app.py` - Ejecución idéntica
- 📋 `README.md` - Documentación principal

## Soporte

Para problemas o preguntas:
1. Revisa los logs en `log.txt`
2. Verifica que todas las dependencias estén instaladas
3. Asegúrate de que el modelo Vosk está descargado

¡Vosk está listo para usar! 🎙️
