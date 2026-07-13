# Guión para Evaluación con Expertos — FocuzVoz 3.0
## Qué decir y hacer: ANTES, DURANTE y DESPUÉS

---

## ANTES DE LA SESIÓN — Preparación y Recepción

### 1. Preparación del equipo (tú solo, 10 min antes)

**Qué hacer:**
1. Encender el PC, conectar cámara web y micrófono.
2. Abrir FocuzVoz 3.0 → verificar que la cámara muestra el preview del rostro.
3. Mover tu cabeza → confirmar que el cursor responde.
4. Decir "clic izquierdo" → confirmar que el micrófono detecta la voz.
5. Tener abierta una carpeta con íconos en el escritorio para las tareas.
6. Tener listo: Bloc de Notas abierto (minimizado) para la tarea de dictado.
7. Tener impresos: consentimiento informado, ficha demográfica y cuestionario de heurísticas.

### 2. Recepción del experto

**Qué decir (saludo):**

> *"Buenos días/tardes, ingeniero/a [nombre]. Muchas gracias por su tiempo y disponibilidad para participfar en esta evaluación técnica.*
>
> *Mi nombre es [tu nombre], soy estudiante de la Universidad de las Fuerzas Armadas ESPE y estoy desarrollando, junto con mi equipo, un proyecto de titulación llamado FocuzVoz 3.0."*

**Qué decir (contexto del proyecto):**

> *"FocuzVoz 3.0 es un sistema de interacción humano-computador no intrusivo, diseñado para personas con discapacidad motriz en miembros superiores. Es decir, personas que no pueden usar mouse ni teclado.*
>
> *El sistema permite controlar el computador usando dos modalidades combinadas:*
> - *Primero, rastreo facial: el sistema detecta la punta de la nariz del usuario mediante puntos faciales y traduce sus movimientos en desplazamiento del cursor en la pantalla. Para hacer clic o ejecutar acciones, el usuario realiza gestos faciales como abrir la boca, mover la mandíbula o levantar una ceja.*
> - *Segundo, reconocimiento de voz offline: el usuario puede dictar comandos como 'abrir navegador', 'clic izquierdo' o dictar texto directamente, sin necesidad de conexión a internet.*
>
> *Todo el procesamiento se ejecuta localmente en el computador del usuario."*

**Qué decir (propósito de la evaluación):**

> *"El propósito de esta sesión es que usted interactúe con el sistema de forma multimodal — es decir, combinando gestos faciales y comandos de voz — y luego evalúe la interfaz aplicando las 10 heurísticas de usabilidad de Jakob Nielsen.*
>
> *La evaluación tiene tres partes: primero le explico la arquitectura del sistema y calibramos, luego usted realiza tareas guiadas, y al final completa el cuestionario heurístico. En total, tomará aproximadamente 25 a 30 minutos.*
>
> *Su valoración técnica es muy importante para identificar fortalezas y debilidades del sistema."*

**Qué hacer:** 
1. Entregar el consentimiento informado → que lo lea y firme.
2. Entregar la ficha demográfica → que complete: nombre, especialidad, años de experiencia, nivel académico.
3. Entregarle el cuestionario de heurísticas para que lo revise antes de empezar.

---

## DURANTE LA SESIÓN

### Actividad 1 — Explicación Técnica y Calibración (5–7 min)

**Qué decir (arquitectura del sistema):**

> *"Permítame explicarle la arquitectura del sistema. FocuzVoz 3.0 está organizado en módulos funcionales que se comunican entre sí. Le voy a explicar el flujo completo desde los sensores de entrada hasta la acción en el sistema operativo."*

**Qué decir (sensores de entrada):**

> *"El sistema tiene dos sensores de entrada:*
> - *La cámara web, gestionada por un módulo de captura de video basado en OpenCV. Este componente se encarga de obtener los fotogramas de la cámara en alta definición y los procesa en un hilo independiente para que la aplicación no se congele ni pierda fluidez durante el uso.*
> - *El micrófono, gestionado por un módulo de captura de audio basado en PyAudio. Este componente recibe la señal de audio en formato PCM mono a 16 kHz con un buffer de 2048 muestras, preparándola para el reconocimiento de voz."*

