from pathlib import Path
import shutil
import yaml

BASE_DIR = Path(__file__).resolve().parent
PAGES_DIR = BASE_DIR / 'pages'
GALLERIES_DIR = BASE_DIR / 'galleries'
PUBLIC_DIR = BASE_DIR / 'public'
TEMPLATE_FILE = BASE_DIR / 'template_page.html'
TEMPLATE_GALLERY_FILE = BASE_DIR / 'template_gallery.html'
TEMPLATE_EVENT_FILE = BASE_DIR / 'template_event.html'
STATIC_ASSETS = ['styles.css', 'scripts.js']


def load_template(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def load_page_data(page_file: Path) -> dict:
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
    if image_path:
        image_path = f'/galleries/{gallery_dir.name}/{image_path.lstrip('/')}'

    return {
        'path': f'galleries/{gallery_dir.name}/index.html',
        'nav_path': f'galleries/{gallery_dir.name}',
        'title': str(data['title']),
        'content': str(data['content']),
        'image_path': image_path,
    }


def render_page(template: str, title: str, content: str, page_nav: str, gallery_nav: str) -> str:
    return (
        template
        .replace('{{title}}', title)
        .replace('{{content}}', content)
        .replace('{{page_nav}}', page_nav)
        .replace('{{gallery_nav}}', gallery_nav)
    )


def build_nav(pages: list[dict], current_path: str, label: str) -> str:
    if not pages:
        return ''

    items = []
    for page in pages:
        href_path = str(page.get('nav_path', page['path'])).lstrip('/')
        href = f'/{href_path}'
        title = str(page['title'])
        active = ' nav-item--active' if href_path == current_path else ''
        items.append(
            f'<li class="nav-item{active}"><a href="{href}">{title}</a></li>'
        )

    return (
        '<div class="nav-dropdown">'
        f'<button class="nav-toggle" type="button" aria-expanded="false">{label}</button>'
        f'<ul class="nav-list">{"".join(items)}</ul>'
        '</div>'
    )


def copy_static_assets() -> None:
    for asset_name in STATIC_ASSETS:
        asset_path = BASE_DIR / asset_name
        if not asset_path.exists():
            raise FileNotFoundError(f"Static asset not found: {asset_path}")
        destination = PUBLIC_DIR / asset_name
        shutil.copy2(asset_path, destination)
        print(f'Copied {asset_name} to {destination}')


def scan_gallery_pages() -> list[dict]:
    if not GALLERIES_DIR.exists():
        return []

    pages = []
    for entry in sorted(GALLERIES_DIR.iterdir()):
        if entry.is_dir() and (entry / 'gallery.yaml').exists():
            pages.append(load_gallery_data(entry))
    return pages


def scan_event_directories() -> dict:
    """Return a mapping of gallery_name -> list of event dicts.

    Each event dict contains: name, title, content, path, src (Path to source dir)
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
                title = str(data.get('title', entry.name))
                content = str(data.get('content', ''))
                image_path = str(data.get('image_path', '')).strip()
                if image_path:
                    image_path = f'/galleries/{gallery_dir.name}/{entry.name}/{image_path.lstrip('/')}'
                path = f'galleries/{gallery_dir.name}/{entry.name}/index.html'
                event_list.append({
                    'name': entry.name,
                    'title': title,
                    'content': content,
                    'image_path': image_path,
                    'path': path,
                    'src': entry,
                })

        if event_list:
            events[gallery_dir.name] = event_list

    return events


def adjust_asset_paths(html: str, output_path: Path) -> str:
    """Adjust `styles.css` and `scripts.js` paths in templates based on output depth."""
    try:
        rel = output_path.parent.relative_to(PUBLIC_DIR)
        depth = len(rel.parts)
    except Exception:
        depth = 0

    prefix = '../' * depth
    updated = html
    updated = updated.replace('href="styles.css"', f'href="{prefix}styles.css"')
    updated = updated.replace('src="scripts.js"', f'src="{prefix}scripts.js"')
    return updated


def main() -> None:
    page_template = load_template(TEMPLATE_FILE)
    gallery_template = load_template(TEMPLATE_GALLERY_FILE)
    event_template = load_template(TEMPLATE_EVENT_FILE)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    copy_static_assets()

    page_files = sorted(PAGES_DIR.glob('*.yaml'))
    pages_data = [load_page_data(page_file) for page_file in page_files]
    gallery_pages = scan_gallery_pages()
    events_map = scan_event_directories()
    all_pages = pages_data

    if not pages_data and not gallery_pages and not events_map:
        print(f'No pages or galleries found in {PAGES_DIR} or {GALLERIES_DIR}')
        return

    for page_data in all_pages:
        current_path = str(page_data.get('nav_path', page_data['path'])).lstrip('/')
        page_nav_html = build_nav(pages_data, current_path, 'Pages')
        gallery_nav_html = build_nav(gallery_pages, current_path, 'Galleries')
        template = page_template if page_data in pages_data else gallery_template
        content = str(page_data['content'])

        if template is gallery_template:
            gallery_name = Path(page_data['path']).stem
            gallery_events = events_map.get(gallery_name, [])
            if gallery_events:
                event_items = ''.join(
                    f'<li><a href="./{gallery_name}/{ev["name"]}/index.html">{ev["title"]}</a></li>'
                    for ev in gallery_events
                )
                content += '\n\n<h2>Events</h2>\n<ul>' + event_items + '</ul>'

        output_text = render_page(
            template,
            title=str(page_data['title']),
            content=content,
            page_nav=page_nav_html,
            gallery_nav=gallery_nav_html,
        )
        output_text = adjust_asset_paths(output_text, PUBLIC_DIR / str(page_data['path']).lstrip('/'))

        output_path = PUBLIC_DIR / str(page_data['path']).lstrip('/')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text, encoding='utf-8')
        print(f'Generated {output_path}')

    # Scan for event directories and generate event pages + gallery index pages

    for gallery_name, events in events_map.items():
        for ev in events:
            current_path = str(ev['path']).lstrip('/')
            page_nav_html = build_nav(pages_data, current_path, 'Pages')
            gallery_nav_html = build_nav(gallery_pages, current_path, 'Galleries')

            # Add a direct "Back to gallery" link in the header for event pages
            gallery_link = f'<a class="nav-link" href="../index.html">Back to {gallery_name}</a>'
            # Place the gallery link before the gallery navigation dropdown
            gallery_nav_html = gallery_link + gallery_nav_html

            output_path = PUBLIC_DIR / ev['path']
            # copy event assets (skip event.yaml)
            dest_dir = output_path.parent
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(ev['src'], dest_dir, ignore=shutil.ignore_patterns('event.yaml'))

            # Add cover image if provided in event.yaml
            cover_html = ''
            if ev.get('image_path'):
                cover_html = (
                    f'<div class="gallery-cover"><img src="{ev["image_path"]}" '
                    f'alt="{ev["title"]}"></div>\n'
                )

            # Collect image files in the event directory and render thumbnails
            image_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')
            images = [p.name for p in sorted(dest_dir.iterdir()) if p.is_file() and p.suffix.lower() in image_exts]

            content_with_images = cover_html + str(ev['content'])
            if images:
                imgs_html = '<div class="event-gallery">' + ''.join(
                    f'<a href="{name}"><img src="{name}" alt="{ev["title"]} - {i+1}" class="event-thumb"></a>'
                    for i, name in enumerate(images)
                ) + '</div>'
                content_with_images += '\n\n' + imgs_html

            event_html = render_page(
                event_template,
                title=ev['title'],
                content=content_with_images,
                page_nav=page_nav_html,
                gallery_nav=gallery_nav_html,
            )
            event_html = adjust_asset_paths(event_html, output_path)
            output_path.write_text(event_html, encoding='utf-8')
            print(f'Copied and generated event {output_path}')

        # create gallery index file under public/galleries/<gallery>/index.html
        gallery_data = next((g for g in gallery_pages if g['nav_path'] == f'galleries/{gallery_name}'), None)
        title = gallery_data['title'] if gallery_data else gallery_name
        intro = gallery_data['content'] if gallery_data else ''
        image_html = ''
        if gallery_data and gallery_data.get('image_path'):
            image_html = (
                f'<div class="gallery-cover"><img src="{gallery_data["image_path"]}" '
                f'alt="{title}"></div>\n'
            )
        items = []
        for ev in events:
            href = f'./{ev["name"]}/index.html'
            items.append(f'<h2><a href="{href}">{ev["title"]}</a></h2>\n<p>{ev["content"]}</p>')

        gallery_index_content = image_html + intro + '\n' + '\n'.join(items)
        gallery_index_path = PUBLIC_DIR / f'galleries/{gallery_name}/index.html'
        page_nav_html = build_nav(pages_data, f'galleries/{gallery_name}', 'Pages')
        gallery_nav_html = build_nav(gallery_pages, f'galleries/{gallery_name}', 'Galleries')
        gallery_html = render_page(
            gallery_template,
            title=title,
            content=gallery_index_content,
            page_nav=page_nav_html,
            gallery_nav=gallery_nav_html,
        )
        gallery_html = adjust_asset_paths(gallery_html, gallery_index_path)
        gallery_index_path.parent.mkdir(parents=True, exist_ok=True)
        gallery_index_path.write_text(gallery_html, encoding='utf-8')
        print(f'Generated gallery index {gallery_index_path}')


if __name__ == '__main__':
    main()
