"""Configuration and constants for the static site generator."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PAGES_DIR = BASE_DIR / 'pages'
GALLERIES_DIR = BASE_DIR / 'galleries'
PUBLIC_DIR = BASE_DIR / 'public'
TEMPLATE_FILE = BASE_DIR / 'template_page.html'
TEMPLATE_GALLERY_FILE = BASE_DIR / 'template_gallery.html'
TEMPLATE_EVENT_FILE = BASE_DIR / 'template_event.html'
STATIC_ASSETS = ['styles.css', 'scripts.js']
