#!/usr/bin/env python
"""Script de configuración para el reconocimiento de voz fuera de línea de Vosk.

Este script prepara la aplicación FocuzVoz para el reconocimiento de voz fuera de línea usando Vosk.
Instala las dependencias requeridas y descarga el modelo de idioma en español.

Uso:
    python setup_vosk.py
"""

import sys
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def install_requirements():
    """Instalar los paquetes requeridos desde requirements.txt."""
    logger.info("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("✓ Packages installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ Failed to install packages: {e}")
        return False


def download_vosk_model():
    """Descargar el modelo de Vosk en español."""
    logger.info("Setting up Vosk Spanish model...")
    try:
        from src.utils.vosk_setup import setup_model, download_model_manual, model_exists
        
        if model_exists():
            logger.info("✓ Vosk model already available")
            return True
        
        if setup_model():
            logger.info("✓ Vosk model downloaded and extracted successfully")
            return True
        else:
            logger.error("✗ Failed to download Vosk model")
            logger.info(download_model_manual())
            return False
    except Exception as e:
        logger.error(f"✗ Error during Vosk setup: {e}")
        return False


def main():
    """Ejecutar los pasos de configuración."""
    logger.info("=" * 60)
    logger.info("FocuzVoz - Vosk Offline Speech Recognition Setup")
    logger.info("=" * 60)
    
    # Paso 1: Instalar los requisitos
    if not install_requirements():
        logger.error("Setup failed at package installation step")
        sys.exit(1)
    
    # Paso 2: Descargar el modelo de Vosk
    if not download_vosk_model():
        logger.warning("Vosk model not available. Speech recognition may not work until model is installed.")
        logger.info("You can manually download the model later by running:")
        logger.info("  python -m src.utils.vosk_setup")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("✓ Setup completed successfully!")
    logger.info("=" * 60)
    logger.info("You can now run the application with: python run_app.py")
    sys.exit(0)


if __name__ == "__main__":
    main()
