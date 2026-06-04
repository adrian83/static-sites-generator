"""Main generator logic for creating static site."""
import shutil
try:
    from PIL import Image, ImageOps
except Exception:  # Pillow may not be installed yet
    Image = None
    ImageOps = None
from pathlib import Path
import html
try:
    from markdown import markdown as _md_to_html
except Exception:
    _md_to_html = None

from .config import (
    BASE_DIR, PUBLIC_DIR, TEMPLATE_FILE, TEMPLATE_GALLERY_FILE, TEMPLATE_EVENT_FILE, STATIC_ASSETS, PAGES_DIR
)
from .loaders import load_template, load_page_data, scan_gallery_pages, scan_event_directories
from .renderers import render_page, build_nav, adjust_asset_paths


def copy_static_assets() -> None:
    """Copy static assets (CSS, JS) to public directory."""
    for asset_name in STATIC_ASSETS:
        asset_path = BASE_DIR / asset_name
        if not asset_path.exists():
            raise FileNotFoundError(f"Static asset not found: {asset_path}")
        destination = PUBLIC_DIR / asset_name
        shutil.copy2(asset_path, destination)
        print(f'Copied {asset_name} to {destination}')


def generate_pages(page_template: str, gallery_template: str, pages_data: list[dict], 
                   gallery_pages: list[dict], events_map: dict) -> None:
    """Generate page HTML files."""
    for page_data in pages_data:
        current_path = str(page_data.get('nav_path', page_data['path'])).lstrip('/')
        page_nav_html = build_nav(pages_data, current_path, 'Pages')
        gallery_nav_html = build_nav(gallery_pages, current_path, 'Galleries')
        content = render_markdown(page_data.get('content', ''))

        output_text = render_page(
            page_template,
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


def create_main_image(src_path: Path, dest_path: Path, target_width: int = 600, target_height: int = 400) -> None:
    """Create a width-limited main image and crop it to the requested height."""
    with Image.open(src_path) as img:
        # Apply EXIF orientation if available so images are upright
        if ImageOps is not None:
            img = ImageOps.exif_transpose(img)

        width, height = img.size
        if width == 0 or height == 0:
            raise ValueError(f'Invalid image size for {src_path}')

        new_height = max(1, int(target_width * height / width))
        resized = img.resize((target_width, new_height), Image.LANCZOS)
        if new_height >= target_height:
            top = (new_height - target_height) // 2
            cropped = resized.crop((0, top, target_width, top + target_height))
        else:
            cropped = resized

        dest_path.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(dest_path, format='JPEG', quality=85)


def render_markdown(text: str) -> str:
    """Convert markdown text to HTML. If Markdown isn't installed, fall back to simple paragraphs."""
    if text is None:
        return ''
    s = str(text)
    if _md_to_html is not None:
        try:
            return _md_to_html(s, extensions=['extra', 'sane_lists'])
        except Exception:
            pass

    # Fallback: escape and convert paragraphs/linebreaks
    escaped = html.escape(s)
    paras = [p.strip() for p in escaped.split('\n\n') if p.strip()]
    return ''.join(f'<p>{p.replace('\n', '<br>')}</p>' for p in paras)


def create_thumbnail(src_path: Path, dest_path: Path, target_height: int = 200) -> None:
    """Create a height-limited thumbnail preserving aspect ratio."""
    with Image.open(src_path) as img:
        # Apply EXIF orientation so thumbnails keep correct orientation
        if ImageOps is not None:
            img = ImageOps.exif_transpose(img)

        width, height = img.size
        if width == 0 or height == 0:
            raise ValueError(f'Invalid image size for {src_path}')

        new_width = max(1, int(width * (target_height / height)))
        resized = img.resize((new_width, target_height), Image.LANCZOS)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        resized.save(dest_path, format='JPEG', quality=85)


def slugify(value: str) -> str:
    return '-'.join(
        segment for segment in ''.join(
            ch.lower() if ch.isalnum() else '-' for ch in value.strip()
        ).split('-') if segment
    )


def build_tag_counts(event_list: list[dict], gallery_name: str | None = None) -> str:
    tags = {}
    for ev in event_list:
        if gallery_name is None or ev.get('gallery') == gallery_name:
            for tag in ev.get('tags', []):
                tags[tag] = tags.get(tag, 0) + 1

    if not tags:
        return ''

    items = []
    for tag, count in sorted(tags.items(), key=lambda item: (-item[1], item[0])):
        slug = slugify(tag)
        items.append(
            f'<li class="tag-count-item"><a href="/tags_gallery/{slug}/">{tag} <span>({count})</span></a></li>'
        )

    content = '<ul>' + ''.join(items) + '</ul>'
    return (
        '<div class="tag-counts">'
        '<button class="tag-counts-toggle" type="button" aria-expanded="false">📍 Tags</button>'
        '<div class="tag-counts-content">'
        '<h2>Tags</h2>'
        f'{content}'
        '</div>'
        '</div>'
    )


def build_event_card_grid(events: list[dict]) -> str:
    if not events:
        return ''

    items = []
    for ev in sorted(events, key=lambda item: item.get('date_obj'), reverse=True):
        href = '/' + str(ev['path']).lstrip('/')
        main_img_html = ''
        if ev.get('image_path'):
            image_name = Path(ev['image_path']).name
            thumb_path = f'/galleries/{ev["gallery"]}/{ev["name"]}/thumbs/main-{image_name}'
            main_img_html = (
                f'<a class="event-card-image-link" href="{href}">'
                f'<img src="{thumb_path}" alt="{ev["title"]}" class="event-card-image"></a>'
            )

        event_item_html = (
            '<div class="event-card">'
            f'{main_img_html}'
            '<div class="event-card-body">'
            f'<h2 class="event-card-title"><a href="{href}">{ev["title"]}</a></h2>'
            f'<p class="event-card-date">{ev["date"]}</p>'
            '</div></div>'
        )
        items.append(event_item_html)

    return '<div class="event-card-grid">' + ''.join(items) + '</div>'


def generate_events(event_template: str, gallery_template: str, gallery_pages: list[dict], 
                    pages_data: list[dict], events_map: dict) -> None:
    """Generate event pages and gallery indices."""
    for gallery_name, events in events_map.items():
        events.sort(key=lambda ev: ev.get('date_obj'), reverse=True)
        for ev in events:
            current_path = str(ev['path']).lstrip('/')
            page_nav_html = build_nav(pages_data, current_path, 'Pages')
            gallery_nav_html = build_nav(gallery_pages, current_path, 'Galleries')

            output_path = PUBLIC_DIR / ev['path']
            dest_dir = output_path.parent
            if dest_dir.exists():
                shutil.rmtree(dest_dir)
            shutil.copytree(ev['src'], dest_dir, ignore=shutil.ignore_patterns('event.yaml'))

            # Create thumbnails and main image for the event
            if Image is None:
                raise RuntimeError('Pillow is required to scale images. Please install via requirements.txt in a virtualenv')

            thumbs_dir = dest_dir / 'thumbs'
            thumbs_dir.mkdir(parents=True, exist_ok=True)
            main_image_name = None
            if ev.get('image_path'):
                main_image_name = Path(ev['image_path']).name
                main_image_src = dest_dir / main_image_name
                main_image_dest = thumbs_dir / f'main-{main_image_name}'
                if main_image_src.exists():
                    try:
                        create_main_image(main_image_src, main_image_dest, target_width=600, target_height=400)
                        ev['main_image_path'] = f'thumbs/main-{main_image_name}'
                        ev['main_image_gallery_path'] = f'./{ev["name"]}/thumbs/main-{main_image_name}'
                    except Exception as e:
                        print(f'Warning: could not create main image for {main_image_src}: {e}')

            for p in sorted(dest_dir.iterdir()):
                if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg') and p.parent == dest_dir:
                    try:
                        thumb_path = thumbs_dir / p.name
                        create_thumbnail(p, thumb_path, target_height=200)
                    except Exception as e:
                        print(f'Warning: could not create thumbnail for {p}: {e}')

            # Add cover image if provided in event.yaml
            cover_html = ''
            main_cover_path = ev.get('main_image_path')
            if main_cover_path:
                cover_html = (
                    f'<div class="gallery-cover"><img src="{main_cover_path}" '
                    f'alt="{ev["title"]}"></div>\n'
                )

            # Collect original images and use scaled versions for display (link to original)
            image_exts = ('.jpg', '.jpeg')
            originals = [p.name for p in sorted(dest_dir.iterdir()) if p.is_file() and p.suffix.lower() in image_exts and p.parent == dest_dir]

            content_with_images = cover_html + render_markdown(ev.get('content', ''))
            if originals:
                imgs_html = '<div class="event-gallery">'
                for i, orig in enumerate(originals):
                    thumb_rel = f'thumbs/{orig}'
                    thumb_exists = (dest_dir / 'thumbs' / orig).exists()
                    thumb_src = thumb_rel if thumb_exists else orig
                    imgs_html += (
                        f'<a href="{orig}"><img src="{thumb_src}" alt="{ev["title"]} - {i+1}" class="event-thumb"></a>'
                    )
                imgs_html += '</div>'
                content_with_images += '\n\n' + imgs_html

            tag_counts_html = build_tag_counts(events, gallery_name)
            event_html = render_page(
                event_template,
                title=ev['title'],
                content=content_with_images,
                page_nav=page_nav_html,
                gallery_nav=gallery_nav_html,
                tag_counts=tag_counts_html,
            )
            event_html = adjust_asset_paths(event_html, output_path)
            output_path.write_text(event_html, encoding='utf-8')
            print(f'Copied and generated event {output_path}')

        # Create gallery index file
        gallery_data = next((g for g in gallery_pages if g['nav_path'] == f'galleries/{gallery_name}'), None)
        title = gallery_data['title'] if gallery_data else gallery_name
        intro = render_markdown(gallery_data.get('content', '')) if gallery_data else ''
        image_html = ''
        if gallery_data and gallery_data.get('image_src'):
            gallery_image_src = gallery_data['image_src']
            gallery_thumb_dir = PUBLIC_DIR / f'galleries/{gallery_name}/thumbs'
            gallery_thumb_dir.mkdir(parents=True, exist_ok=True)
            gallery_main_dest = gallery_thumb_dir / f'main-{gallery_image_src.name}'
            try:
                create_main_image(gallery_image_src, gallery_main_dest, target_width=600, target_height=400)
                image_html = (
                    f'<div class="gallery-cover"><img src="./thumbs/main-{gallery_image_src.name}" '
                    f'alt="{title}"></div>\n'
                )
            except Exception as e:
                print(f'Warning: could not create gallery main image for {gallery_image_src}: {e}')
        elif gallery_data and gallery_data.get('image_path'):
            image_html = (
                f'<div class="gallery-cover"><img src="{gallery_data["image_path"]}" '
                f'alt="{title}"></div>\n'
            )
        items = []
        for ev in sorted(events, key=lambda item: item.get('date_obj'), reverse=True):
            href = f'./{ev["name"]}/index.html'
            event_item_html = '<div class="event-card">'
            main_gallery_path = ev.get('main_image_gallery_path')
            if main_gallery_path:
                event_item_html += (
                    f'<a class="event-card-image-link" href="{href}">'
                    f'<img src="{main_gallery_path}" alt="{ev["title"]}" class="event-card-image"></a>'
                )
            event_item_html += (
                '<div class="event-card-body">'
                f'<h2 class="event-card-title"><a href="{href}">{ev["title"]}</a></h2>'
                f'<p class="event-card-date">{ev["date"]}</p>'
                '</div></div>'
            )
            items.append(event_item_html)

        gallery_index_content = image_html + intro + '\n<div class="event-card-grid">' + '\n'.join(items) + '</div>'
        gallery_index_path = PUBLIC_DIR / f'galleries/{gallery_name}/index.html'
        page_nav_html = build_nav(pages_data, f'galleries/{gallery_name}', 'Pages')
        gallery_nav_html = build_nav(gallery_pages, f'galleries/{gallery_name}', 'Galleries')
        gallery_html = render_page(
            gallery_template,
            title=title,
            content=gallery_index_content,
            page_nav=page_nav_html,
            gallery_nav=gallery_nav_html,
            tag_counts=build_tag_counts(events, gallery_name),
        )
        gallery_html = adjust_asset_paths(gallery_html, gallery_index_path)
        gallery_index_path.parent.mkdir(parents=True, exist_ok=True)
        gallery_index_path.write_text(gallery_html, encoding='utf-8')
        print(f'Generated gallery index {gallery_index_path}')


def generate_tag_pages(gallery_template: str, pages_data: list[dict], gallery_pages: list[dict], events_map: dict) -> None:
    tags = {}
    for gallery_events in events_map.values():
        for ev in gallery_events:
            for tag in ev.get('tags', []):
                tags.setdefault(tag, []).append(ev)

    tags_dir = PUBLIC_DIR / 'tags_gallery'
    if tags_dir.exists():
        shutil.rmtree(tags_dir)

    all_events = [ev for gallery_events in events_map.values() for ev in gallery_events]
    for tag, events in sorted(tags.items(), key=lambda item: item[0]):
        slug = slugify(tag)
        output_path = PUBLIC_DIR / f'tags_gallery/{slug}/index.html'
        output_path.parent.mkdir(parents=True, exist_ok=True)

        page_nav_html = build_nav(pages_data, f'tags_gallery/{slug}', 'Pages')
        gallery_nav_html = build_nav(gallery_pages, f'tags_gallery/{slug}', 'Galleries')

        tag_page_cover = ''
        if events:
            sorted_events = sorted(events, key=lambda item: item.get('date_obj'), reverse=True)
            for ev in sorted_events:
                if ev.get('image_path'):
                    image_name = Path(ev['image_path']).name
                    main_gallery_path = f'/galleries/{ev["gallery"]}/{ev["name"]}/thumbs/main-{image_name}'
                    tag_page_cover = (
                        f'<div class="gallery-cover"><img src="{main_gallery_path}" '
                        f'alt="{ev["title"]}"></div>\n'
                    )
                    break

        # Place tag events into a gallery-style card grid in the main content area
        tag_page_html = render_page(
            gallery_template,
            title=tag,
            content=tag_page_cover + build_event_card_grid(events),
            page_nav=page_nav_html,
            gallery_nav=gallery_nav_html,
            tag_counts=build_tag_counts(all_events),
            page_links='',
        )
        tag_page_html = adjust_asset_paths(tag_page_html, output_path)
        output_path.write_text(tag_page_html, encoding='utf-8')
        print(f'Generated tag page {output_path}')


def build() -> None:
    """Build the entire static site."""
    # Load templates
    page_template = load_template(TEMPLATE_FILE)
    gallery_template = load_template(TEMPLATE_GALLERY_FILE)
    event_template = load_template(TEMPLATE_EVENT_FILE)

    # Initialize output directory
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    copy_static_assets()

    # Load data
    page_files = sorted(PAGES_DIR.glob('*.yaml'))
    pages_data = [load_page_data(page_file) for page_file in page_files]
    gallery_pages = scan_gallery_pages()
    events_map = scan_event_directories()

    if not pages_data and not gallery_pages and not events_map:
        print(f'No pages or galleries found in {PAGES_DIR}')
        return

    # Generate pages
    generate_pages(page_template, gallery_template, pages_data, gallery_pages, events_map)

    # Generate events and gallery indices
    generate_events(event_template, gallery_template, gallery_pages, pages_data, events_map)

    # Generate tag pages for all event tags
    generate_tag_pages(gallery_template, pages_data, gallery_pages, events_map)
