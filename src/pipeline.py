import logging
import threading
import time

from src.camera_manager import CameraManager
from src.controllers import Keybinder, MouseController
from src.detectors import FaceMesh

logger = logging.getLogger("Pipeline")


class Pipeline:

    def __init__(self):
        logger.info("Init Pipeline")
        self._thread = None
        self._stop_event = threading.Event()

    def start(self):
        """Starts the pipeline background processing thread."""
        if self._thread is None or not self._thread.is_alive():
            logger.info("Starting Pipeline background thread...")
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self):
        """Stops the pipeline background processing thread."""
        logger.info("Stopping Pipeline background thread...")
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run_loop(self):
        while not self._stop_event.is_set():
            start_time = time.time()
            try:
                self.pipeline_tick()
            except Exception as e:
                logger.error(f"Error in pipeline background loop: {e}", exc_info=e)
            
            # Mantener una tasa de 15 FPS (~66ms) (30 frames por cada 2 segundos) para ahorrar procesamiento
            elapsed = time.time() - start_time
            sleep_time = max(0.005, 0.066 - elapsed)
            time.sleep(sleep_time)     

    def pipeline_tick(self) -> None:
        frame_rgb = CameraManager().get_raw_frame() 
        if frame_rgb is None:
            return

        # Detect landmarks (async) and save in it's buffer
        FaceMesh().detect_frame(frame_rgb)

        # Get facial landmarks
        landmarks = FaceMesh().get_landmarks()
        if (landmarks is None):
            CameraManager().draw_overlay(track_loc=None)
            return

        # Control mouse position
        track_loc = FaceMesh().get_track_loc()
        # Control keyboard
        blendshape_values = FaceMesh().get_blendshapes()
        Keybinder().act(blendshape_values, track_loc)

        MouseController().act(track_loc)

        # Draw frame overlay
        CameraManager().draw_overlay(track_loc)
