import time
import logging
from src.singleton_meta import Singleton

logger = logging.getLogger("FacialEventManager")


class FacialEventManager(metaclass=Singleton):
    """Procesador de eventos de gestos con estado que implementa la lógica Anti-Midas Touch.
    
    Utiliza tiempos de dwell (espera), cooldown (enfriamiento) y filtros de estabilidad
    a nivel de cuadro para separar los movimientos faciales accidentales de las
    activaciones de control intencionales.
    """

    def __init__(self):
        logger.info("Initializing FacialEventManager singleton")
        self.gesture_states = {}
        
        # Configuraciones de Filtro por Defecto (se pueden personalizar mediante SQLite / ConfigManager)
        self.default_dwell_time_ms = 150.0       # Tiempo que un gesto debe mantenerse activo para activarse
        self.default_cooldown_ms = 350.0         # Enfriamiento antes de que el mismo gesto pueda dispararse de nuevo
        self.default_stability_active_frames = 2   # Cuadros activos consecutivos para registrarse como activo
        self.default_stability_inactive_frames = 3 # Cuadros inactivos consecutivos para registrarse como inactivo

    def get_gesture_state(self, gesture_name: str) -> dict:
        """Obtener o inicializar el diccionario de estado para un gesto."""
        if gesture_name not in self.gesture_states:
            self.gesture_states[gesture_name] = {
                "is_active": False,               # Estado estable actual del gesto
                "active_frames": 0,               # Cuadros consecutivos por encima del umbral
                "inactive_frames": 0,             # Cuadros consecutivos por debajo del umbral
                "activation_start_time": None,    # Marca de tiempo cuando el gesto pasó a estable-activo
                "last_trigger_time": 0.0,         # Marca de tiempo de la última ejecución de la acción
                "trigger_fired": False            # Bandera para evitar disparos duplicados durante una misma pulsación
            }
        return self.gesture_states[gesture_name]

    def filter_gesture(self, gesture_name: str, value: float, threshold: float,
                       dwell_time_ms: float = None, cooldown_ms: float = None,
                       stability_active_frames: int = None, stability_inactive_frames: int = None) -> bool:
        """Filtra las señales de blendshapes crudas y determina si se debe disparar una acción.
        
        Args:
            gesture_name: Identificador único del gesto (ej. 'Mouth left')
            value: Intensidad de la señal cruda [0.0 - 1.0] del reconocedor facial
            threshold: Umbral de activación configurado
            dwell_time_ms: Sobrescribir duración de espera de activación
            cooldown_ms: Sobrescribir tiempo de enfriamiento de redisparo
            stability_active_frames: Sobrescribir tamaño del buffer de cuadros activos
            stability_inactive_frames: Sobrescribir tamaño del buffer de cuadros inactivos
            
        Returns:
            True si el gesto constituye un evento de disparo intencional y filtrado.
        """
        # Resolver configuraciones (usar valores por defecto si no se especifican)
        dwell = dwell_time_ms if dwell_time_ms is not None else self.default_dwell_time_ms
        cooldown = cooldown_ms if cooldown_ms is not None else self.default_cooldown_ms
        act_frames_req = stability_active_frames if stability_active_frames is not None else self.default_stability_active_frames
        inact_frames_req = stability_inactive_frames if stability_inactive_frames is not None else self.default_stability_inactive_frames

        state = self.get_gesture_state(gesture_name)
        now = time.time()

        # Comprobar cruce del umbral crudo
        if value >= threshold:
            state["active_frames"] += 1
            state["inactive_frames"] = 0
            
            # Transición a estable-activo si el conteo de cuadros coincide con el requisito
            if state["active_frames"] >= act_frames_req:
                if not state["is_active"]:
                    state["is_active"] = True
                    state["activation_start_time"] = now
                    logger.debug(f"Gesture '{gesture_name}' reached stable ACTIVE state.")
        else:
            state["inactive_frames"] += 1
            state["active_frames"] = 0
            
            # Transición a estable-inactivo si el conteo de cuadros coincide con el requisito
            if state["inactive_frames"] >= inact_frames_req:
                if state["is_active"]:
                    state["is_active"] = False
                    state["trigger_fired"] = False
                    state["activation_start_time"] = None
                    logger.debug(f"Gesture '{gesture_name}' returned to stable INACTIVE state.")

        # Evaluar condiciones de disparo
        if state["is_active"] and not state["trigger_fired"]:
            # 1. Comprobación de dwell-time (tiempo de espera)
            elapsed_active = now - state["activation_start_time"]
            if elapsed_active >= (dwell / 1000.0):
                # 2. Comprobación de cooldown (tiempo de enfriamiento)
                elapsed_cooldown = now - state["last_trigger_time"]
                if elapsed_cooldown >= (cooldown / 1000.0):
                    # ¡Disparo exitoso!
                    state["trigger_fired"] = True
                    state["last_trigger_time"] = now
                    logger.info(f"Anti-Midas Touch passed: Triggering '{gesture_name}' (Hold time: {elapsed_active*1000:.1f}ms)")
                    return True

        return False

    def reset_all(self):
        """Restablecer los buffers de seguimiento de estado interno (ej. al cambiar de perfil)."""
        self.gesture_states.clear()
        logger.info("FacialEventManager states reset.")
