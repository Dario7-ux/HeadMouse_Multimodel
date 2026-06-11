import os
import logging
import zipfile
import shutil
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None

from src.utils.resource_helper import get_resource_path

logger = logging.getLogger("VoskSetup")

VOSK_MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip"
VOSK_MODEL_DIR = get_resource_path("assets/models")
VOSK_MODEL_NAME = "vosk-model-es-0.42"



def get_model_path() -> str:
    """Get the full path to the Vosk model directory.
    
    Returns:
        Path to the model directory
    """
    return os.path.join(VOSK_MODEL_DIR, VOSK_MODEL_NAME)


def model_exists() -> bool:
    """Check if Vosk model is already downloaded.
    
    Returns:
        True if model exists, False otherwise
    """
    model_path = get_model_path()
    return os.path.exists(model_path) and os.path.isdir(model_path)


def setup_model() -> bool:
    """Download and setup Vosk Spanish model.
    
    Returns:
        True if setup successful, False otherwise
    """
    if model_exists():
        logger.info("Vosk model already exists")
        return True
    
    if not requests:
        logger.error("requests library not installed. Run: pip install requests")
        return False
    
    try:
        # Create model directory if it doesn't exist
        os.makedirs(VOSK_MODEL_DIR, exist_ok=True)
        
        logger.info(f"Downloading Vosk Spanish model from {VOSK_MODEL_URL}...")
        response = requests.get(VOSK_MODEL_URL, stream=True)
        response.raise_for_status()
        
        # Save zip file
        zip_path = os.path.join(VOSK_MODEL_DIR, f"{VOSK_MODEL_NAME}.zip")
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        percent = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {percent:.1f}%")
        
        logger.info("Download complete. Extracting model...")
        
        # Extract zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(VOSK_MODEL_DIR)
        
        # Remove zip file
        os.remove(zip_path)
        
        if model_exists():
            logger.info(f"Vosk model successfully installed at {get_model_path()}")
            return True
        else:
            logger.error("Model extraction failed")
            return False
            
    except Exception as e:
        logger.error(f"Error downloading Vosk model: {e}")
        return False


def download_model_manual() -> str:
    """Provide instructions for manual model download.
    
    Returns:
        Instructions string
    """
    instructions = f"""
    Vosk model not found. Please download manually:
    
    1. Visit: https://alphacephei.com/vosk/models
    2. Download: vosk-model-es-0.42.zip (Spanish model)
    3. Extract to: {os.path.abspath(VOSK_MODEL_DIR)}/
    
    Final structure should be:
    {os.path.abspath(get_model_path())}/
    ├── am/
    ├── conf/
    ├── graph/
    ├── ivector/
    └── model
    """
    return instructions


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    if setup_model():
        print("✓ Vosk setup complete")
    else:
        print("✗ Vosk setup failed")
        print(download_model_manual())
