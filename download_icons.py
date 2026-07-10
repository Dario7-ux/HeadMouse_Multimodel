"""Descarga logos reales de tecnologias para FocuzVoz PPTX"""
import os, requests
from io import BytesIO
from PIL import Image

DEST = r'C:\Servidores\Lectura_FocuzVoz\FocuzVoz3.0\assets\icons'
os.makedirs(DEST, exist_ok=True)

H = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

LOGOS = {
    'python':    'https://www.python.org/static/img/python-logo.png',
    # OpenCV from opencv.org direct
    'opencv':    'https://opencv.org/wp-content/uploads/2022/05/logo.png',
    # Windows from Wikimedia as PNG direct (not SVG thumbnail)
    'windows':   'https://upload.wikimedia.org/wikipedia/commons/e/e6/Windows_11_logo.png',
    # NumPy from numpy.org
    'numpy':     'https://numpy.org/images/logo.svg',
    # SQLite official
    'sqlite':    'https://www.sqlite.org/images/sqlite370_banner.gif',
    # MediaPipe / Google logo from Google Fonts CDN
    'mediapipe': 'https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Google-favicon-2015.png/120px-Google-favicon-2015.png',
    'pyaudio':   'https://www.python.org/static/img/python-logo.png',
    'vosk':      'https://www.python.org/static/img/python-logo.png',
    'pyinstaller':'https://www.python.org/static/img/python-logo.png',
}

for name, url in LOGOS.items():
    path = os.path.join(DEST, f'{name}.png')
    try:
        r = requests.get(url, headers=H, timeout=10)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert('RGBA')
        # Fondo blanco, convertir a RGB
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
        bg.thumbnail((120, 120), Image.LANCZOS)
        bg.save(path)
        print(f'  [OK] {name}.png  ({bg.size[0]}x{bg.size[1]})')
    except Exception as e:
        print(f'  [FAIL] {name}: {e}')

print(f'\nIconos guardados en: {DEST}')
