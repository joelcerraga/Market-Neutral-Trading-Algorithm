"""Check the generated site's local links, metadata and preserved research outputs."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import hashlib
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://joelcerraga.github.io/Market-Neutral-Trading-Algorithm/"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.meta, self.h1_count = [], set(), {}, 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'h1':
            self.h1_count += 1
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if tag == 'meta':
            self.meta[attrs.get('property', attrs.get('name'))] = attrs.get('content')
        for key in ['href', 'src', 'data-src']:
            if attrs.get(key):
                self.links.append(attrs[key])


def verify():
    pages = [ROOT / 'index.html', *sorted((ROOT / 'explorers').rglob('index.html'))]
    assert len(pages) == 6
    parsed = {}
    for path in pages:
        p = Page(); p.feed(path.read_text()); parsed[path.resolve()] = p
        assert p.h1_count == 1, path
        assert p.meta['og:url'].startswith(BASE), path
        assert p.meta['og:image'].startswith(BASE + 'assets/thumbnails/'), path
        assert p.meta['twitter:card'] == 'summary_large_image', path
        assert (ROOT / p.meta['og:image'].removeprefix(BASE)).is_file()
    link_count = 0
    for path, page in parsed.items():
        for link in page.links:
            u = urlsplit(link)
            if u.scheme or u.netloc:
                continue
            target = (path.parent / unquote(u.path)).resolve() if u.path else path
            if target.is_dir():
                target /= 'index.html'
            assert target.exists(), (path.relative_to(ROOT), link)
            if u.fragment and target in parsed:
                assert u.fragment in parsed[target].ids, (target, u.fragment)
            link_count += 1
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    assert len(ET.parse(ROOT / 'sitemap.xml').findall('s:url', ns)) == 6
    inventory = json.loads((ROOT / 'package-manifest.json').read_text())['files']
    outputs = {p: item for p, item in inventory.items() if p.startswith('outputs/')}
    assert len(outputs) == 175
    assert all(hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == item['sha256'] for p, item in outputs.items())
    assert not (ROOT / 'GITHUB_UPLOAD.md').exists()
    return {'status': 'passed', 'pages': 6, 'local_links_checked': link_count,
            'social_thumbnails': 2, 'unchanged_research_outputs': 175}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
