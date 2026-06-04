# Static Sites Generator

This project is a minimal static site generator for a gallery website. It reads YAML files for pages, galleries, and events, applies HTML templates, generates a `public/` static site, and can serve the generated output locally.

## Goal

- Generate static HTML pages from YAML content and templates
- Support gallery overview pages and event pages with image thumbnails
- Allow markdown in `content` fields so text renders as HTML
- Support a simple local server for previewing the generated site

## Requirements

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

## Run the generator

Generate the static site into `public/` using:

```bash
python run.py
```

This copies static assets, processes templates, and writes HTML into `public/`.

## Preview the results

Use the built-in local server to preview the generated site:

```bash
python server.py
```

Then open:

```
http://0.0.0.0:8000
```

## Directory structure

The expected layout is:

```text
.
├── galleries/
│   ├── <gallery-name>/
│   │   ├── gallery.yaml
│   │   ├── <event-name>/
│   │   │   ├── event.yaml
│   │   │   ├── IMG_....jpg
│   │   │   └── ...
│   │   └── ...
│   └── ...
├── pages/
│   ├── index.yaml
│   ├── about.yaml
│   └── ...
├── public/
│   ├── index.html
│   ├── about/index.html
│   ├── galleries/
│   ├── tags_gallery/
│   ├── styles.css
│   └── scripts.js
├── ssg/
│   ├── config.py
│   ├── generator.py
│   ├── loaders.py
│   ├── renderers.py
│   └── ...
├── template_page.html
├── template_gallery.html
├── template_event.html
├── run.py
├── server.py
└── requirements.txt
```

## YAML file contents

### `pages/*.yaml`

Each top-level page must contain:

- `path`: output path for the page, e.g. `index.html` or `about/index.html`
- `title`: page title shown in the page header and `<title>` tag
- `content`: markdown content for the page body

Example:

```yaml
path: index.html
title: Home
content: |
  Welcome to the gallery site.
  
  - Explore galleries
  - Browse events
```

### `galleries/<gallery>/gallery.yaml`

Each gallery directory must contain a `gallery.yaml` with:

- `title`: gallery title
- `content`: markdown intro text for the gallery page
- `image_path` (optional): relative path to a gallery cover image inside the gallery directory

Example:

```yaml
title: Sea
content: |
  A gallery of seaside photos and coastal views.
image_path: cover.jpg
```

### `galleries/<gallery>/<event>/event.yaml`

Each event directory must contain `event.yaml` with:

- `title`: event title
- `content`: markdown text for the event page body
- `date`: event date in `YYYY-MM-DD` format
- `tags`: list of tags for the event
- `image_path` (optional): image file name used as the main event cover image

Example:

```yaml
title: Sea 1
content: |
  Pictures of the sea from around the world.
  
  **Highlights**:
  - sunrise shots
  - water motion blur
date: 2024-06-01
tags:
  - ocean
  - sea
  - water
image_path: IMG_20240601_123456.jpg
```

## Markdown support

The `content` field in all YAML files may contain markdown. It is rendered to HTML when the site is generated.

## Templates

- `template_page.html`: used for top-level pages
- `template_gallery.html`: used for gallery index pages and tag pages
- `template_event.html`: used for event pages

These templates use simple placeholders like `{{title}}`, `{{content}}`, `{{page_nav}}`, `{{gallery_nav}}`, and `{{tag_counts}}`.

## Notes

- Place image files alongside `event.yaml` inside each event directory.
- The generator currently supports `.jpg` and `.jpeg` event images for thumbnails.
- The `public/` folder is overwritten by the generator output.
