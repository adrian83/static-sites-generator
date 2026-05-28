"""Template rendering and navigation building functions."""
from pathlib import Path

from .config import PUBLIC_DIR


def render_page(
    template: str,
    title: str,
    content: str,
    page_nav: str,
    gallery_nav: str,
    tag_counts: str = '',
    page_links: str = '',
) -> str:
    """Render a page template with given data."""
    return (
        template
        .replace('{{title}}', title)
        .replace('{{content}}', content)
        .replace('{{page_nav}}', page_nav)
        .replace('{{gallery_nav}}', gallery_nav)
        .replace('{{tag_counts}}', tag_counts)
        .replace('{{page_links}}', page_links)
    )


def build_nav(pages: list[dict], current_path: str, label: str) -> str:
    """Build navigation HTML from page list."""
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


def adjust_asset_paths(html: str, output_path: Path) -> str:
    """Adjust `styles.css` and `scripts.js` paths based on output depth."""
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