**Qué decir (módulo de procesamiento visual):**

> *"Para el control del cursor y la detección de gestos, el video de la cámara pasa por un pipeline de 4 componentes:*
>
> 1. *MediaPipe FaceLandmarker: detecta 478 puntos faciales y genera 52 blendshapes. Cada blendshape es un valor de 0.0 a 1.0 que mide la activación de una expresión facial. Por ejemplo, si usted abre la boca, el blendshape 'jawOpen' sube de 0 a 1.*
>
> 2. *OneEuroFilter2D: un filtro de señal adaptativo que suaviza las coordenadas del landmark de rastreo. Elimina el temblor, o jitter, del cursor sin añadir latencia perceptible.*
>
> 3. *FacialEventManager: es una máquina de estados finitos que valida si un gesto es deliberado. Implementa un mecanismo anti-Midas Touch para evitar que movimientos involuntarios del rostro disparen acciones no deseadas.*
>
> 4. *MouseController: transforma las coordenadas filtradas de la punta de la nariz en movimiento real del cursor en pantalla. Aplica aceleración logarítmica, lo que significa que movimientos pequeños de la nariz producen desplazamientos finos y precisos, mientras que movimientos amplios mueven el cursor más rápido."*

**Qué decir (módulo de procesamiento de voz):**

> *"Para el reconocimiento de voz, el audio del micrófono pasa por otro pipeline:*
>
> 1. *NumPy procesa el audio PCM y calcula la amplitud RMS del sonido. Esto funciona como una puerta de ruido: si el volumen no supera un umbral configurable, el audio se reemplaza por silencio para evitar que el sistema interprete ruidos de fondo.*
>
> 2. *Vosk STT: es un motor de reconocimiento de voz completamente offline. Usa un modelo de lenguaje en español de 1.4 GB almacenado localmente. No necesita conexión a internet en ningún momento.*
>
> 3. *pyttsx3: proporciona retroalimentación de voz al usuario. Cuando el sistema reconoce un comando, le confirma en voz alta lo que ejecutó. Por ejemplo, si usted dice 'clic izquierdo', el sistema responde 'Clic izquierdo'.*
>
> 4. *pynput y pyautogui: traducen los comandos de voz en acciones reales. En modo dictado, el texto reconocido se escribe carácter por carácter en la aplicación enfocada."*

**Qué decir (interfaz y persistencia):**

> *"La interfaz gráfica está construida con una biblioteca de interfaz moderna para Python. Desde la ventana principal, el usuario puede configurar perfiles, ajustar velocidades, asignar gestos a acciones y ver el indicador visual del micrófono en tiempo real.*
>
> *Toda la configuración se almacena en una base de datos local SQLite. Un gestor de datos dedicado se encarga de guardar y recuperar los perfiles de calibración, el mapeo de gestos y las analíticas de usabilidad de forma persistente.*
>
> *Además, existe un módulo de recolección de datos que registra telemetría local para fines de investigación: cada clic, comando de voz y movimiento queda registrado y se puede exportar en formato CSV para análisis posterior.*
>
> *Finalmente, un módulo de inyección de acciones se comunica directamente con el sistema operativo Windows, simulando clics, movimientos del puntero y pulsaciones de teclado a nivel de sistema, para que las acciones del usuario se ejecuten como si estuviera usando un ratón y teclado físicos."*

---

**Qué decir (gestos faciales configurados):**

> *"Ahora le muestro los gestos faciales que tiene configurados el sistema. Le hago una demostración de cada uno:"*

**(Hacer cada gesto mientras lo explicas):**

