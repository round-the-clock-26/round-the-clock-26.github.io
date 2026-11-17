"""Fetch free-licensed driver portraits from Wikidata/Wikimedia Commons.

For every driver in the bundle: find the Wikidata item whose occupation is racing driver,
take its image (P18, always a Commons file, so freely licensed), download a small thumbnail
to drivers/ and record author + licence in drivers/credits.json. Drivers without a
verified item or image are skipped (they keep a name-only entry on the page).
"""
import glob, html, json, os, re, time, urllib.error, urllib.parse, urllib.request

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {'User-Agent': 'round-the-clock-fan-site/1.0'}
# Wikidata image checked by eye and not usable as a portrait (a car, a tiny figure, two people)
NOT_A_PORTRAIT = {'Anthony McIntosh', 'Daniel Juncadella', 'Dries Vanthoor', 'Jonny Edgar', 'Peter Dempsey', 'Antares Au', 'Sebastian Priaulx',
                  'Mathieu Jaminet', 'Mathys Jaubert', 'Mattia Drudi', 'Simon Mann', 'Zacharie Robichon'}
RACING_DRIVER = {'Q378622', 'Q10841764', 'Q15117302'}  # racing driver, racecar driver, sports car racing driver

def fetch(url):
    # Wikimedia rate-limits generic clients: back off on 429 instead of hammering
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5: raise
            time.sleep(int(e.headers.get('Retry-After') or 0) or 20 * (attempt + 1))

def get(url, **q):
    return json.loads(fetch(url + '?' + urllib.parse.urlencode({**q, 'format': 'json'})))

def drivers():
    src = [p for p in glob.glob(f'{root}/assets/app-*.js') if not p.endswith('app-ko.js')][0]
    s = open(src, encoding='utf-8').read()
    names = re.findall(r'\[`([^`]+)`,`[A-Z]{3}`\]', s)                 # Hypercar crews: [name, NAT]
    for crew in re.findall(r'crew:\[(`[^`\]]+`(?:,`[^`\]]+`)+)\]', s):   # LMGT3 crews: [name, name, name]
        names += re.findall(r'`([^`]+)`', crew)
    return sorted(set(names))

def wikidata_image(name):
    hits = get('https://www.wikidata.org/w/api.php', action='wbsearchentities', search=name, language='en', limit=10)['search']
    if not hits: return None
    ents = get('https://www.wikidata.org/w/api.php', action='wbgetentities', ids='|'.join(h['id'] for h in hits), props='claims')['entities']
    for h in hits:
        claims = ents[h['id']].get('claims', {})
        jobs = {c['mainsnak'].get('datavalue', {}).get('value', {}).get('id') for c in claims.get('P106', [])}
        driver = jobs & RACING_DRIVER or re.search(r'\b(racing|racecar|race car|motorsport) driver', h.get('description', ''), re.I)
        if driver and 'P18' in claims:
            return h['id'], claims['P18'][0]['mainsnak']['datavalue']['value']
    return None

def commons_info(filename):
    pages = get('https://commons.wikimedia.org/w/api.php', action='query', titles='File:' + filename,
                prop='imageinfo', iiprop='url|extmetadata', iiurlwidth=320)['query']['pages']
    ii = next(iter(pages.values()))['imageinfo'][0]
    meta = ii['extmetadata']
    strip = lambda v: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', '', v))).strip()
    return {
        'thumb': ii['thumburl'],
        'page': ii['descriptionurl'],
        'author': strip(meta.get('Artist', {}).get('value', 'Unknown')),
        'license': strip(meta.get('LicenseShortName', {}).get('value', '')),
        'licenseUrl': meta.get('LicenseUrl', {}).get('value', ''),
    }

def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower().encode('ascii', 'ignore').decode()).strip('-')

if __name__ == '__main__':
    os.makedirs(f'{root}/drivers', exist_ok=True)
    done = f'{root}/drivers/credits.json'
    out, missing = (json.load(open(done, encoding='utf-8')) if os.path.exists(done) else {}), []
    for name in drivers():
        if name in out or name in NOT_A_PORTRAIT: continue  # resumable; skip rejected photos
        try:
            found = wikidata_image(name)
            if not found: missing.append(name); continue
            qid, filename = found
            info = commons_info(filename)
            # Commons only hosts free files, but refuse anything not clearly CC/public domain anyway
            if not re.match(r'(CC|Public domain|PD)', info['license'], re.I): missing.append(name + ' (licence: ' + info['license'] + ')'); continue
            path = f'drivers/{slug(name)}.jpg'
            open(f'{root}/{path}', 'wb').write(fetch(info['thumb']))
            out[name] = {'src': './' + path, 'wikidata': qid, 'file': filename, **{k: info[k] for k in ('page', 'author', 'license', 'licenseUrl')}}
            print('ok  ', name, '|', info['license'], '|', info['author'][:40])
        except Exception as e:
            missing.append(f'{name} (error: {e})')
        time.sleep(2)
    json.dump(out, open(f'{root}/drivers/credits.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n{len(out)} photos, {len(missing)} without:', *missing, sep='\n  ')
