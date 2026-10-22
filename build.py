"""Small static blog builder. Python standard library only."""
import argparse
import html
import hashlib
from datetime import datetime, timezone
from email.utils import format_datetime
import json
from pathlib import Path
import re
import shutil
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def build(preview=False, base_path='', site_url=None):
    config = json.loads((ROOT / 'site.json').read_text())
    origin = (site_url or config['url']).rstrip('/')
    if urlsplit(origin).scheme != 'https' or not urlsplit(origin).hostname or urlsplit(origin).path or urlsplit(origin).query or urlsplit(origin).fragment or urlsplit(origin).username:
        raise ValueError('Site URL must be an HTTPS origin without a path')
    base = '/' + base_path.strip('/') + '/' if base_path.strip('/') else '/'
    if not re.fullmatch(r'/[A-Za-z0-9/_-]*', base) or '..' in base:
        raise ValueError('Invalid base path')
    out = ROOT / ('preview' if preview else 'dist')
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    shutil.copytree(ROOT / 'assets', out / 'assets')
    (out / '.nojekyll').touch()
    asset_version = hashlib.sha256(b''.join((ROOT/'assets'/name).read_bytes() for name in ('style.css','theme.js','favicon.svg'))).hexdigest()[:12]
    pages = []
    esc = html.escape
    def render(route, title, description, body, active='', draft=False, article=False):
        canonical = origin + base + route
        robots = '<meta name="robots" content="noindex, nofollow">' if preview or draft else ''
        nav = ''.join(f'<a href="{base}{slug}"' + (' aria-current="page"' if active == label else '') + f'>{label}</a>' for label, slug in [('Writing',''),('Projects','projects/'),('About','about/'),('Archive','archive/')])
        banner = '<aside class="review-banner">Local review copy. Article drafts are excluded from the publishing build.</aside>' if preview else ''
        doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} | {esc(config['name'])}</title><meta name="description" content="{esc(description, quote=True)}">{robots}<link rel="canonical" href="{esc(canonical, quote=True)}"><meta property="og:type" content="{'article' if draft or article else 'website'}"><meta property="og:title" content="{esc(title, quote=True)}"><meta property="og:description" content="{esc(description, quote=True)}"><meta property="og:url" content="{esc(canonical, quote=True)}"><meta property="og:site_name" content="{esc(config['name'])}"><meta property="og:image" content="{origin}{base}assets/og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Shreyansh Pathak. Notes on machine learning systems."><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="{base}assets/favicon.svg?v={asset_version}" type="image/svg+xml"><link rel="alternate" type="application/rss+xml" title="Shreyansh Pathak RSS" href="{base}feed.xml"><script src="{base}assets/theme.js?v={asset_version}"></script><link rel="stylesheet" href="{base}assets/style.css?v={asset_version}"></head><body><a class="skip" href="#main">Skip to content</a><header><a class="wordmark" aria-label="Shreyansh Pathak home" href="{base}">SP<span aria-hidden="true">.</span></a><nav aria-label="Main navigation">{nav}<button class="theme-toggle" type="button" data-theme-toggle aria-label="Dark theme" aria-pressed="false" hidden>Dark mode</button></nav></header><main id="main" tabindex="-1">{banner}{body.replace('{{base}}',base)}</main><footer><span>© 2026 Shreyansh Pathak</span><nav aria-label="Footer navigation"><a href="{base}tags/">Tags</a><a href="{base}feed.xml">RSS</a><a href="https://github.com/Shrey327">GitHub</a></nav></footer></body></html>'''
        target = out / route / 'index.html' if route else out / 'index.html'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(doc)
        if not draft:
            pages.append(canonical)
    # Explicit publication boundary: only content/posts is eligible for RSS and sitemap.
    posts = [json.loads(p.read_text()) for p in sorted((ROOT/'content/posts').glob('*.json'))]
    posts.sort(key=lambda x: x['date'], reverse=True)
    drafts = [dict(json.loads(p.read_text()), draft=True) for p in sorted((ROOT/'content/drafts').glob('*.json'))] if preview else []
    visible_posts = posts + drafts
    def listing(items):
        return '<ul class="plain-list">' + ''.join(f'<li><a href="{base}{"drafts" if p.get("draft") else "posts"}/{esc(p["slug"])}/">{esc(p["title"])}</a><p class="article-meta">{"Unpublished draft · revised " if p.get("draft") else ""}{esc(p["date"])}</p><p>{esc(p["description"])}</p></li>' for p in items) + '</ul>' if items else ''
    for p in posts:
        if not re.fullmatch(r'[a-z0-9-]+', p['slug']):
            raise ValueError('Post slugs must use lowercase letters, numbers or hyphens')
        if Path(p['body']).name != p['body'] or not p['body'].endswith('.html'):
            raise ValueError('Post body must name a sibling HTML file')
        datetime.fromisoformat(p['date'])
        body = (ROOT/'content/posts'/p['body']).read_text()
        render('posts/'+p['slug']+'/',p['title'],p['description'],f'<article><h1>{esc(p["title"])}</h1><p class="article-meta">{esc(p["date"])} · Shreyansh Pathak</p><div>{"".join(f'<a class="tag" href="{base}tags/{esc(t)}/">{esc(t)}</a>' for t in p['tags'])}</div>{body}</article>',article=True)
    for slug, title in [('', 'Notes on machine learning systems'),('about/','About'),('projects/','Projects')]:
        body=(ROOT/'content/pages'/('home.html' if not slug else slug.strip('/')+'.html')).read_text()
        draft_link = listing(drafts)
        render(slug,title,config['description'],body.replace('{{posts}}',listing(posts)).replace('{{draft_link}}',draft_link),{'':'Writing','about/':'About','projects/':'Projects'}[slug])
    render('archive/','Archive','Published technical notes by date.','<p class="eyebrow">Writing</p><h1>Archive</h1>'+ (listing(visible_posts) or '<p>No articles published on this site yet.</p><p>New notes will appear here with their publication dates.</p>'), 'Archive')
    tags=sorted({t for p in visible_posts for t in p['tags']})
    render('tags/','Tags','Browse technical notes by topic.','<p class="eyebrow">Topics</p><h1>Tags</h1>'+(''.join(f'<a class="tag" href="{base}tags/{esc(t)}/">{esc(t)}</a>' for t in tags) or '<p>Topics will appear here when the first article is published.</p>'))
    for tag in tags:
        if not re.fullmatch(r'[a-z0-9-]+',tag):
            raise ValueError('Tags must use lowercase slugs')
        render('tags/'+tag+'/',tag, 'Articles tagged '+tag, '<h1>'+esc(tag)+'</h1>'+listing([p for p in visible_posts if tag in p['tags']]),draft=not any(tag in p['tags'] for p in posts))
    render('404/','Page not found','The requested page could not be found.','<h1>Page not found</h1><p>Try the <a href="'+base+'">homepage</a> or <a href="'+base+'archive/">archive</a>.</p>')
    shutil.copy(out/'404/index.html', out/'404.html')
    pages.pop()  # Do not advertise the error page in sitemap.
    if preview:
        for path in (ROOT/'content/drafts').glob('*.json'):
            p=json.loads(path.read_text())
            body=(path.parent/p['body']).read_text()
            render('drafts/'+p['slug']+'/',p['title'],p['description'],f'<article><p class="eyebrow">Unpublished article draft</p><h1>{esc(p["title"])}</h1><p class="article-meta">Shreyansh Pathak · Revised {esc(p["date"])} · {max(1, round(len(re.findall(r"\w+", re.sub(r"<[^>]+>", " ", body))) / 220))} min read</p>{body}</article>',draft=True)
    rss=ET.Element('rss',version='2.0'); channel=ET.SubElement(rss,'channel')
    for k,v in [('title',config['name']),('link',origin+base),('description',config['description']),('language','en')]: ET.SubElement(channel,k).text=v
    for p in posts:
        item=ET.SubElement(channel,'item')
        ET.SubElement(item,'pubDate').text=format_datetime(datetime.fromisoformat(p['date']).replace(tzinfo=timezone.utc))
        for k,v in [('title',p['title']),('link',origin+base+'posts/'+p['slug']+'/'),('guid',origin+base+'posts/'+p['slug']+'/'),('description',p['description'])]: ET.SubElement(item,k).text=v
    ET.ElementTree(rss).write(out/'feed.xml',encoding='utf-8',xml_declaration=True)
    sitemap=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for url in pages: ET.SubElement(ET.SubElement(sitemap,'url'),'loc').text=url
    ET.ElementTree(sitemap).write(out/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n' if preview else 'User-agent: *\nAllow: /\nSitemap: '+origin+base+'sitemap.xml\n')
    print(f'Built {out.name}: {len(pages)} primary pages, {len(posts)} published articles. Drafts: {"preview only" if preview else "excluded"}.')
    return out

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--base-path',default='')
    parser.add_argument('--site-url')
    args=parser.parse_args()
    build(args.preview,args.base_path,args.site_url)
