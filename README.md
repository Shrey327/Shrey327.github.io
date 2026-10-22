# Shreyansh Pathak

Personal technical blog at https://shrey327.github.io/.

## Build

Python 3.13 or newer builds the site with the standard library. Node.js runs the small theme behavior check. No packages need to be installed.

```sh
python3 tools/check.py
node tools/check_theme.cjs
python3 build.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:8000/ for local review. GitHub Actions validates the source and deploys the generated `dist/` directory to GitHub Pages on pushes to `main`.

## Content

Published articles have JSON manifests and HTML bodies in `content/posts/`. Each manifest specifies a title, description, ISO publication date, lowercase slug, tag slugs and sibling HTML body filename. Public source links and attribution appear in the articles.

Unpublished work belongs in `content/drafts/`. The normal build excludes drafts from output, RSS and sitemap. `python3 build.py --preview` includes drafts for local review with noindex/nofollow on every page. Keep that output local.

The monochrome theme follows system preference until an explicit choice is made. The small local theme script stores that choice in browser local storage. There are no analytics, remote fonts or third-party rendering scripts. Without JavaScript, the theme follows the system preference.

The content checker validates internal links, anchors, metadata, XML feeds, publication boundaries and prose punctuation. Article text uses no en dash, em dash or comma followed by the word "and".

## Structure

- `content/pages/`: homepage, About and project index.
- `content/posts/`: published technical articles.
- `assets/`: CSS, theme script and local images.
- `build.py`: static output generator with root and project-path support.
- `tools/`: isolated build and theme checks.
- `.github/workflows/pages.yml`: GitHub Pages build and deployment.