| Gesto | Demostración | Acción asignada |
|---|---|---|
| Abrir boca | Abrir la boca ampliamente | Clic izquierdo |
| Mover boca a la izquierda | Desplazar mandíbula a la izquierda | Clic derecho |
| Mover boca a la derecha | Desplazar mandíbula a la derecha | Pausar/reanudar cursor |
| Estirar labio inferior | Enrollar el labio inferior | Doble clic izquierdo |
| Levantar ceja izquierda | Elevar solo la ceja izquierda | Restablecer cursor al centro |
| Levantar ceja derecha | Elevar solo la ceja derecha | Cambiar monitor |
| Inflar mejillas | Inflar ambas mejillas | Tecla configurable |

**Qué decir (comandos de voz):**

> *"En cuanto a la voz, estos son los comandos que el sistema reconoce:"*

| Comando | Resultado |
|---|---|
| "clic izquierdo" | Ejecuta clic izquierdo |
| "clic" | Ejecuta clic derecho |
| "doble clic izquierdo" | Ejecuta doble clic izquierdo |
| "abrir navegador" / "abrir internet" | Abre el navegador web |
| "abrir Word" | Abre Microsoft Word |
| "abrir bloc de notas" | Abre Notepad |
| "escribir" / "voz on" | Activa modo dictado |
| "silencio" / "voz off" | Desactiva modo dictado |
| "mover" / "activar cursor" | Reactiva el cursor |
| "quieto" / "desactivar cursor" | Congela el cursor |
| "borrar" | Borra último segmento dictado |
| "borrar todo" | Borra todo el texto |
| "Focuz finish" / "Focuz cerrar" | Cierra la aplicación |

---

**Qué decir (calibración):**

> *"Ahora vamos a calibrar el sistema para su rostro. Le pido que se siente cómodamente frente a la cámara, a unos 50–60 centímetros, y mire al frente de forma natural."*

**Qué hacer:**
1. Iniciar FocuzVoz 3.0 → verificar que el rostro aparece en el preview.
2. Ajustar velocidad del cursor si es necesario (valores típicos: 18–22).
3. Pedirle que diga "clic izquierdo" para verificar el micrófono.
4. Dejar que explore libremente 1–2 minutos.
5. Preguntar: *"¿Se siente cómodo con el control? ¿Alguna duda antes de las tareas?"*

---

### Actividad 2 — Tareas Guiadas Multimodales (10–15 min)

**Qué decir antes de iniciar:**

> *"Ahora le voy a pedir que realice 5 tareas que combinan gestos faciales y comandos de voz. Se las iré indicando una por una. Le pido que verbalice en voz alta cualquier observación técnica: si algo le parece confuso, si detecta un error, si algo funciona bien."*

---

**TAREA 1 — Cursor + clic con gesto facial**

**Qué decir:**
> *"Primera tarea: mueva el cursor con movimientos de la nariz hacia el ícono de la Papelera de Reciclaje en el escritorio. Cuando esté posicionado sobre él, haga clic izquierdo abriendo la boca."*

**Qué observar:** Fluidez del cursor, precisión, detección del gesto al primer intento, falsos positivos.

---

**TAREA 2 — Navegación web con voz y gestos**

**Qué decir:**
> *"Segunda tarea: diga en voz alta 'abrir navegador'."*
> *(Esperar ejecución)*
> *"Ahora, usando movimientos de la nariz, lleve el cursor hasta la barra de búsqueda del navegador. Haga clic con gesto facial (abriendo la boca) y luego dicte una búsqueda, por ejemplo: 'tecnología asistiva'. Navegue por los resultados moviendo la nariz y seleccione un enlace con un clic facial."*

**Qué observar:** Reconocimiento del comando de voz, latencia, capacidad de navegación combinando nariz + gestos + voz, precisión al apuntar a enlaces.

---

**TAREA 3 — Dictado de voz**

