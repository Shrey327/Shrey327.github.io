"""Build checks for publication boundaries, local links and prose style."""
from html.parser import HTMLParser
from pathlib import Path
import importlib.util
import json
import re
import shutil
import tempfile
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blog_build',ROOT/'build.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__(convert_charrefs=True)
        self.links=[]; self.scripts=[]; self.ids=set(); self.text=[]; self.h1=0; self.noindex=False; self.canonical=False
        self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='script':
            self.scripts.append(attrs.get('src'))
            if attrs.get('src'): self.links.append(attrs['src'])
        if tag=='h1': self.h1+=1
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, 'Duplicate id'
            self.ids.add(attrs['id'])
        if tag in ('a','link') and 'href' in attrs: self.links.append(attrs['href'])
        if tag=='meta' and attrs.get('name')=='robots': self.noindex='noindex' in attrs.get('content','')
        if tag=='link' and attrs.get('rel')=='canonical': self.canonical=True
    def handle_data(self,data): self.text.append(data)

def check_output(out,base='/',preview=False):
    for path in out.rglob('*.html'):
        source=path.read_text()
        assert source.index('assets/theme.js') < source.index('assets/style.css'), 'Theme must precede stylesheet'
        page=Page(source)
        assert 'https://medium.com/p/' not in path.read_text(), f'Private editor link: {path}'
        assert page.h1==1, path
        assert page.canonical, path
        assert len(page.scripts)==1 and urlsplit(page.scripts[0] or '').path==base+'assets/theme.js', f'Unexpected script: {path}'
        assert page.noindex==preview, path
        text=' '.join(page.text)
        assert not re.search('[\u2013\u2014]|,\\s+and\\b',text,re.I), f'Prose style: {path}'
        for link in page.links:
            url=urlsplit(link)
            if url.scheme or url.netloc: continue
            raw=unquote(url.path)
            if not raw: target=path
            else:
                assert raw.startswith(base), (path,link)
                target=out/raw[len(base):]
                if target.is_dir(): target=target/'index.html'
            assert target.exists(), (path,link)
            if url.fragment: assert unquote(url.fragment) in Page(target.read_text()).ids,(path,link)
    ET.parse(out/'feed.xml'); ET.parse(out/'sitemap.xml')

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    for item in ['assets','content','site.json']:
        src=ROOT/item
        shutil.copytree(src,root/item) if src.is_dir() else shutil.copy(src,root/item)
    module.ROOT=root
    draft_dir=root/'content/drafts'
    draft_dir.mkdir(parents=True,exist_ok=True)
    fixture={'title':'Private test draft','description':'Publication boundary fixture.','date':'2026-10-22','slug':'private-test-draft','tags':['private-test'],'body':'private-test-draft.html'}
    (draft_dir/'private-test-draft.json').write_text(json.dumps(fixture))
    (draft_dir/'private-test-draft.html').write_text('<p>This fixture must stay unpublished.</p>')
    out=module.build()
    check_output(out)
    assert not (out/'drafts').exists()
    assert 'private-test-draft' not in (out/'feed.xml').read_text()
    assert 'drafts/' not in (out/'sitemap.xml').read_text()
    out=module.build(True)
    check_output(out,preview=True)
    assert (out/'drafts/private-test-draft/index.html').exists()
    assert 'Disallow: /' in (out/'robots.txt').read_text()
    out=module.build(True,base_path='blog')
    check_output(out,base='/blog/',preview=True)
    # A synthetic published post exercises the feed, tag route and archive together.
    post={'title':'Test note','description':'A test description.','date':'2026-10-22','slug':'test-note','tags':['measurement'],'body':'test-note.html'}
    (root/'content/posts/test-note.json').write_text(json.dumps(post))
    (root/'content/posts/test-note.html').write_text('<p>A checked example.</p>')
    out=module.build(base_path='blog')
    check_output(out,base='/blog/')
    assert (out/'tags/measurement/index.html').exists()
    assert 'test-note' in (out/'feed.xml').read_text()
    assert 'test-note' in (out/'archive/index.html').read_text()
    assert 'drafts/' not in (out/'sitemap.xml').read_text()
    try: module.build(base_path='../unsafe')
    except ValueError: pass
    else: raise AssertionError('Invalid path accepted')
print('PASS: root and project paths, preview noindex, draft exclusion, links, anchors, metadata, XML, published feed/archive/tags and prose style.')
