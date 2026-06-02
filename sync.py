#!/usr/bin/env python3
"""
Sync-script: haalt woordenlijsten op uit Google Sheets en werkt index.html bij.

Gebruik:
    python3 sync.py

De data in index.html wordt vervangen tussen de markers:
    // @@DATA_START@@
    // @@DATA_END@@
"""

import urllib.request, csv, io, re, sys, os

SHEET_BASE = (
    'https://docs.google.com/spreadsheets/d/e/'
    '2PACX-1vR2WAYMOoitL_wbt9tIIDpKkCuHHic8kxoDb4qkFaD2YxGtg4RVYAXvosKGPNt62fpmmyfrTaUjzGd0'
    '/pub'
)

TABS = {
    'personages':       {'gid': '0',          'has_short': True},
    'plekken':          {'gid': '1589295359', 'has_short': False},
    'problemen':        {'gid': '1605467095', 'has_short': False},
    'personagesSimple': {'gid': '784166873',  'has_short': True},
    'plekkenSimple':    {'gid': '911735940',  'has_short': False},
    'problemenSimple':  {'gid': '368808453',  'has_short': False},
}

HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
START_MARKER = '    // @@DATA_START@@'
END_MARKER = '    // @@DATA_END@@'


def fetch_tab(name, cfg):
    url = f"{SHEET_BASE}?gid={cfg['gid']}&single=true&output=csv"
    data = urllib.request.urlopen(url).read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(data))
    items = []
    for row in reader:
        text = row['text'].strip()
        if not text:
            continue
        min_age = int(row.get('minAge', '6').strip() or '6')
        if cfg['has_short']:
            short = row.get('short', '').strip()
            items.append({'text': text, 'short': short, 'minAge': min_age})
        else:
            items.append({'text': text, 'minAge': min_age})
    return items


def escape_js(s):
    return s.replace('\\', '\\\\').replace("'", "\\'")


def items_to_js(name, items, has_short):
    lines = [f'    const {name} = [']
    for item in items:
        text = escape_js(item['text'])
        age = item['minAge']
        if has_short:
            short = escape_js(item['short'])
            lines.append(f"        {{ text: '{text}', short: '{short}', minAge: {age} }},")
        else:
            lines.append(f"        {{ text: '{text}', minAge: {age} }},")
    lines.append('    ];')
    return '\n'.join(lines)


def main():
    print('Woordenlijsten ophalen uit Google Sheets...')

    all_js = []
    for name, cfg in TABS.items():
        items = fetch_tab(name, cfg)
        js = items_to_js(name, items, cfg['has_short'])
        all_js.append(js)
        print(f'  {name}: {len(items)} items')

    data_block = '\n\n'.join(all_js)

    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()

    if START_MARKER not in html or END_MARKER not in html:
        print(f'FOUT: markers niet gevonden in {HTML_FILE}')
        sys.exit(1)

    start_idx = html.index(START_MARKER) + len(START_MARKER)
    end_idx = html.index(END_MARKER)

    new_html = html[:start_idx] + '\n\n' + data_block + '\n\n' + html[end_idx:]

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(new_html)

    print(f'\nindex.html bijgewerkt! Vergeet niet te committen en pushen.')


if __name__ == '__main__':
    main()