**Qué decir:**
> *"Tercera tarea: primero, diga 'abrir bloc de notas' para abrir el editor de texto."*
> *(Esperar ejecución)*
> *"Ahora active la escritura diciendo 'escribir' o 'voz on'."*
> *(Esperar: "Escritura activada")*
> *"Bien, ahora le voy a pedir que dicte un fragmento del poema 'No te rindas' de Mario Benedetti. Dicte lo siguiente:"*
>
> *«No te rindas, aún estás a tiempo de alcanzar y comenzar de nuevo, aceptar tus sombras, enterrar tus miedos, liberar el lastre, retomar el vuelo.»*
>
> — Mario Benedetti, *No te rindas* (1999)
>
> *(Esperar que se escriba)*
> *"Desactive el dictado diciendo 'silencio' o 'voz off'."*

**Qué observar:** Palabras correctas vs errores, precisión del reconocimiento en frases largas, activación/desactivación del dictado.

---

**TAREA 4 — Cerrar ventana multimodal**

**Qué decir:**
> *"Cuarta tarea: cierre la ventana del Bloc de Notas. Lleve el cursor al botón × usando movimientos de la nariz y haga clic con gesto facial (abriendo la boca)."*

**Qué observar:** Precisión en zona pequeña (botón ×), intentos necesarios, control fino de la nariz.

---

**TAREA 5 — Palabra clave de cierre**

**Qué decir:**
> *"Última tarea: para finalizar la interacción con el sistema, diga 'Focuz finish' o 'Focuz cerrar'."*

**Qué observar:** Reconocimiento al primer intento, retroalimentación antes de cerrarse.

---

### Actividad 3 — Evaluación Heurística (5–8 min)

**Qué decir:**

> *"Hemos terminado las tareas prácticas. Ahora le pido que complete la evaluación heurística basándose en su experiencia de uso.*
>
> *El cuestionario tiene las 10 heurísticas de Jakob Nielsen. Para cada una, asigne una puntuación de severidad:*
> - *0 = No es un problema de usabilidad*
> - *1 = Problema cosmético*
> - *2 = Problema menor*
> - *3 = Problema mayor, importante corregirlo*
> - *4 = Catástrofe de usabilidad, debe corregirse obligatoriamente*
>
> *Además, le agradeceré que escriba comentarios: qué funcionó bien y qué debería mejorar."*

**Las 10 heurísticas:**

| # | Heurística |
|---|---|
| 1 | Visibilidad del estado del sistema |
| 2 | Correspondencia entre el sistema y el mundo real |
| 3 | Control y libertad del usuario |
| 4 | Consistencia y estándares |
| 5 | Prevención de errores |
| 6 | Reconocimiento antes que recuerdo |
| 7 | Flexibilidad y eficiencia de uso |
| 8 | Diseño estético y minimalista |
| 9 | Ayuda a reconocer, diagnosticar y recuperarse de errores |
| 10 | Ayuda y documentación |

**Qué hacer:** Entregar el cuestionario, darle tiempo sin prisa, aclarar dudas si las tiene.

---

## DESPUÉS DE LA SESIÓN

**Qué decir:**

> *"Muchas gracias, ingeniero/a [nombre]. Su evaluación es muy valiosa y nos ayudará a mejorar el sistema. ¿Tiene algún comentario adicional o recomendación?"*

*(Anotar todo)*

> *"Sus datos serán tratados de forma confidencial y utilizados exclusivamente para fines académicos."*

**Qué hacer después:**
1. Recoger el cuestionario heurístico firmado.
2. Verificar que las 10 heurísticas tengan puntuación y comentarios.
3. Guardar ficha demográfica + cuestionario emparejados.
4. Repetir con cada uno de los 5 expertos.
5. Al terminar todos:
   - Calcular **media de severidad** por heurística.
   - Identificar heurísticas con **mayor problema** (media ≥ 3).
   - Listar **recomendaciones de mejora**.
   - Triangular con los resultados SUS de los estudiantes.

---

> **Recordatorio:** Entre cada experto, reiniciar FocuzVoz 3.0 para calibración limpia.
