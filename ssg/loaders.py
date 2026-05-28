"""Data loading functions for pages, galleries, and events."""
from datetime import datetime
from pathlib import Path
import yaml

from .config import GALLERIES_DIR


def load_template(path: Path) -> str:
    """Load HTML template from file."""
    return path.read_text(encoding='utf-8')


def load_page_data(page_file: Path) -> dict:
    """Load and validate page data from YAML file."""
    data = yaml.safe_load(page_file.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f"Page file {page_file} must contain a YAML mapping.")
    for required in ('path', 'title', 'content'):
        if required not in data:
            raise ValueError(f"Missing '{required}' field in {page_file}")

    page_path = str(data['path'])
    normalized_path = page_path.lstrip('/')
    nav_path = normalized_path
    if normalized_path.endswith('index.html'):
        nav_path = str(Path(normalized_path).parent)
        if nav_path == '.':
            nav_path = ''

    return {
        **data,
        'path': page_path,
        'nav_path': nav_path,
    }


def load_gallery_data(gallery_dir: Path) -> dict:
    """Load and validate gallery data from gallery.yaml."""
    page_file = gallery_dir / 'gallery.yaml'
    if not page_file.exists():
        raise FileNotFoundError(f"Missing gallery.yaml in {gallery_dir}")

    data = yaml.safe_load(page_file.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError(f"Gallery file {page_file} must contain a YAML mapping.")
    for required in ('title', 'content'):
        if required not in data:
            raise ValueError(f"Missing '{required}' field in {page_file}")

    image_path = str(data.get('image_path', '')).strip()
    image_src = None
    if image_path:
        image_src = gallery_dir / image_path.lstrip('/')
        image_path = f'/galleries/{gallery_dir.name}/{image_path.lstrip('/')}'

    return {
        'path': f'galleries/{gallery_dir.name}/index.html',
        'nav_path': f'galleries/{gallery_dir.name}',
        'title': str(data['title']),
        'content': str(data['content']),
        'image_path': image_path,
        'image_src': image_src,
    }


def scan_gallery_pages() -> list[dict]:
    """Scan galleries directory and load all gallery pages."""
    if not GALLERIES_DIR.exists():
        return []

    pages = []
    for entry in sorted(GALLERIES_DIR.iterdir()):
        if entry.is_dir() and (entry / 'gallery.yaml').exists():
            pages.append(load_gallery_data(entry))
    return pages


def scan_event_directories() -> dict:
    """Scan galleries for event directories and return event data mapping.

    Returns:
        A mapping of gallery_name -> list of event dicts.
        Each event dict contains: name, title, content, image_path, path, tags, src
    """
    events = {}
    if not GALLERIES_DIR.exists():
        return events

    for gallery_dir in sorted(GALLERIES_DIR.iterdir()):
        if not gallery_dir.is_dir():
            continue

        event_list = []
        for entry in sorted(gallery_dir.iterdir()):
            if entry.is_dir() and (entry / 'event.yaml').exists():
                data = yaml.safe_load((entry / 'event.yaml').read_text(encoding='utf-8')) or {}
                if not isinstance(data, dict):
                    raise ValueError(f"Event file {(entry / 'event.yaml')} must contain a YAML mapping.")
                for required in ('title', 'content', 'tags'):
                    if required not in data:
                        raise ValueError(f"Missing '{required}' field in {(entry / 'event.yaml')}")
                tags = data.get('tags', [])
                if not isinstance(tags, list):
                    raise ValueError(f"The 'tags' field in {(entry / 'event.yaml')} must be a list.")

                date_str = str(data.get('date', '')).strip()
                if not date_str:
                    raise ValueError(f"Missing 'date' field in {(entry / 'event.yaml')}")
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid date format in {(entry / 'event.yaml')}: {date_str}. "
                        "Expected yyyy-mm-dd."
                    ) from exc

                title = str(data.get('title', entry.name))
                content = str(data.get('content', ''))
                image_path = str(data.get('image_path', '')).strip()
                if image_path:
                    image_path = f'/galleries/{gallery_dir.name}/{entry.name}/{image_path.lstrip('/')}'
                path = f'galleries/{gallery_dir.name}/{entry.name}/index.html'
                event_list.append({
                    'name': entry.name,
                    'gallery': gallery_dir.name,
                    'title': title,
                    'content': content,
                    'image_path': image_path,
                    'path': path,
                    'date': date_str,
                    'date_obj': date_obj,
                    'tags': [str(tag) for tag in tags],
                    'src': entry,
                })

        if event_list:
            events[gallery_dir.name] = event_list

    return events
