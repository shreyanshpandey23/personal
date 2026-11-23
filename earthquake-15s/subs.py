"""Write subtitles_en.srt from the page's subtitle cues (the same numbers the cards use)."""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.environ['LIB']
lines = {l['id']: l['text'] for l in json.load(open(os.path.join(HERE, 'lines.json')))}
dur = json.load(open(os.path.join(HERE, 'voices', 'dur.json')))
ev = [e for e in json.load(open(os.path.join(HERE, 'events.json')))['ev'] if e['type'] == 'voice']
cues = []
for i, e in enumerate(ev):
    t1 = max(e['t'] + dur[e['id']] + .6, e['t'] + 1.8)
    nxt = ev[i + 1]['t'] - .1 if i + 1 < len(ev) else None
    t1 = min(t1 + .5, nxt) if nxt else json.load(open(os.path.join(HERE, 'events.json')))['dur']
    cues.append({'t0': e['t'], 't1': t1, 'text': lines[e['id']]})
json.dump(cues, open(os.path.join(HERE, 'out', 'cues.json'), 'w'))
subprocess.run([os.path.join(LIB, '.venv/bin/python'), os.path.join(LIB, 'core/render/srt.py'), os.path.join(HERE, 'out', 'cues.json'), os.path.join(HERE, 'subtitles_en.srt')], check=True)
