import json
from collections import defaultdict
from datetime import datetime

DATA_PATH = 'data/caer_messages.json'

def coerce_datetime(v):
    if not v:
        return None
    try:
        return datetime.fromisoformat(v)
    except Exception:
        try:
            return datetime.strptime(v, '%m/%d/%Y %I:%M:%S %p')
        except Exception:
            return None

def posted_fields(v):
    dt = coerce_datetime(v)
    if not dt:
        return (str(v or ''), '')
    return (dt.date().isoformat(), dt.strftime('%H:%M:%S'))

def tags_cat(rec):
    tags = rec.get('category') or []
    return '; '.join(tags)


def source_label(url):
    url = (url or '').lower()
    if 'mobile' in url or 'app' in url:
        return 'Mobile API'
    if 'archive' in url:
        return 'Archive'
    return 'Website'


def render_current(records, limit=10):
    active = [r for r in records if r.get('status') != 'cleared']
    active.sort(key=lambda r: r.get('posted_datetime') or '', reverse=True)
    rows = []
    for r in active[:limit]:
        pd, pt = posted_fields(r.get('posted_datetime'))
        rows.append([
            r.get('status',''), r.get('facility',''), pd, pt, tags_cat(r), r.get('message_text',''), r.get('first_seen',''), r.get('last_seen',''), source_label(r.get('source_url','')), 'TRUE' if r.get('previously_seen') else 'FALSE', r.get('message_id','')
        ])
    return rows


def render_new(records, limit=10):
    new = [r for r in records if r.get('status') == 'new']
    new.sort(key=lambda r: r.get('posted_datetime') or '', reverse=True)
    rows = []
    for r in new[:limit]:
        pd, pt = posted_fields(r.get('posted_datetime'))
        rows.append([r.get('status',''), r.get('facility',''), pd, pt, tags_cat(r), r.get('message_text',''), r.get('first_seen',''), r.get('last_seen',''), source_label(r.get('source_url','')), 'TRUE' if r.get('previously_seen') else 'FALSE', r.get('message_id','')])
    return rows


def render_still_posted(records, limit=10):
    s = [r for r in records if r.get('status') == 'previous message still posted']
    s.sort(key=lambda r: r.get('posted_datetime') or '', reverse=True)
    rows=[]
    for r in s[:limit]:
        pd, pt = posted_fields(r.get('posted_datetime'))
        rows.append([r.get('facility',''), pd, pt, tags_cat(r), r.get('message_text',''), r.get('first_seen',''), r.get('last_seen',''), str(len(r.get('versions') or [])), source_label(r.get('source_url',''))])
    return rows


def render_cleared(records, limit=10):
    c = [r for r in records if r.get('status') == 'cleared']
    c.sort(key=lambda r: r.get('posted_datetime') or '', reverse=True)
    rows=[]
    for r in c[:limit]:
        pd, pt = posted_fields(r.get('posted_datetime'))
        first = coerce_datetime(r.get('first_seen'))
        last = coerce_datetime(r.get('last_seen'))
        dur = ''
        if first and last:
            dur = f"{(last-first).total_seconds()/86400:.2f} days"
        rows.append([r.get('facility',''), pd, pt, tags_cat(r), r.get('message_text',''), r.get('first_seen',''), r.get('last_seen',''), r.get('last_seen',''), dur, source_label(r.get('source_url',''))])
    return rows


def render_app_vs_website(records, limit=10):
    byid = defaultdict(list)
    for r in records:
        byid[r.get('message_id')].append(r)
    rows=[]
    for mid, bucket in list(byid.items())[:limit]:
        rep = bucket[0]
        srcs = set(source_label(b.get('source_url')) for b in bucket)
        pd, pt = posted_fields(rep.get('posted_datetime'))
        first = min((b.get('first_seen') for b in bucket if b.get('first_seen')), default='')
        last = max((b.get('last_seen') for b in bucket if b.get('last_seen')), default='')
        rows.append([mid, rep.get('facility',''), (pd+' '+pt).strip(), 'TRUE' if 'Website' in srcs else 'FALSE', 'TRUE' if 'Mobile API' in srcs else 'FALSE', first, last, tags_cat(rep), rep.get('message_text','')])
    return rows


def main():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception as e:
        print('Unable to read data file:', e)
        return

    out = []
    out.append('=== Current Messages (sample) ===')
    for r in render_current(data):
        out.append('|'.join(r))
    out.append('\n=== New Messages (sample) ===')
    for r in render_new(data):
        out.append('|'.join(r))
    out.append('\n=== Still Posted (sample) ===')
    for r in render_still_posted(data):
        out.append('|'.join(r))
    out.append('\n=== Cleared Messages (sample) ===')
    for r in render_cleared(data):
        out.append('|'.join(r))
    out.append('\n=== App vs Website (sample) ===')
    for r in render_app_vs_website(data):
        out.append('|'.join(r))

    preview = '\n'.join(out)
    with open('scripts/output_preview.txt', 'w', encoding='utf-8') as fh:
        fh.write(preview)
    print('Preview written to scripts/output_preview.txt')

if __name__ == '__main__':
    main()
